#!/usr/bin/env python3
"""Düğme Instagram: sıradaki ürünlerin paylaşım görsellerini ve yazılarını hazırlar.

Kullanım:  python3 instagram/hazirla.py <başlangıç YYYY-AA-GG veya YYYY-AA-GGTSS> [gün sayısı=7]
- Paylaşım saatleri: her gün 09:00–22:00 arası saatte bir (14 paylaşım/gün), Europe/Istanbul.
- Daha önce paylaşılan veya sıraya konan ürünler instagram/paylasilan.json'da tutulur; tekrar seçilmez.
- Sadece resmi olan ürünler (DATA[5] == 1) seçilir; marka grupları sırayla karıştırılır.
- Çıktı: instagram/p/<kod>.jpg (1080x1350) ve instagram/sira.json (Metricool'a girilecek liste).
  Görsel adresi: https://raw.githubusercontent.com/oto19-kadir/otodugmemarket/claude/bold-keller-az3ld6/instagram/p/<kod>.jpg
  (instagram/ klasörü Netlify yayınını tetiklemez, netlify.toml'daki ignore kuralı.)
- Metin kuralları: düzgün Türkçe, garanti iddiası yok, ödeme/fiyat yazılmaz (fiyat WhatsApp'tan).
"""
import datetime as dt
import json
import os
import re
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IG = os.path.join(KOK, "instagram")
CIKIS = os.path.join(IG, "p")
KAYIT = os.path.join(IG, "paylasilan.json")
SIRA = os.path.join(IG, "sira.json")
HAM_URL = "https://raw.githubusercontent.com/oto19-kadir/otodugmemarket/claude/bold-keller-az3ld6/instagram/p/"
SAATLER = list(range(9, 23))

F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
LACI, TURUNCU, GRI, BEYAZ = (17, 26, 43), (232, 89, 12), (91, 103, 120), (255, 255, 255)

ETIKET = {  # marka grubu -> görselde sağ üstte yazan ad, etiketler
    "VW - SEAT": ("VW - SEAT", ["vw", "seat"]),
    "HYUNDAI - KIA": ("HYUNDAI - KIA", ["hyundai", "kia"]),
    "MERCEDES-BENZ  -  SMART": ("MERCEDES-BENZ", ["mercedesbenz", "smart"]),
    "AĞIR VASITA": ("AĞIR VASITA", ["agirvasita"]),
    "RENAULT - DACIA": ("RENAULT - DACIA", ["renault", "dacia"]),
    "OPEL - CHEVROLET": ("OPEL - CHEVROLET", ["opel", "chevrolet"]),
    "BMW": ("BMW", ["bmw"]),
    "FIAT - ALFA ROMEO - LANCIA": ("FIAT", ["fiat", "alfaromeo", "lancia"]),
    "PEUGEOT  -  CITROËN": ("PEUGEOT - CITROËN", ["peugeot", "citroen"]),
    "AUDI": ("AUDI", ["audi"]),
    "FORD": ("FORD", ["ford"]),
    "ŠKODA": ("SKODA", ["skoda"]),
    "PORSCHE": ("PORSCHE", ["porsche"]),
    "TOYOTA": ("TOYOTA", ["toyota"]),
    "HONDA": ("HONDA", ["honda"]),
    "NISSAN": ("NISSAN", ["nissan"]),
    "IVECO": ("IVECO", ["iveco"]),
    "JEEP - CHRYSLER - DODGE - MASERATI": ("JEEP - CHRYSLER", ["jeep", "chrysler", "dodge", "maserati"]),
    "MAZDA": ("MAZDA", ["mazda"]),
    "MITSUBISHI": ("MITSUBISHI", ["mitsubishi"]),
    "ISUZU": ("ISUZU", ["isuzu"]),
    "LAND ROVER": ("LAND ROVER", ["landrover"]),
    "VOLVO": ("VOLVO", ["volvo"]),
    "TESLA": ("TESLA", ["tesla"]),
    "SUZUKI": ("SUZUKI", ["suzuki"]),
    "UNIVERSAL": ("UNIVERSAL", ["universal"]),
    "SSANGYONG": ("SSANGYONG", ["ssangyong"]),
}


def veri():
    s = open(os.path.join(KOK, "index.html"), encoding="utf-8").read()
    return json.loads(re.search(r"const DATA=(\[.*?\]);", s, re.S).group(1))


def font(agirlik, boy):
    return ImageFont.truetype(F.format(agirlik), boy)


def sar(d, metin, f, gen):
    satirlar, s = [], ""
    for k in metin.split():
        t = (s + " " + k).strip()
        if d.textlength(t, font=f) <= gen:
            s = t
        else:
            satirlar.append(s)
            s = k
    return satirlar + [s] if s else satirlar


def kart(kod, aciklama, oem, grup, slug, marka_adi):
    W, H = 1080, 1350
    im = Image.new("RGB", (W, H), BEYAZ)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=LACI)
    x = 55
    for parca, renk in (("Oto", BEYAZ), ("Düğme", TURUNCU)):
        f = font("ExtraBold", 46)
        d.text((x, 34), parca, font=f, fill=renk)
        x += d.textlength(parca, font=f)
    d.text((x + 16, 52), "MARKET", font=font("Medium", 27), fill=(200, 205, 214))
    fm = font("SemiBold", 28)
    d.text((W - 55 - d.textlength(marka_adi, font=fm), 44), marka_adi, font=fm, fill=(200, 205, 214))

    urun = Image.open(os.path.join(KOK, "img", slug + ".webp")).convert("RGB")
    s = min(660 / urun.width, 640 / urun.height)
    urun = urun.resize((int(urun.width * s), int(urun.height * s)), Image.LANCZOS)
    im.paste(urun, ((W - urun.width) // 2, 140 + (650 - urun.height) // 2))

    marka = "KRAW"
    y = 820
    d.text((55, y), f"{kod} {marka}", font=font("ExtraBold", 66), fill=TURUNCU)
    y += 95
    fa = font("Bold", 38)
    for satir in sar(d, aciklama, fa, W - 110)[:3]:
        d.text((55, y), satir, font=fa, fill=LACI)
        y += 50
    if oem:
        fo = font("Regular", 32)
        oem_s = sar(d, "OEM: " + oem, fo, W - 110)[0]
        d.text((55, y + 8), oem_s, font=fo, fill=GRI)

    d.rectangle((0, 1190, W, H), fill=TURUNCU)
    d.text((55, 1218), "Fiyat ve stok için WhatsApp", font=font("Bold", 38), fill=BEYAZ)
    d.text((55, 1272), "0546 919 33 54    otodugmemarket.com", font=font("SemiBold", 36), fill=BEYAZ)
    os.makedirs(CIKIS, exist_ok=True)
    yol = os.path.join(CIKIS, slug + ".jpg")
    im.save(yol, "JPEG", quality=88, optimize=True)
    return yol


def metin(kod, aciklama, oem, slug, etiketler):
    t = f"{kod} KRAW – {aciklama}\n"
    if oem:
        t += f"OEM: {oem}\n"
    t += ("\nFiyat ve stok için WhatsApp'tan yazın 👇\n💬 0546 919 33 54\n"
          f"🌐 otodugmemarket.com/urun/{slug}/\n\n")
    kod_et = "#" + re.sub(r"[^A-Za-z0-9]", "", kod)
    t += " ".join([kod_et, "#kraw"] + ["#" + e for e in etiketler] +
                  ["#camdüğmesi", "#camanahtarı", "#yedekparça", "#otoyedekparça", "#oto19kartal", "#kartal"])
    return t


def sec(adet, paylasilan):
    gruplar = {}
    for r in veri():
        if r[5] == 1 and r[0] not in paylasilan and r[3] in ETIKET:
            gruplar.setdefault(r[3], []).append(r)
    secilen, sira = [], sorted(gruplar, key=lambda g: -len(gruplar[g]))
    while len(secilen) < adet and any(gruplar.values()):
        for g in sira:
            if gruplar[g] and len(secilen) < adet:
                secilen.append(gruplar[g].pop(0))
    return secilen


def main():
    a = sys.argv[1].split("T")
    bas, ilk_saat = dt.date.fromisoformat(a[0]), int(a[1]) if len(a) > 1 else SAATLER[0]
    gun = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    paylasilan = json.load(open(KAYIT, encoding="utf-8")) if os.path.exists(KAYIT) else {}
    zamanlar = [f"{bas + dt.timedelta(days=i)}T{h:02d}:00:00" for i in range(gun) for h in SAATLER
                if i > 0 or h >= ilk_saat]
    urunler = sec(len(zamanlar), paylasilan)
    sira = []
    for z, (kod, aciklama, oem, grup, slug, _) in zip(zamanlar, urunler):
        marka_adi, etiketler = ETIKET[grup]
        kart(kod, aciklama, oem, grup, slug, marka_adi)
        sira.append({"kod": kod, "zaman": z, "gorsel": HAM_URL + slug + ".jpg",
                     "metin": metin(kod, aciklama, oem, slug, etiketler)})
        paylasilan[kod] = z
    json.dump(sira, open(SIRA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(paylasilan, open(KAYIT, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    kalan = sum(1 for r in veri() if r[5] == 1 and r[0] not in paylasilan)
    print(f"hazırlanan: {len(sira)}  ilk: {sira[0]['zaman'] if sira else '-'}  son: {sira[-1]['zaman'] if sira else '-'}"
          f"  paylaşılmamış resimli ürün: {kalan}")


if __name__ == "__main__":
    main()
