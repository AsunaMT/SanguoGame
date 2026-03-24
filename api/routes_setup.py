"""开局流程接口 v2.0"""
from __future__ import annotations
from typing import List
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from game.state import GameState, Resources, ConquestProgress
from game.ministers import MINISTER_CANDIDATES, build_minister, CANDIDATE_MAP
from game.map_data import build_initial_territories, build_initial_diplomacy
from game.save_load import (
    save_game, load_game, list_saves, delete_save,
    save_game_with_slot, load_game_from_slot
)
from api.state_manager import set_state, get_state, reset_state

router = APIRouter(prefix="/api/setup", tags=["setup"])


# ─── 请求/响应模型 ──────────────────────────────────────────
class CreateGameRequest(BaseModel):
    ruler_name: str
    minister_ids: List[str]


class CreateGameResponse(BaseModel):
    success: bool
    message: str
    state_summary: dict


# ─── 路由 ─────────────────────────────────────────────────────
@router.get("/candidates")
async def get_candidates():
    """返回6位候选大臣信息（含表面性格，不含隐藏特质）"""
    # 过滤掉隐藏特质信息
    safe_candidates = []
    for c in MINISTER_CANDIDATES:
        safe_c = {k: v for k, v in c.items() if k not in ("hidden", "emotion")}
        safe_candidates.append(safe_c)
    return {"candidates": safe_candidates}


@router.post("/reset")
async def reset_game():
    """重置游戏状态"""
    from game.save_load import DEFAULT_SAVE_FILE

    reset_state()

    if os.path.exists(DEFAULT_SAVE_FILE):
        os.remove(DEFAULT_SAVE_FILE)

    return {"success": True, "message": "游戏已重置"}


@router.post("/create", response_model=CreateGameResponse)
async def create_game(req: CreateGameRequest):
    # 验证大臣选择
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

    # 基础资源（不再应用 Buff）
    base_resources = {
        "gold": 1000, "food": 5000,
        "troops": 10000, "population": 50000, "prestige": 30,
    }

    # 构建大臣（使用 minister.id 作为 key，而非 role）
    ministers = {}
    for role, mid in roles_selected.items():
        minister = build_minister(mid)
        ministers[minister.id] = minister

    # 构建领土
    territories = build_initial_territories()

    # 构建初始游戏状态
    state = GameState(
        ruler_name=req.ruler_name,
        resources=Resources(**base_resources),
        territories=territories,
        diplomacy=build_initial_diplomacy(),
        ministers=ministers,
        max_turns=20,
        conquest=ConquestProgress(
            total_provinces=len(territories),
            owned_provinces=sum(1 for t in territories if t.owner == "player"),
        ),
    )
    state.conquest.update(territories)

    set_state(state)
    save_game(state)

    summary = {
        "ruler_name": state.ruler_name,
        "ministers": {m.role: m.name for m in state.ministers.values()},
        "resources": state.resources.model_dump(),
        "territories_count": state.conquest.owned_provinces,
        "total_territories": state.conquest.total_provinces,
        "conquest_progress": state.conquest.progress_percent,
    }

    return CreateGameResponse(
        success=True,
        message=f"游戏已创建！{req.ruler_name}的传奇从公元208年秋开始！20轮内统一天下，否则寿命将尽！",
        state_summary=summary,
    )


# ─── 存档管理 ─────────────────────────────────────────────────
@router.get("/saves")
async def get_save_list():
    saves = list_saves()
    return {"saves": saves}


@router.post("/saves")
async def create_save_slot(slot_name: str = "auto"):
    try:
        state = get_state()
        save_game_with_slot(state, slot_name)
        return {"success": True, "message": f"存档已保存到槽位: {slot_name}"}
    except Exception as e:
        raise HTTPException(500, f"保存失败: {str(e)}")


@router.delete("/saves/{filename}")
async def delete_save_api(filename: str):
    try:
        if not filename.endswith(".json"):
            raise HTTPException(400, "只能删除 .json 格式的存档文件")
        success = delete_save(os.path.join("saves", filename))
        if success:
            return {"success": True, "message": f"存档 {filename} 已删除"}
        else:
            raise HTTPException(404, f"存档 {filename} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"删除失败: {str(e)}")


@router.post("/saves/{filename}")
async def load_save_api(filename: str):
    try:
        if not filename.endswith(".json"):
            raise HTTPException(400, "只能加载 .json 格式的存档文件")
        state = load_game(os.path.join("saves", filename))
        if state is None:
            raise HTTPException(404, f"存档 {filename} 不存在或损坏")
        set_state(state)
        return state.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"加载失败: {str(e)}")
