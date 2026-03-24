"""AI大臣对话代理（Gemini 版）"""
from __future__ import annotations
import asyncio
import re
from pathlib import Path
from typing import List, Dict
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

from game.state import Minister, GameState
from game.ministers import ROLE_NAMES
from config import GEMINI_API_KEY, MINISTER_MODEL, MAX_HISTORY_ROUNDS

genai.configure(api_key=GEMINI_API_KEY)

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_template(filename: str) -> str:
    return (_PROMPT_DIR / filename).read_text(encoding="utf-8")


def _extract_retry_delay(exc: ResourceExhausted) -> float:
    """从异常消息里提取 retry_delay 秒数，默认30秒"""
    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", str(exc))
    return float(m.group(1)) + 2 if m else 30.0


async def _call_with_retry(coro_fn, max_retries: int = 2):
    """遇到限流自动等待重试"""
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except ResourceExhausted as e:
            if attempt == max_retries:
                raise
            wait = _extract_retry_delay(e)
            await asyncio.sleep(wait)


class MinisterAgent:
    """封装单个大臣的 Gemini API 对话"""

    def __init__(self, minister: Minister, game_state: GameState):
        self.minister = minister
        self.state = game_state
        self._base_template = _load_template("minister_base.txt")
        self._phase_template = _load_template("court_phases.txt")

    async def respond(self, user_message: str, phase: str, decree: str = "") -> str:
        system = self._build_system_prompt(phase, decree)
        history = self._build_gemini_history()

        model = genai.GenerativeModel(
            model_name=MINISTER_MODEL,
            system_instruction=system,
        )
        chat = model.start_chat(history=history)

        async def _call():
            return await chat.send_message_async(user_message)

        response = await _call_with_retry(_call)
        reply = response.text
        self._append_history(user_message, reply)
        return reply

    async def bingzou(self) -> str:
        trigger = f"（{self.minister.name}走上前来，开始禀报）"
        return await self.respond(trigger, phase="bingzou")

    async def confirm_decree(self, decree: str) -> str:
        return await self.respond(f"朕旨：{decree}", phase="nizhi", decree=decree)

    # ── 对话历史管理 ──────────────────────────────────────────
    def _append_history(self, user: str, assistant: str):
        hist = self.minister.conversation_history
        hist.append({"user": user, "assistant": assistant})

        if len(hist) > MAX_HISTORY_ROUNDS + 5:
            to_summarize = hist[:10]
            hist[:10] = []
            old_text = "\n".join(
                f"玩家: {h['user']}\n{self.minister.name}: {h['assistant']}"
                for h in to_summarize
            )
            self.minister.history_summary = old_text[:500] + "…（摘要）"

    def _build_gemini_history(self) -> List[Dict]:
        """转换为 Gemini 的 history 格式"""
        history = []
        for h in self.minister.conversation_history[-MAX_HISTORY_ROUNDS:]:
            history.append({"role": "user",  "parts": [h["user"]]})
            history.append({"role": "model", "parts": [h["assistant"]]})
        return history

    # ── System Prompt 构建 ────────────────────────────────────
    def _build_system_prompt(self, phase: str, decree: str = "") -> str:
        m = self.minister
        s = self.state

        player_territories = [t for t in s.territories if t.owner == "player"]
        territories_summary = (
            "、".join(f"{t.name}（兵{t.troops}）" for t in player_territories)
            if player_territories else "尚无领土"
        )

        diplo_parts = []
        for fid, rel in s.diplomacy.items():
            alliance_str = "【盟友】" if rel.alliance else ""
            diplo_parts.append(f"{fid} 关系{rel.relation:+d}{alliance_str}")
        diplomacy_summary = "；".join(diplo_parts) if diplo_parts else "无外交往来"

        role_responsibility_map = {
            "internal":  "掌管钱粮、人口、农桑、税收等内政事务，确保仓廪充实、民心稳定",
            "military":  "掌管兵马操练、战阵部署、城防修筑，确保军备精良、边境安全",
            "diplomacy": "掌管诸侯邦交、遣使结盟、刺探情报，在乱世中为主公争取最优外交格局",
        }
        role_responsibility = role_responsibility_map.get(m.role, "辅佐主公")

        phase_lines = {k: v for k, v in (
            line.split(": ", 1) for line in self._phase_template.strip().splitlines()
            if ": " in line
        )}
        court_phase_instruction = phase_lines.get(
            phase, "按常礼议事，随时听候主公吩咐"
        ).replace("{role}", ROLE_NAMES.get(m.role, m.role)).replace("{decree}", decree)

        return self._base_template.format(
            minister_name=m.name,
            courtesy_name=m.courtesy_name,
            ruler_name=s.ruler_name,
            role_name=ROLE_NAMES.get(m.role, m.role),
            traits="、".join(m.personality.traits),
            speech_style=m.personality.speech_style,
            values="、".join(m.personality.values),
            dislikes="、".join(m.personality.dislikes),
            background=m.background,
            date=s.date,
            turn=s.turn,
            troops=s.resources.troops,
            gold=s.resources.gold,
            food=s.resources.food,
            prestige=s.resources.prestige,
            territories_summary=territories_summary,
            diplomacy_summary=diplomacy_summary,
            role_responsibility=role_responsibility,
            court_phase_instruction=court_phase_instruction,
            history_summary=m.history_summary or "（暂无历史对话摘要）",
        )
