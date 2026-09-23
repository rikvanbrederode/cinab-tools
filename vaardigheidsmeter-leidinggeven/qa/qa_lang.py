import re,json,subprocess

STUB='''
const fs=require('fs');
function el(){ const e={style:{setProperty(){}},dataset:{},classList:{add(){},remove(){},toggle(){},contains:()=>false},
  hidden:false,textContent:"",innerHTML:"",value:"",checked:false,
  setAttribute(){},getAttribute:()=>null,appendChild(){},removeChild(){},focus(){},click(){},
  addEventListener(){},querySelector:()=>el(),querySelectorAll:()=>[],insertAdjacentHTML(){},remove(){}};
  return e; }
global.window=global;
global.document={documentElement:{},getElementById:()=>el(),querySelector:()=>el(),querySelectorAll:()=>[],
  addEventListener(){},createElement:()=>el(),body:el()};
global.location={search:"",pathname:"/",origin:"https://x",href:"https://x"};
global.localStorage={getItem:()=>null,setItem(){},removeItem(){}};
global.sessionStorage={getItem:()=>null,setItem(){},removeItem(){}};
global.history={replaceState(){}};
global.fetch=()=>Promise.reject(new Error("no-net"));
global.setTimeout=()=>0; global.requestAnimationFrame=f=>0;
window.addEventListener=function(){}; window.print=function(){};
global.URLSearchParams=URLSearchParams;
try{ eval(fs.readFileSync("/tmp/_x.js","utf8")); }catch(e){ console.error("EVALFAIL "+e.message); process.exit(3); }
'''

def dump(html, varname):
    s=open(html,encoding='utf-8').read()
    js=re.findall(r'<script>(.*?)</script>', s, re.S)[-1]
    open('/tmp/_x.js','w',encoding='utf-8').write(js+"\n;console.log('@@'+JSON.stringify(%s));"%varname)
    r=subprocess.run(['node','-e',STUB],capture_output=True,text=True)
    for line in r.stdout.splitlines():
        if line.startswith('@@'):
            return json.loads(line[2:])
    print("  KON %s NIET LEZEN: %s"%(varname,(r.stderr or r.stdout).strip()[:160]))
    return None

def flat(o,pre=""):
    out={}
    if isinstance(o,dict):
        for k,v in o.items(): out.update(flat(v,pre+"."+k if pre else k))
    elif isinstance(o,list):
        for i,v in enumerate(o): out.update(flat(v,"%s[%d]"%(pre,i)))
    elif isinstance(o,str): out[pre]=o
    return out

ALLOW={"phEmail","progress"}   # uitzonderingen: e-mailformaat/teller zijn taalneutraal

def check(name,obj):
    nl,en=flat(obj.get('nl',{})),flat(obj.get('en',{}))
    print("\n=== %s ==="%name)
    only_nl=sorted(set(nl)-set(en)); only_en=sorted(set(en)-set(nl))
    print("  sleutels NL: %d | EN: %d"%(len(nl),len(en)))
    bad=False
    if only_nl: print("  ONTBREEKT IN EN:",only_nl[:12]); bad=True
    if only_en: print("  ONTBREEKT IN NL:",only_en[:12]); bad=True
    same=[k for k in nl if k in en and nl[k].strip()==en[k].strip()
          and len(nl[k].split())>=3 and k.split('.')[-1] not in ALLOW]
    if same: print("  GELIJKE WAARDEN (ontbrekende vertaling):",same); bad=True
    empty=sorted({k for k in set(nl)|set(en) if not (nl.get(k) or "").strip() or not (en.get(k) or "").strip()})
    if empty: print("  LEGE WAARDEN:",empty[:12]); bad=True
    if not bad: print("  OK — pariteit compleet, geen lege of onvertaalde waarden")
    return not bad

ok=True; read=0
m=dump('vaardigheidsmeter-leidinggeven.html','MODEL')
if m: read+=1; ok&=check("MODEL — domeinen + 20 competenties + 40 stellingen",{'nl':m['nl'],'en':m['en']})
else: ok=False
for var,label,f in [('UI','UI hoofd-app','vaardigheidsmeter-leidinggeven.html'),
                    ('TEKST_ALL','TEKST perspectieven','vaardigheidsmeter-leidinggeven.html'),
                    ('JUI','JUI join-pagina','vaardigheidsmeter_join.html')]:
    d=dump(f,var)
    if d: read+=1; ok&=check(label,d)
    else: ok=False
print("\nuitgelezen objecten: %d/4"%read)
print("RESULTAAT:", "GEEN BEVINDINGEN" if ok else "BEVINDINGEN — zie hierboven")
