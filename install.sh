#!/usr/bin/env bash
# Boomusic - The Music Player | Kurulum betiği
#
# Kullanım:
#   bash install.sh
#
# Bu betik CachyOS / Arch tabanlı sistemler için tasarlanmıştır ama sadece
# python3 + pip olan herhangi bir Linux masaüstünde de (tepsi simgesi için
# gereken sistem paketleri kurulu olduğu sürece) çalışabilir.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src/boomusic"

INSTALL_DIR="$HOME/.local/share/boomusic/install"
VENV_DIR="$INSTALL_DIR/venv"
APP_DIR="$INSTALL_DIR/app"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/boomusic"
AUTOSTART_DIR="$HOME/.config/autostart"
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

ask_yes_no() {
    # $1 = soru metni, varsayılan: Evet
    local reply
    read -r -p "$1 [E/h]: " reply
    reply=${reply:-E}
    [[ "$reply" =~ ^[EeYy] ]]
}

fail() {
    printf "\n${YELLOW}HATA:${RESET} %s\n" "$1" >&2
    exit 1
}

# Kullanıcının GERÇEK (yerelleştirilmiş) Belgeler klasörünü bulur -- Türkçe
# sistemde "Belgeler", İngilizce'de "Documents" olabilir; sabit "Documents"
# varsaymak yanlış klasör açabilir. config.py'deki _localized_documents_dir()
# ile aynı mantık (üç kademeli: xdg-user-dir -> user-dirs.dirs -> son çare).
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

# Kurulum/güncelleme sırasında hâlâ çalışan (özellikle eski, "Çıkış"ı
# düzgün çalışmayan bir sürümden kalma) bir Boomusic örneği varsa düzgünce
# (gerekirse zorla) kapatır. Böylece kullanıcı elle 'killall python3'
# yapmak zorunda kalmaz ve güncelleme temiz bir başlangıç yapar.
stop_existing_instance() {
    local lock_file="$HOME/.local/share/boomusic/boomusic.lock"
    [[ -f "$lock_file" ]] || return 0

    local pid
    pid="$(tr -d '[:space:]' < "$lock_file" 2>/dev/null)"
    [[ "$pid" =~ ^[0-9]+$ ]] || return 0
    kill -0 "$pid" 2>/dev/null || return 0  # süreç zaten yok, kilit eskimiş

    info "Çalışan bir Boomusic örneği bulundu (pid=$pid), kapatılıyor..."
    kill -TERM "$pid" 2>/dev/null || true
    local i
    for i in $(seq 1 10); do
        if ! kill -0 "$pid" 2>/dev/null; then
            ok "Önceki örnek düzgünce kapandı."
            return 0
        fi
        sleep 0.5
    done

    warn "Önceki örnek 5 saniyede kapanmadı, zorla sonlandırılıyor..."
    kill -KILL "$pid" 2>/dev/null || true
    sleep 0.5
    if kill -0 "$pid" 2>/dev/null; then
        warn "Süreç hâlâ görünüyor (pid=$pid); kuruluma yine de devam ediliyor."
    else
        ok "Önceki örnek zorla kapatıldı."
    fi
}

printf "${BOLD}Boomusic - The Music Player kurulumu${RESET}\n"
printf "${DIM}%s${RESET}\n" "$SRC_DIR"

if [[ ! -d "$SRC_DIR" ]]; then
    fail "Kaynak kod bulunamadı: $SRC_DIR (bu betiği proje klasörünün içinden çalıştırın)"
fi

# ---------------------------------------------------------------------------
step "1/10 - Önceki çalışan örnek kontrol ediliyor"
stop_existing_instance

# ---------------------------------------------------------------------------
step "2/10 - Python3 kontrol ediliyor"
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 bulunamadı. CachyOS/Arch'ta kurmak için: sudo pacman -S python"
fi
PYTHON_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
ok "python3 bulundu (sürüm $PYTHON_VERSION)"

if ! python3 -c "import venv" >/dev/null 2>&1; then
    fail "python3 'venv' modülü bulunamadı. CachyOS/Arch'ta genelde python paketiyle birlikte gelir: sudo pacman -S python"
fi

# ---------------------------------------------------------------------------
step "3/10 - Tepsi simgesi, GUI penceresi ve ses motoru için sistem bağımlılıkları"
info "Boomusic'in çalışması için gerekli sistem paketleri kuruluyor: tepsi"
info "simgesi için python-gobject + appindicator, pencere için GTK +"
info "WebKit2GTK, ses çalma/sarma için VLC, ses kaydırıcısı için zenity,"
info "YouTube araması için yt-dlp."

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
        warn "pacman kurulumu başarısız oldu; bazı özellikler (pencere/tepsi/kaydırıcı) çalışmayabilir."
        warn "Elle deneyebilirsin: sudo pacman -S ${pkgs_to_install[*]}"
    fi
else
    warn "pacman bulunamadı (Arch tabanlı bir sistemde değilsiniz gibi görünüyor)."
    info "Dağıtımınızın PyGObject + AppIndicator + WebKit2GTK + VLC paketlerini kurması gerekebilir."
fi

# ---------------------------------------------------------------------------
step "4/10 - Python sanal ortamı (venv) hazırlanıyor"
mkdir -p "$INSTALL_DIR"
if [[ -d "$VENV_DIR" ]]; then
    ok "Sanal ortam zaten var, yeniden kullanılıyor: $VENV_DIR"
else
    # --system-site-packages: pacman ile kurulan python-gobject'in (PyGObject)
    # venv içinden de görülebilmesi için gerekli (pip ile PyGObject kurmak
    # derleyici/geliştirme paketleri gerektirdiği için pratik değil).
    python3 -m venv --system-site-packages "$VENV_DIR" || fail "Sanal ortam oluşturulamadı."
    ok "Sanal ortam oluşturuldu: $VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip --quiet
info "Python paketleri kuruluyor (pystray, pillow, python-vlc, pywebview, mutagen, python-xlib)..."
# NOT: Ses motoru artık 'pygame'/'pygame-ce' DEĞİL, python-vlc. Sebep: arayüzdeki
# "istediğin saniyeye sar" özelliği için MP3'lerde GÜVENİLİR, mutlak seek
# gerekiyordu; SDL_mixer bunu MP3'te sadece göreceli ve bazen hatalı yapabiliyor,
# libVLC ise formattan bağımsız doğru seek sağlıyor. Önceki bir kurulumdan kalan
# pygame/pygame-ce varsa (çakışmasın diye) önce kaldırılır.
"$VENV_DIR/bin/pip" uninstall --quiet -y pygame pygame-ce >/dev/null 2>&1 || true
if ! "$VENV_DIR/bin/pip" install --quiet pystray pillow python-vlc pywebview mutagen python-xlib; then
    fail "Python paketleri kurulamadı. İnternet bağlantınızı kontrol edip tekrar deneyin."
fi
ok "Python paketleri kuruldu."

# ---------------------------------------------------------------------------
step "5/10 - Uygulama dosyaları kopyalanıyor"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
if ! cp -r "$SRC_DIR" "$APP_DIR/boomusic"; then
    fail "Uygulama dosyaları kopyalanamadı ($APP_DIR)."
fi
ok "Kopyalandı: $APP_DIR/boomusic"

# ---------------------------------------------------------------------------
step "6/10 - Anthropic Serif font dosyası indiriliyor (çevrimdışı kullanım için)"
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
step "7/10 - Başlatıcı komut oluşturuluyor (~/.local/bin/boomusic)"
mkdir -p "$BIN_DIR"
    cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
# Boomusic başlatıcı - install.sh tarafından otomatik oluşturuldu.
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

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR PATH içinde görünmüyor."
    if ask_yes_no "Kabuk yapılandırma dosyanıza (~/.bashrc veya ~/.zshrc) otomatik eklememi ister misiniz?"; then
        shell_rc="$HOME/.bashrc"
        case "${SHELL:-}" in
            *zsh*) shell_rc="$HOME/.zshrc" ;;
        esac
        if ! grep -q '\.local/bin' "$shell_rc" 2>/dev/null; then
            {
                echo ""
                echo "# Boomusic tarafından eklendi"
                echo 'export PATH="$HOME/.local/bin:$PATH"'
            } >> "$shell_rc"
            ok "$shell_rc güncellendi (etkili olması için terminali yeniden açın)."
        else
            ok "$shell_rc içinde zaten bir '.local/bin' girişi var."
        fi
    else
        info "Elle eklemek için: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

# ---------------------------------------------------------------------------
step "8/9 - Varsayılan müzik klasörü"
mkdir -p "$DEFAULT_MUSIC_DIR"
ok "Müziklerini şu klasöre koyabilirsin: $DEFAULT_MUSIC_DIR"
info "  (Sisteminizin dilindeki Belgeler klasörü otomatik bulundu; alt klasörler"
info "  de taranır; mp3/ogg/wav/flac desteklenir.)"

# Değişiklik günlüğünü boomusic.log ile AYNI klasöre kopyalıyoruz ki
# sorun yaşandığında ikisi yan yana bulunabilsin.
DATA_DIR="$HOME/.local/share/boomusic"
mkdir -p "$DATA_DIR"
if [[ -f "$SCRIPT_DIR/CHANGELOG.md" ]]; then
    cp "$SCRIPT_DIR/CHANGELOG.md" "$DATA_DIR/CHANGELOG.md"
    ok "Değişiklik günlüğü kopyalandı: $DATA_DIR/CHANGELOG.md (günlük dosyasıyla aynı yerde)"
fi

# ---------------------------------------------------------------------------
step "9/9 - Uygulama menüsüne ekleniyor (kolay açılış)"
# Bu, autostart'tan FARKLI: uygulamanın KDE/GNOME/rofi/wofi gibi her uygulama
# başlatıcısında görünmesini sağlar (çift tıkla / arat, aç). Hiçbir yan etkisi
# olmadığı için (sadece görünürlük) izin sormaya gerek yok.
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
info "  Artık uygulama başlatıcından (KDE Kickoff, GNOME Overview, rofi/wofi, vb.)"
info "  'Boomusic' araması yaparak da açabilirsin -- terminale yazmaya gerek yok."

if ask_yes_no "Masaüstüne de (~/Desktop) çift tıklanabilir bir simge koyayım mı?"; then
    desktop_dir="$(documents_dir)"  # yalnızca fallback için; asıl Desktop yolu aşağıda
    desktop_dir="$HOME/Desktop"
    if command -v xdg-user-dir >/dev/null 2>&1; then
        d="$(xdg-user-dir DESKTOP 2>/dev/null)"
        [[ -n "$d" ]] && desktop_dir="$d"
    fi
    if [[ -d "$desktop_dir" ]]; then
        cp "$APPLICATIONS_DIR/boomusic.desktop" "$desktop_dir/boomusic.desktop"
        chmod +x "$desktop_dir/boomusic.desktop"
        # GNOME/Nautilus, güvenmediği .desktop dosyalarını "Truste Launch"
        # onayı istemeden çalıştırmaz; varsa 'gio' ile güvenilir işaretliyoruz.
        if command -v gio >/dev/null 2>&1; then
            gio set "$desktop_dir/boomusic.desktop" metadata::trusted true >/dev/null 2>&1 || true
        fi
        ok "Masaüstüne eklendi: $desktop_dir/boomusic.desktop"
        info "  (GNOME'da ilk çift tıklamada 'Güven/Launch' onayı isteyebilir, normaldir.)"
    else
        warn "Masaüstü klasörü bulunamadı ($desktop_dir); bu adım atlandı."
    fi
fi

# ---------------------------------------------------------------------------
step "10/10 - Otomatik başlatma"
if ask_yes_no "Boomusic, bilgisayar açılışında otomatik olarak başlasın mı?"; then
    mkdir -p "$AUTOSTART_DIR"
    cat > "$AUTOSTART_DIR/boomusic.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Boomusic
Comment=Boomusic - The Music Player (tepsi simgesinden çalışır)
Exec=$LAUNCHER
Icon=$ICON_INSTALLED_PATH
Terminal=false
Categories=AudioVideo;Audio;Player;
StartupWMClass=boomusic
X-GNOME-Autostart-enabled=true
EOF
    ok "Otomatik başlatma etkinleştirildi: $AUTOSTART_DIR/boomusic.desktop"
    info "  Bu, GNOME/KDE/XFCE/LXQt/MATE gibi masaüstü ortamlarında otomatik işler."

    if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" || -f "$HOME/.config/hypr/hyprland.conf" ]]; then
        printf "\n"
        warn "Hyprland kullanıyor gibisiniz."
        info "  Hyprland, XDG 'autostart' klasörünü kendiliğinden işlemez (bir 'dex'"
        info "  gibi bir araç yoksa). Garantiye almak için ~/.config/hypr/hyprland.conf"
        info "  dosyanıza şu satırı da eklemeni öneririm:"
        printf "\n      ${BOLD}exec-once = %s${RESET}\n\n" "$LAUNCHER"
        info "  (Noctalia kullanıyorsan tepsi simgesinin görünmesi için bar ayarlarında"
        info "  'Tray' bileşeninin eklendiğinden de emin ol.)"
    fi
else
    info "Otomatik başlatma atlandı. İstediğin zaman şu komutla başlatabilirsin: boomusic"
fi

# ---------------------------------------------------------------------------
printf "\n${BOLD}${GREEN}Kurulum tamamlandı!${RESET}\n\n"
info "  Müzik klasörü : $DEFAULT_MUSIC_DIR"
info "  Ayarlar       : ~/.config/boomusic/config.json"
info "  İstatistikler : ~/.local/share/boomusic/stats.json"
info "  Günlük (log)  : ~/.local/share/boomusic/boomusic.log"
info "  Değişiklikler : ~/.local/share/boomusic/CHANGELOG.md"
info ""
info "Açtığında bir masaüstü penceresi ve bir tepsi simgesi birlikte açılır."
info "Pencereyi kapatırsan (X) uygulama KAPANMAZ, sadece gizlenir; tepsi"
info "simgesinden 'Pencereyi Göster'e tıklayarak geri getirebilirsin."
info ""
info "Açmak için üç yolun var:"
info "  1. Terminale 'boomusic' yaz"
info "  2. Uygulama menünden 'Boomusic' ara"
info "  3. (işaretlediysen) Masaüstündeki simgeye çift tıkla"
info ""
info "Sorun yaşarsan README.md dosyasındaki 'Sorun Giderme' bölümüne bak."

if ask_yes_no $'\nBoomusic\'i şimdi başlatmak ister misin?'; then
    setsid "$LAUNCHER" >/dev/null 2>&1 &
    disown
    sleep 1
    ok "Boomusic başlatıldı, tepsi simgesini kontrol et."
fi
