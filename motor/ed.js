
/* ================= Editor da Ficha do Deck ================= */
const BL=__BLOCOS__;
const MARCAS=["YoungNetwork Group","YN Angola","YN Moçambique","YN Color","Taylor","Alice"];
const TOM={"YoungNetwork Group":"Tom de voz YoungNetwork: ousado, criativo e confiante; frases curtas e impactantes; verbos no presente; direto, sem rodeios nem formalidade a mais; energia e atitude, sem exageros vazios. Assinatura: Leading Brave Brands."};
let ED=null, assetsNS=null, sampleNS=null, roomNS=null;

/* ---------- esquemas dos blocos (galeria) ---------- */
function sk(tipo){
  const R=(x,y,w,h,c,r)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r??1.5}" class="${c}"/>`;
  const C=(x,y,r,c)=>`<circle cx="${x}" cy="${y}" r="${r}" class="${c}"/>`;
  const P=(x,y,s,c)=>`<path d="M${x} ${y-s}L${x+s*1.6} ${y}L${x} ${y+s}Z" class="${c}"/>`;
  const L=(x,y,w,n,g,c)=>Array.from({length:n},(_,i)=>R(x,y+i*g,i==n-1?w*.6:w,2.2,c||"m",1)).join("");
  let g="";
  switch(tipo){
    case"abertura": g=R(0,0,100,60,"k",0)+R(8,8,14,4,"a")+R(8,26,62,8,"w")+R(8,38,40,8,"w")+R(8,50,24,4,"a",2); break;
    case"hero": g=R(0,0,100,60,"s",0)+R(12,24,76,10,"w")+R(30,40,40,3,"w"); break;
    case"texto": g=R(8,10,36,6,"k")+L(8,22,36,5,6)+R(54,8,38,44,"s",3); break;
    case"numeros": g=[8,38,68].map(x=>R(x,14,24,14,"a")+R(x,32,20,2.5,"m",1)+R(x,37,14,2.5,"m",1)).join(""); break;
    case"cases": g=[0,1,2].flatMap(c=>[0,1].map(r=>R(8+c*29,8+r*24,26,20,"s",2)+P(19+c*29,18+r*24,4,"w"))).join(""); break;
    case"equipa": g=[0,1,2,3].map(i=>C(17+i*22,24,8,"s")+R(9+i*22,37,16,3,"k",1)+R(11+i*22,43,12,2.2,"m",1)).join(""); break;
    case"lista": g=[0,1,2,3].map(i=>R(8,8+i*12,8,8,"a")+R(20,9+i*12,50,3,"k",1)+R(20,14+i*12,34,2,"m",1)).join(""); break;
    case"logos": g=[0,1,2,3].flatMap(c=>[0,1,2].map(r=>R(8+c*22,8+r*16,18,10,"m",2))).join(""); break;
    case"contacto": g=[0,1].map(i=>R(8+i*44,12,40,36,"m",3)+C(20+i*44,24,5,"s")+R(14+i*44,33,26,3,"k",1)+R(14+i*44,39,20,2,"a",1)).join(""); break;
    case"video": g=R(0,0,100,60,"k",0)+C(50,30,10,"a")+P(47,30,5,"w"); break;
    case"cartoes": g=[0,1,2].map(i=>R(8+i*18,6,15,5,i?"m":"a",2.5)).join("")+[0,1,2].map(i=>R(8+i*29,16,26,36,"m",3)+R(12+i*29,22,14,2.5,"a",1)+L(12+i*29,30,18,3,5)).join(""); break;
    case"calendario": g=[0,1,2,3,4].map(i=>R(8+i*17.5,10,15,40,i==2?"a":"m",2)+R(11+i*17.5,14,9,6,i==2?"w":"k",1)).join(""); break;
    case"tarefas": g=[0,1,2,3].map(i=>R(8,8+i*12,16,7,"a",2)+R(28,10+i*12,56,3,"k",1)).join(""); break;
    case"barras": g=[0,1,2,3].map(i=>R(8,10+i*11,84,5,"m",2.5)+R(8,10+i*11,[70,52,80,34][i],5,"a",2.5)).join(""); break;
    case"perguntas": g=[0,1,2].map(i=>R(8+i*29,10,26,40,i==1?"a":"m",3)+`<text x="${21+i*29}" y="35" text-anchor="middle" font-size="14" font-weight="800" class="${i==1?"w":"k"}">?</text>`).join(""); break;
    case"checklist": g=[0,1,2,3].map(i=>R(8,8+i*12,8,8,i<2?"a":"m",2)+R(22,10+i*12,50,3,"k",1)).join(""); break;
    case"regras": g=[0,1].flatMap(c=>[0,1].map(r=>R(8+c*43,8+r*23,40,20,"m",3)+R(13+c*43,13+r*23,22,3,"k",1)+R(13+c*43,19+r*23,28,2,"s",1))).join(""); break;
    case"galeria": g=R(8,8,30,26,"s",2)+R(8,37,30,15,"m",2)+R(41,8,24,15,"m",2)+R(41,26,24,26,"s",2)+R(68,8,24,30,"s",2)+R(68,41,24,11,"m",2); break;
    default: g=`<rect x="8" y="8" width="84" height="44" rx="4" class="o"/>`+R(30,26,40,3,"s",1)+R(38,32,24,2.2,"m",1);
  }
  return `<svg class="sk" viewBox="0 0 100 60" aria-hidden="true">${g}</svg>`;
}

/* ---------- utilidades ---------- */
const clone=o=>JSON.parse(JSON.stringify(o??null));
function merge(a,b){ if(b===null||typeof b!=="object"||Array.isArray(b)) return clone(b); const o=(a&&typeof a==="object"&&!Array.isArray(a))?{...a}:{}; for(const k in b) o[k]=merge(o[k],b[k]); return o }
function nest(path,v){ const o={}; let c=o; path.forEach((k,i)=>{ if(i===path.length-1) c[k]=v; else c=c[k]={} }); return o }
function at(o,path){ return path.reduce((c,k)=>c==null?undefined:c[k],o) }
const hora=()=>new Date().toLocaleTimeString("pt-PT",{hour:"2-digit",minute:"2-digit"});
const tr=v=>v&&typeof v==="object"?v:{pt:v||"",en:""};
const nid=p=>p+Date.now().toString(36)+Math.random().toString(36).slice(2,5);

/* ---------- dados: servidor + pendentes ---------- */
function docRef(key){ return key==="cfg"?db.doc("fichas/"+ED.id):db.doc("fichas/"+ED.id+"/seccoes/"+key) }
function view(key){
  const base=key==="cfg"?ED.cfgDoc:ED.secs[key];
  return merge(merge(base||{},ED.voo[key]||{}),ED.pend[key]||{});
}
function getv(key,path){ return at(view(key),path) }
function setv(key,path,v,{now}={}){
  ED.pend[key]=merge(ED.pend[key]||{},nest(path,v));
  estadoGrav("A gravar...");
  clearTimeout(ED.tmr[key]); ED.tmr[key]=setTimeout(()=>flush(key),now?0:650);
}
async function flush(key){
  if(ED.voo[key]){ ED.again[key]=true; return }
  const p=ED.pend[key]; if(!p) return;
  ED.voo[key]=p; delete ED.pend[key];
  try{ await docRef(key).update(p); estadoGrav("Gravado às "+hora()) }
  catch(err){ ED.pend[key]=merge(p,ED.pend[key]||{}); estadoGrav(err&&err.code==="invalid_argument"?"Sem permissão para gravar. Peça acesso de Contributor ao JD.":"Não gravou. Volta a tentar sozinho.","err"); setTimeout(()=>flush(key),4000) }
  finally{ delete ED.voo[key]; if(ED.again[key]){ ED.again[key]=false; flush(key) } }
}
function estadoGrav(t,k){ const e=$("#edSave"); if(e){ e.textContent=t; e.dataset.k=k||"" } }

/* ---------- abrir e fechar ---------- */
function rota(){ const h=decodeURIComponent(location.hash.slice(1)); if(h.startsWith("ficha-")&&db) abrirFicha(h.slice(6)); else fecharFicha() }
addEventListener("hashchange",rota);
function fecharFicha(){
  if(!ED) { $("#home").hidden=false; $("#ed").hidden=true; return }
  for(const k in ED.pend) flush(k);
  ED.unsub.forEach(f=>{ try{f()}catch(e){} }); if(ED.room) ED.room.leave().catch(()=>{});
  ED=null; $("#ed").hidden=true; $("#home").hidden=false; window.scrollTo(0,0);
}
async function abrirFicha(id){
  if(ED&&ED.id===id) return;
  if(ED) fecharFicha();
  ED={id,cfgDoc:null,secs:{},pend:{},voo:{},again:{},tmr:{},unsub:[],aberta:null,lang:"pt",sig:"",peers:[],nomes:{},prev:{},carregado:{cfg:false,secs:false}};
  $("#home").hidden=true; $("#ed").hidden=false; window.scrollTo(0,0);
  $("#ed").replaceChildren(el("p",{class:"note",text:"A abrir a ficha..."}));
  ED.unsub.push(db.doc("fichas/"+id).onSnapshot(s=>{ ED.cfgDoc=s.exists?s.data():null; ED.carregado.cfg=true; sincronizar() },()=>estadoGrav("Perdi a ligação. Recarregue a página.","err")));
  ED.unsub.push(db.collection("fichas/"+id+"/seccoes").onSnapshot(q=>{ const o={}; q.docs.forEach(d=>o[d.id]=d.data()); ED.secs=o; ED.carregado.secs=true; sincronizar() },()=>{}));
  if(!assetsNS) claude.use("assets").then(a=>{ assetsNS=a; if(ED) desenhar(true) });
  ligarSala(id);
}
async function ligarSala(id){
  try{ if(!roomNS) roomNS=await claude.use("room"); if(!roomNS||!ED) return;
    const r=await roomNS.join("ficha-"+id); if(!ED||ED.id!==id){ r.leave(); return }
    ED.room=r; r.presence({secao:ED.aberta||null});
    ED.unsub.push(r.onPeers(async ch=>{ if(!ED) return; ED.peers=ch.peers.filter(p=>p.kind==="viewer");
      const ids=ED.peers.map(p=>p.by).filter(Boolean).filter(x=>!(x in ED.nomes));
      if(ids.length&&user){ try{ const ps=await user.profiles(ids); for(const k in ps) ED.nomes[k]=ps[k].name||"" }catch(e){} }
      desenharPeers() }));
  }catch(e){}
}
function nomePeer(p){ return p.isMe?"Eu":(ED.nomes[p.by]||"Colega") }
function desenharPeers(){
  const box=$("#edPeers"); if(!box||!ED) return;
  const outros=ED.peers.filter(p=>!p.isMe);
  box.replaceChildren(...outros.map(p=>el("span",{class:"peer",title:p.presence&&p.presence.secao?"Na secção "+tituloSec(p.presence.secao):"",text:nomePeer(p)})));
  document.querySelectorAll("[data-who]").forEach(n=>{ const sid=n.dataset.who; const q=outros.filter(p=>p.presence&&p.presence.secao===sid);
    n.hidden=!q.length; n.textContent=q.map(nomePeer).join(", ") });
}

/* ---------- desenho ---------- */
function ordem(){ const o=(getv("cfg",["ordem"])||[]).filter(s=>ED.secs[s]||ED.pend[s]); return o }
function assinatura(){
  const c=view("cfg");
  return JSON.stringify([ED.lang,c.config&&c.config.formato,c.config&&c.config.com_senha,ordem(),ordem().map(s=>{ const v=view(s); return [v.bloco,v.incluir,v.escrever_no_draft,itensDe(v).map(i=>[i.id,i.incluir!==false])] }),!!assetsNS,ED.aberta,!!ED.cfgDoc])
}
function sincronizar(){
  if(!ED||!ED.carregado.cfg||!ED.carregado.secs) return;
  const s=assinatura(); if(s!==ED.sig){ desenhar(); return }
  document.querySelectorAll("#ed [data-k]").forEach(n=>{
    if(n===document.activeElement) return;
    const v=getv(n.dataset.k,JSON.parse(n.dataset.p));
    if(n.type==="checkbox") n.checked=!!v; else if((v??"")!==n.value) n.value=v??"";
  });
  document.querySelectorAll("#ed [data-ptref]").forEach(n=>{ n.textContent=getv(n.dataset.k,JSON.parse(n.dataset.ptref))||"(em branco em português)" });
  document.querySelectorAll("#ed [data-sum]").forEach(n=>{ n.textContent=resumoSec(n.dataset.sum) });
  desenharToc(); desenharPeers();
}
function itensDe(v){ return Object.entries(v.itens||{}).filter(([,i])=>i&&!i.apagado).map(([id,i])=>({id,...i})).sort((a,b)=>(a.o||0)-(b.o||0)) }
function tituloSec(sid){ const v=view(sid); return (v.menu&&v.menu.pt)||(v.cab&&v.cab.title&&tr(v.cab.title).pt)||v.bloco||"Secção" }
function resumoSec(sid){ const v=view(sid); const t=v.cab&&v.cab.title?tr(v.cab.title).pt:""; return [v.bloco,t].filter(Boolean).join(" · ") }

function desenhar(soCabecalho){
  if(!ED) return;
  const foco=document.activeElement&&document.activeElement.id, sel=foco&&document.activeElement.selectionStart;
  ED.sig=assinatura();
  if(!ED.cfgDoc){ $("#ed").replaceChildren(topo(), el("div",{class:"empty"},el("b",{text:"Esta apresentação ainda não tem ficha no Studio."}),"A ficha deste deck ainda está no Excel. Use o botão \"Ficha do Deck\" na lista para a abrir.")); return }
  const cards=el("div",{class:"cards"}, cartaoCfg(), ...ordem().map((sid,i)=>cartaoSec(sid,i)));
  $("#ed").replaceChildren(topo(), el("div",{class:"ed-body"}, el("nav",{class:"toc",id:"edToc","aria-label":"Secções"}), cards));
  desenharToc(); desenharPeers();
  if(foco){ const n=document.getElementById(foco); if(n){ n.focus(); try{ if(sel!=null) n.setSelectionRange(sel,sel) }catch(e){} } }
}
function topo(){
  const r=rows.find(x=>x.id===ED.id)||{};
  const lang=el("div",{class:"lang",role:"group","aria-label":"Língua a editar"},
    ...["pt","en"].map(l=>{ const b=el("button",{type:"button","aria-pressed":String(ED.lang===l)},l.toUpperCase()); b.onclick=()=>{ ED.lang=l; desenhar() }; return b }));
  const go=el("div",{class:"go"});
  if(r.draft_link) go.append(el("a",{class:"btn sm",href:r.draft_link,target:"_blank",rel:"noopener"},"Ver draft"));
  if(["pronta","draft","publicada","erro"].includes(r.estado)&&podeEscrever) go.append(el("button",{class:"btn sm primary",type:"button","data-acao":"gerar_draft","data-id":ED.id},r.draft_link?"Gerar novo draft":"Gerar draft"));
  else if(r.estado) go.append(el("span",{class:"pill p-"+r.estado,text:ESTADOS[r.estado]||r.estado}));
  return el("div",{class:"ed-top"},
    el("a",{class:"back",href:"#"},"← Apresentações"),
    el("h1",{text:r.nome||ED.id}),
    el("span",{class:"grow"}),
    el("div",{class:"peers",id:"edPeers"}),
    lang, el("span",{class:"ed-save",id:"edSave",text:"Tudo gravado"}), go);
}
function desenharToc(){
  const t=$("#edToc"); if(!t) return;
  const a=(sid,i)=>{ const v=view(sid); const n=el("a",{href:"#",draggable:"true","data-sid":sid,class:v.incluir===false?"off":""},el("i",{text:String(i+1)}),el("span",{text:tituloSec(sid)}));
    n.onclick=e=>{ e.preventDefault(); abrirSec(sid,true) };
    n.ondragstart=e=>{ e.dataTransfer.setData("text/plain",sid); e.dataTransfer.effectAllowed="move" };
    n.ondragover=e=>{ e.preventDefault(); n.classList.add("drop") };
    n.ondragleave=()=>n.classList.remove("drop");
    n.ondrop=e=>{ e.preventDefault(); n.classList.remove("drop"); const de=e.dataTransfer.getData("text/plain"); if(!de||de===sid) return;
      const o=ordem().filter(x=>x!==de); o.splice(o.indexOf(sid),0,de); setv("cfg",["ordem"],o,{now:true}); desenhar() };
    return n };
  const add=el("button",{class:"btn sm",type:"button"},"+ Juntar secção"); add.onclick=()=>galeria(null);
  t.replaceChildren(el("b",{text:"Secções"}), ...ordem().map(a), podeEscrever?add:"");
}
function abrirSec(sid,rolar){
  ED.aberta=(ED.aberta===sid&&!rolar)?null:sid; if(ED.room) ED.room.presence({secao:ED.aberta}).catch(()=>{});
  desenhar();
  if(ED.aberta){ const c=document.getElementById("c-"+sid); if(c&&rolar) c.scrollIntoView({behavior:"smooth",block:"start"}) }
}

/* ---------- campos ---------- */
let fseq=0;
function campo({key,path,label,ajuda,traduz,multi,tipo,ex,wide}){
  const id="f"+(++fseq)+"-"+key+"-"+path.join("_");
  const p=traduz?[...path,ED.lang]:path;
  const v=getv(key,p);
  let inp;
  if(tipo==="select"){ inp=el("select",{id}); (ex||[]).forEach(o=>{ const op=el("option",{value:o},o); if(o===v) op.selected=true; inp.append(op) }) }
  else if(multi){ inp=el("textarea",{id,rows:"3"}); inp.value=v||"" }
  else { inp=el("input",{id,type:tipo||"text"}); inp.value=v||"" }
  if(ex&&tipo!=="select") inp.placeholder=ex;
  inp.dataset.k=key; inp.dataset.p=JSON.stringify(p);
  if(!podeEscrever) inp.disabled=true;
  inp.addEventListener(tipo==="select"?"change":"input",()=>{
    setv(key,p,inp.value);
    if(traduz&&ED.lang==="pt"){ const en=getv(key,[...path,"en"]), man=getv(key,[...path,"en_m"]); if(en&&!man) setv(key,[...path,"en"],"") }
    if(traduz&&ED.lang==="en") setv(key,[...path,"en_m"],!!inp.value);
    if(path[0]==="menu"||(path[0]==="cab"&&path[1]==="title")) desenharToc();
  });
  const lab=el("span",{},label, ajuda?el("em",{text:ajuda}):"", traduz&&ED.lang==="en"?el("em",{text:"inglês"}):"");
  const f=el("label",{class:"f"+(wide?" wide":""),for:id},lab,inp);
  if(traduz&&ED.lang==="en") f.append(el("div",{class:"pt","data-k":key,"data-ptref":JSON.stringify([...path,"pt"]),text:getv(key,[...path,"pt"])||"(em branco em português)"}));
  return f;
}
function interruptor(key,path,label){
  const id="t"+(++fseq)+"-"+key;
  const i=el("input",{type:"checkbox",id}); i.checked=getv(key,path)!==false; i.dataset.k=key; i.dataset.p=JSON.stringify(path);
  if(!podeEscrever) i.disabled=true;
  i.onchange=()=>{ setv(key,path,i.checked,{now:true}); desenhar() };
  return el("label",{class:"tog",for:id},i,label);
}
function ehImagem(n){ return /\.(png|jpe?g|gif|webp|svg|avif)$/i.test(n||"") }
function campoMedia({key,path,label,ajuda}){
  const id="m"+(++fseq)+"-"+key;
  const v=getv(key,path)||"";
  const thumb=el("div",{class:"thumb"});
  const pinta=val=>{ const m=/^asset:([^/]+)\/(.*)$/.exec(val||""); thumb.style.backgroundImage=""; thumb.textContent="";
    if(m&&ehImagem(m[2])) thumb.style.backgroundImage=`url("/_blob/${m[1]}")`;
    else thumb.textContent=val?(/^https?:/i.test(val)?"link":/^asset:/.test(val)?"ficheiro":"Media"):"sem"; };
  pinta(v);
  const inp=el("input",{id,type:"text",placeholder:"nome na pasta Media ou link"});
  inp.value=v.startsWith("asset:")?v.replace(/^asset:[^/]+\//,"carregado: "):v;
  inp.dataset.p=JSON.stringify(path);
  if(!podeEscrever) inp.disabled=true;
  inp.addEventListener("input",()=>{ if(inp.value.startsWith("carregado: ")) return; setv(key,path,inp.value.trim()); pinta(inp.value.trim()) });
  const ctl=el("div",{class:"ctl"},inp);
  const box=el("div",{class:"media"},thumb,ctl);
  const enviar=async file=>{
    if(!assetsNS){ estadoGrav("Sem permissão para carregar ficheiros: use a pasta Media ou um link.","err"); return }
    if(file.size>20*1024*1024){ estadoGrav("O ficheiro passa dos 20 MB: ponha-o na pasta Media ou use um link.","err"); return }
    estadoGrav("A carregar "+file.name+"...");
    try{ const r=await assetsNS.upload(file); const val="asset:"+r.id+"/"+file.name.replace(/[^\w.\-]+/g,"-");
      setv(key,path,val,{now:true}); inp.value="carregado: "+val.replace(/^asset:[^/]+\//,""); pinta(val); estadoGrav("Carregado às "+hora()) }
    catch(err){ estadoGrav(err&&err.code==="unsupported_type"?"Esse tipo de ficheiro não é aceite.":"Não carregou o ficheiro. Tente de novo.","err") }
  };
  if(assetsNS&&podeEscrever){
    const fi=el("input",{type:"file",hidden:"",accept:"image/*,video/*,.pdf,.svg"});
    fi.onchange=()=>{ if(fi.files[0]) enviar(fi.files[0]) };
    const b=el("button",{class:"btn sm",type:"button"},"Carregar"); b.onclick=()=>fi.click();
    ctl.append(b,fi);
    box.ondragover=e=>{ e.preventDefault(); box.classList.add("over") };
    box.ondragleave=()=>box.classList.remove("over");
    box.ondrop=e=>{ e.preventDefault(); box.classList.remove("over"); const f=e.dataTransfer.files&&e.dataTransfer.files[0]; if(f) enviar(f) };
  }
  if(v){ const x=el("button",{class:"ib",type:"button",title:"Tirar ficheiro","aria-label":"Tirar ficheiro"},"×"); x.onclick=()=>{ setv(key,path,"",{now:true}); inp.value=""; pinta("") }; if(podeEscrever) ctl.append(x) }
  return el("div",{class:"f"},el("span",{},label,ajuda?el("em",{text:ajuda}):""),box);
}

/* ---------- cartão: dados gerais ---------- */
function cartaoCfg(){
  const k="cfg", c=(view("cfg").config)||{}; const P=a=>["config",...a];
  const aberto=ED.aberta==="cfg";
  const h=el("div",{class:"card-h"},el("span",{class:"num",text:"·"}),
    el("div",{class:"tt"},el("b",{text:"Dados gerais"}),el("small",{text:[c.cliente,c.marca,c.formato,c.idiomas].filter(Boolean).join(" · ")})),
    el("div",{class:"tools"},el("span",{class:"chip blk",text:aberto?"Fechar":"Abrir"})));
  h.onclick=()=>abrirSec("cfg");
  const card=el("section",{class:"card cfg",id:"c-cfg"},h);
  if(!aberto) return card;
  const corpo=el("div",{class:"card-b"},
    el("div",{class:"row2"},
      campo({key:k,path:P(["titulo"]),label:"Título da apresentação",traduz:true,ex:"ex.: Galp 2027"}),
      campo({key:k,path:P(["barra"]),label:"Texto da barra de topo",traduz:true,ex:"ex.: YOUNGNETWORK · PROPOSTA 2027"})),
    el("div",{class:"row2"},
      campo({key:k,path:P(["cliente"]),label:"Cliente"}),
      campo({key:k,path:P(["marca"]),label:"Marca que assina",tipo:"select",ex:MARCAS}),
      campo({key:k,path:P(["formato"]),label:"Formato",tipo:"select",ex:["Página","Reel"]}),
      campo({key:k,path:P(["idiomas"]),label:"Idiomas",tipo:"select",ex:["PT+EN","PT","PT+EN+ES","EN"]})),
    el("div",{class:"row2"},
      el("div",{class:"f"},el("span",{},"Acesso"),interruptor(k,P(["com_senha"]),"Só abre com senha")),
      c.com_senha!==false?campo({key:k,path:P(["senha"]),label:"Senha do cliente",ajuda:"em branco, o sistema cria uma"}):"",
      el("div",{class:"f"},el("span",{},"Resumo"),interruptor(k,P(["one_page"]),"Gerar também a one page")),
      c.formato==="Reel"?el("div",{class:"f"},el("span",{},"Reel"),interruptor(k,P(["autoplay"]),"Abre a correr sozinho")):""),
    el("div",{class:"row2"},
      campo({key:k,path:P(["cor1"]),label:"Cor principal",ajuda:"hexadecimal, só para trocar a da marca",ex:"#E74F3D"}),
      campo({key:k,path:P(["cor2"]),label:"Cor secundária",ex:"#0044FF"}),
      campo({key:k,path:P(["pedido_por"]),label:"Email de quem pede",tipo:"email",ajuda:"recebe os links e as senhas"})),
    campoMedia({key:k,path:P(["logo_cliente"]),label:"Logótipo do cliente",ajuda:"opcional"}));
  card.append(corpo); return card;
}

/* ---------- cartão: secção ---------- */
function cartaoSec(sid,i){
  const v=view(sid), b=BL[v.bloco]||BL["Bloco livre"], aberto=ED.aberta===sid, n=ordem().length;
  const mexe=(d)=>{ const o=ordem(); const j=o.indexOf(sid), t=j+d; if(t<0||t>=o.length) return; [o[j],o[t]]=[o[t],o[j]]; setv("cfg",["ordem"],o,{now:true}); desenhar() };
  const up=el("button",{class:"ib",type:"button",title:"Subir","aria-label":"Subir secção"},"↑"); up.disabled=i===0||!podeEscrever; up.onclick=e=>{ e.stopPropagation(); mexe(-1) };
  const dn=el("button",{class:"ib",type:"button",title:"Descer","aria-label":"Descer secção"},"↓"); dn.disabled=i===n-1||!podeEscrever; dn.onclick=e=>{ e.stopPropagation(); mexe(1) };
  const tools=el("div",{class:"tools"},
    el("span",{class:"chip who","data-who":sid,hidden:""}),
    v.escrever_no_draft?el("span",{class:"chip wr",text:"Escreve no draft"}):"",
    v.incluir===false?el("span",{class:"chip blk",text:"Fora do deck"}):"", up, dn);
  const h=el("div",{class:"card-h"},el("span",{class:"num",text:String(i+1)}),
    el("div",{class:"tt"},el("b",{text:tituloSec(sid)}),el("small",{"data-sum":sid,text:resumoSec(sid)})),tools);
  h.onclick=()=>abrirSec(sid);
  const card=el("section",{class:"card"+(v.incluir===false?" off":""),id:"c-"+sid},h);
  if(!aberto) return card;

  const troca=el("button",{class:"btn sm",type:"button"},"Trocar bloco"); troca.onclick=()=>galeria(sid); if(!podeEscrever) troca.disabled=true;
  const corpo=el("div",{class:"card-b"});
  const blk=el("div",{class:"blkrow"}); blk.innerHTML=sk(b.tipo); blk.append(el("p",{},el("b",{text:v.bloco}),b.desc),troca);
  corpo.append(blk);
  corpo.append(el("div",{class:"row2"},
    campo({key:sid,path:["menu"],label:"Nome no menu",traduz:true,ex:"ex.: Resultados"}),
    el("div",{class:"f"},el("span",{},"No deck"),interruptor(sid,["incluir"],"Incluir esta secção")),
    (view("cfg").config||{}).formato==="Reel"?campo({key:sid,path:["dur"],label:"Duração no reel (s)",ex:"8"}):""));
  // ideias + escrita
  const ide=campo({key:sid,path:["ideias"],label:"Ideias",ajuda:"em bruto: o que quer dizer nesta secção",multi:true}); ide.classList.add("ideias");
  corpo.append(ide, linhaEscrever(sid));
  // campos do bloco
  const cab=b.cab.filter(c=>c.k!=="pedido");
  const grid=el("div",{class:"row2"});
  cab.forEach(c=>{
    if(c.k==="media") return;
    grid.append(campo({key:sid,path:["cab",c.k],label:c.l,traduz:c.t,multi:c.k==="text",ajuda:c.k==="text"?"até 40 palavras":""}));
  });
  corpo.append(grid);
  const med=b.cab.find(c=>c.k==="media"); if(med) corpo.append(campoMedia({key:sid,path:["cab","media"],label:med.l,ajuda:"imagem ou vídeo"}));
  if(b.tab.length) corpo.append(listaItens(sid,b));
  corpo.append(campo({key:sid,path:["cab","pedido"],label:"Como deve ficar",ajuda:v.bloco==="Bloco livre"?"obrigatório neste bloco":"opcional",multi:true,ex:"ex.: vídeo à esquerda, números à direita"}));
  const apagar=el("button",{class:"btn sm",type:"button"},"Tirar secção do deck");
  apagar.onclick=()=>{ if(apagar.dataset.ok){ setv("cfg",["ordem"],ordem().filter(x=>x!==sid),{now:true}); ED.aberta=null; desenhar(); return }
    apagar.dataset.ok="1"; apagar.textContent="Carregue outra vez para tirar"; apagar.classList.add("primary") };
  if(podeEscrever) corpo.append(el("div",{class:"actions"},apagar));
  card.append(corpo); return card;
}
function linhaEscrever(sid){
  const v=view(sid), box=el("div",{class:"write"});
  if(!podeEscrever) return box;
  const ja=el("button",{class:"btn sm primary",type:"button"},"Escrever agora com o Claude");
  ja.onclick=()=>escreverAgora(sid,ja);
  const nd=el("button",{class:"btn sm",type:"button"},v.escrever_no_draft?"Não escrever no draft":"Escrever no próximo draft");
  nd.onclick=()=>{ setv(sid,["escrever_no_draft"],!v.escrever_no_draft,{now:true}); desenhar() };
  box.append(ja,nd);
  if(ED.prev[sid]){ const u=el("button",{class:"btn sm",type:"button"},"Desfazer"); u.onclick=()=>{ const p=ED.prev[sid]; delete ED.prev[sid]; for(const k in p) setv(sid,["cab",k],p[k],{now:true}); desenhar() }; box.append(u) }
  box.append(el("span",{class:"note2",id:"wn-"+sid,text:v.escrever_no_draft?"O sistema escreve os textos a partir das ideias no próximo draft, na conta do JD.":"Agora: gasta do seu plano Claude. No draft: não gasta nada, vê-se no draft."}));
  return box;
}
async function escreverAgora(sid,btn){
  const nota2=$("#wn-"+sid), v=view(sid), b=BL[v.bloco]||BL["Bloco livre"], cfg=view("cfg").config||{};
  if(!(v.ideias||"").trim()){ nota2.textContent="Escreva primeiro as ideias desta secção."; return }
  if(!sampleNS) sampleNS=await claude.use("sample");
  if(!sampleNS){ nota2.textContent="O Claude não está disponível nesta vista. Use \"Escrever no próximo draft\"."; return }
  btn.disabled=true; btn.textContent="A escrever..."; nota2.textContent="O Claude está a escrever. Pode demorar uns segundos.";
  const campos=b.cab.filter(c=>c.t).map(c=>`"${c.k}" (${c.l})`).join(", ");
  const temLista=b.tab.length&&!itensDe(v).length;
  const colunas=b.tab.filter(c=>c.k!=="media"&&c.k!=="poster").map(c=>`"${c.k}" (${c.l}${c.a?": "+c.a:""})`).join(", ");
  const pedido=`És redator do YoungNetwork Group. Escreve os textos de uma secção de uma apresentação web.
Marca: ${cfg.marca||"YoungNetwork Group"}. ${TOM[cfg.marca]||"Tom profissional, claro e direto."}
Cliente: ${cfg.cliente||"(não indicado)"}. Deck: ${tr(cfg.titulo).pt||""}.
Bloco: ${v.bloco} (${b.desc}).
Ideias do autor:
"""${v.ideias}"""
Regras: português de Portugal; sem travessões (usa vírgulas, dois pontos ou parênteses); usa só o que está nas ideias, nunca inventes números, nomes, datas, clientes ou resultados; pequeno título até 4 palavras; título até 8 palavras; texto até 40 palavras.
Responde só com JSON com as chaves ${campos}${temLista?`, e "itens": uma lista de objetos com as chaves ${colunas} (uma linha por elemento que as ideias referem; só o que lá está)`:""}, e "falta": o que faltou nas ideias para completar (texto curto, ou vazio).`;
  try{
    const r=await sampleNS.json(pedido,{modelTier:"default"});
    const prev={}; b.cab.filter(c=>c.t).forEach(c=>{ if(typeof r[c.k]==="string"&&r[c.k].trim()){ prev[c.k]=clone(getv(sid,["cab",c.k])||{pt:"",en:""}); setv(sid,["cab",c.k],{pt:r[c.k].trim(),en:"",en_m:false}) } });
    if(temLista&&Array.isArray(r.itens)) r.itens.slice(0,15).forEach((it,j)=>{ const d={o:j+1,incluir:true}; b.tab.forEach(c=>{ const x=it[c.k]; if(x==null||x==="") return; d[c.k]=c.t?{pt:String(x),en:""}:String(x) }); setv(sid,["itens",nid("i")],d) });
    ED.prev[sid]=prev; flush(sid);
    desenhar(); const n=$("#wn-"+sid); if(n) n.textContent="Escrito. Reveja e corrija o que precisar."+(r.falta?" Faltou: "+r.falta:"");
  }catch(err){
    btn.disabled=false; btn.textContent="Escrever agora com o Claude";
    nota2.textContent=err&&err.code==="not_granted"?"Sem autorização para usar o Claude aqui. Use \"Escrever no próximo draft\".":err&&err.code==="rate_limited"?"Chegou ao limite do seu plano por agora. Use \"Escrever no próximo draft\".":"Não conseguiu escrever. Tente outra vez ou use \"Escrever no próximo draft\".";
  }
}

/* ---------- listas (cases, números, contactos...) ---------- */
function listaItens(sid,b){
  const its=itensDe(view(sid));
  const box=el("div",{class:"items"},el("b",{text:"Elementos · "+its.length}));
  its.forEach((it,j)=>{
    const flds=el("div",{class:"flds"});
    b.tab.forEach(c=>{
      const path=["itens",it.id,c.k];
      if(c.k==="media"||c.k==="poster") flds.append(campoMedia({key:sid,path,label:c.l}));
      else flds.append(campo({key:sid,path,label:c.l,traduz:c.t,multi:c.k==="text",ex:c.ex||c.a,wide:c.k==="text"}));
    });
    const tro=(d)=>{ const o=its[j+d]; if(!o) return; setv(sid,["itens",it.id,"o"],o.o||j+1+d); setv(sid,["itens",o.id,"o"],it.o||j+1,{now:true}); desenhar() };
    const up=el("button",{class:"ib",type:"button","aria-label":"Subir"},"↑"); up.disabled=j===0; up.onclick=()=>tro(-1);
    const dn=el("button",{class:"ib",type:"button","aria-label":"Descer"},"↓"); dn.disabled=j===its.length-1; dn.onclick=()=>tro(1);
    const vis=el("button",{class:"ib",type:"button",title:it.incluir===false?"Mostrar no deck":"Esconder do deck","aria-label":"Mostrar ou esconder"},it.incluir===false?"◌":"●"); vis.onclick=()=>{ setv(sid,["itens",it.id,"incluir"],it.incluir===false,{now:true}); desenhar() };
    const x=el("button",{class:"ib",type:"button",title:"Apagar","aria-label":"Apagar elemento"},"×"); x.onclick=()=>{ setv(sid,["itens",it.id,"apagado"],true,{now:true}); desenhar() };
    const ctl=podeEscrever?el("div",{class:"ctl"},up,dn,vis,x):el("div");
    box.append(el("div",{class:"it"+(it.incluir===false?" off":"")},flds,ctl));
  });
  if(podeEscrever){ const add=el("button",{class:"btn sm",type:"button"},"+ Juntar elemento"); add.onclick=()=>{ const m=Math.max(0,...its.map(i=>i.o||0)); setv(sid,["itens",nid("i")],{o:m+1,incluir:true},{now:true}); desenhar() }; box.append(add) }
  if(its.length>=15) box.append(el("p",{class:"note",text:"O motor usa até 15 elementos por secção."}));
  return box;
}

/* ---------- galeria de blocos ---------- */
function galeria(sid){
  const d=el("dialog",{class:"gal"});
  const fechar=el("button",{class:"btn sm",type:"button"},"Fechar"); fechar.onclick=()=>d.close();
  const g=el("div",{class:"gal-g"});
  const atual=sid?view(sid).bloco:null;
  Object.entries(BL).forEach(([nome,b])=>{
    const bt=el("button",{type:"button","aria-current":String(nome===atual)}); bt.innerHTML=sk(b.tipo); bt.append(el("b",{text:nome}),el("small",{text:b.desc}));
    bt.onclick=async()=>{ d.close();
      if(sid){ setv(sid,["bloco"],nome,{now:true}); desenhar(); return }
      const novo=nid("s"); const agora=new Date().toISOString();
      try{ await db.doc("fichas/"+ED.id+"/seccoes/"+novo).set({bloco:nome,incluir:true,menu:{pt:"",en:""},ideias:"",cab:{},itens:{},criado_em:agora});
        setv("cfg",["ordem"],[...ordem(),novo],{now:true}); ED.aberta=novo; setTimeout(()=>abrirSec(novo,true),300) }
      catch(err){ estadoGrav("Não foi possível juntar a secção.","err") } };
    g.append(bt);
  });
  d.append(el("div",{class:"gal-h"},el("h2",{text:sid?"Trocar bloco":"Escolha o bloco da nova secção"}),fechar),g);
  d.addEventListener("close",()=>d.remove());
  document.body.append(d); d.showModal();
}
