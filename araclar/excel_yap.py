#!/usr/bin/env python3
"""araclar/veri/*.txt dosyalarından araclar/VAG_Arac_Listesi.xlsx üretir."""
import glob, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

KOK = os.path.dirname(os.path.abspath(__file__))
YAKIT = {"B": "Benzinli", "D": "Dizel", "H": "Hibrit", "E": "Elektrikli", "L": "LPG"}
def sanziman(k):
    if k.startswith("DSG"): return f"{k} Şanzıman"
    if k.startswith("ST"): return f"S tronic {k[2:]} Şanzıman"
    if k.startswith("PDK"): return f"PDK{k[3:]} Şanzıman"
    if k.startswith("ASG"): return f"{k[3:]} ileri Yarı Otomatik (ASG)"
    if k == "CVT": return "Multitronic (CVT) Şanzıman"
    if k == "1A": return "Tek vites (Otomatik)"
    if k == "2A": return "2 ileri Otomatik"
    if k == "M4": return "4 ileri Manuel"
    if k[0] == "M": return f"{k[1:]} ileri Manuel"
    if k[0] == "A": return f"{k[1:]} ileri Otomatik"
    if k[0] == "T": return f"{k[1:]} ileri Tiptronic"
    return k

sira_m = ["Volkswagen", "Seat", "Skoda", "Audi", "Porsche"]
sira = ["vw", "seat", "skoda", "audi", "porsche"]
satirlar = []
for ad in sira:
    marka = model = kasa = None
    for no, l in enumerate(open(os.path.join(KOK, "veri", ad + ".txt"), encoding="utf-8"), 1):
        l = l.strip()
        if not l: continue
        if l.startswith("#"):
            p = [x.strip() for x in l[1:].split("|")]
            if len(p) == 3 and not p[0].startswith("Biçim"): marka, model, kasa = p
            continue
        p = [x.strip() for x in l.split("|")]
        assert len(p) == 6, (ad, no, l)
        motor, kod, hp, yk, sz, yil = p
        a, b = map(int, yil.split("-"))
        satirlar.append((marka, f"{marka} {model} {motor} ({kasa})", kod, f"{hp} beygir",
                         YAKIT[yk], sanziman(sz), ", ".join(map(str, range(a, b + 1))), a,
                         f"{model}|{kasa}", model, len(satirlar)))

# Marka > model adının ilk kelimesi > nesil başlangıç yılı > motor sırasına göre diz
ilk = {}
for i, r in enumerate(satirlar):
    nes = r[1].rsplit(" (", 1)[0]
    ilk.setdefault((r[0], r[8]), (r[9].split()[0], r[7], i))
satirlar.sort(key=lambda r: (sira_m.index(r[0]), ilk[(r[0], r[8])], r[10]))
wb = Workbook(); wb.remove(wb.active)
BAS = ["Araç", "Motor kodu", "Beygir", "Yakıt", "Şanzıman", "Yıllar"]
GEN = [44, 12, 12, 12, 30, 60]
def sayfa(ad, rows):
    ws = wb.create_sheet(ad[:31])
    ws.append(BAS)
    for r in rows: ws.append(list(r[1:7]))
    for i, g in enumerate(GEN, 1):
        ws.column_dimensions[get_column_letter(i)].width = g
        c = ws.cell(1, i); c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="0F1C2E"); c.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
sayfa("Tümü", satirlar)
for m in dict.fromkeys(r[0] for r in satirlar):
    sayfa(m, [r for r in satirlar if r[0] == m])
cikti = os.path.join(KOK, "VAG_Arac_Listesi.xlsx")
wb.save(cikti)
from collections import Counter
print(len(satirlar), Counter(r[0] for r in satirlar), cikti)
