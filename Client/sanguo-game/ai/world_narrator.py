"""旁白 / 世界动态 AI 生成 & 命令解析（Gemini 版）"""
from __future__ import annotations
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

from game.state import GameState
from config import GEMINI_API_KEY, NARRATOR_MODEL, PARSER_MODEL

genai.configure(api_key=GEMINI_API_KEY)

_PROMPT_DIR = Path(__file__).parent / "prompts"
_narrator_template = (_PROMPT_DIR / "narrator.txt").read_text(encoding="utf-8")


def _extract_retry_delay(exc: ResourceExhausted) -> float:
    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", str(exc))
    return float(m.group(1)) + 2 if m else 30.0


async def _call_with_retry(coro_fn, max_retries: int = 2):
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except ResourceExhausted as e:
            if attempt == max_retries:
                raise
            await asyncio.sleep(_extract_retry_delay(e))


# ── 旁白生成 ─────────────────────────────────────────────────
async def narrate_week(state: GameState, raw_events: str) -> str:
    r = state.resources
    prompt = _narrator_template.format(
        date=state.date, turn=state.turn, ruler_name=state.ruler_name,
        troops=r.troops, gold=r.gold, food=r.food, prestige=r.prestige,
        raw_events=raw_events,
    )
    model = genai.GenerativeModel(model_name=NARRATOR_MODEL)
    resp = await _call_with_retry(lambda: model.generate_content_async(prompt))
    return resp.text


# ── 命令解析 ─────────────────────────────────────────────────
_PARSE_SYSTEM = """你是三国策略游戏的命令解析器。
将玩家的自然语言命令转换为结构化JSON。

支持的action列表：
- train_troops: 训练兵马，amount=兵力数量
- recruit: 征募士卒，amount=数量
- diplomacy_gift: 馈赠诸侯，target=势力ID(cao_cao/liu_bei/sun_quan)
- build_farm: 开垦农田
- build_walls: 修筑城防
- spy: 遣派细作，target=势力ID
- rest: 休养生息

输出格式（JSON数组）：
[{"action": "xxx", "amount": 0, "target": ""}]

若命令不明确或无法解析，返回：[{"action": "rest"}]
只输出JSON，不要任何解释。"""


async def parse_orders(decree_text: str) -> List[Dict]:
    model = genai.GenerativeModel(model_name=PARSER_MODEL, system_instruction=_PARSE_SYSTEM)
    resp = await _call_with_retry(lambda: model.generate_content_async(decree_text))
    raw = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"action": "rest"}]
