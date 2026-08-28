"""Boomusic yapılandırma (config) yönetimi.

Ayarlar, XDG standardına uygun şekilde kullanıcının
``~/.config/boomusic/config.json`` dosyasında saklanır. Dosya her
kaydedişte atomic olarak (önce .tmp'ye yazıp sonra yerine taşıyarak)
güncellenir; böylece uygulama kapanırken/çökerken yarım yazılmış bir
dosya kalıp ayarları bozmaz.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Optional


def default_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "boomusic"


def default_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "boomusic"


def _localized_documents_dir() -> Path:
    """Kullanıcının GERÇEK (yerelleştirilmiş) Belgeler/Documents klasörünü bulur.

    Türkçe bir sistemde bu genelde "Belgeler", İngilizce'de "Documents"
    olur; sabit "Documents" varsaymak yanlış klasör açabilir. Üç kademeli
    dener: (1) 'xdg-user-dir DOCUMENTS' komutu -- en güvenilir, resmi yol
    -- (2) ~/.config/user-dirs.dirs dosyasını elle okumak, (3) son çare
    olarak ~/Documents.
    """
    xdg_user_dir = shutil.which("xdg-user-dir")
    if xdg_user_dir:
        try:
            result = subprocess.run(
                [xdg_user_dir, "DOCUMENTS"],
                capture_output=True, text=True, timeout=3,
            )
            path_str = result.stdout.strip()
            if result.returncode == 0 and path_str:
                return Path(path_str)
        except Exception:
            pass

    user_dirs_file = Path.home() / ".config" / "user-dirs.dirs"
    if user_dirs_file.exists():
        try:
            for line in user_dirs_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("XDG_DOCUMENTS_DIR"):
                    value = line.split("=", 1)[1].strip().strip('"')
                    value = value.replace("$HOME", str(Path.home()))
                    if value:
                        return Path(value)
        except Exception:
            pass

    return Path.home() / "Documents"


def default_music_dir() -> Path:
    # Kullanıcının (yerelleştirilmiş) Belgeler klasörü altında "BooPlaylist".
    return _localized_documents_dir() / "BooPlaylist"


@dataclass
class Settings:
    music_folder: str
    volume: float = 0.1
    muted: bool = False
    volume_before_mute: float = 0.1
    notifications_enabled: bool = False
    shuffle_enabled: bool = True
    nowplaying_visible: bool = True
    youtube_mix_with_local: bool = True
    youtube_search_limit: int = 30
    font_family: str = "DM Sans"
    language: str = "en"
    sidebar_width: int = 220  # kullanıcının elle sürüklediği genişlik (px)

    @classmethod
    def defaults(cls) -> "Settings":
        return cls(music_folder=str(default_music_dir()))


class Config:
    """``config.json`` dosyasını okuyup yazan basit bir yönetici."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = Path(config_dir) if config_dir else default_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.settings = self._load()

    def _load(self) -> Settings:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        known_fields = {f.name for f in fields(Settings)}
        merged = asdict(Settings.defaults())

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    merged.update({k: v for k, v in data.items() if k in known_fields})
            except (json.JSONDecodeError, OSError):
                # Bozuk/okunamayan dosya varsayılanlarla değiştirilir.
                pass

        settings = Settings(**merged)
        # Müzik klasörünün var olduğundan emin ol (ilk çalıştırmada oluştur).
        try:
            Path(settings.music_folder).expanduser().mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self._save(settings)
        return settings

    def _save(self, settings: Optional[Settings] = None) -> None:
        settings = settings or self.settings
        self.config_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.config_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=2)
        tmp.replace(self.config_file)

    def save(self) -> None:
        self._save(self.settings)

    def update(self, **kwargs) -> None:
        """Bir veya daha fazla ayarı günceller ve diske kaydeder."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save()

    @property
    def music_folder_path(self) -> Path:
        return Path(self.settings.music_folder).expanduser()
