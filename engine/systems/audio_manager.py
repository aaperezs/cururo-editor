import json
import os
import pygame
from engine.project_paths import data_dir, assets_dir
from engine.systems.user_prefs import load as _load_prefs

_RUTA = data_dir("audio.json")


class AudioManager:
    def __init__(self):
        self._config = self._load_config()
        _prefs = _load_prefs()
        self._bgm_volume = float(_prefs.get("bgm_volume", 0.7))
        self._sfx_volume = float(_prefs.get("sfx_volume", 1.0))
        self._current_bgm = None
        self._sounds = {}

    def _load_config(self):
        if not os.path.exists(_RUTA):
            return {}
        try:
            with open(_RUTA, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _resolve_path(self, asset_id):
        adir = assets_dir()
        for ext in (".ogg", ".wav", ".mp3"):
            path = os.path.join(adir, f"{asset_id}{ext}")
            if os.path.exists(path):
                return path
        return None

    def play_bgm(self, asset_id, fade_ms=0):
        entry = self._config.get(asset_id)
        vol = entry.get("volumen", self._bgm_volume) if entry else self._bgm_volume
        path = self._resolve_path(asset_id)
        if not path:
            return
        try:
            if fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1 if (entry and entry.get("loop", True)) else 0,
                                        fade_ms=fade_ms)
            else:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1 if (entry and entry.get("loop", True)) else 0)
            self._current_bgm = asset_id
        except pygame.error:
            pass

    def stop_bgm(self, fade_ms=0):
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        self._current_bgm = None

    def play_sfx(self, asset_id):
        path = self._resolve_path(asset_id)
        if not path:
            return
        try:
            if asset_id not in self._sounds:
                self._sounds[asset_id] = pygame.mixer.Sound(path)
            entry = self._config.get(asset_id)
            vol = entry.get("volumen", self._sfx_volume) if entry else self._sfx_volume
            self._sounds[asset_id].set_volume(vol)
            self._sounds[asset_id].play()
        except pygame.error:
            pass

    def set_bgm_volume(self, vol):
        self._bgm_volume = max(0.0, min(1.0, vol))
        pygame.mixer.music.set_volume(self._bgm_volume)

    def set_sfx_volume(self, vol):
        self._sfx_volume = max(0.0, min(1.0, vol))

    def get_bgm_volume(self):
        return self._bgm_volume

    def get_sfx_volume(self):
        return self._sfx_volume

    def get_current_bgm(self):
        return self._current_bgm

