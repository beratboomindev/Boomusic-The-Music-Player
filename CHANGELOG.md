# Boomusic - Changelog

This file documents changes for each release. After installation a copy
sits at `~/.local/share/boomusic/CHANGELOG.md` (same folder as `boomusic.log`).

---

## v1.7.2 — Bug fixes & i18n, splash screen, keyboard shortcuts, songs filter

- **i18n (language support) added.** English (default) and Turkish can be
  toggled from Settings.
- **Font selection added.** DM Sans or Anthropic Serif can be chosen in Settings.
- **Splash screen added.** Prevents white flash on startup; shows Boomusic
  branded purple splash with logo.
- **Keyboard shortcuts:** Space → play/pause, K → toggle now-playing panel,
  ←/→ → previous/next track.
- **Songs-only filter.** ♪ toggle shows only audio files
  (mp3/flac/ogg/wav/m4a/wma/opus/aac).
- **`t is not a function` bug fixed.** `var t = tracks[i]` hoisting issue resolved.
- **Config now has font + language.** `font_family` and `language` fields,
  `set_font()`/`set_language()` APIs.

---

## v1.7.2 — Now-playing panel, notifications removed, track list expanded

- **Now-Playing Panel added** (right side). Fixed overlay when a track plays:
  200×200 playlist cover, divider, track name, artist (hidden if empty),
  duration. Opacity 0.5, `pointer-events: none`, transparent background.
- **Toggle in Settings** (Now-Playing Panel toggle). Panel width adapts via
  `min(300px, 24vw)`.
- **Cover class conflict fixed.** `.np-cover` clashed with bottom bar;
  renamed to `.np-panel-cover`.
- **Notifications removed.** All `notifier.notify()` calls, UI toggle, and
  API cleaned up entirely.
- **Settings button moved to top-right** (from bottom bar to `.search-area`,
  absolute position).
- **Track list expanded.** Row padding 7→10px, font 13→14px, grid columns
  28→32px, gap 8→12px. Playlist header cover 120→140px, title 24→28px.
- **Default notification state off** (`notifications_enabled: bool = False`).
- **Default volume stays at 10%** (carried over from previous releases).
- `__version__` = "1.7.2"

---

## v1.7.gd-1 — Bug fixes: icon, animation, cover size, sidebar resize

- **Window icon fixed.** GTK now uses `assets/icon.png` as the window icon
  (previously unset).
- **Search animation loop stopped.** `renderSearchResults()` ran every 600ms,
  causing the stagger animation to replay continuously. DOM is no longer
  rebuilt when results haven't changed.
- **Playlist cover size fixed.** Cover images on playlists without the `pl-cover`
  class on the outer `<span>` could exceed the 28×28 constraint.
- **Sidebar now resizable.** A 4px resize handle on the right edge allows
  dragging between 140–400px.
- Build: `boomusic_1.7.gd-1.tar.gz`

---

## v1.7.gd — Premium/minimalist UI redesign (FROM SCRATCH)

- **gui.html rewritten from scratch.** Entire old UI replaced with a premium,
  dark-theme, glassmorphism, gradient-transition, fluid-animation interface.
- **Grid-based layout:** Cards, lists, and panels use a flexible grid that
  adapts fluidly to window size.
- **CSS variable scaling:** `--scale` dynamically adjusts from 0.75× to 1.8×
  based on viewport; a `resize` listener updates it instantly.
- **"1.7.gd" badge in sidebar** marking this experimental design version.
- This release touches only the visual layer; no logic changes.
- `__version__` = "1.7.gd"
- Build: `boomusic_1.7.gd.tar.gz` (134K)

---

## v1.7.1 — Code review fixes + responsive window size

### Audio engine
- **Bug:** `--pulse-audio-name=Boomusic` passed to `vlc.Instance()` is not
  recognized by VLC 3.0.23. When the VLC instance failed to create,
  `'NoneType' object has no attribute 'media_player_new'` was raised and the
  app ran silently (no audio).
- **Fix:** Removed `--pulse-audio-name`; this function was already handled
  by the `PULSE_PROP_application.name` environment variable in `__main__.py`.
- **Extra guard:** If `vlc.Instance()` returns `None`, a `RuntimeError` is now
  explicitly raised and logged instead of silently failing.

### Critical bug fixes
- **Download progress modal not working.** `get_active_downloads()` returned
  a list, but JS checked `count > 0`; `[...] > 0` is always `false` in JS,
  so the modal never opened.
- **`get_download_progress()` called without arguments.** JS called it without
  a key parameter, causing a TypeError in Python. Now uses the key from the first
  active download returned by `get_active_downloads()`.
- **XSS vulnerability closed.** All external text data (track names, artists,
  YouTube titles, playlist names and descriptions) is now HTML-escaped
  (`escapeHtml()`) before being written to `innerHTML`. Affected points: search
  results, home cards, track lists, bottom bar, settings panel.

### Thread safety
- **`_download_progress` dict synchronized.** Multiple download threads could
  write to the same dict simultaneously; all reads/writes are now protected by
  `_download_lock`. Added `_update_dl_progress()` helper for cleaner interface.

### Security
- **`rename_playlist()` path traversal protection.** Characters `..`, `/`, `\\`
  are rejected in playlist names; invalid names raise `ValueError`.

### Responsive Window
- **Window size now adapts to screen resolution.** Instead of a fixed 980×640,
  GTK detects screen size and computes width as 70% and height as 78% of the
  screen (minimum 980×640). High-DPI/high-resolution screens no longer get a
  tiny window.
- **`--scale` CSS variable is now dynamic.** Based on window size (base: 980×640),
  auto-scales between 0.75× and 1.8×. Sidebar width also scales proportionally.
- `--scale` recalculates on window `resize` events.

### Performance & Architecture
- **`played_at` sort removed.** `Track`/`TrackEntry` had no `played_at` field;
  the meaningless sort in "Recently Played" was replaced with descending
  `play_count` order.
- **Dead code cleaned:** `Settings.youtube_enabled`, `toggle_youtube()`,
  `_do_toggle_youtube()`, `youtube_enabled()` removed (this setting was never
  toggled from any UI element; all UI uses `youtube_mix_with_local`).
- **`import re` moved to module level** (`youtube.py`).

### Technical
- `__version__` = "1.7.1"

---

## v1.7.0 — YouTube Music integration (yt-dlp) + Unified Search + MP3 Download

**New feature: YouTube Music integration.** Uses yt-dlp to search YouTube
Music for tracks and podcasts, play them directly, and download as MP3.

### New Features
- **Unified search bar:** Separate YouTube search box removed from sidebar;
  single centered search bar searches local library + YouTube together.
  Results shown in the same list with "Local" and "YT" labels.
- **YouTube Music search:** Uses `ymsearch` (falls back to `ytsearch` if no
  results); only music content returned — videos/clips/ads excluded.
- **Duration filter:** Videos shorter than 30 seconds automatically filtered.
- **Ad-free:** yt-dlp inherently strips ads.
- **Stream URL cache:** Played tracks cached for 30 minutes. First 2 search
  result videos prewarmed into cache.
- **YouTube MP3 download:** Any YouTube video (or URL) can be downloaded as
  MP3 into a "YouTube Downloads" folder under the music directory. Download
  progress shown as percentage in the UI. Library auto-rescans after download.
- **YouTube + local mix mode:** Toggleable on/off.
- **Tray menu YouTube toggle** added, labeled "Online" / "Offline".
- **Playlist management:** Create, rename, and add descriptions to playlists
  from within the app (`create_playlist()`, `rename_playlist()`, `playlist_meta()`).
- **Clipboard reading:** `wl-paste` / `xclip` / `xsel` support for easy URL
  pasting.

### Performance
- **Stats batch save:** `record_play` now debounces writes for 2 seconds instead
  of writing every call. Reduces disk writes significantly during continuous playback.

### Technical Details
- `youtube.py` **(new file, 373 lines):** All YouTube logic (search, stream URL,
  cache, video info, MP3 download, progress tracking)
- `config.py`: Added `youtube_enabled`, `youtube_mix_with_local`,
  `youtube_search_limit` settings
- `library.py`: Added `source`, `thumbnail_url`, `youtube_video_id` fields to
  Track; `is_youtube` property; `create_playlist()`, `rename_playlist()`,
  `playlist_meta()`, `set_playlist_meta()` methods; `PLAYLIST_META_FILENAME`
- `player.py`: Added `set_current_path()` (for YouTube stream URLs)
- `app.py`: Added `search_youtube()`, `search_all()`, `play_youtube()`,
  `play_youtube_in_mix()`, `toggle_youtube()`, `toggle_youtube_mix()`,
  `download_youtube()`, `download_youtube_url()`, `get_download_progress()`,
  `get_active_downloads()`, `create_playlist()`, `edit_playlist()` methods;
  `playback_state()` now includes `youtube_enabled`/`youtube_mix_enabled`
- `gui.py`: JS bridge methods for all above; `get_state()` YouTube fields
- `tray.py`: YouTube toggle menu text "Online" / "Offline"
- `stats.py`: Batch save (2s debounce) optimization
- `shuffle.py`: `add_track()` support for YouTube tracks
- `install.sh`: Added yt-dlp as dependency

### Requirements
- `yt-dlp` must be installed (`install.sh` installs it automatically)
- Internet connection required

## v1.0.0 — Initial release

- Tray-based local music player for CachyOS/Arch Linux.
- Default music folder (`~/Documents/BooPlaylist`), mp3/ogg/wav/flac support,
  subdirectory scanning.
- **Smart Shuffle**: no track repeats until all others have been played
  ("bag shuffle" algorithm).
- Next/previous, pause/resume, volume control.
- Listening stats (`stats.json`) — how many times each track was played.
- `install.sh` / `uninstall.sh`: virtual environment setup, optional autostart,
  safe uninstall that never touches music files.
