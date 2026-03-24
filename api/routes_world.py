"""世界状态查询接口 v2.0"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from api.state_manager import get_state
from game.map_data import FACTION_NAMES, TERRITORY_POSITIONS

router = APIRouter(prefix="/api/world", tags=["world"])


@router.get("/state")
async def get_world_state():
    """当前完整游戏状态摘要"""
    state = get_state()
    r = state.resources
    return {
        "turn": state.turn,
        "max_turns": state.max_turns,
        "date": state.date,
        "ruler_name": state.ruler_name,
        "court_phase": state.court_phase,
        "resources": r.model_dump(),
        "conquest": state.conquest.model_dump(),
        "ministers": {
            mid: {
                "name": m.name,
                "courtesy_name": m.courtesy_name,
                "role": m.role,
                "position": m.position,
                "surface_trait": m.personality.surface_trait,
                "loyalty": m.emotion.loyalty,
                "satisfaction": m.emotion.satisfaction,
                "special_ability": m.special_ability,
                "status": m.status,
                "stats": {
                    "wuli": m.stats.wuli,
                    "zhili": m.stats.zhili,
                    "tongshuai": m.stats.tongshuai,
                    "koucai": m.stats.koucai,
                },
            }
            for mid, m in state.ministers.items()
        },
        "diplomacy": {
            fid: rel.model_dump() for fid, rel in state.diplomacy.items()
        },
        "history_log": state.history_log,
        "game_over": state.game_over,
    }


@router.get("/map")
async def get_map():
    """领土地图数据"""
    state = get_state()
    territories = []
    for t in state.territories:
        td = t.model_dump()
        td["owner_name"] = FACTION_NAMES.get(t.owner, t.owner)
        pos = TERRITORY_POSITIONS.get(t.id)
        if pos:
            td["cx"] = pos["cx"]
            td["cy"] = pos["cy"]
            td["rx"] = pos["rx"]
            td["ry"] = pos["ry"]
        territories.append(td)
    return {"territories": territories}


@router.get("/progress")
async def get_progress():
    """称霸进度"""
    state = get_state()
    return {
        "turn": state.turn,
        "max_turns": state.max_turns,
        "conquest": state.conquest.model_dump(),
        "game_over": state.game_over,
        "ending": state.ending.model_dump() if state.ending else None,
    }


@router.get("/report/{turn}")
async def get_report(turn: int):
    state = get_state()
    report = state.week_reports.get(str(turn))
    if not report:
        raise HTTPException(404, f"第{turn}周周报不存在")
    return {"turn": turn, "report": report}


@router.get("/ministers")
async def get_ministers():
    """所有大臣详情（不含隐藏特质和对话历史）"""
    state = get_state()
    result = {}
    for mid, m in state.ministers.items():
        result[mid] = {
            "id": m.id,
            "name": m.name,
            "courtesy_name": m.courtesy_name,
            "role": m.role,
            "position": m.position,
            "personality": m.personality.model_dump(),
            "stats": m.stats.model_dump(),
            "emotion": {
                "loyalty": m.emotion.loyalty,
                "satisfaction": m.emotion.satisfaction,
                # 不暴露 fear 和 ambition 给前端
            },
            "background": m.background,
            "special_ability": m.special_ability,
            "action_log": m.action_log[-10:],
            "status": m.status,
        }
    return {"ministers": result}


@router.get("/minister/{minister_id}")
async def get_minister_detail(minister_id: str):
    """单个大臣的详情面板数据"""
    state = get_state()
    if minister_id not in state.ministers:
        raise HTTPException(404, f"大臣 {minister_id} 不存在")

    m = state.ministers[minister_id]
    return {
        "id": m.id,
        "name": m.name,
        "courtesy_name": m.courtesy_name,
        "role": m.role,
        "position": m.position,
        "personality": m.personality.model_dump(),
        "stats": m.stats.model_dump(),
        "emotion": {
            "loyalty": m.emotion.loyalty,
            "satisfaction": m.emotion.satisfaction,
        },
        "background": m.background,
        "special_ability": m.special_ability,
        "ability_effect": m.ability_effect,
        "action_log": m.action_log,
        "status": m.status,
    }
