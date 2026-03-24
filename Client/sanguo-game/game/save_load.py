"""游戏存档管理"""
from __future__ import annotations
import json
import os
from pathlib import Path

from game.state import GameState
from config import SAVE_DIR, DEFAULT_SAVE_FILE

os.makedirs(SAVE_DIR, exist_ok=True)


def save_game(state: GameState, filepath: str = DEFAULT_SAVE_FILE) -> None:
    Path(filepath).write_text(state.model_dump_json(indent=2), encoding="utf-8")


def load_game(filepath: str = DEFAULT_SAVE_FILE) -> GameState | None:
    p = Path(filepath)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return GameState(**data)
