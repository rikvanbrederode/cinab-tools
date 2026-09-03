#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading, functools, http.server, socketserver, json, re, sys
SECTIONS=set(sys.argv[1:]) or {'A','B','C','D'}
from playwright.sync_api import sync_playwright
PORT=8791
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
socketserver.TCPServer.allow_reuse_address=True
srv=socketserver.TCPServer(('127.0.0.1',PORT),functools.partial(H,directory='.')); threading.Thread(target=srv.serve_forever,daemon=True).start()
U=f'http://127.0.0.1:{PORT}/'
FILES=[f'risicobeheersing_fase{i}.html' for i in range(6)]+['risicobeheersing_rapport.html']
passed=failed=0; findings=[]
def check(n,c,e=''):
    global passed,failed
    if c: passed+=1
    else: failed+=1; print(' ✗',n,e); findings.append(f'{n} {e}')
def jserrs(p,bucket):
    p.on('pageerror', lambda e: bucket.append(str(e)))
BAD=re.compile(r'\{[a-zA-Z]+\}|\bundefined\b|\bnull\b|\[object ')

def text_problems(p):
    return p.evaluate('''() => {
    const out=[]; const bad=/\\{[a-zA-Z]+\\}|\\bundefined\\b|\\bnull\\b|\\[object /;
    for (const el of document.querySelectorAll('body *')){
        if (['SCRIPT','STYLE'].includes(el.tagName)) continue;
        if (el.children.length) continue;
        const t=(el.textContent||'').trim(); if(!t) continue;
        if (bad.test(t)) out.push(t.slice(0,60));
    }
    return out.slice(0,6); }''')

# seed: volledige sessie-data (uit de casus-run) om alle schermen te kunnen tonen
SEED = {
 'rb_session': json.dumps({'orgName':'Zorggroep Rijnland','sector':'zorg','sessionName':'Medicatieveiligheid','date':'2026-09-02','facilitator':'Marieke','analysisType':'preventief','domain':'','scope':'','participants':[{'name':'Anne','email':''},{'name':'Bram','email':''}],'sessionId':'QA1234'}),
 'rb_consequence': 'Verkeerde dosering met ernstige schade',
 'rb_risks': json.dumps([{'id':1,'text':'Onduidelijke overdracht'},{'id':2,'text':'Verouderd systeem'},{'id':3,'text':'Geen dubbele controle'}]),
 'rb_individual_scores': json.dumps({'1':[{'participant':'Anne','kans':'D','impact':5},{'participant':'Bram','kans':'E','impact':6}],'2':[{'participant':'Anne','kans':'B','impact':2},{'participant':'Bram','kans':'C','impact':3}],'3':[{'participant':'Anne','kans':'C','impact':4},{'participant':'Bram','kans':'D','impact':4}]}),
 'rb_group_scores': json.dumps({'1':{'kans':'E','impact':6},'2':{'kans':'B','impact':2},'3':{'kans':'D','impact':4}}),
}

with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    # ── A. Popups + i18n per bestand ──────────────────────────────────────────
    print('== A. popups / i18n / info-icons')
    for fn in (FILES if 'A' in SECTIONS else []):
        ctx=b.new_context(viewport={'width':1280,'height':900}); p=ctx.new_page(); errs=[]; jserrs(p,errs)
        p.on('dialog', lambda d: d.accept())
        p.goto(U+fn, wait_until='domcontentloaded'); p.wait_for_timeout(400)
        p.evaluate('(seed)=>{ for(const k in seed) localStorage.setItem(k, seed[k]); }', SEED)
        p.reload(wait_until='domcontentloaded'); p.wait_for_timeout(600)
        for lg in ('nl','en'):
            p.evaluate(f'setLang("{lg}")'); p.wait_for_timeout(250)
            probs=text_problems(p)
            check(f'{fn} [{lg}] geen placeholders/undefined in UI', not probs, probs)
            if p.query_selector('#t-theoryBtn'):
                p.click('#t-theoryBtn'); p.wait_for_timeout(150)
                op=p.evaluate('document.getElementById("rbTipPopup").classList.contains("open")')
                ttl=p.evaluate('document.getElementById("rbTipTitle").textContent.trim()')
                bod=p.evaluate('document.getElementById("rbTipBody").textContent.trim().length')
                check(f'{fn} [{lg}] onderbouwing-popup open, titel+inhoud', op and ttl and bod>200, f'open={op} titel={ttl[:20]!r} len={bod}')
                p.keyboard.press('Escape'); p.wait_for_timeout(100)
                esc=p.evaluate('!document.getElementById("rbTipPopup").classList.contains("open")')
                if not esc: p.click('#rbTipCloseBtn'); p.wait_for_timeout(80)
                check(f'{fn} [{lg}] popup sluit met Escape', esc)
        # info-icons: elk icoon geeft inhoud
        icons=p.query_selector_all('.info-icon')
        empty=0
        for ic in icons[:6]:
            try:
                ic.click(timeout=1500); p.wait_for_timeout(40)
                if p.evaluate('document.getElementById("rbTipBody").textContent.trim().length')<10: empty+=1
                p.evaluate('rbCloseTip()')
            except Exception as e: empty+=1
        check(f'{fn} info-icons ({len(icons)}) geven inhoud', empty==0, f'leeg={empty}')
        check(f'{fn} geen JS-fouten', not errs, errs[:1])
        ctx.close()

    # ── B. Directe load zonder data (guards) ──────────────────────────────────
    print('== B. directe load zonder sessiedata')
    for fn in (FILES[1:] if 'B' in SECTIONS else []):
        ctx=b.new_context(); p=ctx.new_page(); errs=[]; jserrs(p,errs)
        p.on('dialog', lambda d: d.accept())
        p.goto(U+fn, wait_until='domcontentloaded'); p.wait_for_timeout(500)
        if p.query_selector('#t-introStart'):
            try: p.click('#t-introStart', timeout=1500); p.wait_for_timeout(200)
            except Exception: pass
        check(f'{fn} zonder data: geen crash', not errs, errs[:1])
        ctx.close()

    # ── C. Refresh-herstel + terug-navigatie + randgevallen fase 1 ───────────
    if 'C' in SECTIONS:
     print('== C. refresh / terug / randgevallen')
     ctx=b.new_context(); p=ctx.new_page(); errs=[]; jserrs(p,errs)
     dialogs=[]
     def on_dialog(d):
          dialogs.append(d.message); d.dismiss()
     p.on('dialog', on_dialog)
     p.goto(U+'risicobeheersing_fase1.html', wait_until='domcontentloaded'); p.wait_for_timeout(300)
     p.evaluate('(seed)=>{ for(const k in seed) localStorage.setItem(k, seed[k]); localStorage.removeItem("rb_risks"); }', SEED)
     p.reload(wait_until='domcontentloaded'); p.wait_for_timeout(500)
     p.click('#t-introStart'); p.wait_for_timeout(150)
     check('fase1: clusterknop disabled zonder inzendingen', p.evaluate('document.getElementById("t-toCluster").disabled'))
     p.evaluate('showPView(); showPStage("input")'); p.fill('#pRiskInput','   '); p.click('#t-pSubmit'); p.wait_for_timeout(80)
     check('fase1: lege inzending geweigerd', p.evaluate('(JSON.parse(localStorage.getItem("rb_phase1_live_subs")||"[]")).length')==0)
     p.fill('#pRiskInput','Onduidelijke overdracht'); p.click('#t-pSubmit'); p.wait_for_timeout(80); p.evaluate('hidePView()')
     p.reload(wait_until='domcontentloaded'); p.wait_for_timeout(600)
     scr=p.evaluate('[...document.querySelectorAll(".screen.open")].map(e=>e.id)')
     check('fase1: refresh herstelt verzamelscherm + inzending', scr==['sCollect'] and p.evaluate('(JSON.parse(localStorage.getItem("rb_phase1_live_subs")||"[]")).length')==1, str(scr))
     p.click('#t-toCluster'); p.wait_for_timeout(200)
     check('fase1: bevestigen met 1 cluster mogelijk', not p.evaluate('document.getElementById("t-confirmBtn").disabled'))
     p.evaluate('deleteCluster(0)'); p.wait_for_timeout(80)
     check('fase1: bevestigen disabled bij 0 clusters', p.evaluate('document.getElementById("t-confirmBtn").disabled'))
     p.evaluate('goPrevPhase()'); p.wait_for_timeout(200)
     check('fase1: terug-naar-vorige vraagt bevestiging en blijft bij annuleren', len(dialogs)>=1 and 'fase1' in p.url)
     check('fase1: geen JS-fouten in randgevallen', not errs, errs[:1])
     ctx.close()

     # ── D. Rapport: knoppen, export, print, refresh ───────────────────────────
    if 'D' in SECTIONS:
     print('== D. rapport-knoppen')
     ctx=b.new_context(accept_downloads=True); p=ctx.new_page(); errs=[]; jserrs(p,errs)
     p.goto(U+'risicobeheersing_rapport.html', wait_until='domcontentloaded'); p.wait_for_timeout(300)
     p.evaluate('(seed)=>{ for(const k in seed) localStorage.setItem(k, seed[k]); }', SEED)
     p.reload(wait_until='domcontentloaded'); p.wait_for_timeout(900)
     body=p.evaluate('document.body.innerText')
     check('rapport rendert seed-casus (geen demo)', 'Zorggroep Rijnland' in body and 'Gemeente Leiden' not in body)
     with p.expect_download(timeout=4000) as dl:
          p.click('button[aria-label="Data exporteren"]')
     d=dl.value; path=d.path(); data=json.load(open(path,encoding='utf-8'))
     check('data-export levert JSON met sessie', isinstance(data,dict) and any('session' in k or 'rb_session' in k or 'meta' in k for k in data.keys()), list(data.keys())[:6])
     p.evaluate('window.__printed=false; window.print=()=>{window.__printed=true;}')
     p.click('button[aria-label*="PDF"], button:has(#t-printBtn)'); p.wait_for_timeout(200)
     check('PDF-knop roept print aan', p.evaluate('window.__printed===true'))
     check('rapport heeft @media print-regels', p.evaluate('[...document.styleSheets].some(ss=>{try{return [...ss.cssRules].some(r=>r.media&&/print/.test(r.media.mediaText));}catch(e){return false;}})'))
     check('rapport geen JS-fouten', not errs, errs[:1])
     ctx.close(); b.close()
srv.shutdown()
print(f'\nTOTAAL: {passed} geslaagd, {failed} gefaald')
for f in findings: print(' -', f)
