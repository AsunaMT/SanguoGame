"""开局流程接口"""
from __future__ import annotations
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from game.state import GameState, Resources
from game.ministers import MINISTER_CANDIDATES, build_minister, CANDIDATE_MAP
from game.buffs import STARTER_BUFFS, apply_buffs
from game.map_data import build_initial_territories, build_initial_diplomacy
from game.save_load import save_game
from api.state_manager import set_state

router = APIRouter(prefix="/api/setup", tags=["setup"])


# ─── 请求/响应模型 ───────────────────────────────────────────
class CreateGameRequest(BaseModel):
    ruler_name: str
    buff_ids: List[str]         # 选择的起始buff（建议选2个）
    minister_ids: List[str]     # 选择的大臣ID（每个role选1个，共3个）


class CreateGameResponse(BaseModel):
    success: bool
    message: str
    state_summary: dict


# ─── 路由 ────────────────────────────────────────────────────
@router.get("/candidates")
async def get_candidates():
    """返回6位候选大臣信息"""
    return {"candidates": MINISTER_CANDIDATES}


@router.get("/buffs")
async def get_buffs():
    """返回所有可选起始buff"""
    return {"buffs": STARTER_BUFFS}


@router.post("/create", response_model=CreateGameResponse)
async def create_game(req: CreateGameRequest):
    # 验证大臣选择（每个role必须有且仅有一个）
    roles_selected = {}
    for mid in req.minister_ids:
        if mid not in CANDIDATE_MAP:
            raise HTTPException(400, f"未知大臣ID: {mid}")
        role = CANDIDATE_MAP[mid]["role"]
        if role in roles_selected:
            raise HTTPException(400, f"每个职位只能选一位大臣，{role}已重复")
        roles_selected[role] = mid

    required_roles = {"internal", "military", "diplomacy"}
    missing = required_roles - set(roles_selected.keys())
    if missing:
        raise HTTPException(400, f"缺少职位大臣：{missing}")

    # 应用buff到初始资源
    base_resources = {
        "gold": 1000, "food": 5000,
        "troops": 10000, "population": 50000, "prestige": 30,
    }
    boosted = apply_buffs(base_resources, req.buff_ids)

    # 构建初始游戏状态
    state = GameState(
        ruler_name=req.ruler_name,
        buffs=req.buff_ids,
        resources=Resources(**boosted),
        territories=build_initial_territories(),
        diplomacy=build_initial_diplomacy(),
        ministers={
            role: build_minister(mid)
            for role, mid in roles_selected.items()
        },
    )

    # 注册到内存 & 存档
    set_state(state)
    save_game(state)

    # 返回摘要
    summary = {
        "ruler_name": state.ruler_name,
        "buffs": req.buff_ids,
        "ministers": {role: state.ministers[role].name for role in state.ministers},
        "resources": state.resources.model_dump(),
        "territories_count": len([t for t in state.territories if t.owner == "player"]),
    }
    return CreateGameResponse(
        success=True,
        message=f"游戏已创建，{req.ruler_name}的传奇从公元208年秋开始！",
        state_summary=summary,
    )
