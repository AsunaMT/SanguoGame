"""旁白 / 世界动态 AI 生成 & 命令解析（DeepSeek 版）"""
from __future__ import annotations
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict
from openai import OpenAI, APIError, RateLimitError

from game.state import GameState
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    NARRATOR_MODEL,
    PARSER_MODEL,
    DEEPSEEK_MAX_TOKENS,
    DEEPSEEK_TEMPERATURE
)

# 创建 DeepSeek 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

_PROMPT_DIR = Path(__file__).parent / "prompts"
_narrator_template = (_PROMPT_DIR / "narrator.txt").read_text(encoding="utf-8")


def _extract_retry_delay(exc: RateLimitError) -> float:
    m = re.search(r"retry_after[\"']?\s*:\s*(\d+)", str(exc), re.IGNORECASE)
    return float(m.group(1)) + 2 if m else 30.0


async def _call_with_retry(coro_fn, max_retries: int = 2):
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            await asyncio.sleep(_extract_retry_delay(e))
        except APIError as e:
            if attempt == max_retries:
                raise
            await asyncio.sleep(5)


# ── 旁白生成 ─────────────────────────────────────────────────
async def narrate_week(state: GameState, raw_events: str) -> str:
    r = state.resources
    prompt = _narrator_template.format(
        date=state.date, turn=state.turn, ruler_name=state.ruler_name,
        troops=r.troops, gold=r.gold, food=r.food, prestige=r.prestige,
        raw_events=raw_events,
    )

    async def _call():
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=NARRATOR_MODEL,
                messages=[
                    {"role": "system", "content": "你是三国策略游戏的旁白，用文言文或半文言风格叙述一周发生的重大事件。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=DEEPSEEK_MAX_TOKENS,
                temperature=DEEPSEEK_TEMPERATURE,
            )
        )
        return response.choices[0].message.content

    return await _call_with_retry(_call)


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
    async def _call():
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=PARSER_MODEL,
                messages=[
                    {"role": "system", "content": _PARSE_SYSTEM},
                    {"role": "user", "content": decree_text}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
        )
        return response.choices[0].message.content

    raw = await _call_with_retry(_call)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"action": "rest"}]
