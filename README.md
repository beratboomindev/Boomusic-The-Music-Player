# Boomusic — The Music Player

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="src/boomusic/assets/icon.png">
  <img src="src/boomusic/assets/icon.png" width="64" align="left" style="margin-right:16px">
</picture>

**Premium yok. Reklam yok. Dert yok.** Boomusic, Linux için yerel bir müzik çalar. Hem masaüstü penceresi hem de tepsi simgesi ile çalışır; pencereyi kapatsan da uygulama tepsiden devam eder.

<br clear="left">

> No premium, no ads, no problems. Boomusic brings you a fast and smooth experience.

---

## Download / İndir

**One-liner (önerilen):**
```bash
curl -fsSL https://github.com/beratboomindev/Boomusic-The-Music-Player/releases/download/v1.7.2/install-boomusic.sh | bash
```
Sistem bağımlılıklarını (GTK, VLC, WebKit) kurar, masaüstü girişi oluşturur, başlatır.

**Manuel:**
```bash
git clone https://github.com/beratboomindev/Boomusic-The-Music-Player.git
cd Boomusic-The-Music-Player
bash install.sh
```

Ya da [Releases](https://github.com/beratboomindev/Boomusic-The-Music-Player/releases) sayfasından son sürümü indir.

---

## EN — English

### Introduction
Boomusic doesn't need your money. No premium, no ads, no problems! 
Boomusic brings you a fast and smooth experience.

### What Sets Boomusic Apart?
No doubt. **Trust the process.**

### Features
- **YT-dlp Support** — Search, download, and play songs from YouTube directly in Boomusic.
- **Drag-Drop Song** — Drag and drop audio files into your playlists. Manually set title and artist.
- **Playlist Feature** — Create unlimited playlists with unlimited songs. Add custom cover images.
- **Smart Shuffle** — Our shuffle algorithm ensures the same song won't play again until all songs in the playlist have been played. Once all songs have been played, the algorithm resets.
- **Listening Statistics** — Boomusic tracks how many times and how long you've listened to each song.
- **Only Songs Filter** — Toggle the ♪ button to show only audio files (mp3/flac/ogg/wav).
- **Keyboard Shortcuts** — Space (play/pause), K (toggle now-playing panel), ←/→ (prev/next).
- **i18n Language Support** — Switch between English (default) and Turkish in Settings.
- **Font Selection** — Choose between DM Sans and Anthropic Serif.
- **Automatic Startup** — Optionally start Boomusic in the background at boot.
- **Just Icon Mode** — Control Boomusic solely through the system tray. *(Coming with 1.7.3)*
- **Recommended for You** — Song suggestions based on your listening habits. *(Coming Soon)*
- **Plugins** — Community plugins to extend functionality. *(Coming Soon)*
- **Theme Customization** — Full visual customization. *(Coming Soon)*

### Platform Support
Currently Linux only. Windows and Android planned for v2.0.

### Which AI models were used?
At versions 0.1–1.5: **Claude Sonnet 5 Free Max**. 
At version 1.7+: **DeepSeek Flash 4 Free OpenCode Zen** (credit limits forced the switch).

### Keyboard Shortcuts

| Key | Function |
|-----|----------|
| Space | Play / Pause |
| K | Toggle now-playing panel |
| ← → | Previous / Next track |
| Escape | Close search panel |

### File Locations

| What | Where |
|------|-------|
| Music | `~/BooPlaylist` (configurable) |
| Settings | `~/.config/boomusic/config.json` |
| Statistics | `~/.local/share/boomusic/stats.json` |
| Log | `~/.local/share/boomusic/boomusic.log` |
| Program files | `~/.local/share/boomusic/install/` |
| Launcher | `~/.local/bin/boomusic` |

---

## TR — Türkçe

### Tanıtım
**Boomusic'in paranıza ihtiyacı yok.** Reklam yok, premium veya başka saçmalıkları yok. Hızlı, akıcı ve kullanışlı bir deneyim sunar.

### Farkımız Ne?
Şüphe yok. Sonuca güven.

### Özellikler
- **YT-dlp Desteği** — Boomusic içinden YouTube'da şarkı ara, indir ve çal.
- **Sürükle-Bırak Şarkı** — Ses dosyasını playlist'e sürükle, adını ve sanatçısını manuel düzenle.
- **Playlist Özelliği** — İstediğin kadar playlist oluştur, istediğin kadar şarkı ekle. Kapak resmi ata.
- **Boomin Tarzı Karışık Çalma (Smart Shuffle)** — Aynı şarkı, playlist'teki diğer tüm şarkılar çalınmadan tekrar çalmaz. Tüm şarkılar çalındığında algoritma sıfırlanır.
- **Dinleme İstatistikleri** — Hangi şarkıyı kaç kere ve kaç dakika dinlediğinin kaydı tutulur.
- **Sadece Şarkılar Filtresi** — ♪ düğmesi ile playlist'te sadece ses dosyalarını göster (mp3/flac/ogg/wav).
- **Klavye Kısayolları** — Space (oynat/duraklat), K (şimdi çalan paneli), ←/→ (önceki/sonraki).
- **Dil Desteği (i18n)** — Ayarlar'dan İngilizce ve Türkçe arasında geçiş yap.
- **Yazı Tipi Seçimi** — DM Sans veya Anthropic Serif arasında seçim yap.
- **Otomatik Başlatma** — Bilgisayar açılırken Boomusic arka planda otomatik başlar.
- **Sadece İkon Modu** — Sadece sistem tepsisi ikonu üzerinden yönetim. *(1.7.3 ile geliyor)*
- **Sana Özel Öneriler** — Dinleme alışkanlıklarına göre şarkı önerileri. *(Yakında)*
- **Eklentiler** — Topluluk pluginleri ile Boomusic'i kişiselleştir. *(Yakında)*
- **Tema Özelleştirme** — Uygulama temasını baştan sona değiştir. *(Yakında)*

### Klavye Kısayolları

| Tuş | İşlev |
|-----|-------|
| Space | Oynat / Duraklat |
| K | Şimdi çalan panelini aç/kapat |
| ← → | Önceki / Sonraki şarkı |
| Escape | Arama panelini kapat |

### Dosya Konumları

| Ne | Nerede |
|----|--------|
| Müzik | `~/BooPlaylist` (Ayarlar'dan değiştirilebilir) |
| Ayarlar | `~/.config/boomusic/config.json` |
| İstatistikler | `~/.local/share/boomusic/stats.json` |
| Günlük | `~/.local/share/boomusic/boomusic.log` |
| Program dosyaları | `~/.local/share/boomusic/install/` |
| Başlatıcı | `~/.local/bin/boomusic` |

---

## Smart Shuffle / Smart Shuffle Nasıl Çalışır?

**EN:** One song cannot be selected again until every other song in the playlist has been played at least once. When all songs have been played, the round ends and the algorithm resets.

**TR:** Bir şarkı, playlist'teki diğer bütün şarkılar en az bir kez çalınmadan tekrar seçilemez. Tüm şarkılar çalındığında tur biter, algoritma sıfırlanır.

---

## Installation / Kurulum

```bash
bash install.sh
```

The script will:
1. Install required system packages (python-gobject, gtk3, webkit2gtk, vlc, etc.)
2. Create a Python virtual environment
3. Install Python dependencies (pystray, pillow, python-vlc, pywebview, mutagen)
4. Copy application files
5. Create launcher at `~/.local/bin/boomusic`
6. Add to application menu
7. Optionally enable autostart

---

*Built with Python, pywebview, libVLC, and ♥*
