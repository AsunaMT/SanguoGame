"""朝堂接口 v2.0 — 7步朝堂流程 + 群聊 + 私聊 + 影响结算"""
from __future__ import annotations
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.state_manager import get_state, set_state
from ai.minister_agent import (
    MinisterAgent, calculate_speech_impact, check_betrayal_conditions
)
from ai.world_narrator import parse_orders, narrate_week
from game.court import (
    next_phase, can_group_chat, can_private_chat, can_decree,
    can_skip_to_decision, PHASE_DISPLAY, get_random_scene_event,
    normalize_phase
)
from game.world import process_week
from game.save_load import save_game

router = APIRouter(prefix="/api/court", tags=["court"])

# 限流间隔
_REQUEST_INTERVAL = 6.0


# ─── 请求/响应模型 ──────────────────────────────────────────
class GroupChatRequest(BaseModel):
    message: str

class PrivateChatRequest(BaseModel):
    minister_id: str
    message: str

class DecreeRequest(BaseModel):
    decree_text: str


# ─── 1. 开朝 ────────────────────────────────────────────────
@router.post("/start")
async def start_court():
    """开朝：旁白描述 + 随机场景事件"""
    state = get_state()
    phase = normalize_phase(state.court_phase)

    if phase != "idle":
        raise HTTPException(400, f"当前阶段 {state.court_phase} 无法开始上朝")

    state.court_phase = "opening"
    state.current_impacts = []
    state.week_orders = []

    # 生成随机场景事件
    scene_event = get_random_scene_event(state.ministers, state.diplomacy)
    if scene_event:
        from game.state import SceneEvent
        state.current_scene_event = SceneEvent(
            id=scene_event["id"],
            description=scene_event["description"],
            hint=scene_event["hint"],
            affected_ministers=[scene_event.get("affected_minister", "")],
        )

    set_state(state)
    save_game(state)

    result = {
        "phase": "opening",
        "turn": state.turn,
        "max_turns": state.max_turns,
        "date": state.date,
        "conquest_progress": state.conquest.progress_percent,
        "scene_event": None,
    }

    if state.current_scene_event:
        result["scene_event"] = {
            "description": state.current_scene_event.description,
            "hint": state.current_scene_event.hint,
        }

    return result


# ─── 2. 情报汇报 ─────────────────────────────────────────────
@router.post("/intel")
async def intel_phase():
    """情报阶段：所有大臣依次汇报本领域情况"""
    state = get_state()
    phase = normalize_phase(state.court_phase)

    if phase != "opening":
        # 允许从 opening 直接进入 intel
        if phase == "idle":
            state.court_phase = "opening"
        state.court_phase = "intel"

    state.court_phase = "intel"
    set_state(state)

    # 按角色顺序汇报
    minister_order = sorted(state.ministers.keys())
    reports = []

    for i, mid in enumerate(minister_order):
        if i > 0:
            await asyncio.sleep(_REQUEST_INTERVAL)
        agent = MinisterAgent(state.ministers[mid], state)
        reply = await agent.report_intel()
        reports.append({
            "minister_id": mid,
            "minister_name": state.ministers[mid].name,
            "role": state.ministers[mid].role,
            "content": reply,
        })

    save_game(state)

    return {
        "phase": "intel",
        "reports": reports,
    }


# ─── 3. 群议 ─────────────────────────────────────────────────
@router.post("/group_chat")
async def group_chat(req: GroupChatRequest):
    """群议：玩家说一句话，所有大臣依次回应"""
    state = get_state()
    phase = normalize_phase(state.court_phase)

    # 允许从intel或group_discuss进入
    if phase in ("intel", "group_discuss"):
        state.court_phase = "group_discuss"
    elif phase != "group_discuss":
        raise HTTPException(400, f"当前阶段 {state.court_phase} 不支持群聊")

    set_state(state)

    # 场景事件描述
    scene_desc = ""
    if state.current_scene_event:
        scene_desc = state.current_scene_event.description

    # 按顺序让每个大臣回应
    minister_order = sorted(state.ministers.keys())
    responses = []
    response_map = {}

    for i, mid in enumerate(minister_order):
        if i > 0:
            await asyncio.sleep(_REQUEST_INTERVAL)

        agent = MinisterAgent(state.ministers[mid], state)

        # 传入之前大臣的回应作为上下文
        other_responses = [
            {"name": r["minister_name"], "content": r["content"]}
            for r in responses
        ]

        reply = await agent.respond_group(
            player_message=req.message,
            other_responses=other_responses,
            scene_event=scene_desc,
        )

        responses.append({
            "minister_id": mid,
            "minister_name": state.ministers[mid].name,
            "role": state.ministers[mid].role,
            "content": reply,
        })
        response_map[mid] = reply

    # 计算影响
    impacts = calculate_speech_impact(state, req.message, response_map)
    state.current_impacts.extend(impacts)

    save_game(state)

    return {
        "phase": "group_discuss",
        "responses": responses,
        "impacts": [imp.model_dump() for imp in impacts],
    }


# ─── 4. 密谈 ─────────────────────────────────────────────────
@router.post("/private_chat")
async def private_chat(req: PrivateChatRequest):
    """密谈：1对1私聊某位大臣"""
    state = get_state()
    phase = normalize_phase(state.court_phase)

    # 允许从 group_discuss 或 private_meet 进入
    if phase in ("group_discuss", "private_meet"):
        state.court_phase = "private_meet"
    elif phase != "private_meet":
        raise HTTPException(400, f"当前阶段 {state.court_phase} 不支持私聊")

    if req.minister_id not in state.ministers:
        raise HTTPException(400, f"大臣 {req.minister_id} 不存在")

    set_state(state)

    agent = MinisterAgent(state.ministers[req.minister_id], state)
    reply = await agent.respond_private(req.message)

    save_game(state)

    return {
        "phase": "private_meet",
        "minister_id": req.minister_id,
        "minister_name": state.ministers[req.minister_id].name,
        "content": reply,
    }


# ─── 5. 决策（下旨）──────────────────────────────────────────
@router.post("/decree")
async def issue_decree(req: DecreeRequest):
    """决策阶段：玩家下旨，大臣依次确认"""
    state = get_state()
    phase = normalize_phase(state.court_phase)

    # 允许从群议或密谋跳到决策
    if phase in ("group_discuss", "private_meet", "decision"):
        state.court_phase = "decision"
    elif phase != "decision":
        raise HTTPException(400, f"当前阶段 {state.court_phase} 不支持下旨")

    state.week_orders.append(req.decree_text)
    set_state(state)

    # 大臣确认
    minister_order = sorted(state.ministers.keys())
    confirmations = []

    for i, mid in enumerate(minister_order):
        if i > 0:
            await asyncio.sleep(_REQUEST_INTERVAL)
        agent = MinisterAgent(state.ministers[mid], state)
        reply = await agent.confirm_decree(req.decree_text)
        confirmations.append({
            "minister_id": mid,
            "minister_name": state.ministers[mid].name,
            "role": state.ministers[mid].role,
            "content": reply,
        })

    save_game(state)

    return {
        "phase": "decision",
        "confirmations": confirmations,
    }


# ─── 6. 影响结算 ─────────────────────────────────────────────
@router.post("/impact")
async def impact_settlement():
    """影响结算：展示每个大臣本轮的状态变化"""
    state = get_state()
    state.court_phase = "impact"
    set_state(state)

    # 为每个大臣生成内心独白
    impacts_with_comments = []
    minister_order = sorted(state.ministers.keys())

    for i, mid in enumerate(minister_order):
        if i > 0:
            await asyncio.sleep(max(2, _REQUEST_INTERVAL / 2))

        # 汇总本轮所有影响
        mid_impacts = [imp for imp in state.current_impacts if imp.minister_id == mid]
        total_loyalty = sum(imp.loyalty_delta for imp in mid_impacts)
        total_satisfaction = sum(imp.satisfaction_delta for imp in mid_impacts)
        total_fear = sum(imp.fear_delta for imp in mid_impacts)
        total_ambition = sum(imp.ambition_delta for imp in mid_impacts)

        # 生成AI独白
        agent = MinisterAgent(state.ministers[mid], state)
        comment = await agent.generate_impact_comment()

        impacts_with_comments.append({
            "minister_id": mid,
            "minister_name": state.ministers[mid].name,
            "loyalty_delta": total_loyalty,
            "satisfaction_delta": total_satisfaction,
            "fear_delta": total_fear,
            "ambition_delta": total_ambition,
            "comment": comment,
            "current_loyalty": state.ministers[mid].emotion.loyalty,
            "current_satisfaction": state.ministers[mid].emotion.satisfaction,
        })

    # 检查背叛条件
    betrayal = check_betrayal_conditions(state)

    # 检查暗流事件（大臣之间的互动）
    undercurrent = _generate_undercurrent(state)

    save_game(state)

    return {
        "phase": "impact",
        "impacts": impacts_with_comments,
        "betrayal_warning": betrayal,
        "undercurrent": undercurrent,
    }


def _generate_undercurrent(state) -> Optional[str]:
    """生成暗流涌动事件"""
    import random

    ministers = list(state.ministers.values())
    if len(ministers) < 2:
        return None

    # 40%概率触发暗流事件
    if random.random() > 0.4:
        return None

    templates = [
        "{a}散朝后私下找了{b}密谈...",
        "有人看到{a}深夜出府，去向不明...",
        "{a}最近和{b}走得很近，不知在谋划什么...",
        "据说{a}收到了一封来历不明的信...",
        "{a}的府中最近多了不少陌生人出入...",
    ]

    a = random.choice(ministers)
    b = random.choice([m for m in ministers if m.id != a.id])
    template = random.choice(templates)

    return template.format(a=a.name, b=b.name)


# ─── 7. 退朝 → 世界结算 ──────────────────────────────────────
@router.post("/end")
async def end_court():
    """退朝 → 命令解析 → 世界结算 → 周报 → 胜负判定"""
    state = get_state()
    state.court_phase = "world_update"

    # 命令解析
    all_orders_text = "；".join(state.week_orders)
    structured = await parse_orders(all_orders_text) if all_orders_text else []

    # 世界结算
    week_result, order_results = process_week(state, structured)

    # AI 旁白
    await asyncio.sleep(_REQUEST_INTERVAL)
    narrated = await narrate_week(state, week_result.report)
    week_result.report = narrated

    # 保存周报
    state.week_reports[str(week_result.turn)] = narrated

    # 更新称霸进度
    state.conquest.update(state.territories)

    # 胜负判定
    ending = _check_game_ending(state)

    state.court_phase = "idle"
    state.current_impacts = []
    state.current_scene_event = None
    set_state(state)
    save_game(state)

    result = {
        "turn_completed": week_result.turn,
        "new_turn": state.turn,
        "max_turns": state.max_turns,
        "new_date": state.date,
        "report": narrated,
        "events": week_result.events,
        "resource_delta": week_result.resource_delta,
        "resources": state.resources.model_dump(),
        "conquest_progress": state.conquest.progress_percent,
        "game_over": state.game_over,
        "ending": None,
    }

    if ending:
        result["game_over"] = True
        result["ending"] = ending

    return result


def _check_game_ending(state) -> Optional[dict]:
    """检查游戏是否结束"""
    from game.state import GameEnding

    # 胜利：称霸进度 100%
    if state.conquest.progress_percent >= 100:
        state.game_over = True
        state.ending = GameEnding(
            type="victory",
            description="天下归一！四海臣服！你成功统一了天下，开创了千秋基业！",
            turn=state.turn,
        )
        return state.ending.model_dump()

    # 寿命将尽：超过20轮
    if state.turn > state.max_turns:
        state.game_over = True
        state.ending = GameEnding(
            type="death_age",
            description=f"第{state.turn}轮，你已年迈体衰，含恨未能统一天下。但你的传奇将被后人铭记。",
            turn=state.turn,
        )
        return state.ending.model_dump()

    # 背叛检查
    betrayal = check_betrayal_conditions(state)
    if betrayal:
        if betrayal == "mass_betrayal":
            state.game_over = True
            state.ending = GameEnding(
                type="betrayal",
                description="众叛亲离！所有大臣联合起来发动了政变，你被废黜了。",
                turn=state.turn,
            )
            return state.ending.model_dump()

        if betrayal.startswith("betrayal_"):
            mid = betrayal.replace("betrayal_", "")
            name = state.ministers.get(mid, None)
            if name:
                state.game_over = True
                state.ending = GameEnding(
                    type="betrayal",
                    description=f"{name.name}发动兵变！趁夜率军包围了王宫，你被迫退位。",
                    turn=state.turn,
                )
                return state.ending.model_dump()

    # 兵力归零：被俘虏
    if state.resources.troops <= 0:
        state.is_captured = True
        state.capture_turn = state.turn
        # 不直接结束，进入俘虏流程
        return {
            "type": "captured",
            "description": "兵力耗尽，你被敌军俘虏！但这不一定是终点...",
            "turn": state.turn,
        }

    return None


# ─── 辅助端点 ────────────────────────────────────────────────
@router.post("/advance_phase")
async def advance_phase():
    """手动推进阶段（兼容旧前端）"""
    state = get_state()
    old_phase = normalize_phase(state.court_phase)
    state.court_phase = next_phase(old_phase)
    set_state(state)
    save_game(state)
    return {"old_phase": old_phase, "new_phase": state.court_phase}


@router.get("/ministers_status")
async def get_ministers_status():
    """获取所有大臣的当前情绪状态（玩家可见部分）"""
    state = get_state()
    result = {}
    for mid, m in state.ministers.items():
        result[mid] = {
            "name": m.name,
            "role": m.role,
            "position": m.position,
            "surface_trait": m.personality.surface_trait,
            "loyalty": m.emotion.loyalty,
            "satisfaction": m.emotion.satisfaction,
            "status": m.status,
        }
    return {"ministers": result}
