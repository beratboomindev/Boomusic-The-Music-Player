#!/usr/bin/env bash
# Boomusic - The Music Player | Kaldırma betiği
#
# Kullanım:
#   bash uninstall.sh
#
# Varsayılan olarak SADECE program dosyalarını (venv, kopyalanan kaynak
# kod, başlatıcı komut, otomatik başlatma girişi) kaldırır. Müzik
# dosyalarına ASLA dokunmaz. Ayarlar/istatistikler için ayrıca ve açıkça
# sorar; onlar da varsayılan olarak SİLİNMEZ.
set -uo pipefail

INSTALL_DIR="$HOME/.local/share/boomusic/install"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/boomusic"
AUTOSTART_FILE="$HOME/.config/autostart/boomusic.desktop"
APPLICATIONS_FILE="$HOME/.local/share/applications/boomusic.desktop"
CONFIG_DIR="$HOME/.config/boomusic"
DATA_DIR="$HOME/.local/share/boomusic"

# config.py'deki _localized_documents_dir() ile aynı mantık: kullanıcının
# yerelleştirilmiş Belgeler klasörünü bulmaya çalışır (Türkçe'de "Belgeler"
# olabilir), böylece doğru müzik klasörü yolunu gösterebiliriz.
documents_dir() {
    if command -v xdg-user-dir >/dev/null 2>&1; then
        local d
        d="$(xdg-user-dir DOCUMENTS 2>/dev/null)"
        [[ -n "$d" ]] && { echo "$d"; return; }
    fi
    echo "$HOME/Documents"
}
MUSIC_DIR="$(documents_dir)/BooPlaylist"

DESKTOP_ICON_FILE=""
if command -v xdg-user-dir >/dev/null 2>&1; then
    d="$(xdg-user-dir DESKTOP 2>/dev/null)"
    [[ -n "$d" && -f "$d/boomusic.desktop" ]] && DESKTOP_ICON_FILE="$d/boomusic.desktop"
elif [[ -f "$HOME/Desktop/boomusic.desktop" ]]; then
    DESKTOP_ICON_FILE="$HOME/Desktop/boomusic.desktop"
fi

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

ok()   { printf "  ${GREEN}✔${RESET} %s\n" "$1"; }
info() { printf "%s\n" "$1"; }

ask_yes_no() {
    local reply
    read -r -p "$1 [E/h]: " reply
    reply=${reply:-h}
    [[ "$reply" =~ ^[EeYy] ]]
}

printf "${BOLD}Boomusic kaldırılıyor...${RESET}\n\n"

rm -f "$LAUNCHER" && ok "Başlatıcı komut kaldırıldı: $LAUNCHER"
rm -f "$AUTOSTART_FILE" && ok "Otomatik başlatma girişi kaldırıldı: $AUTOSTART_FILE"
rm -f "$APPLICATIONS_FILE" && ok "Uygulama menüsü girişi kaldırıldı: $APPLICATIONS_FILE"
if [[ -n "$DESKTOP_ICON_FILE" ]]; then
    rm -f "$DESKTOP_ICON_FILE" && ok "Masaüstü simgesi kaldırıldı: $DESKTOP_ICON_FILE"
fi
rm -rf "$INSTALL_DIR" && ok "Program dosyaları (venv + uygulama kodu) kaldırıldı: $INSTALL_DIR"

info ""
info "Aşağıdakiler HENÜZ SİLİNMEDİ (varsayılan olarak korunur):"
info "  - Müzik klasörün:      $MUSIC_DIR"
info "  - Ayarların:           $CONFIG_DIR"
info "  - Dinleme istatistiğin: $DATA_DIR (stats.json, boomusic.log)"
info ""

if ask_yes_no "Ayarları ve dinleme istatistiklerini de silmek ister misin? (müzik dosyaların ETKİLENMEZ)"; then
    rm -rf "$CONFIG_DIR"
    rm -f "$DATA_DIR"/stats.json "$DATA_DIR"/boomusic.log* "$DATA_DIR"/boomusic.lock "$DATA_DIR"/CHANGELOG.md
    # DATA_DIR'in altında install/ zaten kaldırıldı; klasör boşsa temizle.
    rmdir "$DATA_DIR" 2>/dev/null || true
    ok "Ayarlar ve istatistikler silindi."
else
    info "Ayarlar ve istatistikler korundu (Boomusic'i yeniden kurarsan aynı yerden devam eder)."
fi

printf "\n"
if ask_yes_no "${YELLOW}DİKKAT:${RESET} $MUSIC_DIR klasöründeki MÜZİK DOSYALARINI da silmek ister misin?"; then
    if ask_yes_no "Bundan gerçekten emin misin? Bu geri alınamaz"; then
        rm -rf "$MUSIC_DIR"
        ok "Müzik klasörü silindi: $MUSIC_DIR"
    else
        info "İptal edildi, müzik klasörü korundu."
    fi
else
    info "Müzik klasörü korundu: $MUSIC_DIR"
fi

printf "\n${BOLD}${GREEN}Kaldırma tamamlandı.${RESET}\n"
info "Not: ~/.bashrc veya ~/.zshrc dosyana eklenmiş olabilecek PATH satırını"
info "istersen elle kaldırabilirsin (zararsızdır, başka bir şeyi bozmaz)."
