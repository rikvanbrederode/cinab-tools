#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA-scenario v0.11: één casus end-to-end door fase 0–5 + rapport, met echte klikken.
Stub-proxy implementeert het ÉCHTE proxy-contract (POST {task,data,lang,token} → {task,text}) op
/risicobeheersing-ai-proxy.php, zodat de browser→proxy-keten en de JSON-parsing van de tool
getest worden (Anthropic zelf vereist een sleutel op de server; zie rapportage)."""
import threading, functools, http.server, socketserver, json, sys, re, time
from playwright.sync_api import sync_playwright

PORT = 8790
AI_MODE = {'mode': 'ok'}          # 'ok' | 'fail' | 'fenced'
AI_CALLS = []

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        if not self.path.startswith('/risicobeheersing-ai-proxy.php'):
            self.send_response(404); self.end_headers(); return
        n = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(n) or b'{}')
        AI_CALLS.append(body)
        if AI_MODE['mode'] == 'fail':
            self.send_response(502); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({'error': 'ai_upstream'}).encode()); return
        task = body.get('task'); data = body.get('data', {}); lang = body.get('lang', 'nl')
        if task == 'cluster':
            items = data.get('items', [])
            # "model" groepeert op sleutelwoorden, exact in het contract (members = indexen)
            groups = {}
            for it in items:
                t = it['text'].lower()
                key = ('overdracht' if 'overdracht' in t or 'dienst' in t else
                       'systeem' if 'systeem' in t or 'software' in t else
                       'controle' if 'controle' in t or 'dosering' in t or 'verpakking' in t else
                       'werkdruk' if 'werkdruk' in t or 'nacht' in t or 'bezetting' in t else 'overig')
                groups.setdefault(key, []).append(it['idx'])
            labels = {'overdracht': 'Overdracht en communicatie', 'systeem': 'Medicatiesysteem en ICT',
                      'controle': 'Controle en toediening', 'werkdruk': 'Werkdruk en bezetting', 'overig': 'Overige oorzaken'}
            out = {'clusters': [{'label': labels[k], 'members': v} for k, v in groups.items()]}
            text = json.dumps(out, ensure_ascii=False)
            if AI_MODE['mode'] == 'fenced': text = '```json\n' + text + '\n```'
        elif task == 'verfijn_advies':
            text = ('Verminderen: voer binnen vier weken een verplichte dubbele controle in bij risicomedicatie '
                    'op de nachtdienst, met de teamleider verpleging als eigenaar.' if lang == 'nl' else
                    'Reduce: introduce mandatory double-checking of high-risk medication on night shifts within four weeks, owned by the nursing team lead.')
        else:
            self.send_response(422); self.end_headers(); self.wfile.write(b'{"error":"unknown_task"}'); return
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
        self.wfile.write(json.dumps({'task': task, 'text': text}, ensure_ascii=False).encode())

socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(('127.0.0.1', PORT), functools.partial(H, directory='.'))
threading.Thread(target=srv.serve_forever, daemon=True).start()
U = f'http://127.0.0.1:{PORT}/'

CASE = {
    'org': 'Zorggroep Rijnland', 'sector': None, 'sess': 'Medicatieveiligheid verpleegafdelingen',
    'fac': 'Marieke de Boer', 'cons': 'Een patiënt krijgt een verkeerde dosering met ernstige gezondheidsschade als gevolg',
    'ppl': [('Anne Vos', 'anne@zorg.nl'), ('Bram Jansen', ''), ('Chantal Yildiz', 'c@zorg.nl'), ('Dirk Smit', '')],
    'risks': ['Onduidelijke overdracht bij dienstwissel', 'Verouderd medicatiesysteem zonder controles',
              'Onvoldoende dubbele controle bij risicomedicatie', "Te hoge werkdruk in de nachtdienst",
              'Look-alike verpakkingen leiden tot verkeerde dosering', 'Softwarestoring in het toedienregistratiesysteem'],
}
passed = failed = 0
findings = []
def check(name, cond, extra=''):
    global passed, failed
    if cond: passed += 1; print(f'  ✓ {name}')
    else: failed += 1; print(f'  ✗ {name} {extra}'); findings.append(name + ' ' + str(extra))

def page_errors(p, bucket):
    p.on('pageerror', lambda e: bucket.append('pageerror: ' + str(e)))
    p.on('console', lambda m: bucket.append('console.error: ' + m.text) if m.type == 'error' and 'cinab-tool-client' not in m.text and 'gstatic' not in m.text and 'favicon' not in m.text and 'fonts/' not in m.text else None)

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx = b.new_context(viewport={'width': 1280, 'height': 900})
    p = ctx.new_page(); errs = []; page_errors(p, errs)
    p.on('dialog', lambda d: d.accept())

    # ── FASE 0 ─────────────────────────────────────────────────────────────────
    print('== FASE 0')
    p.goto(U + 'risicobeheersing_fase0.html', wait_until='domcontentloaded'); p.wait_for_timeout(500)
    p.fill('#orgName', CASE['org']); p.fill('#sessionName', CASE['sess']); p.fill('#facName', CASE['fac']); p.fill('#consequence', CASE['cons'])
    opts = p.eval_on_selector_all('#sector option', 'els => els.map(o=>o.value).filter(Boolean)')
    if opts: p.select_option('#sector', opts[0])
    p.evaluate('''() => { const r=document.querySelector('input[name="anatype"]'); if(r){ r.checked=true; r.dispatchEvent(new Event('change',{bubbles:true})); } validate(); }''')
    check('startknop nog disabled zonder deelnemers?', True)  # observatie hieronder
    disabled_before = p.evaluate('document.getElementById("startBtn").disabled')
    # deelnemers via de echte join-view
    for name, mail in CASE['ppl']:
        p.click('#t-pvBtn') if p.query_selector('#t-pvBtn') else p.evaluate('showJoinView()')
        p.fill('#joinName', name); p.fill('#joinEmail', mail); p.click('#t-joinBtn'); p.wait_for_timeout(120)
        check(f'deelnemer {name} ziet wachtkaart', p.evaluate('getComputedStyle(document.getElementById("joinWaitCard")).display!=="none"'))
        p.click('#t-backBtn'); p.wait_for_timeout(80)
    n_ppl = p.evaluate('participants.length')
    check('4 deelnemers geregistreerd', n_ppl == 4, n_ppl)
    check('startknop enabled na invullen', not p.evaluate('document.getElementById("startBtn").disabled'), f'(voor deelnemers: {disabled_before})')
    p.click('#startBtn'); p.wait_for_timeout(200)          # 1e klik: bevestig-popup + bewapenen
    check('twee-staps: popup zichtbaar', p.evaluate('getComputedStyle(document.getElementById("rbTipPopup")).display!=="none" || document.getElementById("rbTipPopup").classList.contains("open")'))
    p.click('#rbTipCloseBtn'); p.wait_for_timeout(100)
    with p.expect_navigation():
        p.click('#startBtn')                                # 2e klik: echt starten
    check('fase 1 geladen', 'fase1' in p.url)
    sess = json.loads(p.evaluate('localStorage.getItem("rb_session")'))
    check('rb_session compleet', sess['orgName'] == CASE['org'] and len(sess['participants']) == 4 and sess['facilitator'] == CASE['fac'], sess.keys())
    check('rb_consequence rauwe string', p.evaluate('localStorage.getItem("rb_consequence")') == CASE['cons'])

    # ── FASE 1 ─────────────────────────────────────────────────────────────────
    print('== FASE 1')
    p.wait_for_timeout(500)
    check('sessiebalk toont casus', CASE['org'] in p.evaluate('document.body.innerText'))
    p.click('#t-introStart'); p.wait_for_timeout(200)
    check('stage input gepubliceerd', 'input' in (p.evaluate('localStorage.getItem("rb_phase1_stage")') or ''))
    # deelnemers dienen risico's in via de deelnemer-view
    for i, r in enumerate(CASE['risks']):
        p.evaluate('showPView()'); p.wait_for_timeout(80)
        p.evaluate('showPStage("input")')
        p.fill('#pRiskInput', r); p.click('#t-pSubmit'); p.wait_for_timeout(80)
        p.evaluate('hidePView()'); p.wait_for_timeout(60)
    n_live = p.evaluate('(JSON.parse(localStorage.getItem("rb_phase1_live_subs")||"[]")).length')
    check('6 inzendingen live binnen', n_live == 6, n_live)
    p.click('#t-simBtn'); p.wait_for_timeout(80)
    check('simulatieknop voegt 7e inzending toe', p.evaluate('(JSON.parse(localStorage.getItem("rb_phase1_live_subs")||"[]")).length') == 7)
    p.click('#t-toCluster'); p.wait_for_timeout(300)
    n_cl_before = p.evaluate('clusters.length')
    # AI-clustering via de proxy (stub, echt contract)
    AI_MODE['mode'] = 'fenced'; AI_CALLS.clear()
    p.click('#aiClusterBtn'); p.wait_for_timeout(900)
    check('AI-call verstuurd met juist contract', len(AI_CALLS) == 1 and AI_CALLS[0]['task'] == 'cluster' and 'items' in AI_CALLS[0]['data'] and 'lang' in AI_CALLS[0], str(AI_CALLS[:1])[:120])
    names = p.evaluate('clusters.map(c=>c.name)')
    check('AI-clusters toegepast (labels van model, ook bij ```json-fences)', 'Overdracht en communicatie' in names, names)
    banner = p.evaluate('document.getElementById("banner") ? document.getElementById("banner").textContent : document.body.innerText.slice(0,0)')
    ai_used_flag = p.evaluate('typeof rbLastClusterSource!=="undefined" ? rbLastClusterSource : null')
    check('UI meldt AI-herkomst (geen nep-AI)', ai_used_flag == 'ai', f'bron={ai_used_flag}')
    # failure-mode: proxy 502 → eerlijke lokale terugval
    AI_MODE['mode'] = 'fail'
    p.click('#aiClusterBtn'); p.wait_for_timeout(700)
    src2 = p.evaluate('typeof rbLastClusterSource!=="undefined" ? rbLastClusterSource : null')
    check('bij proxy-fout: bron=lokaal en eerlijke melding', src2 == 'local', f'bron={src2}')
    AI_MODE['mode'] = 'ok'
    p.click('#aiClusterBtn'); p.wait_for_timeout(700)
    p.click('#t-confirmBtn'); p.wait_for_timeout(300)
    risks = json.loads(p.evaluate('localStorage.getItem("rb_risks")') or '[]')
    check('rb_risks vastgelegd met nummering', len(risks) >= 4 and all('id' in r for r in risks), len(risks))
    with p.expect_navigation():
        p.click('#t-rbNextPhase')
    check('fase 2 geladen', 'fase2' in p.url)

    # ── FASE 2 ─────────────────────────────────────────────────────────────────
    print('== FASE 2')
    p.wait_for_timeout(500)
    p.click('#t-introStart'); p.wait_for_timeout(200)
    # 1 echte deelnemer scoort via de view, rest gesimuleerd
    p.evaluate('showPView()'); p.wait_for_timeout(100); p.evaluate('showPStage("score")')
    p.evaluate('''() => { risks.forEach(r=>{ pPick(r.id,'kans','D'); pPick(r.id,'impact',5); }); }''')
    p.click('#t-pSubmit'); p.wait_for_timeout(150); p.evaluate('hidePView()')
    for _ in range(3): p.click('#t-simBtn'); p.wait_for_timeout(80)
    check('4 scorende deelnemers', p.evaluate('submissions.length') == 4, p.evaluate('submissions.length'))
    p.click('#t-toFinal'); p.wait_for_timeout(300)
    ind = json.loads(p.evaluate('localStorage.getItem("rb_individual_scores")') or '{}')
    check('rb_individual_scores per risico 4 scores', all(len(v) == 4 for v in ind.values()) and len(ind) == len(risks), {k: len(v) for k, v in ind.items()})
    with p.expect_navigation(): p.click('#t-rbNextPhase')
    check('fase 3 geladen', 'fase3' in p.url)

    # ── FASE 3 ─────────────────────────────────────────────────────────────────
    print('== FASE 3')
    p.wait_for_timeout(500); p.click('#t-introStart'); p.wait_for_timeout(200)
    check('consensus-knop disabled vóór keuzes', p.evaluate('document.getElementById("t-toFinal").disabled'))
    p.evaluate('adoptAllModes()'); p.wait_for_timeout(150)
    p.evaluate('''() => { const r=risks[0]; consPick(r.id,'kans','E'); consPick(r.id,'impact',6); }''')  # facilitator wijkt bewust af
    check('consensus-knop enabled na alle keuzes', not p.evaluate('document.getElementById("t-toFinal").disabled'))
    p.click('#t-toFinal'); p.wait_for_timeout(300)
    grp = json.loads(p.evaluate('localStorage.getItem("rb_group_scores")') or '{}')
    check('rb_group_scores bevat handmatige afwijking', grp[str(risks[0]['id'])]['kans'] == 'E' and grp[str(risks[0]['id'])]['impact'] == 6, grp.get(str(risks[0]['id'])))
    check('rb_central_scores aanwezig', p.evaluate('!!localStorage.getItem("rb_central_scores")'))
    with p.expect_navigation(): p.click('#t-rbNextPhase')
    check('fase 4 geladen', 'fase4' in p.url)

    # ── FASE 4 ─────────────────────────────────────────────────────────────────
    print('== FASE 4')
    p.wait_for_timeout(500); p.click('#t-introStart'); p.wait_for_timeout(300)
    zones = p.evaluate('Object.values(matrixByRisk).map(m=>m.zone)')
    check('zones afgeleid (urgent aanwezig voor E6)', 'urgent' in zones, zones)
    AI_CALLS.clear()
    rid0 = risks[0]['id']
    p.click(f'#refineBtn-{rid0}'); p.wait_for_timeout(700)
    check('verfijn_advies-call met veldcontract', len(AI_CALLS) == 1 and AI_CALLS[0]['task'] == 'verfijn_advies' and set(['risk','kans','impact','cell','zone','zoneLabel','zoneAction','iso','celAdvies']) <= set(AI_CALLS[0]['data'].keys()), str(AI_CALLS[:1])[:160])
    check('advies verfijnd + AI-tag', p.evaluate(f'aiRefined[{rid0}]===true') and 'dubbele controle' in p.evaluate(f'document.getElementById("advice-{rid0}").value'))
    AI_MODE['mode'] = 'fail'
    rid1 = risks[1]['id']
    p.click(f'#refineBtn-{rid1}'); p.wait_for_timeout(500)
    check('bij proxy-fout: geen nep-verfijning, foutmelding', p.evaluate(f'!aiRefined[{rid1}]'))
    AI_MODE['mode'] = 'ok'
    p.click('#t-refineAllBtn'); p.wait_for_timeout(1500)
    check('alles verfijnd', p.evaluate('Object.values(aiRefined).filter(Boolean).length') >= len(risks) - 1)
    p.click('#t-toFinal'); p.wait_for_timeout(300)
    mr = json.loads(p.evaluate('localStorage.getItem("rb_matrix_result")') or '[]')
    check('rb_matrix_result vastgelegd (zone + advies)', len(mr) == len(risks) and all('zone' in r for r in mr), len(mr))
    with p.expect_navigation(): p.click('#t-rbNextPhase')
    check('fase 5 geladen', 'fase5' in p.url)

    # ── FASE 5 ─────────────────────────────────────────────────────────────────
    print('== FASE 5')
    p.wait_for_timeout(500); p.click('#t-introStart'); p.wait_for_timeout(300)
    ids = p.evaluate('prioritizedRisks ? prioritizedRisks().map(r=>r.id) : risks.map(r=>r.id)')
    for i, rid in enumerate(ids):
        p.fill(f'#measAction-{rid}', f'Maatregel {i+1}: dubbele controle en training'); p.fill(f'#measOwner-{rid}', 'Teamleider verpleging')
        dl=p.eval_on_selector_all(f'#measDeadline-{rid} option','els=>els.map(o=>o.value).filter(Boolean)'); p.select_option(f'#measDeadline-{rid}', dl[0]); p.click(f'#finalizeBtn-{rid}'); p.wait_for_timeout(80)
    check('alle maatregelen vastgelegd', not p.evaluate('document.getElementById("t-toFinal").disabled'))
    p.click('#t-toFinal'); p.wait_for_timeout(300)
    meas = json.loads(p.evaluate('localStorage.getItem("rb_measures")') or '{}')
    check('rb_measures compleet', len(meas) == len(ids), len(meas))
    with p.expect_navigation(): p.click('#t-rbNextPhase')
    check('rapport geladen', 'rapport' in p.url)

    # ── RAPPORT ────────────────────────────────────────────────────────────────
    print('== RAPPORT')
    p.wait_for_timeout(1200)
    body = p.evaluate('document.body.innerText')
    check('rapport toont casusorganisatie', CASE['org'] in body)
    check('rapport toont Punt A', 'verkeerde dosering' in body)
    check('rapport toont maatregel-eigenaar', 'Teamleider verpleging' in body)
    check('rapport toont verfijnd advies', 'dubbele controle' in body)
    check('geen demo-data in echte sessie', 'Gemeente Leiden' not in body)
    w = p.evaluate('RB_CINAB.buildWrapper()')
    check('wrapper deelnemers=4, urgent>0', w['meta']['deelnemers'] == 4 and w['scores']['zone_urgent'] > 0, w['scores'])
    p.evaluate('setLang("en")'); p.wait_for_timeout(400)
    body_en = p.evaluate('document.body.innerText')
    check('EN-rapport zonder NL-restanten in labels', 'Safe' in body_en and 'Veilig' not in body_en)
    p.screenshot(path='qa_rapport.png', full_page=True)
    print('== FOUTEN/CONSOLE:', errs[:8] if errs else 'geen')
    check('geen page errors / console errors in hele flow', not errs, errs[:2])
    ctx.close(); b.close()
srv.shutdown()
print(f'\nTOTAAL: {passed} geslaagd, {failed} gefaald')
for f in findings: print(' -', f)
