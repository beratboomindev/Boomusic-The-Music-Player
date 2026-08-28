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

```bash
git clone https://github.com/beratboomindev/Boomusic-The-Music-Player.git
cd Boomusic-The-Music-Player
bash install.sh
```

For non-interactive updates (e.g. CI, or to keep a `just_icon_mode=true`
session uninterrupted), use `update.sh` — same as `install.sh` but it
asks no questions and does not launch the app at the end:
```bash
bash update.sh
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
- **Just Icon Mode** — Run Boomusic with no window at all. Control everything
  from the tray icon: play/pause, next/previous, shuffle, volume presets,
  playlists, individual tracks, and switch back to window mode. *Now
  available (planned for 1.7.3, shipped with 1.7.2).*
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
- **Sadece İkon Modu** — Boomusic'i penceresiz, sadece tepsi simgesiyle çalıştır.
  Tüm kontrol tepsi menüsünden: oynat/duraklat, sonraki/önceki, karıştır, ses
  preset'leri, çalma listeleri, tek tek şarkılar ve pencere moduna geri dönüş.
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

`install.sh` interaktif olur (autostart, masaüstü simgesi, vb. için soru
sorar) ve sonda uygulamayı başlatır. Güncelleme için etkileşimsiz ve
başlatmayan sürüm istersen `update.sh` kullan:

```bash
bash update.sh
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

## Just Icon Mode / Sadece İkon Modu

**EN:** Just Icon Mode is a **separate, independent launcher** —
`boomusic-tray` (or the *Boomusic (Sadece İkon)* entry in your app menu).
It opens the same rich tray menu but **no window at all**. The full UI is
inside that tray menu:
- Now-playing title at the top
- Play/Pause, Previous, Next
- Shuffle toggle (checked state shows whether it's on)
- Volume submenu: 0/10/20/.../100% presets, ±5 buttons, mute toggle
- Playlists submenu: each playlist expands to its tracks; click to play
- Rescan, open the music folder in your file manager
- Quit

The **GUI and Just Icon run as two completely separate processes** with
their own locks (`boomusic-gui.lock` and `boomusic-tray.lock`), so you
can start both at the same time and they won't conflict. If you only
want one, just don't launch the other.

CLI equivalent: `python3 -m boomusic --tray-only` (or `-t`).

**TR:** Sadece İkon Modu, **ayrı ve bağımsız bir başlatıcıdır** —
`boomusic-tray` (veya uygulama menüsündeki *Boomusic (Sadece İkon)*
girdisi). Aynı zengin tepsi menüsünü açar ama **pencere hiç açılmaz**:
- Üstte "şu an çalıyor" başlığı
- Oynat/Duraklat, Önceki, Sonraki
- Karıştır aç/kapat
- Ses alt menüsü: preset'ler, ±5, sustur
- Çalma listeleri alt menüsü: tıkla çal
- Yeniden tara, klasör aç
- Çıkış

**GUI ve Just Icon tamamen ayrı süreçlerdir** (kendi lock dosyaları:
`boomusic-gui.lock`, `boomusic-tray.lock`), aynı anda çalıştırılabilirler
ve birbirleriyle çakışmazlar. Sadece birini istiyorsanız diğerini
başlatmazsınız.

CLI eşdeğeri: `python3 -m boomusic --tray-only` (veya `-t`).

---

## Troubleshooting / Sorun Giderme

### EN

**"python3 not found" or "venv module not found"**
Boomusic needs Python 3 with the `venv` module. Install it for your distro:
- Arch / Manjaro / CachyOS: `sudo pacman -S python`
- Debian / Ubuntu / Mint:  `sudo apt install python3 python3-venv python3-pip`
- Fedora:                   `sudo dnf install python3 python3-pip`
- openSUSE:                 `sudo zypper install python3 python3-pip`

The installer prints the exact command for your distro before quitting.

**"pip install failed" / some Python packages missing**
The installer no longer aborts; it prints the failing package and the exact
`pip install ...` command you can re-run once you fix the underlying cause
(usually: no internet, mirror down, corporate proxy, or pip needs an upgrade).
Boomusic will still install and may launch, but any feature whose module is
missing (e.g. `pywebview` → no main window, `python-vlc` → no audio) will
fail at use time. The final summary block at the end of the installer lists
everything it couldn't get.

**App opens but the main window never appears, only the tray icon**
You're missing `webkit2gtk` (the engine pywebview uses). Install:
- Arch:     `sudo pacman -S webkit2gtk-4.1`
- Debian:   `sudo apt install libwebkit2gtk-4.1-0`
- Fedora:   `sudo dnf install webkit2gtk4.1`
If it's not in your distro's repos at all, Boomusic will still run from the
tray — playback, volume, next/previous and YouTube downloads all work.

**App opens but no audio / VLC error**
Install VLC: `sudo pacman -S vlc` / `sudo apt install vlc` /
`sudo dnf install vlc`. The Python package `python-vlc` needs the system
`vlc` shared library to actually play.

**Interface looks broken after switching to a smaller monitor**
This was a real bug: when you dragged the sidebar wider on a big monitor
and then plugged into a smaller screen, the sidebar (and sometimes the
"now playing" panel) overflowed. Two fixes ship with 1.7.2:
- The sidebar width is now saved in `~/.config/boomusic/config.json`
  and re-applied at next launch.
- The window JS automatically clamps the sidebar to the current viewport
  width whenever you resize the window or change monitors (listens to
  the `resize` and `orientationchange` events), and CSS media queries
  under 760px / 540px also compact the layout defensively.
- If you manually shrank the window to below 480x380 (the minimum), just
  drag it larger from any corner — the layout snaps back.

**"ImportError: No module named boomusic" or "ModuleNotFoundError"**
The launcher at `~/.local/bin/boomusic` was probably created before a
re-install, or your venv got partially wiped. Re-run `bash install.sh`
and let it finish; it detects the existing venv and reuses it.

### TR

**"python3 bulunamadı" veya "venv modülü bulunamadı"**
Boomusic için `venv` modülüyle birlikte Python 3 gerekiyor. Dağıtımınıza göre:
- Arch / Manjaro / CachyOS: `sudo pacman -S python`
- Debian / Ubuntu / Mint:  `sudo apt install python3 python3-venv python3-pip`
- Fedora:                   `sudo dnf install python3 python3-pip`
- openSUSE:                 `sudo zypper install python3 python3-pip`
Kurulum betiği çıkmadan önce dağıtımınıza uygun komutu ekrana yazdırır.

**"pip install başarısız" / bazı Python paketleri eksik**
Kurulum betiği artık ölümcül hata vermez; başarısız paketi ve elle
çalıştırabileceğiniz `pip install ...` komutunu ekrana yazar (genelde
sebep: internet yok, ayna çökmüş, kurumsal proxy veya pip güncel değil).
Bunlar olsa bile uygulama kurulur ve açılabilir; ama eksik modüle
bağlı özellik kullanıldığında hata alırsınız (örn. `pywebview` yoksa
ana pencere açılmaz, `python-vlc` yoksa ses çalmaz). Kurulum sonundaki
özet, eksik bileşenleri listeler.

**Uygulama açılıyor ama ana pencere hiç gelmiyor, sadece tepsi simgesi var**
`webkit2gtk` kurulu değil (pywebview'in kullandığı motor). Kurmak için:
- Arch:    `sudo pacman -S webkit2gtk-4.1`
- Debian:  `sudo apt install libwebkit2gtk-4.1-0`
- Fedora:  `sudo dnf install webkit2gtk4.1`
Dağıtımınızda hiç yoksa yine de tepsi simgesinden müzik çalabilir, ses
seviyesiyle oynayabilir, sonraki/önceki şarkıya geçebilir, YouTube
indirmesi yapabilirsiniz.

**Pencere açılıyor ama ses gelmiyor / VLC hatası**
VLC kurulu değil: `sudo pacman -S vlc` / `sudo apt install vlc` /
`sudo dnf install vlc`. Python paketi `python-vlc`, gerçek ses için
sistemdeki `vlc` paylaşımlı kütüphanesine ihtiyaç duyar.

**Monitör değiştirince arayüz bozuluyor (küçük monitöre geçince taşıyor)**
Bu gerçek bir bug'dı: büyük monitörde sidebar'ı genişletip sonra küçük
bir ekrana (örn. dizüstüne) bağlandığınızda sidebar ve bazen "şimdi
çalan" paneli pencereyi taşırıyordu. 1.7.2 ile iki düzeltme geldi:
- Sidebar genişliği artık `~/.config/boomusic/config.json` içinde
  saklanıyor, sonraki açılışta uygulanıyor.
- Pencere JS tarafı, pencere yeniden boyutlandırıldığında veya monitör
  değiştiğinde sidebar'ı otomatik olarak mevcut viewport'a sığacak
  şekilde clamp'liyor (`resize` + `orientationchange` olaylarını
  dinliyor); 760px ve 540px altındaki CSS media sorguları da savunma
  amaçlı layout'u kompaktlaştırıyor.
- Pencereyi yanlışlıkla 480x380'in altına küçülttüyseniz, kenarlardan
  tutup büyütün; layout kendini toplar.

**"ImportError: No module named boomusic" / "ModuleNotFoundError"**
`~/.local/bin/boomusic` başlatıcısı eski bir kurulumdan kalmış ya da
venv kısmen silinmiş olabilir. `bash install.sh`'i tekrar çalıştırıp
bitmesini bekleyin; mevcut venv'i algılar ve yeniden kullanır.

*Built with Python, pywebview, libVLC, and ♥*
