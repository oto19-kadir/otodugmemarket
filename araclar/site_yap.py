#!/usr/bin/env python3
"""Sitedeki araç seçicinin verisini üretir ve sayfalara bağlar.

  python3 araclar/site_yap.py            # ortak liste (kullanıcı listesi ∩ ek liste)
  python3 araclar/site_yap.py --hepsi    # birleşik listenin tamamı

Üretilenler:
  arac/<marka>.txt   karıştırılmış (XOR + base64) araç verisi, marka marka
  arac/secici.js     seçici arayüzü (ana sayfa + ürün sayfaları)
  index.html         ana sayfaya seçici bloğu + filtre bağlantısı
  urun/*/index.html  ürün sayfalarına "Aracınıza uyar mı?" bloğu
"""
import base64, contextlib, io, json, os, re, runpy, sys
from collections import defaultdict, OrderedDict

KOK = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(KOK)
ANAHTAR = b"OtoDugme19Kartal"
HEPSI = "--hepsi" in sys.argv

# ---------- araç verisi ----------
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(KOK, "excel_yap.py"))
kul, ek, tum, kodlar = g["kul"], g["ek"], g["tum"], g["kodlar"]
if HEPSI:
    araclar = tum
else:
    bende = defaultdict(set)
    for r in ek:
        for k in kodlar(r["kod"]):
            bende[(r["marka"], r["anahtar"], k)] |= r["yillar"]
    araclar = [r for r in kul if any(bende.get((r["marka"], r["anahtar"], k), set()) & r["yillar"]
                                     for k in kodlar(r["kod"]))]

# ---------- ürünler ----------
html = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
DATA = json.loads(re.search(r"const DATA=(\[.*?\]\]);", html, re.S).group(1))
GRUP = {"Volkswagen": {"VW - SEAT"}, "Seat": {"VW - SEAT"}, "Skoda": {"ŠKODA", "VW - SEAT"},
        "Audi": {"AUDI", "VW - SEAT"}, "Porsche": {"PORSCHE"},
        "Mercedes-Benz": {"MERCEDES-BENZ  -  SMART"}, "Smart": {"MERCEDES-BENZ  -  SMART"}}

ROMA = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
NESIL = {  # ürün adındaki nesil -> yıl aralığı
    "golf": {3: (1991, 1998), 4: (1997, 2004), 5: (2003, 2009), 6: (2008, 2013), 7: (2012, 2020),
             7.5: (2017, 2020), 8: (2019, 2026)},
    "jetta": {3: (2005, 2010)},  # üründe Golf V ile birlikte geçiyor
    "passat": {"B5": (1996, 2005), "B6": (2005, 2010), "B7": (2010, 2015), "B8": (2014, 2023)},
    "multivan": {"T4": (1990, 2003), "T5": (2003, 2015), "T6": (2015, 2024), "T7": (2022, 2026)},
    "transporter": {"T4": (1990, 2003), "T5": (2003, 2015), "T6": (2015, 2024), "T7": (2022, 2026)},
    "caravelle": {"T4": (1990, 2003), "T5": (2003, 2015), "T6": (2015, 2024), "T7": (2022, 2026)},
    "tiguan": {2: (2016, 2024)}, "polo": {5: (2009, 2017), 6: (2017, 2026)},
}
modeller = defaultdict(set)  # grup -> model anahtarları
for r in araclar:
    for gr in GRUP[r["marka"]]:
        modeller[gr].add(r["anahtar"])
for gr in modeller:
    if gr == "VW - SEAT": modeller[gr] |= {"transporter", "caravelle", "multivan"}


def yil2(a):
    a = int(a); return 1900 + a if a > 40 else 2000 + a


def ipucu(model, metin):
    """Model kelimesinden sonra gelen nesil / yıl bilgisini yıl aralığına çevirir."""
    m = re.match(r"\s*(\d\d)\s*-\s*(\d\d)(?!\d)", metin)
    if m: return (yil2(m.group(1)), yil2(m.group(2)))
    m = re.match(r"\s*(\d\d)\s*->", metin)
    if m: return (yil2(m.group(1)), 2026)
    tab = NESIL.get(model, {})
    m = re.match(r"\s*(VIII|VII|VI|IV|V|III|II|I|7\.5|\d)(?![\w.])", metin)
    if m and tab:
        v = m.group(1); n = ROMA.get(v) or float(v) if v != "7.5" else 7.5
        n = int(n) if n != 7.5 else 7.5
        if n in tab: return tab[n]
    m = re.match(r"\s*(B\d)\b", metin)
    if m and m.group(1) in tab: return tab[m.group(1)]
    m = re.match(r"\s*(\d\d)(?!\d|\s*-)", metin)  # tek yıl: "Q4 22"
    if m and model.startswith(("q", "a", "e")): y = yil2(m.group(1)); return (y, y)
    return None


def urun_modelleri(ad, grup):
    ad = re.sub(r"(\d\d)\s+-\s+(\d\d)(?!\d)", r"\1-\2", ad.upper())
    parcalar, sonuc = [p.strip() for p in ad.split(" - ")], []
    for i, p in enumerate(parcalar):
        tok = re.match(r"(T[4-7])\b", p)
        if tok and grup == "VW - SEAT":
            sonuc.append([i, "multivan", NESIL["multivan"][tok.group(1)]]); continue
        for m in sorted(modeller.get(grup, ())):
            for mm in re.finditer(r"(?<![A-Z0-9])" + re.escape(m.upper()) + r"(?![A-Z0-9])", p):
                y = ipucu(m, p[mm.end():])
                if y is None:  # "POLO CLASSIC 00-01": yıl biraz ileride olabilir
                    ym = re.search(r"(?<!\d)(\d\d)\s*-\s*(\d\d)(?!\d)|(?<!\d)(\d\d)\s*->", p[mm.end():])
                    if ym: y = ipucu(m, ym.group(0))
                sonuc.append([i, m, y])
    # ipucu olmayanlar en yakın ipucunu alır (önce soldaki, yoksa sağdaki)
    for s in sonuc:
        if s[2] is None:
            sol = [t for t in sonuc if t[2] and t[0] < s[0]]
            sag = [t for t in sonuc if t[2] and t[0] > s[0]]
            if sol: s[2] = sol[-1][2]
            elif sag: s[2] = sag[0][2]
    return [(m, y) for _, m, y in sonuc]


urunler = []
for d in DATA:
    code, name, oem, grup, slug = d[0], d[1], d[2], d[3], d[4]
    urunler.append(dict(slug=slug, grup=grup, mods=urun_modelleri(name, grup)))


def kasalar(metin):
    """'W204' / '901-905' / '907 / 910' / '124 SAĞ' -> {204} ..."""
    out = set()
    for a, b in re.findall(r"(?<!\d)(\d{3})\s*-\s*(\d{3})(?!\d)", metin):
        if b > a and int(b) - int(a) < 10: out |= {str(x) for x in range(int(a), int(b) + 1)}
    out |= set(re.findall(r"(?<![\d.,])[A-Z]?(\d{3})(?![\d.,])", metin.upper()))
    return out


for u in urunler:
    u["kasa"] = kasalar(next(d[1] for d in DATA if d[4] == u["slug"]))


def uyar(arac, u):
    if u["grup"] not in GRUP[arac["marka"]]: return False
    if arac["marka"] == "Mercedes-Benz":
        k = kasalar(arac["ad"][arac["ad"].rfind("("):])
        return bool(k & u["kasa"])
    a, b = min(arac["yillar"]), max(arac["yillar"])
    for m, y in u["mods"]:
        if m != arac["anahtar"]: continue
        if y is None: return True
        ortak = min(b, y[1]) - max(a, y[0]) + 1  # aracın yıllarının en az yarısı aralıkta olmalı
        if ortak > 0 and ortak * 2 >= (b - a + 1): return True
    return False


# ---------- dosyalar ----------
def karistir(obj):
    b = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
    return base64.b64encode(bytes(c ^ ANAHTAR[i % len(ANAHTAR)] for i, c in enumerate(b))).decode()


cikis = os.path.join(SITE, "arac")
os.makedirs(cikis, exist_ok=True)
for f in os.listdir(cikis):
    if f.endswith(".txt"): os.remove(os.path.join(cikis, f))
markalar = OrderedDict()
ozet = {}
for marka in g["MARKALAR"]:
    rows = [r for r in araclar if r["marka"] == marka]
    if not rows: continue
    sluglar, sidx, mod = [], {}, OrderedDict()
    for r in sorted(rows, key=lambda r: (r["anahtar"], r["ad"].casefold(), min(r["yillar"]))):
        uy = []
        for u in urunler:
            if uyar(r, u):
                if u["slug"] not in sidx: sidx[u["slug"]] = len(sluglar); sluglar.append(u["slug"])
                uy.append(sidx[u["slug"]])
        model_ad = r["ad"][len(marka):].strip().split()[0]
        y = sorted(r["yillar"]); yil = f"{y[0]}–{y[-1]}" if y[0] != y[-1] else str(y[0])
        etiket = " · ".join(x for x in [r["ad"][len(marka) + len(model_ad) + 1:].strip().lstrip("/ "), r["kod"],
                                        f'{r["hp"]} hp' if r["hp"] else "", r["yakit"],
                                        r["sz"].replace(" Şanzıman", ""), yil] if x)
        mod.setdefault(model_ad, []).append([etiket, uy])
    dosya = re.sub(r"[^a-z]", "", marka.lower())
    open(os.path.join(cikis, dosya + ".txt"), "w").write(karistir({"m": mod, "p": sluglar}))
    markalar[marka] = dosya
    ozet[marka] = (len(rows), sum(1 for v in mod.values() for e in v if e[1]), len(sluglar))
open(os.path.join(cikis, "m.txt"), "w").write(karistir(markalar))

JS = r"""/* OtoDüğme araç seçici */
(function(){
var K="__ANAHTAR__",B="/arac/",C={};
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
""".replace("__ANAHTAR__", ANAHTAR.decode())
open(os.path.join(cikis, "secici.js"), "w").write(JS)

# ---------- sayfalara bağla ----------
I0, I1 = "<!--arac-->", "<!--/arac-->"
def yerlestir(metin, once, blok):
    metin = re.sub(re.escape(I0) + ".*?" + re.escape(I1), "", metin, flags=re.S)
    assert once in metin, once
    return metin.replace(once, I0 + blok + I1 + once, 1)

h = yerlestir(html, '<h2>Parçalar</h2>', '<section id="as"></section><script src="/arac/secici.js" defer></script>')
if "S.v" not in h:
    h = h.replace("const S={q:\"\",g:\"\",lim:48};", "const S={q:\"\",g:\"\",lim:48,v:null};window.aracSec=v=>{S.v=v;S.lim=48;render()};", 1)
    h = h.replace("items.filter(it=>(!S.g||it.g===S.g)&&", "items.filter(it=>(!S.v||S.v.has(it.s))&&(!S.g||it.g===S.g)&&", 1)
    assert "S.v.has" in h and "window.aracSec" in h
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(h)

say = 0
for slug in os.listdir(os.path.join(SITE, "urun")):
    p = os.path.join(SITE, "urun", slug, "index.html")
    if not os.path.exists(p): continue
    t = open(p, encoding="utf-8").read()
    once = '<p style="color:var(--mu)">Aracınıza uyumunu'
    if once not in t: continue
    t = yerlestir(t, once, f'<div id="uy" data-u="{slug}"></div><script src="/arac/secici.js" defer></script>')
    open(p, "w", encoding="utf-8").write(t); say += 1

print("Kaynak:", "birleşik liste" if HEPSI else "ortak liste", "| araç satırı:", len(araclar))
for m, (n, e, p) in ozet.items():
    print(f"  {m}: {n} araç, {e} tanesine en az 1 parça eşleşti, {p} farklı parça")
print("Ürün sayfası güncellendi:", say)
