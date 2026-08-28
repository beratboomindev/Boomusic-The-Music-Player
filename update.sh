#!/usr/bin/env bash
# Boomusic - The Music Player | Güncelleme betiği
#
# Kullanım:
#   bash update.sh
#
# Bu betik, install.sh'in TAMAMEN ETKİLEŞİMSİZ (soru sormayan) ve
# uygulamayı başlatmayan sürümüdür. Mevcut bir kurulumun üzerine yazmak
# için tasarlanmıştır; özellikle şu durumlar için uygundur:
#   - Yeni sürüm çıktı, kaynak dosyalar güncellendi, sadece dosyaların
#     kurulum konumuna kopyalanması + venv'in yenilenmesi yeterli.
#   - CI/CD veya uzaktan yönetim: aynı betiği farklı makinelerde
#     çalıştırıp tutarlı sonuç almak istiyorsun.
#   - Zaten 'just_icon_mode = true' kullanan bir makinede pencere hiç
#     istemiyorsun (yeniden başlatma oturumu bozar).
#
# Bu betik:
#   - Sistem paketlerini (pacman/apt/dnf) aynı install.sh gibi kurar/gunceller.
#   - Python sanal ortamını oluşturur; pip yoksa ensurepip dener; pip
#     kurulumu başarısız olursa yine de dosyaları kopyalar (kısmi kurulum).
#   - Uygulama dosyalarını ~/.local/share/boomusic/install/app altına kopyalar.
#   - Başlatıcıyı (~/.local/bin/boomusic) yeniden oluşturur.
#   - Uygulama menüsü girdisini (~/.local/share/applications/boomusic.desktop)
#     yeniden oluşturur.
#   - Eksik bileşen özetini yazdırır.
#
# Bu betik YAPMAZ (farkları):
#   - PATH sorusu sormaz (gerekirse kullanıcı kendisi ekler).
#   - Masaüstü simgesi sormaz/oluşturmaz.
#   - Otomatik başlatma (autostart) etkinleştirmez.
#   - Sonda uygulamayı başlatmaz.
#   - Mevcut çalışan örneği durdurmaz. Bunu update'ten önce kullanıcının
#     kendisi yapması beklenir (örn. "pkill -f 'boomusic'" veya tepsi
#     menüsünden "Çıkış"). Birden fazla örnek çalışırsa tek-örnek kilidi
#     yenisi başlatılmasını engeller; sorun yaşamamak için update öncesi
#     mevcut örneğin kapatılması önerilir.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src/boomusic"

INSTALL_DIR="$HOME/.local/share/boomusic/install"
VENV_DIR="$INSTALL_DIR/venv"
APP_DIR="$INSTALL_DIR/app"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/boomusic"
APPLICATIONS_DIR="$HOME/.local/share/applications"
ICON_INSTALLED_PATH="$APP_DIR/boomusic/assets/icon.png"

BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

info()  { printf "%s\n" "$1"; }
step()  { printf "\n${BOLD}==>${RESET} %s\n" "$1"; }
ok()    { printf "  ${GREEN}✔${RESET} %s\n" "$1"; }
warn()  { printf "  ${YELLOW}!${RESET} %s\n" "$1"; }

fail() {
    printf "\n${YELLOW}HATA:${RESET} %s\n" "$1" >&2
    exit 1
}

soft_fail() {
    printf "\n  ${YELLOW}!${RESET} %s\n" "$1" >&2
    if [[ -n "${2:-}" ]]; then
        printf "    Deneyebilirsin: %s\n" "$2" >&2
    fi
}

# Kullanıcının GERÇEK (yerelleştirilmiş) Belgeler klasörünü bulur.
documents_dir() {
    if command -v xdg-user-dir >/dev/null 2>&1; then
        local d
        d="$(xdg-user-dir DOCUMENTS 2>/dev/null)"
        if [[ -n "$d" ]]; then
            echo "$d"
            return
        fi
    fi
    if [[ -f "$HOME/.config/user-dirs.dirs" ]]; then
        local line value
        line="$(grep '^XDG_DOCUMENTS_DIR' "$HOME/.config/user-dirs.dirs" 2>/dev/null || true)"
        if [[ -n "$line" ]]; then
            value="${line#*=}"
            value="${value%\"}"; value="${value#\"}"
            value="${value/\$HOME/$HOME}"
            if [[ -n "$value" ]]; then
                echo "$value"
                return
            fi
        fi
    fi
    echo "$HOME/Documents"
}

DEFAULT_MUSIC_DIR="$(documents_dir)/BooPlaylist"

printf "${BOLD}Boomusic - The Music Player güncelleme${RESET}\n"
printf "${DIM}%s${RESET}\n" "$SRC_DIR"

if [[ ! -d "$SRC_DIR" ]]; then
    fail "Kaynak kod bulunamadı: $SRC_DIR (bu betiği proje klasörünün içinden çalıştırın)"
fi

# ---------------------------------------------------------------------------
step "1/9 - Python3 kontrol ediliyor"
if ! command -v python3 >/dev/null 2>&1; then
    printf "\n${YELLOW}HATA:${RESET} python3 bulunamadı.\n" >&2
    if command -v pacman >/dev/null 2>&1; then
        printf "  Arch / Manjaro / CachyOS için:   sudo pacman -S python\n" >&2
    fi
    if command -v apt >/dev/null 2>&1; then
        printf "  Debian / Ubuntu / Mint için:    sudo apt install python3 python3-venv python3-pip\n" >&2
    fi
    if command -v dnf >/dev/null 2>&1; then
        printf "  Fedora için:                    sudo dnf install python3 python3-pip\n" >&2
    fi
    if command -v zypper >/dev/null 2>&1; then
        printf "  openSUSE için:                  sudo zypper install python3 python3-pip\n" >&2
    fi
    exit 1
fi
PYTHON_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
ok "python3 bulundu (sürüm $PYTHON_VERSION)"

if ! python3 -c "import venv" >/dev/null 2>&1; then
    printf "\n${YELLOW}HATA:${RESET} python3 'venv' modülü bulunamadı.\n" >&2
    if command -v pacman >/dev/null 2>&1; then
        printf "  Arch / Manjaro / CachyOS için:   sudo pacman -S python (venv dahil)\n" >&2
    fi
    if command -v apt >/dev/null 2>&1; then
        printf "  Debian / Ubuntu / Mint için:    sudo apt install python3-venv\n" >&2
    fi
    if command -v dnf >/dev/null 2>&1; then
        printf "  Fedora için:                    sudo dnf install python3-virtualenv\n" >&2
    fi
    exit 1
fi
ok "python3 venv modülü hazır."

# ---------------------------------------------------------------------------
step "2/9 - Tepsi simgesi, GUI penceresi ve ses motoru için sistem bağımlılıkları"
info "Boomusic'in çalışması için gerekli sistem paketleri kuruluyor."

if command -v pacman >/dev/null 2>&1; then
    APPINDICATOR_CANDIDATES=(libayatana-appindicator libappindicator-gtk3)
    appindicator_pkg=""
    for cand in "${APPINDICATOR_CANDIDATES[@]}"; do
        if pacman -Si "$cand" >/dev/null 2>&1; then
            appindicator_pkg="$cand"
            break
        fi
    done

    WEBKIT_CANDIDATES=(webkit2gtk-4.1 webkit2gtk)
    webkit_pkg=""
    for cand in "${WEBKIT_CANDIDATES[@]}"; do
        if pacman -Si "$cand" >/dev/null 2>&1; then
            webkit_pkg="$cand"
            break
        fi
    done

    pkgs_to_install=("python-gobject" "gtk3" "vlc" "zenity" "yt-dlp")
    if [[ -n "$appindicator_pkg" ]]; then
        pkgs_to_install+=("$appindicator_pkg")
    else
        warn "Depo içinde bilinen bir appindicator paketi bulunamadı; tepsi simgesi Xorg'a düşebilir."
    fi
    if [[ -n "$webkit_pkg" ]]; then
        pkgs_to_install+=("$webkit_pkg")
    else
        warn "Depo içinde webkit2gtk bulunamadı; GUI penceresi açılamayabilir (tray yine çalışır)."
    fi

    info "Kurulacak paketler: ${pkgs_to_install[*]}"
    if sudo pacman -S --needed --noconfirm "${pkgs_to_install[@]}"; then
        ok "Sistem bağımlılıkları kuruldu."
    else
        soft_fail \
            "Sistem paketleri kurulamadı (sudo parolası reddedildi, depo kilitli ya da ağ yok olabilir)." \
            "sudo pacman -S --needed ${pkgs_to_install[*]}"
    fi
elif command -v apt >/dev/null 2>&1; then
    info "Debian/Ubuntu/Mint tabanlı sistem algılandı."
    info "  Gerekli paketler: python3-gi gir1.2-gtk-3.0 libwebkit2gtk-4.1-0 vlc zenity yt-dlp"
    info "  Kurmak için:      sudo apt install python3-gi gir1.2-gtk-3.0 libwebkit2gtk-4.1-0 vlc zenity yt-dlp"
    warn "Kurulum otomatik yapılmadı; lütfen yukarıdaki komutu elle çalıştırın."
elif command -v dnf >/dev/null 2>&1; then
    info "Fedora/RHEL tabanlı sistem algılandı."
    info "  Gerekli paketler: python3-gobject gtk3 webkit2gtk4.1 vlc zenity yt-dlp"
    info "  Kurmak için:      sudo dnf install python3-gobject gtk3 webkit2gtk4.1 vlc zenity yt-dlp"
    warn "Kurulum otomatik yapılmadı; lütfen yukarıdaki komutu elle çalıştırın."
else
    warn "Bilinen bir paket yöneticisi bulunamadı (pacman/apt/dnf yok)."
fi

# ---------------------------------------------------------------------------
step "3/9 - Python sanal ortamı (venv) hazırlanıyor"
mkdir -p "$INSTALL_DIR"
if [[ -d "$VENV_DIR" ]]; then
    ok "Sanal ortam zaten var, yeniden kullanılıyor: $VENV_DIR"
else
    if ! python3 -m venv --system-site-packages --without-pip "$VENV_DIR" 2>/dev/null; then
        if ! python3 -m venv --system-site-packages "$VENV_DIR"; then
            printf "\n${YELLOW}HATA:${RESET} Sanal ortam oluşturulamadı.\n" >&2
            if command -v apt >/dev/null 2>&1; then
                printf "  Debian/Ubuntu'da:  sudo apt install python3-venv python3-full\n" >&2
            fi
            exit 1
        fi
    fi
    ok "Sanal ortam oluşturuldu: $VENV_DIR"
fi

if [[ ! -x "$VENV_DIR/bin/pip" ]]; then
    info "Sanal ortamda pip yok, 'ensurepip' ile etkinleştiriliyor..."
    if "$VENV_DIR/bin/python3" -m ensurepip --upgrade >/dev/null 2>&1; then
        ok "ensurepip ile pip etkinleştirildi."
    else
        soft_fail \
            "pip etkinleştirilemedi (ensurepip başarısız oldu, internet yok ya da kısıtlı Python)." \
            "$VENV_DIR/bin/python3 -m ensurepip --upgrade"
    fi
fi

if [[ -x "$VENV_DIR/bin/pip" ]]; then
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet 2>/dev/null || \
        soft_fail "pip'in kendisi güncellenemedi; sorun değil, paketlere geçiyoruz." ""

    info "Python paketleri kuruluyor (pystray, pillow, python-vlc, pywebview, mutagen, python-xlib)..."
    "$VENV_DIR/bin/pip" uninstall --quiet -y pygame pygame-ce >/dev/null 2>&1 || true
    PIP_OUTPUT="$("$VENV_DIR/bin/pip" install pystray pillow python-vlc pywebview mutagen python-xlib 2>&1)" || PIP_RC=$?
    PIP_RC="${PIP_RC:-0}"
    if [[ "$PIP_RC" -eq 0 ]]; then
        ok "Python paketleri kuruldu."
    else
        soft_fail "Bazı Python paketleri kurulamadı (exit=$PIP_RC)." \
            "$VENV_DIR/bin/pip install pystray pillow python-vlc pywebview mutagen python-xlib"
        printf "  pip'in son çıktısı:\n"
        printf "%s\n" "$PIP_OUTPUT" | tail -n 12 | sed 's/^/    /'
    fi
fi

# ---------------------------------------------------------------------------
step "4/9 - Uygulama dosyaları kopyalanıyor"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
if ! cp -r "$SRC_DIR" "$APP_DIR/boomusic"; then
    fail "Uygulama dosyaları kopyalanamadı ($APP_DIR). Disk dolu olabilir ya da izinler yetersiz olabilir."
fi
ok "Kopyalandı: $APP_DIR/boomusic"

# ---------------------------------------------------------------------------
step "5/9 - Anthropic Serif font dosyası indiriliyor (çevrimdışı kullanım için)"
FONT_DIR="$APP_DIR/boomusic/assets/fonts"
mkdir -p "$FONT_DIR"
if command -v curl >/dev/null 2>&1; then
  FONT_URL="https://assets-proxy.anthropic.com/claude-ai/v2/assets/v1/c66fc489e-C-BHYa_K.woff2"
  if curl -sL -o "$FONT_DIR/anthropic_serif.woff2" "$FONT_URL"; then
    ok "İndirildi: anthropic_serif.woff2"
  else
    warn "Anthropic Serif indirilemedi (internet?); Georgia yedek font olarak kullanılacak."
  fi
else
  warn "curl bulunamadı; font indirme atlandı. Georgia yedek font olarak kullanılacak."
fi

# ---------------------------------------------------------------------------
step "6/9 - Başlatıcı komutlar oluşturuluyor (~/.local/bin/)"
mkdir -p "$BIN_DIR"
LAUNCHER_TRAY="$BIN_DIR/boomusic-tray"
    cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
# Boomusic başlatıcı - update.sh tarafından otomatik oluşturuldu.
export PULSE_PROP_application.name="Boomusic"
export PULSE_PROP_application.icon_name="boomusic"
cd "$APP_DIR" || exit 1
exec "$VENV_DIR/bin/python3" -m boomusic "\$@"
EOF
chmod +x "$LAUNCHER"
if [[ ! -x "$LAUNCHER" ]]; then
    fail "Başlatıcı komut oluşturulamadı: $LAUNCHER"
fi
ok "Oluşturuldu: $LAUNCHER"

# Just Icon Mode için ayrı launcher.
    cat > "$LAUNCHER_TRAY" <<EOF
#!/usr/bin/env bash
# Boomusic Just Icon (sadece tepsi simgesi) - update.sh tarafından otomatik oluşturuldu.
export PULSE_PROP_application.name="Boomusic"
export PULSE_PROP_application.icon_name="boomusic"
cd "$APP_DIR" || exit 1
exec "$VENV_DIR/bin/python3" -m boomusic --tray-only "\$@"
EOF
chmod +x "$LAUNCHER_TRAY"
if [[ ! -x "$LAUNCHER_TRAY" ]]; then
    fail "Tray-only başlatıcı oluşturulamadı: $LAUNCHER_TRAY"
fi
ok "Oluşturuldu: $LAUNCHER_TRAY"

# ---------------------------------------------------------------------------
step "7/9 - Varsayılan müzik klasörü"
mkdir -p "$DEFAULT_MUSIC_DIR"
ok "Müziklerini şu klasöre koyabilirsin: $DEFAULT_MUSIC_DIR"

DATA_DIR="$HOME/.local/share/boomusic"
mkdir -p "$DATA_DIR"
if [[ -f "$SCRIPT_DIR/CHANGELOG.md" ]]; then
    cp "$SCRIPT_DIR/CHANGELOG.md" "$DATA_DIR/CHANGELOG.md"
    ok "Değişiklik günlüğü kopyalandı: $DATA_DIR/CHANGELOG.md"
fi

# ---------------------------------------------------------------------------
step "8/9 - Uygulama menüsüne ekleniyor (kolay açılış)"
mkdir -p "$APPLICATIONS_DIR"
cat > "$APPLICATIONS_DIR/boomusic.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Boomusic
Comment=Boomusic - The Music Player
Exec=$LAUNCHER
Icon=$ICON_INSTALLED_PATH
Terminal=false
Categories=AudioVideo;Audio;Player;
StartupWMClass=boomusic
EOF
ok "Uygulama menüsüne eklendi: $APPLICATIONS_DIR/boomusic.desktop"

# Just Icon Mode için ayrı .desktop girdisi.
cat > "$APPLICATIONS_DIR/boomusic-tray.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Boomusic (Sadece İkon)
Comment=Boomusic - Just Icon Mode (penceresiz, sadece tepsi simgesi)
Exec=$LAUNCHER_TRAY
Icon=$ICON_INSTALLED_PATH
Terminal=false
Categories=AudioVideo;Audio;Player;
StartupWMClass=boomusic
EOF
ok "Just Icon menüsü eklendi: $APPLICATIONS_DIR/boomusic-tray.desktop"

# ---------------------------------------------------------------------------
step "9/9 - Güncelleme tamamlandı"
info ""
info "  Müzik klasörü : $DEFAULT_MUSIC_DIR"
info "  Ayarlar       : ~/.config/boomusic/config.json"
info "  İstatistikler : ~/.local/share/boomusic/stats.json"
info "  Günlük (log)  : ~/.local/share/boomusic/boomusic.log"
info "  Değişiklikler : ~/.local/share/boomusic/CHANGELOG.md"
info ""
info "Bu betik uygulamayı BAŞLATMADI. Güncelleme sonrası:"
info "  - Yeni bir Boomusic örneği başlatmak için:  ${BOLD}boomusic${RESET}"
info "  - Çalışan örneği durdurmak için:           ${BOLD}pkill -f 'python3 -m boomusic'${RESET}"
info "    (yeni sürüm aktif olsun diye)"
info ""
info "${BOLD}Eksik bileşenler (varsa):${RESET}"
declare -a MISSING=()
if [[ ! -x "$VENV_DIR/bin/pip" ]]; then
    MISSING+=("pip -- pip kurulamadı; Python paketleri indirilemedi")
fi
if [[ ! -x "$VENV_DIR/bin/python3" ]]; then
    MISSING+=("Sanal ortam (venv) -- uygulama başlatılamaz")
fi
if command -v pacman >/dev/null 2>&1; then
    pacman -Qi vlc >/dev/null 2>&1 || MISSING+=("vlc -- ses çalmaz (sudo pacman -S vlc)")
    pacman -Qi zenity >/dev/null 2>&1 || MISSING+=("zenity -- ses kaydırıcısı çalışmaz (sudo pacman -S zenity)")
    pacman -Qi yt-dlp >/dev/null 2>&1 || MISSING+=("yt-dlp -- YouTube arama/indirme çalışmaz (sudo pacman -S yt-dlp)")
elif command -v apt >/dev/null 2>&1; then
    dpkg -s vlc >/dev/null 2>&1 || MISSING+=("vlc -- ses çalmaz (sudo apt install vlc)")
    dpkg -s zenity >/dev/null 2>&1 || MISSING+=("zenity -- ses kaydırıcısı çalışmaz (sudo apt install zenity)")
    dpkg -s yt-dlp >/dev/null 2>&1 || MISSING+=("yt-dlp -- YouTube arama/indirme çalışmaz (sudo apt install yt-dlp)")
elif command -v dnf >/dev/null 2>&1; then
    rpm -q vlc >/dev/null 2>&1 || MISSING+=("vlc -- ses çalmaz (sudo dnf install vlc)")
    rpm -q zenity >/dev/null 2>&1 || MISSING+=("zenity -- ses kaydırıcısı çalışmaz (sudo dnf install zenity)")
    rpm -q yt-dlp >/dev/null 2>&1 || MISSING+=("yt-dlp -- YouTube arama/indirme çalışmaz (sudo dnf install yt-dlp)")
fi
if [[ ${#MISSING[@]} -eq 0 ]]; then
    printf "  ${GREEN}✔${RESET} Tüm bilinen bağımlılıklar kurulu görünüyor.\n"
else
    for m in "${MISSING[@]}"; do
        printf "  ${YELLOW}!${RESET} %s\n" "$m"
    done
    printf "\n  Bu özellikler çalışmayabilir ama uygulama yine de başlatılabilir.\n"
fi
