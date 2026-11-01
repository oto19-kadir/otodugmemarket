# OtoDüğme Market (otodugmemarket.com) – Claude için çalışma kuralları

Bu depo otodugmemarket.com sitesidir. Kullanıcı bu siteye **"Düğme"** der. Sahibi: Kadir Demirkoparan (Oto19 Kartal).
"Kartal" = ayrı site oto19kartal.com, ayrı depo (oto19-kadir/oto19kartal). İkisini karıştırma.

## Kesin kurallar
1. **main dalına push = CANLI.** Netlify (proje: otodugme-site) main'i otomatik yayınlar ve her yayın yaklaşık 15 Netlify kredisi harcar (ayda 300). Kullanıcı açıkça "Düğme ... canlıya al" demeden main'e push YAPILMAZ. Çalışmalar ayrı dalda (branch) tutulur ve GitHub'a o dalda gönderilir.
2. **Ödeme yok.** Düğme'de sepet, kart, kapıda ödeme veya ödeme metni bulunmaz; siparişler WhatsApp'tan alınır (0546 919 33 54).
3. **Gizli bilgi yok.** Şifre, FTP bilgisi, API anahtarı istenmez, sohbete, koda veya depoya yazılmaz; kullanıcı kendisi gizli ayarlara girer.
4. **Yazım:** tam cümle, düzgün Türkçe; "Skoda". Rakip sitelerden metin/görsel kopyalanmaz. Garanti iddiası yazılmaz.
5. **Değişiklik kaydı:** Her iş bitince ilgili dalda commit edilir ve GitHub'a gönderilir (ana dal hariç, kural 1).

## Yapı
Statik site: `index.html` (katalog, JS içinde DATA dizisi; BRAND="OtoDüğme Market", WA="905469193354"), `urun/*/index.html` (1480 ürün sayfası, aynı alt bilgi), `img/`, `sitemap.xml`, `netlify.toml` (publish ".").

## Bekleyen işler
- **Yeni 4 sütunlu alt bilgi** (Oto19 bilgileri, kargo firmaları Yurtiçi/Aras/DHL/HepsiJet/Sürat, Instagram @otodugmemarketi, Künye/SSS/Kargo/Nasıl sipariş bölümleri, ödeme içeriği yok): `bekleyen/alt-bilgi` dalında hazır ve test edildi. Kullanıcı "Alma beklet" dedi; "Düğme alt bilgiyi canlıya al" deyince main'e alınır. 1 Kasım 2026: araç seçiciyle çakışmaması için şimdiki main'e yeniden uygulandı ve "Bu site ETBİS’e kayıtlıdır." satırı eklendi (kullanıcı ETBİS'e kayıt oldu, QR kodu kaldırılmış). Dal: claude/bold-keller-az3ld6.
- **Netlify'dan kullanıcının kendi hostingine taşıma** (Linux, cPanel; aday Hosting Dünyam Professional). Sıra: önce hostinge yükle ve test et, sonra GoDaddy DNS'i hostinge yönlendir, site oradan açılınca Netlify bağlantısını kaldır. Netlify erken kaldırılırsa site kapanır.

İş planı (Kartal ile ortak): https://claude.ai/artifact/DYkm8dfQtVcLpUbrX2RWqa
