# Düğme Instagram paylaşım düzeni (@otodugmemarketi)

Kullanıcı isteği (1 Kasım 2026): paylaşımlar sürekli devam etsin, **saatte bir**, her gün 09:00–22:00 (Europe/Istanbul), günde 14 paylaşım.

## Haftalık iş (zamanlanmış görev her çarşamba çalışır)
1. `git checkout claude/bold-keller-az3ld6 && git pull origin claude/bold-keller-az3ld6` (oto19-kadir/otodugmemarket).
2. `python3 instagram/hazirla.py <yarının tarihi> 7` → 98 ürün seçer, `instagram/p/<kod>.jpg` görsellerini (1080x1350) ve `instagram/sira.json` listesini yazar, `instagram/paylasilan.json` kaydını günceller.
3. Sadece `instagram/` klasörünü commit edip `claude/bold-keller-az3ld6` dalına push et (main'e değil; main = canlı). Bu dal Netlify'da yayınlanmaz; site dosyalarına dokunma.
4. Görsel adresi `https://raw.githubusercontent.com/oto19-kadir/otodugmemarket/claude/bold-keller-az3ld6/instagram/p/<slug>.jpg` açılıyor mu kontrol et.
5. Her kayıt için aynı saatte bir de hikâye gir: createScheduledPost, media [story], text "", instagramData type STORY.
6. `sira.json`'daki her kayıt için Metricool `createScheduledPost`: blogId 7778712, providers instagram, instagramData type POST, autoPublish true, media [gorsel], text [metin], publicationDate {dateTime: zaman, timezone: "Europe/Istanbul"}.
7. Hata olursa kalan kayıtları tekrar dene; başarısız olanları `sira.json`'da işaretleyip kullanıcıya bildir.

## Kurallar
- Ürün seçimi: sadece resmi olan ürünler, daha önce paylaşılmamış olanlar, marka grupları sırayla karıştırılır.
- Metin: düzgün Türkçe, garanti iddiası yok, fiyat yazılmaz (WhatsApp'tan sorulur), ödeme içeriği yok.
- Tüm ürünler bitince (yaklaşık 1.350 ürün, yaklaşık 14 hafta) kullanıcıya sorulur: başa dönülsün mü?

## Zamanlanmış görev
- "Düğme Instagram haftalık paylaşımlar" (trig_017WdeSgE9s2E7YQQMRE37ug): her çarşamba 14:17 (İstanbul), ilk çalışma 4 Kasım 2026; her seferinde ertesi günden başlayan 7 günü doldurur.
- Görevin Metricool'a erişmesi için kullanıcının claude.ai'deki zamanlanmış görev ayarından Metricool bağlantısını eklemesi gerekir (oturumdan eklenemedi).
- 1 Kasım 2026 itibarıyla 4 Kasım 22:00'ye kadar bütün saatler dolu (39 + 11 ürün paylaşıldı veya sırada).
