import re,subprocess
s=open('vaardigheidsmeter-leidinggeven.html',encoding='utf-8').read()
js=re.findall(r'<script>(.*?)</script>', s, re.S)[-1]
harness = js + r'''
;(function(){
 function pctToAB(p){var sum=Math.round(p/100*8+2),a=Math.min(5,Math.max(1,Math.round(sum/2))),b=Math.min(5,Math.max(1,sum-a));return {a:a,b:b,na:false};}
 var S={LV1:85,LV2:80,LV3:78,LV4:82,LV5:75,LV6:88,LV7:80,LV8:85,LV9:70,LV10:90,LV11:55,LV12:50,LV13:48,LV14:52,LV15:58,LV16:60,LV17:55,LV18:62,LV19:45,LV20:58};
 var Tm={LV1:70,LV2:68,LV3:66,LV4:72,LV5:65,LV6:66,LV7:62,LV8:64,LV9:60,LV10:68,LV11:52,LV12:48,LV13:46,LV14:50,LV15:55,LV16:55,LV17:52,LV18:58,LV19:60,LV20:55};
 function setup(lang,persp,variant,withTeam){
   LANG=lang; TEKST=TEKST_ALL[LANG]; rebuildModel();
   state.persp=persp; state.variant=variant; state.answers={}; state.responses=[];
   COMPS.forEach(function(c){state.answers[c.n]=pctToAB(S[c.n]);});
   if(withTeam){ for(var r=0;r<4;r++){ var v={}; COMPS.forEach(function(c){v[c.n]=Math.max(0,Math.min(100,Tm[c.n]+((r*7)%9)-4));});
     state.responses.push({name:"R"+r,naamZichtbaar:false,vals:v}); } }
 }
 var CAP={};
 global.__box={className:"",style:{},innerHTML:"",setAttribute:function(){}};
 var realGet=document.getElementById;
 document.getElementById=function(id){ return id==="beschouwing"?global.__box:realGet(id); };
 [["nl",true],["en",true],["nl",false],["en",false]].forEach(function(p){
   setup(p[0],"lead",p[1]?"paid":"free",p[1]);
   global.__box.innerHTML="";
   renderBeschouwing();
   CAP[p[0]+(p[1]?"_360":"_self")]=global.__box.innerHTML;
 });
 console.log("@@"+JSON.stringify(CAP));
})();
'''
open('/tmp/_b.js','w',encoding='utf-8').write(harness)
STUB=open('/tmp/stub.js','w',encoding='utf-8')
STUB.write(r'''
const fs=require('fs');
function el(){ const e={style:{setProperty(){}},dataset:{},classList:{add(){},remove(){},toggle(){},contains:()=>false},
  hidden:false,textContent:"",innerHTML:"",value:"",checked:false,
  setAttribute(){},getAttribute:()=>null,appendChild(){},removeChild(){},focus(){},click(){},
  addEventListener(){},querySelector:()=>el(),querySelectorAll:()=>[],insertAdjacentHTML(){},remove(){}}; return e; }
global.window=global;
global.document={documentElement:{},getElementById:()=>el(),querySelector:()=>el(),querySelectorAll:()=>[],
  addEventListener(){},createElement:()=>el(),body:el()};
global.location={search:"",pathname:"/",origin:"https://x",href:"https://x"};
global.localStorage={getItem:()=>null,setItem(){}}; global.sessionStorage={getItem:()=>null,setItem(){}};
global.history={replaceState(){}}; global.fetch=()=>Promise.reject(new Error("no-net"));
global.setTimeout=()=>0; global.requestAnimationFrame=f=>0;
window.addEventListener=function(){}; window.print=function(){};
try{ eval(fs.readFileSync("/tmp/_b.js","utf8")); }catch(e){ console.error("EVALFAIL "+e.message); process.exit(3); }
''')
STUB.close()
r=subprocess.run(['node','/tmp/stub.js'],capture_output=True,text=True)
cap=None
for line in r.stdout.splitlines():
    if line.startswith('@@'):
        import json; cap=json.loads(line[2:])
if not cap:
    print("HARNESS FAALDE:", (r.stderr or r.stdout)[:400]); raise SystemExit(1)

def txt(h): return re.sub(r'<[^>]+>',' ',h)
NL_WORDS=r'\b(het|een|zijn|wordt|niet|maar|jouw|je|van|voor|met|deze|daar|erin|ontwikkeling|beeld|sterk|team het|gemiddeld)\b'
EN_WORDS=r'\b(the|and|with|your|this|that|picture|average|strengths|development)\b'
ok=True
for k,v in cap.items():
    t=txt(v); lang=k.split("_")[0]
    leaks=set(re.findall(NL_WORDS if lang=="en" else EN_WORDS, t, re.I))
    print("\n=== %s === (%d tekens)"%(k,len(t)))
    print("  ", " ".join(t.split())[:190]+"...")
    if lang=="en" and leaks: print("   NL-WOORDEN IN EN:",sorted(leaks)); ok=False
    if lang=="nl" and leaks: print("   EN-WOORDEN IN NL:",sorted(leaks)); ok=False
    for bad in ["undefined","null","[object","{","}"]:
        if bad in t: print("   PLACEHOLDER/RUWE WAARDE:",bad); ok=False
print("\nRESULTAAT BESCHOUWING:", "SCHOON" if ok else "BEVINDINGEN")
