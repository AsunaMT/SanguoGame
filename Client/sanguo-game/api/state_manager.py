"""全局游戏状态管理（单例）"""
from __future__ import annotations
from typing import Optional
from game.state import GameState
from game.save_load import load_game
from fastapi import HTTPException

_current_state: Optional[GameState] = None


def get_state() -> GameState:
    global _current_state
    if _current_state is None:
        _current_state = load_game()
    if _current_state is None:
        raise HTTPException(400, "游戏尚未创建，请先调用 /api/setup/create")
    return _current_state


def set_state(state: GameState) -> None:
    global _current_state
    _current_state = state
