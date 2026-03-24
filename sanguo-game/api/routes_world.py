"""世界状态查询接口"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from api.state_manager import get_state
from game.map_data import FACTION_NAMES

router = APIRouter(prefix="/api/world", tags=["world"])


@router.get("/state")
async def get_world_state():
    """当前完整游戏状态摘要"""
    state = get_state()
    r = state.resources
    return {
        "turn": state.turn,
        "date": state.date,
        "ruler_name": state.ruler_name,
        "court_phase": state.court_phase,
        "resources": r.model_dump(),
        "ministers": {
            role: {
                "name": m.name,
                "courtesy_name": m.courtesy_name,
                "role": m.role,
                "loyalty": m.loyalty,
                "special_ability": m.special_ability,
            }
            for role, m in state.ministers.items()
        },
        "diplomacy": {
            fid: rel.model_dump() for fid, rel in state.diplomacy.items()
        },
        "buffs": state.buffs,
        "history_log": state.history_log,
    }


@router.get("/map")
async def get_map():
    """领土地图数据"""
    state = get_state()
    territories = []
    for t in state.territories:
        territories.append({
            **t.model_dump(),
            "owner_name": FACTION_NAMES.get(t.owner, t.owner),
        })
    return {"territories": territories}


@router.get("/report/{turn}")
async def get_report(turn: int):
    """某周的周报"""
    state = get_state()
    report = state.week_reports.get(str(turn))
    if not report:
        raise HTTPException(404, f"第{turn}周周报不存在")
    return {"turn": turn, "report": report}


@router.get("/ministers")
async def get_ministers():
    """当前三位大臣详细信息"""
    state = get_state()
    return {
        role: m.model_dump(exclude={"conversation_history"})
        for role, m in state.ministers.items()
    }
