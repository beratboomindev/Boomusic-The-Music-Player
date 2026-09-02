<p align="center">
  <img src="src/boomusic/assets/icon.png" width="256" alt="Boomusic">
</p>

<h1 align="center">Boomusic — The Music Player</h1>

<p align="center"><strong>No premium. No ads. No nonsense.</strong></p>

<p align="center">
  <a href="https://github.com/beratboomindev/Boomusic-The-Music-Player/releases">Download</a>
  ·
  <a href="https://github.com/beratboomindev/Boomusic-The-Music-Player/issues">Report Bug</a>
  ·
  <a href="https://github.com/beratboomindev/Boomusic-The-Music-Player">Source</a>
</p>

---

## Installation

```bash
git clone https://github.com/beratboomindev/Boomusic-The-Music-Player.git
cd Boomusic-The-Music-Player
bash install.sh
```

Non-interactive update:

```bash
bash update.sh
```

Pre-built releases: [Releases](https://github.com/beratboomindev/Boomusic-The-Music-Player/releases)

---

## Features

- YT-dlp Support
- Drag & Drop Songs
- Playlists (unlimited)
- Right-Click Context Menus
- Smart Shuffle
- Listening Statistics
- Only Songs Filter
- Keyboard Shortcuts
- i18n (English / Turkish)
- Font Selection
- Auto Startup
- Just Icon Mode (Tray-only)
- Theming *(Coming Soon)*
- Plugins *(Coming Soon)*
- Spotify Integration *(Coming Soon)*
- Recommended for You *(Coming Soon)*

See **[WHATNOW.md](WHATNOW.md)** for the full roadmap.

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play / Pause |
| K | Toggle Now Playing panel |
| ← → | Previous / Next |
| Escape | Close search |

---

## File Locations

| What | Path |
|------|------|
| Music | `~/BooPlaylist` |
| Settings | `~/.config/boomusic/config.json` |
| Stats | `~/.local/share/boomusic/stats.json` |
| Log | `~/.local/share/boomusic/boomusic.log` |
| Launcher | `~/.local/bin/boomusic` |

---

## Platform

Linux now. Windows & Android planned.

---

## Troubleshooting

**Window never appears (only tray icon):**
```bash
sudo pacman -S webkit2gtk-4.1      # Arch
sudo apt install libwebkit2gtk-4.1-0   # Debian/Ubuntu
sudo dnf install webkit2gtk4.1     # Fedora
```

**No audio:**
```bash
sudo pacman -S vlc                # Arch
sudo apt install vlc              # Debian/Ubuntu
sudo dnf install vlc              # Fedora
```

**Python / venv missing:**
```bash
sudo pacman -S python                              # Arch
sudo apt install python3 python3-venv python3-pip  # Debian/Ubuntu
sudo dnf install python3 python3-pip               # Fedora
```

---

*Built with Python, pywebview, libVLC, and ♥*
