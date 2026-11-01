#!/usr/bin/env python3
"""Araç listesi Excel'ini üretir: araclar/Arac_Listesi.xlsx

Kaynaklar:
  veri/kullanici_vag.tsv  -> kullanıcının verdiği liste (öncelikli, olduğu gibi alınır)
  veri/*.txt              -> ek liste; kullanıcı listesinde aynı model + motor kodu + yıl
                             varsa atlanır, yoksa eklenir. Kullanıcı listesinde boş/0 olan
                             beygirler buradan doldurulur.
"""
import os, re
from collections import OrderedDict, defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

KOK = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(KOK, "veri")
MARKALAR = ["Volkswagen", "Seat", "Skoda", "Audi", "Porsche", "Mercedes-Benz", "Smart"]
DOSYALAR = ["vw", "seat", "skoda", "audi", "porsche", "mercedes"]
YAKIT = {"B": "Benzinli", "D": "Dizel", "H": "Hibrit", "E": "Elektrikli", "L": "LPG"}
BASLIK = ["Model", "Motor Kodları", "Beygir Gücü", "Yakıt", "Şanzıman", "Model Yılları"]


def sanziman(k, marka):
    n = re.sub(r"\D", "", k)
    if k.startswith("DSG"): return f"DSG{n} Şanzıman"
    if k.startswith("ST"): return "S-Tronic Şanzıman"
    if k.startswith("PDK"): return "PDK Şanzıman"
    if k.startswith("DCT"): return f"{n}G-DCT Şanzıman" if marka == "Mercedes-Benz" else f"DCT{n} Şanzıman"
    if k.startswith("ASG"): return "Yarı Otomatik (ASG) Şanzıman"
    if k == "CVT": return "CVT Şanzıman"
    if k == "1A": return "Tek Vites Şanzıman"
    if k[0] == "M": return "Manuel Şanzıman"
    if k[0] == "A":
        if marka == "Mercedes-Benz" and n in ("5", "7", "9"): return f"{n}G-Tronic Şanzıman"
        return f"{n} ileri Otomatik Şanzıman"
    if k[0] == "T": return f"{n} ileri Tiptronic Şanzıman"
    return k


def model_anahtar(ad, marka):
    """'Seat Leon 1.4 TSI (5F1)' -> 'leon'"""
    kalan = ad[len(marka):].strip()
    return re.split(r"[\s/]+", kalan)[0].lower()


def kodlar(s):
    return [k for k in re.split(r"[\s,./()]+", s.upper()) if re.fullmatch(r"[A-Z0-9]{3,6}", k)]


# ---- 1) Ek liste (txt) ----
ek = []
for dosya in DOSYALAR:
    marka = model = kasa = None
    for no, l in enumerate(open(os.path.join(VERI, dosya + ".txt"), encoding="utf-8"), 1):
        l = l.strip()
        if not l: continue
        if l.startswith("#"):
            p = [x.strip() for x in l[1:].split("|")]
            if len(p) == 3: marka, model, kasa = p
            continue
        p = [x.strip() for x in l.split("|")]
        assert len(p) == 6, (dosya, no, l)
        motor, kod, hp, yk, sz, yil = p
        a, b = map(int, yil.split("-"))
        m0 = model.split()[0]
        if motor.split()[0] == m0 or (model.endswith("Serisi") and motor[0] == m0[0]):
            ad = f"{marka} {motor} ({kasa})"
        else:
            ad = f"{marka} {model} {motor} ({kasa})"
        ek.append(dict(marka=marka, ad=ad, kod=kod, hp=int(hp), yakit=YAKIT[yk],
                       sz=sanziman(sz, marka), yillar=set(range(a, b + 1)),
                       anahtar=model.split()[0].lower()))

# ---- 2) Kullanıcı listesi ----
DUZELT = [(r"(\d\.\d)16V", r"\1 16V"), (r"\bG[Uu][Aa][Tt][Tt][Rr][Oo]\b", "quattro"),
          (r"\bTESI\b", "TFSI"), (r"\bTSFI\b", "TFSI"), (r"\bTFSi\b", "TFSI"),
          (r"(\d),(\d)", r"\1.\2"), (r"\bMPi\b", "MPI"), (r" ve Quattro", " e quattro")]
kul = []
for i, l in enumerate(open(os.path.join(VERI, "kullanici_vag.tsv"), encoding="utf-8")):
    p = [x.strip() for x in l.rstrip("\n").split("\t")]
    if i == 0 or len(p) < 6: continue
    ad, kod, hp, yakit, sz, yil = p[:6]
    for a, b in DUZELT: ad = re.sub(a, b, ad)
    marka = next(m for m in MARKALAR if ad.startswith(m))
    m = re.search(r"\d+", hp)
    kul.append(dict(marka=marka, ad=ad, kod=kod, hp=int(m.group()) if m else 0, yakit=yakit,
                    sz=sz, yillar={int(y) for y in re.findall(r"\d{4}", yil)},
                    anahtar=model_anahtar(ad, marka)))

# ---- 3) Kullanıcı listesinde eksik beygirleri doldur ----
hp_model, hp_kod = defaultdict(set), defaultdict(set)
for r in ek:
    for k in kodlar(r["kod"]):
        hp_model[(r["marka"], r["anahtar"], k)].add(r["hp"])
        hp_kod[(r["marka"], k)].add(r["hp"])
dolan = 0
for r in kul:
    if r["hp"]: continue
    for tablo, anah in ((hp_model, lambda k: (r["marka"], r["anahtar"], k)),
                        (hp_kod, lambda k: (r["marka"], k))):
        bul = set().union(*[tablo.get(anah(k), set()) for k in kodlar(r["kod"])] or [set()])
        if len(bul) == 1:
            r["hp"] = bul.pop(); dolan += 1; break

# ---- 4) Ek listeden, kullanıcı listesinde olmayanları al ----
var = defaultdict(set)  # (marka, model, kod) -> yıllar
for r in kul:
    for k in kodlar(r["kod"]):
        var[(r["marka"], r["anahtar"], k)] |= r["yillar"]
ek_kalan = [r for r in ek
            if not any(var.get((r["marka"], r["anahtar"], k), set()) & r["yillar"] for k in kodlar(r["kod"]))
            or not kodlar(r["kod"])]
# boş kodlu yeni araçlar: kullanıcı listesinde aynı model+beygir+yıl varsa atla
ek_kalan = [r for r in ek_kalan if kodlar(r["kod"]) or not any(
    u["marka"] == r["marka"] and u["anahtar"] == r["anahtar"] and u["hp"] == r["hp"]
    and u["yillar"] & r["yillar"] for u in kul)]

# aynı ad + beygir + yakıt + şanzıman olan ek satırları birleştir (kodlar virgülle)
grup = OrderedDict()
for r in ek_kalan:
    g = grup.setdefault((r["ad"], r["hp"], r["yakit"], r["sz"]), dict(r, kod_l=[], yillar=set()))
    for k in [x.strip() for x in r["kod"].split(",") if x.strip()]:
        if k not in g["kod_l"]: g["kod_l"].append(k)
    g["yillar"] |= r["yillar"]
for g in grup.values(): g["kod"] = ", ".join(g["kod_l"])

tum = kul + list(grup.values())
tum.sort(key=lambda r: (MARKALAR.index(r["marka"]), r["ad"].casefold(), min(r["yillar"]), r["sz"]))


def satir(r):
    return [r["ad"], r["kod"], f'{r["hp"]} beygir' if r["hp"] else "", r["yakit"], r["sz"],
            ", ".join(map(str, sorted(r["yillar"])))]


wb = Workbook(); wb.remove(wb.active)
GEN = [52, 30, 13, 11, 28, 70]
def sayfa(ad, rows):
    ws = wb.create_sheet(ad[:31]); ws.append(BASLIK)
    for r in rows: ws.append(satir(r))
    for i, g in enumerate(GEN, 1):
        ws.column_dimensions[get_column_letter(i)].width = g
        c = ws.cell(1, i); c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="0F1C2E"); c.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
sayfa("Tümü", tum)
for m in MARKALAR:
    rows = [r for r in tum if r["marka"] == m]
    if rows: sayfa(m, rows)
cikti = os.path.join(KOK, "Arac_Listesi.xlsx")
wb.save(cikti)

from collections import Counter
print(f"Kullanıcı satırı: {len(kul)} | beygiri doldurulan: {dolan} | "
      f"hâlâ beygirsiz: {sum(1 for r in kul if not r['hp'])}")
print(f"Ek satır (birleştirilmiş): {len(grup)} | Toplam: {len(tum)}")
print(Counter(r["marka"] for r in tum))
print(cikti)
