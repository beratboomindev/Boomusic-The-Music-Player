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

---

## v1.6.1 — Colored progress/volume bar + hover flicker fix

- **Seek and volume bars now show the filled portion in purple**, clearly
  distinguishing played/set amount from the remainder.
- **Volume bar updates LIVE while dragging** (no need to release); sends IPC
  every ~80ms to avoid flooding the bridge, but visual fill updates instantly.
  Final value is applied on release.
- **Track list hover flicker fixed.** Root cause: the UI unconditionally
  rebuilt the entire track list and playlist panel every ~600ms; the element
  under the cursor was constantly destroyed and recreated, causing hover effects
  to flicker. Now, if the relevant data (current track, selected list, etc.)
  hasn't actually changed, the section is left untouched; only small frequently
  updated values (position, duration) are refreshed. Verified with automated
  tests against a real DOM (jsdom): same state and playback position advance
  keep DOM elements stable; only a real track change triggers a rebuild.

---

## v1.6.0 — CRITICAL: shutdown fix + installation fixes

**Issue 1 (critical): App wouldn't close from "Quit"**, requiring `killall python3`.
Root cause: v1.4.1 made tray and window share the same GTK loop (see that
release's notes), but "Quit" still only called `icon.stop()` — it did NOT close
the window, which owns the shared loop, so the loop never terminated.

**Fix:**
- "Quit" now actually closes the window first (`gui.quit()` → `window.destroy()`),
  which terminates the shared loop.
- **Safety net:** 4 seconds after "Quit" (or any shutdown signal), the process
  is unconditionally terminated. Manual `kill` should never be needed again.
- Added "Exit Boomusic" button in the settings panel as an alternative to the
  tray menu.

**Issue 2 (critical): Old version conflict on reinstall.**
`install.sh` now checks for a running Boomusic instance (via lock file) as its
FIRST step, before installing any packages. If found, it gracefully terminates
(SIGTERM, 5s wait), then force-kills (SIGKILL) if needed, before proceeding.

**Minor fix:** The "now playing" icon in the bottom bar now shows the cover art
of the playlist the current track belongs to (falls back to the note icon if no
cover).

**Note:** Other user requests (description field, center layout, "Boomin's
Shuffle" name + new shuffle modes, volume mixer name/icon, installation screen
simplification, tray↔window sync speed, auto folder watching) have been queued
and will be addressed one by one after critical items.

---

## v1.5.0 — Playlist cover art (step 1/9)

Step 1 of 9 from the user's feature request list: playlist cover images.

- Each playlist (including the root/"General" list) can have a cover image.
- Click the large cover in the selected list's header (pencil icon appears on
  hover) to open a native file picker; the selected image is auto-resized,
  converted to JPEG, and saved.
- Each playlist shows a small cover preview in the sidebar.
- **Covers are stored INSIDE the music folder** (as `cover.jpg` in each
  playlist's subdirectory; "General" uses the root). No separate database:
  covers survive uninstall/reinstall or even moving the folder to another
  computer. This partially addresses the user's 5th request ("data stored in
  music folder, readable after reinstall").
- `cover.jpg` files are never detected as tracks (extension filtering).

**Next up (in user-requested order, feedback expected after each step):**
2) "Boomusic" name/icon in volume mixer instead of "VLC",
3) cleaner/less noisy install output,
4) purple color on the played portion of the seek bar,
5) in-app playlist creation + description field,
6) everything doable from UI including adding tracks,
7) window icon fix,
8) faster tray↔window sync,
9) auto-folder watching (no manual "rescan").

---

## v1.4.1 — GTK conflict fix + diagnostics improvements

**Issue:** On some systems the window never opened; `boomusic.log` showed
"started" then silently hung with no error.

**Root cause:** The tray (pystray/AppIndicator) and window (pywebview/GTK) both
use GTK. Running both on SEPARATE threads with their own main loops is not safe
with GTK's threading model and can cause deadlocks.

**Fix:**
- When both window and tray are available, the tray no longer starts its own
  loop (`icon.run()` → `icon.run_detached()`). It only REGISTERS itself. The
  real SHARED GTK loop is started by the window (`webview.start()`), serving
  both the window and the tray. (Verified against pystray source code:
  `run_detached()` indeed does not start its own loop, only sets up and waits.)
- If the window is unavailable (e.g., webkit2gtk not installed), the tray runs
  on its own (single, safe) background thread as before.
- Added per-step log lines to `boomusic.log`: lock acquired, App/GUI/Tray
  created, mode (shared loop / own thread), GUI mainloop entered/exited, etc.
  If something hangs/crashes, the exact step is now visible.

**Other:**
- `install.sh` now installs required system packages (python-gobject, gtk3,
  appindicator, webkit2gtk-4.1, vlc, zenity) without prompting (the app won't
  work without them, so prompting was pointless).
- This CHANGELOG file added, copied to the same folder as `boomusic.log` during
  installation.

---

## v1.4.0 — Desktop window + VLC audio engine

- **New desktop window** (pywebview): playlists on the left, selected playlist's
  tracks in the center, now-playing + controls + real-time seek bar at the
  bottom, settings at top-right.
- **Playlists = subdirectories**: each subdirectory under `BooPlaylist`
  automatically appears as a separate playlist in the sidebar. No separate
  playlist management system; leverages existing folder scanning logic.
- **Audio engine moved from pygame-ce to libVLC.** Reason: the window needed
  reliable absolute seeking for MP3s (desired "seek to any second" feature).
  SDL_mixer/pygame only supports relative seeking in MP3, with errors on VBR
  encodes. libVLC provides format-independent accurate seeking. Fade in/out
  is now implemented manually (step-by-step volume changes on libVLC — VLC has
  no built-in `fade_ms` like pygame).
- Window close (X) hides the app instead of quitting (Discord/Slack style);
  "Show Window" added to tray menu.
- Settings panel: change music folder (native folder picker), rescan,
  notification toggle.
- Architecture: tray on separate thread, GUI on main thread (designed before
  the GTK conflict was discovered — see v1.4.1).

## v1.3.0 — Icon refresh and minor adjustments

- Tray/app icon redesigned: replaced the previous "circle + rectangle" (note)
  shape with a smoother, minimalist equalizer motif using uniform rounded bars.
- Default volume reduced from 80% to 10%.

## v1.2.0 — Fade in/out, shuffle toggle, easy launch, reliability

- **Fade in/out**: each track fades in over 2 seconds and fades out over
  2 seconds (on manual skip and natural end — duration is read via mutagen and
  used to trigger proactively).
- **Volume control**: one-click presets (0-100%) in tray menu; a real draggable
  slider window via `zenity` if installed.
- **"Pick Track" menu**: lists every track in the playlist for direct selection
  (▶ = playing, ✓ = played this round, ‣ = unplayed).
- **Smart Shuffle toggle**: when off, library plays sequentially.
- **Easy launch**: app now appears in the system application menu
  (KDE/GNOME/rofi/wofi); optional desktop icon.
- Volume mixer (pavucontrol etc.) now shows "Boomusic" instead of "python3"
  (via PulseAudio's `PULSE_PROP_application.name` mechanism).
- Documents folder now located per system language (`xdg-user-dir`); no longer
  hardcoded to "Documents".
- **Reliability fix**: ALL state-changing operations (shuffle toggle, library
  rescan, etc.) now go through a single background queue, making race conditions
  like "what if a track changes while shuffle is being toggled" structurally
  impossible (verified with a 15-random-command stress test).
- Architecture: tray moved to a separate background thread to free the main
  thread for a future GUI (this enabled v1.4.0's window).

## v1.1.0 — pygame mixer fix

- The official `pygame` package on some (especially very new) Python versions
  does not properly bundle the `mixer` submodule ("mixer module not available"
  error). Replaced with `pygame-ce`, a community fork with the same API and
  up-to-date wheels.

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
