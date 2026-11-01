#!/usr/bin/env python3
"""auto-data.net'ten VAG grubu (VW, Audi, Seat, Skoda, Cupra, Porsche) araç tiplerini toplar.

Çıktı: araclar/vag_araclar.csv  (; ile ayrılmış, Excel'de açılır)
Sütunlar: Marka;Model;Kasa/Nesil;Tip;Motor kodu;Beygir;Yakıt;Şanzıman;Yıllar;Başlangıç;Bitiş;Kaynak

Kullanım:
    python3 araclar/autodata_vag.py                # tüm VAG markaları
    python3 araclar/autodata_vag.py Skoda Seat     # sadece seçilen markalar

Sayfalar önbelleğe alınır (araclar/.cache), yarıda kesilirse kaldığı yerden devam eder.
Siteyi yormamak için her istek arasında bekler.
"""
import csv, hashlib, os, re, sys, time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.auto-data.net"
MARKALAR = ["Volkswagen", "Audi", "Seat", "Skoda", "Cupra", "Porsche"]
BEKLE = 1.5  # saniye
KOK = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(KOK, ".cache")
CIKTI = os.path.join(KOK, "vag_araclar.csv")

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
S.headers["Accept-Language"] = "en"


def getir(url):
    os.makedirs(CACHE, exist_ok=True)
    yol = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".html")
    if os.path.exists(yol):
        return open(yol, encoding="utf-8").read()
    for deneme in range(4):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                open(yol, "w", encoding="utf-8").write(r.text)
                time.sleep(BEKLE)
                return r.text
            print(f"  HTTP {r.status_code}: {url}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  hata: {e}", file=sys.stderr)
        time.sleep(2 ** (deneme + 1))
    return ""


def linkler(html, desen):
    soup = BeautifulSoup(html, "html.parser")
    gor, out = set(), []
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"].split("#")[0])
        if re.search(desen, href) and href not in gor:
            gor.add(href)
            out.append((a.get_text(" ", strip=True), href))
    return out


def ozellikler(html):
    """Teknik tablo satırlarını {başlık: değer} olarak döndürür."""
    soup = BeautifulSoup(html, "html.parser")
    d = {}
    for tr in soup.find_all("tr"):
        th, td = tr.find("th"), tr.find("td")
        if th and td:
            k = th.get_text(" ", strip=True)
            if k and k not in d:
                d[k] = td.get_text(" ", strip=True)
    bc = [a.get_text(" ", strip=True) for a in soup.select(".breadcrumb a, #breadcrumbs a, .breadcrumbs a")]
    h1 = soup.find("h1")
    return d, bc, (h1.get_text(" ", strip=True) if h1 else "")


def bul(d, *anahtarlar):
    for k, v in d.items():
        kl = k.lower()
        if any(a in kl for a in anahtarlar):
            return v
    return ""


def yil(s):
    m = re.search(r"(19|20)\d{2}", s or "")
    return int(m.group(0)) if m else None


def yakit_tr(s):
    s = (s or "").lower()
    for k, v in [("hybrid", "Hibrit"), ("electric", "Elektrikli"), ("diesel", "Dizel"),
                 ("lpg", "LPG"), ("cng", "CNG"), ("petrol", "Benzinli"), ("gasoline", "Benzinli")]:
        if k in s:
            return v
    return s


def sanziman_tr(d):
    g = bul(d, "gearbox", "number of gears")
    m = re.search(r"(\d+)\s*gears?,?\s*(.*)", g, re.I)
    if not m:
        return g
    n, tur = m.group(1), m.group(2).lower()
    if "dsg" in tur or "dual clutch" in tur:
        return f"DSG{n} Şanzıman"
    if "automatic" in tur or "tiptronic" in tur:
        return f"{n} ileri Otomatik"
    if "manual" in tur:
        return f"{n} ileri Manuel"
    return f"{n} ileri {tur}".strip()


def marka_url(marka):
    for metin, href in linkler(getir(BASE + "/en/allbrands"), r"/en/[a-z0-9-]+-brand-\d+$"):
        if metin.lower().startswith(marka.lower()):
            return href
    return None


def calistir(markalar):
    yeni = not os.path.exists(CIKTI)
    bitti = set()
    if not yeni:
        with open(CIKTI, encoding="utf-8-sig") as f:
            bitti = {r["Kaynak"] for r in csv.DictReader(f, delimiter=";")}
    f = open(CIKTI, "a", newline="", encoding="utf-8-sig")
    w = csv.writer(f, delimiter=";")
    if yeni:
        w.writerow(["Marka", "Model", "Kasa/Nesil", "Tip", "Motor kodu", "Beygir", "Yakıt",
                    "Şanzıman", "Yıllar", "Başlangıç", "Bitiş", "Kaynak"])
    simdi = time.localtime().tm_year
    for marka in markalar:
        mu = marka_url(marka)
        if not mu:
            print(f"Marka bulunamadı: {marka}", file=sys.stderr)
            continue
        print(f"== {marka}: {mu}")
        modeller = linkler(getir(mu), r"/en/[a-z0-9-]+-model-\d+$")
        for mad, murl in modeller:
            nesiller = linkler(getir(murl), r"/en/[a-z0-9-]+-generation-\d+$")
            print(f"  {mad}: {len(nesiller)} nesil")
            for nad, nurl in nesiller:
                tipler = linkler(getir(nurl), r"/en/[a-z0-9.-]+-\d+$")
                tipler = [t for t in tipler if not re.search(r"-(brand|model|generation)-\d+$", t[1])]
                for tad, turl in tipler:
                    if turl in bitti:
                        continue
                    d, bc, h1 = ozellikler(getir(turl))
                    if not d:
                        continue
                    bas, bit = yil(bul(d, "start of production")), yil(bul(d, "end of production"))
                    yillar = ", ".join(str(y) for y in range(bas, (bit or simdi) + 1)) if bas else ""
                    hp = re.search(r"(\d+)\s*Hp", bul(d, "power"), re.I)
                    w.writerow([marka, mad, nad, bul(d, "modification") or tad,
                                bul(d, "engine model", "engine code"),
                                f"{hp.group(1)} beygir" if hp else bul(d, "power"),
                                yakit_tr(bul(d, "fuel type")), sanziman_tr(d), yillar,
                                bas or "", bit or "", turl])
                    f.flush()
                    bitti.add(turl)
    f.close()
    print(f"Bitti: {CIKTI}")


if __name__ == "__main__":
    calistir(sys.argv[1:] or MARKALAR)
