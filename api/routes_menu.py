"""游戏主界面和设置接口"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/menu", tags=["menu"])


class SettingsModel(BaseModel):
    """游戏设置"""
    text_speed: int = 1  # 文字显示速度
    auto_save: bool = True  # 自动保存
    sound_enabled: bool = True  # 音效开关
    language: str = "zh"  # 语言设置


# 全局设置存储
_game_settings = SettingsModel()


@router.get("/settings")
async def get_settings():
    """获取当前游戏设置"""
    return _game_settings.model_dump()


@router.post("/settings")
async def update_settings(settings: SettingsModel):
    """更新游戏设置"""
    global _game_settings
    _game_settings = settings
    return {"success": True, "message": "设置已更新", "settings": _game_settings.model_dump()}


@router.post("/exit")
async def exit_game():
    """退出游戏（返回主菜单）"""
    # 这里只是返回提示，真正的退出由前端处理
    return {"success": True, "message": "已返回主菜单"}


@router.get("/status")
async def get_game_status():
    """获取游戏状态信息"""
    from game.save_load import list_saves
    from api.state_manager import get_state
    
    saves = list_saves()
    try:
        state = get_state()
        has_active_game = True
        ruler_name = state.ruler_name
        turn = state.turn
        phase = state.court_phase
    except:
        has_active_game = False
        ruler_name = None
        turn = 0
        phase = None
    
    return {
        "has_active_game": has_active_game,
        "ruler_name": ruler_name,
        "turn": turn,
        "phase": phase,
        "save_count": len(saves),
        "latest_save": saves[0] if saves else None
    }
