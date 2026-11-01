/* OtoDüğme araç seçici */
(function(){
var K="OtoDugme19Kartal",B="/arac/",C={};
function ac(t){var s=atob(t.trim()),u=new Uint8Array(s.length);for(var i=0;i<s.length;i++)u[i]=s.charCodeAt(i)^K.charCodeAt(i%K.length);return JSON.parse(new TextDecoder().decode(u))}
function al(f){return C[f]||(C[f]=fetch(B+f+".txt").then(function(r){return r.text()}).then(ac))}
var st=document.createElement("style");st.textContent=".as{background:var(--sf);border:1px solid var(--ln);border-radius:14px;padding:14px 16px;margin:18px 0 4px;-webkit-user-select:none;user-select:none}.as b{display:block;margin-bottom:8px}.as .r{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}.as select{font:inherit;padding:11px;border-radius:10px;border:1px solid var(--ln);background:var(--bg);color:var(--ink);width:100%;min-width:0}.as select:disabled{opacity:.5}.as .s{margin-top:10px;font-weight:600}.as .ok{color:#1f9d55}.as .no{color:#c0392b}.as .t{margin-top:8px;color:var(--mu);font-size:.85rem}.as button{margin-top:10px;padding:7px 12px;font-size:.85rem}";document.head.appendChild(st);
function opt(s,ilk,liste){s.innerHTML='<option value="">'+ilk+'</option>'+liste.map(function(x,i){return '<option value="'+i+'">'+String(x).replace(/[&<>"]/g,"")+'</option>'}).join("");s.disabled=!liste.length}
function kur(el,baslik,sonuc){
 el.className="as";el.oncontextmenu=function(e){e.preventDefault()};
 el.innerHTML='<b>'+baslik+'</b><div class="r"><select aria-label="Marka"></select><select aria-label="Model" disabled></select><select aria-label="Motor" disabled></select></div><div class="s" role="status"></div><div class="t">Uyum bilgisi ürün adına göredir. Kesin uyum için şasi numaranızı WhatsApp’tan gönderin.</div>';
 var ss=el.querySelectorAll("select"),sm=ss[0],sd=ss[1],sv=ss[2],durum=el.querySelector(".s"),MK=[],D=null,MD=[];
 opt(sd,"Model",[]);opt(sv,"Motor / yıl",[]);
 al("m").then(function(m){MK=Object.keys(m);opt(sm,"Marka",MK);sm._m=m});
 sm.onchange=function(){opt(sd,"Model",[]);opt(sv,"Motor / yıl",[]);D=null;sonuc(null,durum);if(sm.value==="")return;
  al(sm._m[MK[sm.value]]).then(function(d){D=d;MD=Object.keys(d.m);opt(sd,"Model",MD)})};
 sd.onchange=function(){opt(sv,"Motor / yıl",[]);sonuc(null,durum);if(sd.value===""||!D)return;opt(sv,"Motor / yıl",D.m[MD[sd.value]].map(function(e){return e[0]}))};
 sv.onchange=function(){if(sv.value===""||!D){sonuc(null,durum);return}var e=D.m[MD[sd.value]][sv.value];
  sonuc(new Set(e[1].map(function(i){return D.p[i]})),durum,MK[sm.value]+" "+MD[sd.value]+" "+e[0])};
}
var ana=document.getElementById("as");
if(ana)kur(ana,"Aracınızı seçin, uyan parçaları gösterelim",function(set,durum,ad){
 if(window.aracSec)window.aracSec(set);
 durum.className="s";durum.textContent=set?(set.size?set.size+" parça aracınıza uyabilir: "+ad:"Bu araç için listede parça bulunamadı. WhatsApp’tan sorun."):"";
 if(set)durum.className="s "+(set.size?"ok":"no")});
var uy=document.getElementById("uy");
if(uy){var slug=uy.getAttribute("data-u");kur(uy,"Aracınıza uyar mı?",function(set,durum,ad){
 durum.className="s";if(!set){durum.textContent="";return}
 if(set.has(slug)){durum.className="s ok";durum.textContent="✓ Bu parça aracınıza uyabilir ("+ad+")."}
 else{durum.className="s no";durum.textContent="✗ Ürün adına göre bu araçla eşleşmiyor. Emin olmak için WhatsApp’tan sorun."}})}
})();
