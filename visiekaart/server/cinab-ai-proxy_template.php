<?php
/**
 * cinab-ai-proxy.template.php — generiek server-side AI-proxy-template voor CINAB methodiek-apps.
 *
 * Doel: de Anthropic-sleutel blijft server-side. De browser stuurt ALLEEN gestructureerde sessiedata
 * + een taaktype; de prompt wordt hier server-side opgebouwd (voorkomt "prompt-as-a-service"/injectie).
 *
 * ════════════════════════════════════════════════════════════════════════════════════════════════
 *  PER APP INVULLEN (zoek op [INVULLEN]):
 *    1. $ALLOWED_ORIGINS        → de tool-subdomeinen van deze app (productie + staging).
 *    2. ANTHROPIC_MODEL         → het gelicentieerde model voor deze app.
 *    3. build_prompt()          → voeg de app-specifieke taken toe (skelet onderaan). 'cluster' is
 *                                 generiek en mag blijven staan als de app clustert.
 *    4. Hernoem dit bestand naar {tool}-ai-proxy.php en zet het op het tool-subdomein.
 *
 *  PRODUCTIE-SCHAKELAARS (niet vergeten vóór go-live):
 *    • CINAB_REQUIRE_TOKEN = true   (op staging tijdelijk false om end-to-end te testen)
 *    • CINAB_VALIDATE_URL  = de PRODUCTIE-url (cinab.nl), niet staging2
 *    • De sleutel staat NOOIT in dit bestand: env-var of een config BOVEN de webroot.
 * ════════════════════════════════════════════════════════════════════════════════════════════════
 *
 * Beveiliging (defense-in-depth; CORS is GEEN poort):
 *   - POST-only, payload-limiet 1 MB (413)
 *   - Origin/Referer-check tegen een whitelist
 *   - CINAB-sessietoken VERPLICHT in productie: non-consuming gevalideerd tegen /validate-token. De poort.
 *   - Rate-limiting per IP (voeg een token-dimensie toe zodra tokens stromen)
 *   - Model + max_tokens server-side vastgezet (de browser kiest niets duurs)
 */

// ── 0. Config laden — sleutel NOOIT hier hardcoderen ───────────────────────────
// Voorkeur 1: env-var.  Voorkeur 2: een config-bestand BOVEN de webroot.
$ANTHROPIC_API_KEY = getenv('ANTHROPIC_API_KEY');
if (!$ANTHROPIC_API_KEY) {
  // Bv. /home/<account>/cinab-secrets.php  →  <?php return ['anthropic_key' => 'sk-ant-...'];
  $secretsFile = __DIR__ . '/../cinab-secrets.php';
  if (is_readable($secretsFile)) {
    $secrets = include $secretsFile;
    $ANTHROPIC_API_KEY = $secrets['anthropic_key'] ?? '';
  }
}

const ANTHROPIC_MODEL      = '[INVULLEN: gelicentieerd model, bv. claude-sonnet-4-6]';
const ANTHROPIC_VERSION    = '2023-06-01';
const ANTHROPIC_MAX_TOKENS = 2000;                       // server-side plafond
const MAX_BODY_BYTES       = 1048576;                    // 1 MB → 413

// Tool-origins die mogen aanroepen (defense-in-depth, geen poort)
$ALLOWED_ORIGINS = [
  'https://[INVULLEN].cinab.nl',           // productie-subdomein
  'https://staging.[INVULLEN].cinab.nl',   // staging-subdomein
];

// CINAB-platform: non-consuming token-validatie.
//   STAGING  : https://staging2.cinab.nl/wp-json/cinab/v1/validate-token
//   PRODUCTIE: https://cinab.nl/wp-json/cinab/v1/validate-token   ← zet dit in productie
const CINAB_VALIDATE_URL  = 'https://staging2.cinab.nl/wp-json/cinab/v1/validate-token';
// ⚠ In PRODUCTIE ALTIJD true. Alleen op STAGING tijdelijk false om AI te testen vóór de koppeling.
const CINAB_REQUIRE_TOKEN = false;  // ← STAGING-instelling; ZET OP true IN PRODUCTIE

const RATE_LIMIT_PER_MIN  = 20;     // per IP per minuut
const RATE_DIR            = '/tmp/cinab_ai_rate';

// ── helpers ────────────────────────────────────────────────────────────────────
function send($code, $payload) {
  http_response_code($code);
  header('Content-Type: application/json; charset=utf-8');
  echo json_encode($payload, JSON_UNESCAPED_UNICODE);
  exit;
}

function clientIp() {
  // Achter een proxy (bv. SiteGround): vertrouw X-Forwarded-For met mate.
  $xff = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? '';
  if ($xff) { $parts = explode(',', $xff); return trim($parts[0]); }
  return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
}

// ── 1. CORS / preflight (alleen whitelisted origins) ────────────────────────────
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin && in_array($origin, $ALLOWED_ORIGINS, true)) {
  header('Access-Control-Allow-Origin: ' . $origin);
  header('Vary: Origin');
  header('Access-Control-Allow-Headers: Content-Type, X-CINAB-Token');
  header('Access-Control-Allow-Methods: POST, OPTIONS');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') { http_response_code(204); exit; }

// ── 2. Method + origin-poort (defense-in-depth) ─────────────────────────────────
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') send(405, ['error' => 'method_not_allowed']);

$referer = $_SERVER['HTTP_REFERER'] ?? '';
$originOk = ($origin && in_array($origin, $ALLOWED_ORIGINS, true));
$refOk    = false;
foreach ($ALLOWED_ORIGINS as $o) { if ($referer && strpos($referer, $o) === 0) { $refOk = true; break; } }
if (!$originOk && !$refOk) send(403, ['error' => 'bad_origin']);

// ── 3. Payload-limiet (413) ─────────────────────────────────────────────────────
$raw = file_get_contents('php://input', false, null, 0, MAX_BODY_BYTES + 1);
if (strlen($raw) > MAX_BODY_BYTES) send(413, ['error' => 'payload_too_large']);
$body = json_decode($raw, true);
if (!is_array($body)) send(422, ['error' => 'invalid_json']);

// ── 4. Rate-limiting per IP (eenvoudige file-bucket; voeg token-dimensie toe in prod) ──
@mkdir(RATE_DIR, 0700, true);
$ip = clientIp();
$bucket = RATE_DIR . '/' . md5($ip) . '_' . floor(time() / 60);
$count = is_readable($bucket) ? (int) file_get_contents($bucket) : 0;
if ($count >= RATE_LIMIT_PER_MIN) send(429, ['error' => 'rate_limited']);
@file_put_contents($bucket, $count + 1, LOCK_EX);

// ── 5. Token-validatie — DE poort (non-consuming) ───────────────────────────────
$token = $body['token'] ?? ($_SERVER['HTTP_X_CINAB_TOKEN'] ?? '');
if (CINAB_REQUIRE_TOKEN) {
  if (!$token) send(401, ['error' => 'missing_token']);
  $vr = http_post_json(CINAB_VALIDATE_URL, ['token' => $token], null, 6);
  if ($vr['status'] !== 200) send(401, ['error' => 'invalid_token']);
}

// ── 6. Sleutel aanwezig? ─────────────────────────────────────────────────────────
if (!$ANTHROPIC_API_KEY) send(500, ['error' => 'server_misconfigured']);

// ── 7. Taak → prompt server-side opbouwen ───────────────────────────────────────
$task = $body['task'] ?? '';
$lang = ($body['lang'] ?? 'nl') === 'en' ? 'en' : 'nl';
$data = $body['data'] ?? [];

$prompt = build_prompt($task, $data, $lang);
if ($prompt === null) send(422, ['error' => 'unknown_task']);

// ── 8. Anthropic aanroepen ───────────────────────────────────────────────────────
$payload = [
  'model'      => ANTHROPIC_MODEL,
  'max_tokens' => ANTHROPIC_MAX_TOKENS,
  'messages'   => [['role' => 'user', 'content' => $prompt]],
];
$resp = http_post_json('https://api.anthropic.com/v1/messages', $payload, [
  'x-api-key: ' . $ANTHROPIC_API_KEY,
  'anthropic-version: ' . ANTHROPIC_VERSION,
], 30);

if ($resp['status'] !== 200) {
  // Geef de tool een nette code zodat hij kan terugvallen op de lokale berekening.
  send(502, ['error' => 'ai_upstream', 'upstream_status' => $resp['status']]);
}
$j = json_decode($resp['body'], true);
$text = '';
foreach (($j['content'] ?? []) as $block) {
  if (($block['type'] ?? '') === 'text') $text .= $block['text'];
}
send(200, ['task' => $task, 'text' => $text]);

// ════════════════════════════════════════════════════════════════════════════════
//  PROMPT-TEMPLATES (server-side; breid uit per taak)
//  Contract met de tool: vraag ALTIJD om strikte JSON ("UITSLUITEND geldige JSON, geen extra tekst").
//  De tool parse't dat en valt bij twijfel terug op zijn lokale berekening.
// ════════════════════════════════════════════════════════════════════════════════
function build_prompt($task, $data, $lang) {

  // ── GENERIEK & HERBRUIKBAAR — laat staan als de app vrije antwoorden clustert ──
  // Clustering van vrije antwoorden/thema's/acties. Contract: members = 0-gebaseerde
  // indexen in de aangeleverde items-array (de tool koppelt index → item terug).
  if ($task === 'cluster') {
    $items    = json_encode($data['items'] ?? [], JSON_UNESCAPED_UNICODE);
    $question = trim((string) ($data['question'] ?? ''));
    $context  = trim((string) ($data['context']  ?? ''));
    $taal     = $lang === 'en' ? 'English' : 'Nederlands';

    // Context-blok: de tool stuurt de vraag en de fase-intentie mee. Zonder die twee
    // clustert het model op woordvorm en worden labels losse werkwoorden.
    $intro = '';
    if ($context  !== '') { $intro .= "Context van de sessie:\n{$context}\n\n"; }
    if ($question !== '') { $intro .= "De vraag die aan de deelnemers is gesteld:\n\"{$question}\"\n\n"; }

    return
      "Je bent een ervaren strategisch facilitator. Hieronder staan de antwoorden van deelnemers ".
      "op één vraag. Werk in {$taal}.\n\n".
      $intro.
      "Antwoorden (genummerd vanaf 0):\n{$items}\n\n".
      "Werkwijze:\n".
      "1. Lees per antwoord wat de deelnemer INHOUDELIJK BEDOELT in het licht van de vraag ".
      "en de context. Kijk naar het onderwerp waarover het gaat, niet naar de woordvorm, ".
      "de zinsbouw of toevallig gedeelde woorden.\n".
      "2. Voeg antwoorden samen die over hetzelfde onderwerp gaan, ook als ze heel andere ".
      "woorden gebruiken. Splits antwoorden die dezelfde woorden gebruiken maar over iets ".
      "anders gaan.\n".
      "3. Geef elk cluster een naam die de gemeenschappelijke NOEMER van die antwoorden ".
      "benoemt, niet slechts één van de antwoorden.\n\n".
      "Regels voor de clusters:\n".
      "- Maak 2 tot 4 clusters (afhankelijk van de variatie); liever te weinig dan te veel.\n".
      "- Elk antwoord komt in PRECIES één cluster; gebruik elke index 0..n-1 exact één keer.\n".
      "- 'members' zijn de indexen (gehele getallen) van de antwoorden in dat cluster.\n\n".
      "Regels voor 'label' (de clusternaam):\n".
      "- Een zelfstandig naamwoord of een naamwoordgroep, 1 tot 4 woorden. ".
      "Bijvoorbeeld: \"Wendbaarheid van de organisatie\", \"Vertrouwen van klanten\", \"Regie op data\".\n".
      "- NOOIT een kaal werkwoord of een infinitief als naam. Dus niet \"krijgen\", \"zorgen\", ".
      "\"verbeteren\", \"samenwerken\". Maak er een naamwoord van: \"samenwerking\", \"verbetering ".
      "van de dienstverlening\".\n".
      "- NOOIT een losse zin, een vraag, een werkwoordelijke zin of een letterlijke kopie van ".
      "één antwoord.\n".
      "- Geen leestekens aan het eind, geen aanhalingstekens, geen nummering.\n".
      "- De naam moet ALLE antwoorden in dat cluster dekken. Dekt hij er maar één, kies dan ".
      "een ruimere naam of splits het cluster.\n".
      "- Begin met een hoofdletter; verder normale spelling.\n\n".
      "Geef UITSLUITEND geldige JSON terug, geen extra tekst, exact in deze vorm:\n".
      '{"clusters":[{"label":"","members":[0,1]}]}';
  }

  // ── VISIEKAART fase 5: roadmap-prioritering (B-23, testprotocol 2026-09-03) ──
  // Contract (tool → proxy): {stip, themes:[{name,score}], acties:[{text,themeName}],
  //   versnellers:[..], remmers:[..], sessie:{urgentie, periodes}}
  // Contract (proxy → tool): {"actions":[{"text":"","priorityScore":0,"justif":"","owner":""}]}
  // De tool legt alleen priorityScore/justif/owner over zijn eigen deterministische structuur.
  if ($task === 'roadmap') {
    $stip   = trim((string) ($data['stip'] ?? ''));
    $themes = json_encode($data['themes'] ?? [], JSON_UNESCAPED_UNICODE);
    $acties = json_encode($data['acties'] ?? [], JSON_UNESCAPED_UNICODE);
    $vers   = json_encode($data['versnellers'] ?? [], JSON_UNESCAPED_UNICODE);
    $rem    = json_encode($data['remmers'] ?? [], JSON_UNESCAPED_UNICODE);
    $sessie = json_encode($data['sessie'] ?? new stdClass(), JSON_UNESCAPED_UNICODE);
    $taal   = $lang === 'en' ? 'English' : 'Nederlands';
    return
      "Je bent een ervaren strategisch adviseur. Een team heeft in een werksessie een stip op de ".
      "horizon, thema's, acties, versnellers en remmers vastgesteld. Werk in {$taal}.\n\n".
      "Stip op de horizon:\n\"{$stip}\"\n\n".
      "Thema's (met stemscore):\n{$themes}\n\n".
      "Acties (met thema):\n{$acties}\n\n".
      "Versnellers (sterke punten):\n{$vers}\n\nRemmers (aandachtspunten):\n{$rem}\n\n".
      "Sessiecontext (urgentiefactor, aantal periodes in de tijdlijn):\n{$sessie}\n\n".
      "Opdracht: geef per actie een prioriteitsscore van 0 tot 100 (hoger = eerder oppakken), ".
      "een korte onderbouwing (één zin, concreet, verwijst naar de stip, een versneller of een remmer) ".
      "en een voorstel voor de eigenaar (functie of rol, geen persoonsnaam).\n".
      "Regels:\n".
      "- Neem ELKE actie precies één keer op, met exact dezelfde 'text' als aangeleverd.\n".
      "- Acties die een remmer wegnemen of direct aan de stip bijdragen scoren hoger; ".
      "acties die op een versneller steunen zijn sneller haalbaar.\n".
      "- Geen aanhalingstekens of kopjes in 'justif'; geen nummering; maximaal 160 tekens.\n\n".
      "Geef UITSLUITEND geldige JSON terug, geen extra tekst, exact in deze vorm:\n".
      '{"actions":[{"text":"","priorityScore":0,"justif":"","owner":""}]}';
  }

  // ── [INVULLEN] APP-SPECIFIEKE TAKEN ───────────────────────────────────────────
  // Patroon: lees velden uit $data, bouw de prompt server-side, eis strikte JSON terug.
  // Kopieer dit skelet per taak, hernoem 'mijn_taak' en vul in. Verwijder het als ongebruikt.
  /*
  if ($task === 'mijn_taak') {
    $veldA = (string) ($data['veldA'] ?? '');
    $lijst = json_encode($data['lijst'] ?? [], JSON_UNESCAPED_UNICODE);
    $taal  = $lang === 'en' ? 'English' : 'Nederlands';
    return
      "Je bent een ... . Werk in {$taal}.\n".
      "Invoer A: {$veldA}\nLijst: {$lijst}\n\n".
      "Geef UITSLUITEND geldige JSON terug, geen extra tekst, exact in deze vorm:\n".
      '{"resultaat":[{"id":"","...":""}]}';
  }
  */

  return null;  // onbekende taak → 422 (de tool valt terug op lokaal)
}

// Eenvoudige cURL JSON-POST-helper (hergebruikt voor validate-token én Anthropic).
function http_post_json($url, $payload, $extraHeaders, $timeout) {
  $headers = array_merge(['Content-Type: application/json'], $extraHeaders ?: []);
  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE),
    CURLOPT_HTTPHEADER     => $headers,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => $timeout,
    CURLOPT_CONNECTTIMEOUT => 8,
  ]);
  $resp = curl_exec($ch);
  $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
  curl_close($ch);
  return ['status' => (int) $status, 'body' => (string) $resp];
}
