"""朝会接口"""
from __future__ import annotations
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.state_manager import get_state, set_state
from ai.minister_agent import MinisterAgent
from ai.world_narrator import parse_orders, narrate_week
from game.court import next_phase, can_chat, can_decree
from game.world import process_week
from game.save_load import save_game

router = APIRouter(prefix="/api/court", tags=["court"])

# 免费tier限流：每次请求间隔（秒）
_REQUEST_INTERVAL = 6.0


class ChatRequest(BaseModel):
    minister_id: str
    message: str
    mentioned_minister: Optional[str] = None


class DecreeRequest(BaseModel):
    decree_text: str


class CourtResponse(BaseModel):
    phase: str
    messages: List[dict]


def _get_agent(minister_id: str) -> MinisterAgent:
    state = get_state()
    if minister_id not in state.ministers:
        raise HTTPException(400, f"大臣 {minister_id} 不在朝中")
    return MinisterAgent(state.ministers[minister_id], state)


@router.post("/start", response_model=CourtResponse)
async def start_court():
    """开始上朝：三位大臣依次（串行）禀报，避免触发免费限额"""
    state = get_state()
    if state.court_phase not in ("idle",):
        raise HTTPException(400, f"当前阶段 {state.court_phase} 无法开始上朝")

    state.court_phase = "bingzou"
    set_state(state)

    ministers_order = ["internal", "military", "diplomacy"]
    available = [mid for mid in ministers_order if mid in state.ministers]

    results = []
    for i, mid in enumerate(available):
        if i > 0:
            await asyncio.sleep(_REQUEST_INTERVAL)  # 限流间隔
        agent = MinisterAgent(state.ministers[mid], state)
        reply = await agent.bingzou()
        results.append({"minister": state.ministers[mid].name, "role": mid, "content": reply})

    save_game(state)
    return CourtResponse(phase="bingzou", messages=results)


@router.post("/advance_phase")
async def advance_phase():
    state = get_state()
    old_phase = state.court_phase
    state.court_phase = next_phase(old_phase)
    set_state(state)
    save_game(state)
    return {"old_phase": old_phase, "new_phase": state.court_phase}


@router.post("/chat", response_model=CourtResponse)
async def chat(req: ChatRequest):
    """议事阶段：与某位大臣对话"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        state = get_state()
        if not can_chat(state.court_phase):
            raise HTTPException(400, f"当前阶段 {state.court_phase} 不是议事阶段")

        agent = _get_agent(req.minister_id)

        context_message = req.message
        if req.mentioned_minister and req.mentioned_minister in state.ministers:
            other = state.ministers[req.mentioned_minister]
            if other.conversation_history:
                last_reply = other.conversation_history[-1]["assistant"]
                context_message = (
                    f"（{other.name}刚才说：{last_reply}）\n"
                    f"主公问：{req.message}"
                )

        logger.info(f"开始调用AI模型: {req.minister_id}, 消息: {context_message[:50]}...")
        reply = await agent.respond(context_message, phase="yishi")
        logger.info(f"AI响应成功，长度: {len(reply)}")
        save_game(state)

        minister_name = state.ministers[req.minister_id].name
        return CourtResponse(
            phase="yishi",
            messages=[{"minister": minister_name, "role": req.minister_id, "content": reply}],
        )
    except Exception as e:
        logger.error(f"聊天接口错误: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(500, f"AI调用失败: {str(e)}")


@router.post("/decree", response_model=CourtResponse)
async def issue_decree(req: DecreeRequest):
    """拟旨：三位大臣串行确认"""
    state = get_state()
    if not can_decree(state.court_phase):
        raise HTTPException(400, f"当前阶段 {state.court_phase} 不是拟旨阶段")

    state.week_orders.append(req.decree_text)

    ministers_order = ["internal", "military", "diplomacy"]
    available = [mid for mid in ministers_order if mid in state.ministers]

    results = []
    for i, mid in enumerate(available):
        if i > 0:
            await asyncio.sleep(_REQUEST_INTERVAL)
        agent = MinisterAgent(state.ministers[mid], state)
        reply = await agent.confirm_decree(req.decree_text)
        results.append({"minister": state.ministers[mid].name, "role": mid, "content": reply})

    save_game(state)
    return CourtResponse(phase="nizhi", messages=results)


@router.post("/end")
async def end_court():
    """退朝 → 世界结算 → 周报"""
    state = get_state()
    state.court_phase = "tui_chao"

    all_orders_text = "；".join(state.week_orders)
    structured = await parse_orders(all_orders_text) if all_orders_text else []

    week_result, order_results = process_week(state, structured)

    await asyncio.sleep(_REQUEST_INTERVAL)
    narrated = await narrate_week(state, week_result.report)
    week_result.report = narrated

    state.week_reports[str(week_result.turn)] = narrated
    state.court_phase = "idle"
    set_state(state)
    save_game(state)

    return {
        "turn_completed": week_result.turn,
        "new_date": state.date,
        "report": narrated,
        "events": week_result.events,
        "resource_delta": week_result.resource_delta,
        "resources": state.resources.model_dump(),
    }
