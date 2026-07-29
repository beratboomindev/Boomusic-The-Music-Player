<div align="center">

<img src="https://github.com/beratboomindev/Boomusic-The-Music-Player/raw/main/src/boomusic/assets/icon.png" width="96" alt="Boomusic logo" />

# Boomusic — The Music Player

**No premium. No ads. No problems.**
A fast, native Linux music player that lives in your desktop *and* your system tray.

[![Latest Release](https://img.shields.io/github/v/release/beratboomindev/Boomusic-The-Music-Player?label=release&color=success)](https://github.com/beratboomindev/Boomusic-The-Music-Player/releases)
[![Stars](https://img.shields.io/github/stars/beratboomindev/Boomusic-The-Music-Player?style=social)](https://github.com/beratboomindev/Boomusic-The-Music-Player/stargazers)
[![Platform](https://img.shields.io/badge/platform-Linux-blue?logo=linux)](#platform-support)
[![Python](https://img.shields.io/badge/python-3.x-blue?logo=python)](#installation--kurulum)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English](#en--english) · [Türkçe](#tr--türkçe) · [Install](#download--i̇ndir) · [Features](#features)

</div>

---

<!--
  SCREENSHOT SPACE — this is the single highest-impact addition you can make.
  Drop 1-3 images or a short GIF here (main window, tray menu, playlist view).
  A visual music player with zero screenshots is a hard sell — people decide
  in about 3 seconds whether to keep reading.

  <p align="center">
    <img src="docs/screenshot-main.png" width="800" alt="Boomusic main window" />
  </p>
-->

## Download / İndir

**One-liner (recommended):**

```bash
curl -fsSL https://github.com/beratboomindev/Boomusic-The-Music-Player/releases/download/v1.7.2/install-boomusic.sh | bash
```

Installs system dependencies (GTK, VLC, WebKit), creates a desktop entry, and launches Boomusic.

**Manual:**

```bash
git clone https://github.com/beratboomindev/Boomusic-The-Music-Player.git
cd Boomusic-The-Music-Player
bash install.sh
```

Or grab the latest build from the [Releases page](https://github.com/beratboomindev/Boomusic-The-Music-Player/releases).

---

## EN — English

### Why Boomusic?

Most "free" music players eventually ask for money, show you ads, or lock features behind a paywall. Boomusic doesn't. It's a local-first player built for people who just want their music to play — fast, clean, and out of the way when you don't need it (thanks to the tray icon).

### Features

| | |
|---|---|
| 🔎 **YT-dlp Support** | Search, download, and play songs from YouTube directly in Boomusic |
| 🖱️ **Drag & Drop** | Drop audio files into playlists; edit title/artist manually |
| 📁 **Unlimited Playlists** | Unlimited playlists, unlimited songs, custom cover art |
| 🔀 **Smart Shuffle** | Won't repeat a song until every other track in the playlist has played |
| 📊 **Listening Stats** | Tracks play count and total listening time per song |
| 🎵 **Audio-only Filter** | One-click toggle to show only mp3/flac/ogg/wav files |
| ⌨️ **Keyboard Shortcuts** | Space, K, arrow keys — see table below |
| 🌐 **i18n** | English and Turkish, switchable in Settings |
| 🔤 **Font Choice** | DM Sans or Anthropic Serif |
| 🚀 **Autostart** | Optional background launch at boot |
| 🧩 **Coming soon** | Icon-only mode (1.7.3), personalized recommendations, plugins, theming |

### Keyboard Shortcuts

| Key | Function |
|---|---|
| `Space` | Play / Pause |
| `K` | Toggle now-playing panel |
| `←` `→` | Previous / Next track |
| `Escape` | Close search panel |

### File Locations

| What | Where |
|---|---|
| Music | `~/BooPlaylist` (configurable) |
| Settings | `~/.config/boomusic/config.json` |
| Statistics | `~/.local/share/boomusic/stats.json` |
| Log | `~/.local/share/boomusic/boomusic.log` |
| Program files | `~/.local/share/boomusic/install/` |
| Launcher | `~/.local/bin/boomusic` |

### Platform Support

Currently **Linux only**. Windows and Android are planned for v2.0.

### Built With

Python · pywebview · libVLC · GTK · WebKit2GTK

---

## TR — Türkçe

### Neden Boomusic?

Çoğu "ücretsiz" müzik çalar bir süre sonra sizden para ister, reklam gösterir ya da özellikleri kilitler. Boomusic bunu yapmaz. Sadece müziğinizin hızlı, sade ve gerektiğinde gözden kaybolarak (tepsi ikonu sayesinde) çalmasını isteyenler için tasarlanmış, yerel bir müzik çalar.

### Özellikler

| | |
|---|---|
| 🔎 **YT-dlp Desteği** | Boomusic içinden YouTube'da şarkı ara, indir ve çal |
| 🖱️ **Sürükle-Bırak** | Ses dosyalarını playlist'e sürükle, ad/sanatçıyı manuel düzenle |
| 📁 **Sınırsız Playlist** | Sınırsız playlist, sınırsız şarkı, özel kapak resmi |
| 🔀 **Smart Shuffle** | Diğer tüm şarkılar çalınmadan aynı şarkı tekrar çalmaz |
| 📊 **Dinleme İstatistikleri** | Her şarkı için çalma sayısı ve süresi kaydı |
| 🎵 **Sadece Ses Filtresi** | Tek tıkla sadece mp3/flac/ogg/wav dosyalarını göster |
| ⌨️ **Klavye Kısayolları** | Space, K, ok tuşları — aşağıdaki tabloya bakın |
| 🌐 **Dil Desteği** | Ayarlar'dan İngilizce/Türkçe geçişi |
| 🔤 **Yazı Tipi Seçimi** | DM Sans veya Anthropic Serif |
| 🚀 **Otomatik Başlatma** | Açılışta arka planda opsiyonel başlatma |
| 🧩 **Yakında** | Sadece ikon modu (1.7.3), kişisel öneriler, eklentiler, tema özelleştirme |

### Klavye Kısayolları

| Tuş | İşlev |
|---|---|
| `Space` | Oynat / Duraklat |
| `K` | Şimdi çalan panelini aç/kapat |
| `←` `→` | Önceki / Sonraki şarkı |
| `Escape` | Arama panelini kapat |

### Dosya Konumları

| Ne | Nerede |
|---|---|
| Müzik | `~/BooPlaylist` (değiştirilebilir) |
| Ayarlar | `~/.config/boomusic/config.json` |
| İstatistikler | `~/.local/share/boomusic/stats.json` |
| Günlük | `~/.local/share/boomusic/boomusic.log` |
| Program dosyaları | `~/.local/share/boomusic/install/` |
| Başlatıcı | `~/.local/bin/boomusic` |

---

## Smart Shuffle

**EN:** A song can't be selected again until every other song in the playlist has played at least once. Once the full round finishes, the algorithm resets.

**TR:** Bir şarkı, playlist'teki diğer tüm şarkılar en az bir kez çalınmadan tekrar seçilemez. Tur bittiğinde algoritma sıfırlanır.

---

## Installation / Kurulum

```bash
bash install.sh
```

The script:

1. Installs system packages (`python-gobject`, `gtk3`, `webkit2gtk`, `vlc`, etc.)
2. Creates a Python virtual environment
3. Installs Python dependencies (`pystray`, `pillow`, `python-vlc`, `pywebview`, `mutagen`)
4. Copies application files
5. Creates a launcher at `~/.local/bin/boomusic`
6. Adds Boomusic to the application menu
7. Optionally enables autostart

---

## Contributing / Katkı

<!-- Add a short paragraph: are PRs welcome? Any coding style / issue template expectations? -->
Issues and pull requests are welcome — check [open issues](https://github.com/beratboomindev/Boomusic-The-Music-Player/issues) to get started.

## License / Lisans

This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute.

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır — kullanmak, değiştirmek ve dağıtmak serbesttir.

## Contact / İletişim

**EN:** Found a bug or have feedback? Reach me at **bertaboomin@proton.me**, or on Instagram [@beratboomindev](https://instagram.com/beratboomindev).

**TR:** Bir şey mi buldun? Bana **bertaboomin@proton.me** adresinden ya da Instagram'dan [@beratboomindev](https://instagram.com/beratboomindev) üzerinden ulaşabilirsin.

---

<div align="center">

Built with Python, pywebview, libVLC, and ♥

</div>
