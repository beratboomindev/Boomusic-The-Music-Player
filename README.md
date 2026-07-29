<picture>
  <source media="(prefers-color-scheme: dark)" srcset="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='url(%23g)'/%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='64' y2='64'%3E%3Cstop offset='0' stop-color='%236C4AFF'/%3E%3Cstop offset='1' stop-color='%239C86FF'/%3E%3C/linearGradient%3E%3C/defs%3E%3Ctext x='32' y='42' text-anchor='middle' fill='white' font-size='28' font-weight='bold' font-family='sans-serif'%3E♪%3C/text%3E%3C/svg%3E">
  <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='url(%23g)'/%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='64' y2='64'%3E%3Cstop offset='0' stop-color='%236C4AFF'/%3E%3Cstop offset='1' stop-color='%239C86FF'/%3E%3C/linearGradient%3E%3C/defs%3E%3Ctext x='32' y='42' text-anchor='middle' fill='white' font-size='28' font-weight='bold' font-family='sans-serif'%3E♪%3C/text%3E%3C/svg%3E" width="64" height="64" align="left" style="margin-right:16px">
</picture>

# Boomusic — The Music Player

**Premium yok. Reklam yok. Dert yok.** Boomusic, Linux için yerel bir müzik çalar. Hem masaüstü penceresi hem de tepsi simgesi ile çalışır; pencereyi kapatsan da uygulama tepsiden devam eder.

> No premium, no ads, no problems. Boomusic brings you a fast and smooth experience.

## Download / İndir

```bash
git clone https://github.com/anomalyco/Boomusic.git
cd Boomusic/boomusic_v1.7
bash install.sh
```

Ya da [Releases](https://github.com/anomalyco/Boomusic/releases) sayfasından son sürümü indir, içindeki `install.sh`'i çalıştır.

## Features / Özellikler

- **YT-dlp Desteği** — Boomusic içinden YouTube'da ara, indir, çal.
- **Sürükle-Bırak Şarkı Ekle** — Ses dosyasını playlist'e sürükle, adını ve sanatçısını manuel düzenle.
- **Playlist Yönetimi** — İstediğin kadar playlist oluştur, şarkı ekle/çıkar, kapak resmi ata.
- **Akıllı Karıştırma (Smart Shuffle)** — Aynı şarkı tüm liste bitmeden tekrar çalmaz.
- **Dinleme İstatistikleri** — Hangi şarkıyı kaç kere dinlediğinin kaydı tutulur.
- **Sadece Şarkılar Filtresi** — ♪ düğmesi ile playlist'te sadece ses dosyalarını göster.
- **i18n Dil Desteği** — İngilizce (varsayılan) ve Türkçe arasında geçiş yapılabilir.
- **Yazı Tipi Seçimi** — DM Sans veya Anthropic Serif.
- **Klavye Kısayolları** — Space (oynat/duraklat), K (panel aç/kapat), ←/→ (önceki/sonraki).
- **Otomatik Başlatma** — İsteğe bağlı, bilgisayar açılırken arka planda başlar.
- **Drag-Drop Song** — Drag and drop audio files into your playlists.
- **Just Icon Mode** — *Coming with 1.7.3*
- **Recommended to You** — *Coming Soon*
- **Plugins** — *Coming Soon*
- **Theme Customization** — *Coming Soon*

## Smart Shuffle Nasıl Çalışır?

Bir şarkı, playlist'teki diğer bütün şarkılar en az bir kez çalınmadan tekrar seçilemez. Tüm şarkılar çalındığında tur biter, algoritma sıfırlanır.

## Kısayollar

| Tuş | İşlev |
|-----|-------|
| Space | Oynat / Duraklat |
| K | Şimdi çalan panelini aç/kapat |
| ← → | Önceki / Sonraki şarkı |
| Escape | Arama panelini kapat |

## Dosya Konumları

| Ne | Nerede |
|---|---|
| Müzik | `~/BooPlaylist` (değiştirilebilir) |
| Ayarlar | `~/.config/boomusic/config.json` |
| İstatistikler | `~/.local/share/boomusic/stats.json` |
| Günlük | `~/.local/share/boomusic/boomusic.log` |

## Desteklenen Sistemler

Şu an için sadece Linux. v2.0 ile Windows ve Android planlanıyor.

## Which AI models did I use?

At 0.1–1.5: **Claude Sonnet 5 Free Max** — but its credit limit was too low so I switched to **DeepSeek Flash 4 Free OpenCode Zen** at version 1.7.

---

## EN — English

### Introduction
Boomusic doesn't need your money. No premium, no ads, no problems! Boomusic brings you a fast and smooth experience.

### What Sets Boomusic Apart?
No doubt. **Trust the process.**

### Features
- **Drag-Drop Song:** Drag and drop audio files into your playlist. Manually set title and artist.
- **Just Icon Mode:** Control Boomusic solely through the system tray icon. *(Coming with 1.7.3)*
- **YT-dlp Feature:** Search and download songs from YouTube via Boomusic.
- **Recommended to You:** Boomusic suggests songs you might like. *(Coming Soon)*
- **Playlist Feature:** Create as many playlists as you want, add as many songs as you want.
- **Boomin's Shuffle:** Our shuffle algorithm ensures songs don't repeat until all have been played. *(Toggleable, coming with 1.8)*
- **Automatic Startup:** App can start automatically in the background.
- **Listening Data Collection:** Boomusic tracks play counts and listening time.
- **Plugins:** Community plugins to customize Boomusic. *(Coming Soon)*
- **Theme Customization:** Full theme customization. *(Coming Soon)*

### Platform Support
Currently Linux only. Windows and Android planned for v2.0.

---

## TR — Türkçe

### Tanıtım
**Boomusic'in paranıza ihtiyacı yok.** Reklam yok, premium veya başka saçmalıkları yok. Hızlı, akıcı ve kullanışlı bir deneyim sunar.

### Farkımız Ne?
Şüphe yok. Sonuca güven.

### Özellikler
- **YT-dlp Desteği:** Boomusic içinden YouTube'dan şarkı indir ve ara.
- **Sadece İkon Modu:** Sadece sistem tepsisi ikonu üzerinden yönetim. *(1.7.3 ile geliyor)*
- **Sürükle-Bırak Şarkı:** Ses dosyasını playlist'e sürükle, adını ve sanatçısını düzenle.
- **Senin için Öneriler:** Dinleme alışkanlıklarına göre şarkı önerileri. *(Yakında)*
- **Playlist Özelliği:** İstediğin kadar playlist ve şarkı.
- **Boomin Tarzı Karışık Çalma:** Aynı şarkı tekrar tekrar çalmaz. *(1.8 ile geliyor)*
- **Kendiliğinden Başlatma:** Bilgisayar açılırken arka planda başlar.
- **Tema Özelleştirme:** Baştan sona tema düzenleme. *(Yakında)*
- **Dinleme Verisi Toplama:** Kaç kere ve kaç dakika dinlediğinin kaydı.
- **Eklentiler:** Topluluk pluginleri. *(Yakında)*

---

*Built with Python, pywebview, and libVLC.*
