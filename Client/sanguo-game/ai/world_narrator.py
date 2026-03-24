"""旁白 / 世界动态 AI 生成 & 命令解析（Venus OpenAPI 版）"""
from __future__ import annotations
import asyncio
import json
import requests
from pathlib import Path
from typing import List, Dict

from game.state import GameState
from config import VENUS_TOKEN, VENUS_URL, NARRATOR_MODEL, PARSER_MODEL

_PROMPT_DIR = Path(__file__).parent / "prompts"
_narrator_template = (_PROMPT_DIR / "narrator.txt").read_text(encoding="utf-8")


def _call_venus(messages: List[Dict], model: str) -> str:
    """同步调用 Venus OpenAPI，返回回复文本"""
    payload = {
        "model": model,
        "messages": messages,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VENUS_TOKEN}",
    }
    response = requests.post(VENUS_URL, headers=headers, data=json.dumps(payload), timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Venus API 请求失败 [{response.status_code}]: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


async def _call_venus_async(messages: List[Dict], model: str) -> str:
    """将同步 Venus 调用包装为异步"""
    return await asyncio.to_thread(_call_venus, messages, model)


# ── 旁白生成 ─────────────────────────────────────────────────
async def narrate_week(state: GameState, raw_events: str) -> str:
    r = state.resources
    prompt = _narrator_template.format(
        date=state.date, turn=state.turn, ruler_name=state.ruler_name,
        troops=r.troops, gold=r.gold, food=r.food, prestige=r.prestige,
        raw_events=raw_events,
    )
    messages = [{"role": "user", "content": prompt}]
    return await _call_venus_async(messages, NARRATOR_MODEL)


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
    messages = [
        {"role": "system", "content": _PARSE_SYSTEM},
        {"role": "user",   "content": decree_text},
    ]
    raw = await _call_venus_async(messages, PARSER_MODEL)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"action": "rest"}]
