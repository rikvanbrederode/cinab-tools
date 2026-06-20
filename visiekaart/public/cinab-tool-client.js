/**
 * CINAB tool-client — route 2 (ADR 0006), contract werkboek v3.1.
 *
 * Framework-agnostische browser-client voor het koppelen van een tool aan het
 * CINAB-platform. Geen HMAC en geen eigen backend nodig: de tool wisselt de
 * launch-code uit de URL in voor een sessietoken en praat daarmee met de
 * REST API van WordPress. Werkt dus ook op statische hosts.
 *
 * Tool-agnostisch: bevat geen enkele tool-specifieke aanname. De inhoud van
 * `data` is opaak voor het platform — precies wat jouw eigen /render nodig heeft.
 *
 * Dekt het volledige v3.1-contract:
 *   - launch-code → POST /start-tool  → { token, betaal_vanaf_fase, credits }
 *   - POST /validate-token            (non-consuming, TK-6)
 *   - POST /saldo                     (advisory poort-check; token in de body)
 *   - POST /sessie-afrekenen          (atomisch + idempotent; 402 → payment_url)
 *   - POST /rapport-opslaan           (dunne wrapper, ADR 0004; single-use TK-7)
 *   - PATCH /rapport/{id}             (multi-step bijwerken binnen de sessie)
 *   - action=resume                   (terugkeer na betaling, ADR 0007)
 * Statuscodes conform contract: 401 / 402 / 409 / 413 / 422 / 429.
 *
 * ── Gebruik (tool starten) ─────────────────────────────────────────────
 *   import { startCinabSession } from './cinab-tool-client.js';
 *
 *   const cinab = await startCinabSession();   // leest ?launch / ?token / ?cinab
 *   cinab.notifyLoaded();
 *
 *   // Poort-config (ADR 0007) — BEWAAR DEZE IN JE PERSISTENTE SESSIE-STATE:
 *   //   cinab.betaalVanafFase  → null = gratis tool; 0 is een geldige fase
 *   //   cinab.credits          → prijs per sessie
 *   // Bij een resume komt deze info NIET opnieuw mee (de launch-code is al
 *   // verbruikt) — haal 'm dan uit je eigen opgeslagen sessie-state.
 *
 * ── De betaalpoort (bij de start van de betaalde fase, werkboek §5.2) ──
 *   const { saldo } = await cinab.getSaldo();      // 1. advisory — alleen UX
 *   // ... toon "verder? (X credits)" of "onvoldoende — kopen?" ...
 *   try {
 *       await cinab.settleSession();               // 2. bindend: atomisch + idempotent
 *   } catch ( e ) {
 *       if ( e.isPaymentRequired ) {               // 402 → credit-shop
 *           // sessie-state staat al persistent server-side (werkboek §5.5)
 *           cinab.goToPayment( e );                // window.top.location (valkuil 5)
 *           return;
 *       }
 *       throw e;
 *   }
 *
 * ── Terugkeer na betaling (?token=...&action=resume) ──────────────────
 *   const cinab = await startCinabSession();       // herkent de resume zelf
 *   if ( cinab.isResume ) {
 *       // 1. eigen sessie-state laden, 2. idempotente retry:
 *       await cinab.settleSession();               // al betaald → no-op
 *       // 3. door naar de fase waar de gebruiker was
 *   }
 *
 * ── Afronden ───────────────────────────────────────────────────────────
 *   const { rapport_url } = await cinab.saveReport({
 *     template_id: 'mijn_tool',     // verplicht
 *     scores:     { dimensie: 72 }, // optioneel — map naam → 0-100
 *     meta:       { deelnemers: 8 },// vrije velden (worden ge-sanitatiseerd + ge-escaped)
 *     data:       { ... },          // opaak; jouw eigen render-payload
 *     verdieping: [ ... ],          // optioneel
 *   });
 *   // multi-step? binnen de token-TTL mag dezelfde sessie nog bijwerken:
 *   await cinab.patchReport( null, { data: { ... } } );  // null = laatste rapport
 *   cinab.notifyCompleted( rapport_url );   // laat WordPress doorschakelen
 *
 * ── Gebruik (render, in /render/{id}) ──────────────────────────────────
 *   import { fetchCinabRapport } from './cinab-tool-client.js';
 *
 *   const wrapper = await fetchCinabRapport( API_BASE, rapportId );
 *   // render wrapper.data / wrapper.scores zoals jouw tool dat wil
 */

const CINAB_API = '/wp-json/cinab/v1';

/** Korte duiding per contract-statuscode (werkboek v3.1, Appendix A). */
export const CINAB_STATUS_TEKST = {
	401: 'Niet geauthenticeerd',
	402: 'Onvoldoende credits of sessie nog niet afgerekend',
	409: 'Token verlopen, ongeldig of al gebruikt',
	413: 'Verzoek te groot (max 1 MB)',
	422: 'Validatiefout in het verzoek',
	429: 'Te veel verzoeken — probeer het zo opnieuw',
};

/**
 * Foutobject met de CINAB-statuscode/-code erbij.
 * Bij 402 bevat het bovendien .payment_url (en .saldo / .nodig voor de
 * poort-UI); bij 429 eventueel .retryAfter (seconden, uit de Retry-After
 * header als de server die meestuurt).
 */
export class CinabError extends Error {
	constructor( message, { status = 0, code = '', payment_url = '', saldo = null, nodig = null, retryAfter = null } = {} ) {
		super( message );
		this.name        = 'CinabError';
		this.status      = status;
		this.code        = code;
		this.payment_url = payment_url;
		this.saldo       = saldo;
		this.nodig       = nodig;
		this.retryAfter  = retryAfter;
	}
	/** 401 — niet geauthenticeerd (bv. ongeldige API-key). */
	get isAuthError()       { return this.status === 401; }
	/** 402 — betaalmuur: onvoldoende credits of nog niet afgerekend. */
	get isPaymentRequired() { return this.status === 402; }
	/** 409 — token verlopen, ongeldig of al gebruikt (was 419 in oude docs). */
	get isTokenError()      { return this.status === 409; }
	/** 413 — payload boven de 1 MB-grens. */
	get isPayloadTooLarge() { return this.status === 413; }
	/** 422 — validatiefout (bv. template_id ontbreekt). */
	get isValidationError() { return this.status === 422; }
	/** 429 — rate-limit geraakt; wacht even en probeer opnieuw. */
	get isRateLimited()     { return this.status === 429; }
}

/** Lees ?launch, ?token, ?cinab (WP-origin) en de context uit de huidige URL. */
export function readCinabParams() {
	const p = new URLSearchParams( window.location.search );
	return {
		launch:          p.get( 'launch' ) || '',
		token:           p.get( 'token' )  || '',
		apiBase:         stripSlash( p.get( 'cinab' ) || '' ),
		parentRapportId: p.get( 'parent_rapport_id' ) || null,
		action:          p.get( 'action' ) || null,
	};
}

/**
 * Start een tool-sessie. Twee routes, automatisch herkend:
 *
 * 1. Verse start: ?launch=... → launch-code inwisselen via POST /start-tool
 *    (ADR 0006/0007). Response { token, betaal_vanaf_fase, credits } komt op
 *    de client te staan als .token / .betaalVanafFase / .credits.
 * 2. Hervatten: ?token=...&action=resume (terugkeer na betaling) of een
 *    direct token in de URL. Geen launch-uitwisseling; het token wordt
 *    non-consuming gevalideerd (zet options.validateOnResume = false om dat
 *    over te slaan). LET OP: betaalVanafFase/credits zijn dan null — die
 *    hoor je bij de verse start in je persistente sessie-state te hebben
 *    bewaard (werkboek §3.4: ze komen alléén uit de start-tool-response).
 *
 * In beide gevallen worden launch/token uit de adresbalk gewist
 * (options.cleanUrl = false schakelt dat uit).
 */
export async function startCinabSession( options = {} ) {
	const params   = readCinabParams();
	const launch   = options.launch  ?? params.launch;
	const urlToken = options.token   ?? params.token;
	const action   = options.action  ?? params.action;
	const apiBase  = stripSlash( options.apiBase ?? params.apiBase );
	const apiKey   = options.apiKey ?? null; // optioneel (route 2 vereist 'm niet)
	const cleanUrl = options.cleanUrl ?? true;

	if ( ! apiBase ) throw new CinabError( 'Geen CINAB-API-base (ontbrekende ?cinab)', { code: 'no_api_base' } );

	// Route 2: hervatten met een bestaand token (action=resume na betaling,
	// of een direct token — niveau A).
	if ( ! launch && urlToken ) {
		if ( cleanUrl ) cleanSensitiveParamsFromUrl();
		const client = createCinabClient( {
			apiBase,
			token:           urlToken,
			apiKey,
			parentRapportId: params.parentRapportId,
			action,
		} );
		if ( options.validateOnResume ?? true ) {
			await client.validate(); // non-consuming; gooit CinabError bij 401/409
		}
		return client;
	}

	if ( ! launch ) throw new CinabError( 'Geen launch-code of token (ontbrekende ?launch)', { code: 'no_launch' } );

	// Route 1: verse start — launch-code inwisselen (single-use, 2 min).
	const out = await postJson( `${apiBase}${CINAB_API}/start-tool`, { launch }, { apiKey } );
	if ( ! out || ! out.token ) throw new CinabError( 'Geen token ontvangen', { code: 'no_token' } );

	// Launch-code uit de adresbalk halen — is toch al eenmalig verbruikt.
	if ( cleanUrl ) cleanSensitiveParamsFromUrl();

	return createCinabClient( {
		apiBase,
		token:           out.token,
		apiKey,
		parentRapportId: params.parentRapportId,
		action,
		// ADR 0007: per-tool poortconfig — null = gratis tool, 0 is geldig.
		betaalVanafFase: ( out.betaal_vanaf_fase === undefined ) ? null : out.betaal_vanaf_fase,
		credits:         ( out.credits === undefined ) ? null : out.credits,
	} );
}

/** Maak een client als je het token al hebt (bv. hervat uit eigen sessie-state). */
export function createCinabClient( { apiBase, token, apiKey = null, parentRapportId = null, action = null, betaalVanafFase = null, credits = null } ) {
	apiBase = stripSlash( apiBase );
	const parentOrigin = safeOrigin( apiBase );
	let lastRapportId  = null;

	return {
		token,
		apiBase,
		parentRapportId,
		action,

		/** Poort-fase uit de start-tool-response (ADR 0007). null = gratis tool. */
		betaalVanafFase,
		/** Credit-prijs per sessie uit de start-tool-response. */
		credits,

		/** True bij terugkeer na betaling (?action=resume) — werkboek §5.5 stap 7. */
		get isResume() { return action === 'resume'; },

		/** Het rapport_id van de laatste succesvolle saveReport() in deze sessie. */
		get lastRapportId() { return lastRapportId; },

		/** Valideer het token (non-consuming, TK-6) en haal de context op. */
		async validate() {
			return postJson( `${apiBase}${CINAB_API}/validate-token`, { token }, { apiKey } );
		},

		/**
		 * Advisory saldo-check voor de betaalpoort (werkboek §5.2 stap 1).
		 * POST met het token in de body — nooit in de URL.
		 * Geeft terug: { saldo }. Alleen UX: de bindende stap is settleSession().
		 */
		async getSaldo() {
			return postJson( `${apiBase}${CINAB_API}/saldo`, { token }, { apiKey } );
		},

		/**
		 * Reken de sessie af — de bindende stap van de betaalpoort (ADR 0007,
		 * werkboek §5.3). Atomisch én idempotent: een tweede aanroep (refresh,
		 * retry, terugkeer na betaling) ziet betaald=true en schrijft NIET
		 * opnieuw af. Geeft terug: { betaald: true, al_betaald: bool, saldo }.
		 *
		 * Bij onvoldoende saldo gooit dit een CinabError met .isPaymentRequired,
		 * .payment_url, .saldo en .nodig — geef die door aan goToPayment().
		 */
		async settleSession() {
			return postJson( `${apiBase}${CINAB_API}/sessie-afrekenen`, { token }, { apiKey } );
		},

		/**
		 * Sla het rapport op (dunne wrapper, ADR 0004) — consumeert het token
		 * (single-use, TK-7; een tweede save → 409).
		 * Verwacht: { template_id, scores?, meta?, data?, verdieping?, parent_rapport_id? }
		 * Geeft terug: { rapport_id, rapport_url }.
		 *
		 * Bij een betaalde tool vereist het platform betaald=true (gezet door
		 * settleSession()); anders 402 met .payment_url. Het token blijft bij
		 * een 402/422 geldig (pay-then-continue), alleen een geslaagde save
		 * verbruikt het.
		 */
		async saveReport( wrapper ) {
			if ( ! wrapper || ! wrapper.template_id ) {
				throw new CinabError( 'template_id ontbreekt in de wrapper', { code: 'no_template', status: 422 } );
			}
			const body = {
				token,
				template_id:       wrapper.template_id,
				schema_version:    wrapper.schema_version || '1.0',
				scores:            wrapper.scores || {},
				meta:              wrapper.meta || {},
				data:              wrapper.data ?? null,
				verdieping:        wrapper.verdieping ?? null,
				parent_rapport_id: wrapper.parent_rapport_id ?? parentRapportId ?? null,
			};
			const out = await postJson( `${apiBase}${CINAB_API}/rapport-opslaan`, body, { apiKey } );
			if ( out && out.rapport_id ) lastRapportId = out.rapport_id;
			return out;
		},

		/**
		 * Werk een eerder opgeslagen rapport bij (multi-step, fase G).
		 * Mag binnen de token-TTL door dezelfde sessie, óók al is het token
		 * door saveReport() geconsumeerd — het platform koppelt het rapport
		 * aan dit token. Hoort het token niet bij dit rapport → 409.
		 *
		 * rapportId: weglaten/null = het laatste rapport van deze sessie.
		 * fields: minimaal één van { scores, meta, data, verdieping }.
		 * template_id/schema_version/parent_rapport_id zijn onveranderlijk (OV-1).
		 * Geeft terug: { rapport_id, bijgewerkt: true, rapport_url }.
		 */
		async patchReport( rapportId, fields = {} ) {
			const id = rapportId || lastRapportId;
			if ( ! id ) {
				throw new CinabError( 'Geen rapport_id (nog geen saveReport gedaan?)', { code: 'no_rapport_id' } );
			}
			const body = { token };
			let any = false;
			for ( const k of [ 'scores', 'meta', 'data', 'verdieping' ] ) {
				if ( k in fields && fields[ k ] !== undefined ) {
					body[ k ] = fields[ k ];
					any = true;
				}
			}
			if ( ! any ) {
				throw new CinabError( 'Geen bij te werken velden meegegeven (scores, meta, data of verdieping)', { code: 'nothing_to_update', status: 422 } );
			}
			return sendJson( 'PATCH', `${apiBase}${CINAB_API}/rapport/${encodeURIComponent( id )}`, body, { apiKey } );
		},

		/**
		 * Stuur de gebruiker naar de credit-shop na een 402 (werkboek §5.5).
		 * Accepteert de CinabError van settleSession()/saveReport() of direct
		 * een payment_url. Navigeert via window.top.location — NIET
		 * window.location — anders blijft Mollie in het iframe hangen
		 * (valkuil 5). Zorg dat je sessie-state vóór de redirect persistent
		 * server-side staat; de terugkeer komt binnen als ?action=resume —
		 * ZONDER token. Het token haal je uit je eigen sessie-state.
		 *
		 * options.returnUrl: VEREIST voor automatische terugkeer — wordt als
		 * ?cinab_return_url aan de payment_url toegevoegd. De 402-payment_url
		 * is bewust kaal (ADR 0006): zonder returnUrl stuurt de Thank-You-
		 * pagina NIET terug naar de tool.
		 */
		goToPayment( target, { returnUrl = '' } = {} ) {
			let url = ( target instanceof CinabError ) ? target.payment_url : String( target || '' );
			if ( ! url ) {
				throw new CinabError( 'Geen payment_url beschikbaar', { code: 'no_payment_url' } );
			}
			if ( returnUrl ) {
				try {
					const u = new URL( url, apiBase );
					u.searchParams.set( 'cinab_return_url', returnUrl );
					url = u.toString();
				} catch ( _ ) { /* url onbruikbaar voor URL() — laat 'm dan zoals hij is */ }
			}
			try {
				window.top.location.href = url;       // uit het iframe breken
			} catch ( _ ) {
				window.location.href = url;           // cross-origin fallback
			}
		},

		/** Laat de parent (WordPress) weten dat het rapport klaar is → die schakelt door. */
		notifyCompleted( rapportUrl ) {
			postToParent( { type: 'cinab:completed', rapport_url: rapportUrl }, parentOrigin );
		},

		/** Geef de parent de gewenste iframe-hoogte door (voorkomt dubbele scrollbars). */
		notifyResize( height ) {
			postToParent( { type: 'cinab:resize', height: Math.ceil( height ) }, parentOrigin );
		},

		/** Meld dat de tool geladen is. */
		notifyLoaded() {
			postToParent( { type: 'cinab:loaded' }, parentOrigin );
		},
	};
}

/**
 * Render-modus: haal een opgeslagen rapport op via de publieke GET.
 * Gebruik dit in je /render/{id}-route; `data` is jouw eigen opake payload.
 */
export async function fetchCinabRapport( apiBase, rapportId ) {
	apiBase = stripSlash( apiBase );
	const res = await fetch( `${apiBase}${CINAB_API}/rapport/${encodeURIComponent( rapportId )}` );
	return handle( res );
}

/* ── interne helpers ─────────────────────────────────────────────────── */

async function postJson( url, body, opts = {} ) {
	return sendJson( 'POST', url, body, opts );
}

async function sendJson( method, url, body, { apiKey } = {} ) {
	const headers = { 'Content-Type': 'application/json' };
	if ( apiKey ) headers['X-CINAB-Key'] = apiKey; // optioneel onder route 2
	const res = await fetch( url, {
		method,
		headers,
		body: JSON.stringify( body ),
	} );
	return handle( res );
}

async function handle( res ) {
	let payload = null;
	try { payload = await res.json(); } catch ( _ ) { /* geen JSON-body */ }

	if ( ! res.ok ) {
		// WP_Error-vorm: { code, message, data: { status, payment_url, saldo, nodig } }
		const d           = ( payload && typeof payload.data === 'object' && payload.data ) || {};
		const code        = payload?.code || '';
		const message     = payload?.message || CINAB_STATUS_TEKST[ res.status ] || `HTTP ${res.status}`;
		const payment_url = d.payment_url || payload?.payment_url || '';
		const saldo       = ( d.saldo  !== undefined ) ? d.saldo  : ( payload?.saldo ?? null );
		const nodig       = ( d.nodig  !== undefined ) ? d.nodig  : ( payload?.nodig ?? null );
		const retryHdr    = res.headers ? res.headers.get( 'Retry-After' ) : null;
		const retryAfter  = ( retryHdr !== null && retryHdr !== '' && ! isNaN( Number( retryHdr ) ) ) ? Number( retryHdr ) : null;
		throw new CinabError( message, { status: res.status, code, payment_url, saldo, nodig, retryAfter } );
	}
	return payload;
}

function postToParent( msg, targetOrigin ) {
	if ( window.parent && window.parent !== window ) {
		window.parent.postMessage( msg, targetOrigin || '*' );
	}
}

function stripSlash( s ) { return String( s ).replace( /\/+$/, '' ); }

function safeOrigin( url ) {
	try { return new URL( url ).origin; } catch ( _ ) { return '*'; }
}

/** Haal launch én token uit de adresbalk/historie (werkboek §3.4-principe). */
function cleanSensitiveParamsFromUrl() {
	try {
		const u = new URL( window.location.href );
		let dirty = false;
		for ( const p of [ 'launch', 'token' ] ) {
			if ( u.searchParams.has( p ) ) {
				u.searchParams.delete( p );
				dirty = true;
			}
		}
		if ( dirty ) window.history.replaceState( {}, document.title, u.toString() );
	} catch ( _ ) { /* niets aan de hand */ }
}
