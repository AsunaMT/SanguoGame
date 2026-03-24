"""AI大臣对话代理 v2.0 — 支持狼人杀人格 + 群聊/私聊模式"""
from __future__ import annotations
import asyncio
import re
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from openai import APIError, RateLimitError

from game.state import Minister, GameState, ImpactRecord
from game.ministers import ROLE_NAMES, HIDDEN_TRAIT_GUIDES
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    MINISTER_MODEL,
    DEEPSEEK_MAX_TOKENS,
    DEEPSEEK_TEMPERATURE,
    MAX_HISTORY_ROUNDS
)

# 创建 OpenAI 兼容客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_template(filename: str) -> str:
    return (_PROMPT_DIR / filename).read_text(encoding="utf-8")


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
            wait = _extract_retry_delay(e)
            await asyncio.sleep(wait)
        except APIError as e:
            if attempt == max_retries:
                raise
            await asyncio.sleep(5)


class MinisterAgent:
    """封装单个大臣的 AI 对话能力（v2.0 含隐藏特质）"""

    def __init__(self, minister: Minister, game_state: GameState):
        self.minister = minister
        self.state = game_state

    # ━━━━━━━━━━━━━━━━ 公开 API ━━━━━━━━━━━━━━━━

    async def respond_group(self, player_message: str,
                            other_responses: List[Dict[str, str]] = None,
                            scene_event: str = "") -> str:
        """群聊模式：所有大臣看到玩家的话 + 之前其他大臣的回应"""
        system = self._build_group_prompt(player_message, other_responses, scene_event)
        messages = self._build_messages(player_message, mode="group")

        reply = await self._call_llm(system, messages)
        self._append_history(player_message, reply)
        return reply

    async def respond_private(self, player_message: str) -> str:
        """私聊模式：1对1对话，暗奸可能趁机进谗言"""
        system = self._build_private_prompt()
        messages = self._build_messages(player_message, mode="private")

        reply = await self._call_llm(system, messages)
        self._append_history(f"[密谈]{player_message}", reply)
        return reply

    async def report_intel(self) -> str:
        """情报阶段：大臣主动汇报本领域情况"""
        system = self._build_intel_prompt()
        trigger = f"（{self.minister.name}走上前来，禀报{ROLE_NAMES.get(self.minister.role, '本职')}工作）"
        messages = [{"role": "user", "content": trigger}]

        reply = await self._call_llm(system, messages)
        self._append_history(trigger, reply)
        return reply

    async def confirm_decree(self, decree: str) -> str:
        """确认旨意"""
        system = self._build_decree_prompt(decree)
        msg = f"主公下旨：{decree}"
        messages = self._build_messages(msg, mode="decree")

        reply = await self._call_llm(system, messages)
        self._append_history(msg, reply)
        return reply

    async def generate_impact_comment(self) -> str:
        """生成本轮影响结算时的内心独白"""
        e = self.minister.emotion
        h = self.minister.hidden

        prompt = (
            f"你是{self.minister.name}，你的真实身份是{h.hidden_trait}。"
            f"当前忠诚度{e.loyalty}，满意度{e.satisfaction}，恐惧{e.fear}，野心{e.ambition}。"
            f"用一句简短的话（不超过20字）表达你此刻的真实内心想法。"
            f"注意：这是你内心深处的真话，不是说给别人听的。"
        )

        async def _call():
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=MINISTER_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一个三国大臣，用简短的话表达内心独白。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=50,
                    temperature=0.9,
                )
            )
            return response.choices[0].message.content.strip()

        try:
            return await _call_with_retry(_call)
        except Exception:
            return "……"

    # ━━━━━━━━━━━━━━━━ LLM 调用 ━━━━━━━━━━━━━━━━

    async def _call_llm(self, system: str, messages: List[Dict]) -> str:
        async def _call():
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=MINISTER_MODEL,
                    messages=[
                        {"role": "system", "content": system},
                        *messages
                    ],
                    max_tokens=DEEPSEEK_MAX_TOKENS,
                    temperature=DEEPSEEK_TEMPERATURE,
                )
            )
            return response.choices[0].message.content

        return await _call_with_retry(_call)

    # ━━━━━━━━━━━━━━━━ Prompt 构建 ━━━━━━━━━━━━━━━━

    def _build_base_context(self) -> str:
        """构建基础上下文（所有模式通用）"""
        m = self.minister
        s = self.state
        e = m.emotion
        st = m.stats

        # 领土摘要
        player_territories = [t for t in s.territories if t.owner == "player"]
        territories_summary = (
            "、".join(f"{t.name}（兵{t.troops}）" for t in player_territories)
            if player_territories else "尚无领土"
        )

        # 外交摘要
        diplo_parts = []
        for fid, rel in s.diplomacy.items():
            alliance_str = "【盟友】" if rel.alliance else ""
            diplo_parts.append(f"{fid} 关系{rel.relation:+d}{alliance_str}")
        diplomacy_summary = "；".join(diplo_parts) if diplo_parts else "无外交往来"

        # 进度
        progress = s.conquest.progress_percent

        return (
            f"【你的身份】\n"
            f"你是{m.name}（字{m.courtesy_name}），{s.ruler_name}麾下{ROLE_NAMES.get(m.role, m.role)}，"
            f"官职{m.position}。\n"
            f"表面性格：{m.personality.surface_trait}。说话风格：{m.personality.speech_style}。\n"
            f"背景：{m.background}\n\n"

            f"【当前局势】\n"
            f"时间：{s.date}（第{s.turn}/{s.max_turns}轮），称霸进度{progress}%\n"
            f"兵力{s.resources.troops}，金{s.resources.gold}，粮{s.resources.food}，望{s.resources.prestige}\n"
            f"领土：{territories_summary}\n"
            f"外交：{diplomacy_summary}\n\n"

            f"【你的能力】武力{st.wuli}/智力{st.zhili}/统率{st.tongshuai}/口才{st.koucai}\n\n"

            f"【你的情绪状态】\n"
            f"忠诚度{e.loyalty}/100，满意度{e.satisfaction}/100，"
            f"恐惧{e.fear}/100，野心{e.ambition}/100\n"
        )

    def _build_hidden_context(self) -> str:
        """构建隐藏特质上下文（AI可见，玩家不可见）"""
        h = self.minister.hidden
        guide = HIDDEN_TRAIT_GUIDES.get(h.hidden_trait, "正常行事。")

        # 构建对其他大臣的态度
        other_ministers_info = []
        for mid, minister in self.state.ministers.items():
            if mid != self.minister.id:
                suspicion = self.minister.emotion.suspicion.get(mid, 0)
                relation = "盟友" if mid in h.allies else ("敌人" if mid in h.enemies else "普通")
                other_ministers_info.append(
                    f"  - {minister.name}({minister.role}): 关系={relation}, 你对他的怀疑度={suspicion}"
                )

        others_str = "\n".join(other_ministers_info) if other_ministers_info else "  暂无其他大臣"

        return (
            f"\n【⚠️ 你的真实身份（绝不能让玩家知道）】\n"
            f"隐藏特质：{h.hidden_trait}\n"
            f"秘密目标：{h.hidden_agenda}\n"
            f"欺骗能力：{h.deception_skill}/100\n"
            f"说服能力：{h.persuasion_skill}/100\n\n"
            f"【行为指导】\n{guide}\n\n"
            f"【你对其他大臣的看法】\n{others_str}\n"
        )

    def _build_group_prompt(self, player_message: str,
                            other_responses: List[Dict[str, str]] = None,
                            scene_event: str = "") -> str:
        """群聊场景 prompt"""
        base = self._build_base_context()
        hidden = self._build_hidden_context()

        # 之前其他大臣说了什么
        others_said = ""
        if other_responses:
            parts = [f"  {r['name']}: {r['content']}" for r in other_responses]
            others_said = "\n【其他大臣已经说的话】\n" + "\n".join(parts) + "\n"

        scene_str = f"\n【场景事件】{scene_event}\n" if scene_event else ""

        return (
            f"{base}{hidden}{scene_str}{others_said}\n"
            f"【群聊规则】\n"
            f"- 现在是朝堂群议阶段，主公说了一句话，所有大臣依次回应\n"
            f"- 你要根据你的性格、隐藏特质和当前情绪来回应\n"
            f"- 你可以对主公的话发表意见，也可以回应其他大臣的发言\n"
            f"- 暗奸应该暗中挑拨；死忠应该提出好建议；墙头草应该附和强者\n"
            f"- 说话直白，不超过150字\n"
            f"- 如果你是暗奸，你可以在发言末尾加一句（低声自语）来暗中进行小动作\n"
            f"- 叫玩家\"主公\"\n"
        )

    def _build_private_prompt(self) -> str:
        """私聊场景 prompt"""
        base = self._build_base_context()
        hidden = self._build_hidden_context()

        return (
            f"{base}{hidden}\n"
            f"【私聊规则】\n"
            f"- 现在是密室召见，只有你和主公两个人\n"
            f"- 其他大臣听不到你们的对话\n"
            f"- 你可以比群聊时更放开地说话\n"
            f"- 暗奸可以趁机进谗言，诬陷忠臣\n"
            f"- 死忠可以趁机告密，揭发可疑行为\n"
            f"- 墙头草可以试探主公对自己的态度\n"
            f"- 说话直白，不超过200字\n"
            f"- 叫玩家\"主公\"\n"
        )

    def _build_intel_prompt(self) -> str:
        """情报汇报 prompt"""
        base = self._build_base_context()
        hidden = self._build_hidden_context()

        role_focus = {
            "internal": "重点汇报：钱粮收支、人口变化、民心趋势、内政问题",
            "military": "重点汇报：兵力状况、边防形势、敌军动向、军事建议",
            "diplomacy": "重点汇报：外交关系变化、诸侯动向、结盟/敌对形势、情报信息",
        }

        return (
            f"{base}{hidden}\n"
            f"【情报汇报规则】\n"
            f"- 现在是情报汇报阶段，你要主动向主公禀报本领域的情况\n"
            f"- {role_focus.get(self.minister.role, '汇报相关工作')}\n"
            f"- 提出1-2个建议\n"
            f"- 暗奸在汇报中可能夹带私货（夸大某些问题、隐瞒关键信息）\n"
            f"- 说话直白，不超过150字\n"
            f"- 叫玩家\"主公\"\n"
        )

    def _build_decree_prompt(self, decree: str) -> str:
        """确认旨意 prompt"""
        base = self._build_base_context()
        hidden = self._build_hidden_context()

        return (
            f"{base}{hidden}\n"
            f"【旨意确认规则】\n"
            f"- 主公已下旨：「{decree}」\n"
            f"- 复述命令要点，说清楚你有没有意见\n"
            f"- 暗奸可能表面赞同但暗中准备阳奉阴违\n"
            f"- 死忠如果觉得命令有问题会委婉劝谏\n"
            f"- 野心家会评估这个命令对自己的利弊\n"
            f"- 说话直白，不超过120字\n"
            f"- 叫玩家\"主公\"\n"
        )

    # ━━━━━━━━━━━━━━━━ 对话历史管理 ━━━━━━━━━━━━━━━━

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

    def _build_messages(self, user_message: str, mode: str = "group") -> List[Dict]:
        messages = []
        for h in self.minister.conversation_history[-MAX_HISTORY_ROUNDS:]:
            messages.append({"role": "user", "content": h["user"]})
            messages.append({"role": "assistant", "content": h["assistant"]})
        messages.append({"role": "user", "content": user_message})
        return messages


# ━━━━━━━━━━━━━━━━ 影响结算引擎 ━━━━━━━━━━━━━━━━

def calculate_speech_impact(
    state: GameState,
    player_message: str,
    responses: Dict[str, str]
) -> List[ImpactRecord]:
    """根据玩家发言和大臣回应，计算对每个大臣的情绪影响"""
    impacts = []

    for mid, minister in state.ministers.items():
        record = ImpactRecord(
            minister_id=mid,
            minister_name=minister.name,
        )

        h = minister.hidden
        e = minister.emotion

        # 基础影响：根据隐藏特质
        if h.hidden_trait == "暗奸":
            # 暗奸总是在暗中积蓄
            record.ambition_delta = 2
            if "怀疑" in player_message or minister.name in player_message:
                record.fear_delta = 15
                record.comment = "主公似乎在怀疑我..."
            else:
                record.satisfaction_delta = 3
                record.comment = "还好，主公没有察觉。"

        elif h.hidden_trait == "死忠":
            # 被采纳建议则满意
            resp = responses.get(mid, "")
            record.loyalty_delta = 2
            record.satisfaction_delta = 3
            record.comment = "能为主公效力，心中甚慰。"

        elif h.hidden_trait == "墙头草":
            # 根据势力强弱调整
            progress = state.conquest.progress_percent
            if progress > 50:
                record.loyalty_delta = 3
                record.comment = "主公势不可挡，跟着主公准没错。"
            else:
                record.loyalty_delta = -2
                record.comment = "这局势...还是多留条后路吧。"

        elif h.hidden_trait == "野心家":
            # 军事话题增加野心
            military_keywords = ["出兵", "攻打", "军", "战", "征", "兵"]
            if any(kw in player_message for kw in military_keywords):
                record.ambition_delta = 5
                record.satisfaction_delta = 5
                record.comment = "又要打仗了，好！"
            else:
                record.satisfaction_delta = -3
                record.comment = "又是文臣的事，无聊。"

        elif h.hidden_trait == "老实人":
            record.loyalty_delta = 1
            record.satisfaction_delta = 2
            record.comment = "听主公的准没错。"

        # 应用影响
        e.loyalty += record.loyalty_delta
        e.satisfaction += record.satisfaction_delta
        e.fear += record.fear_delta
        e.ambition += record.ambition_delta
        minister.clamp_emotion()

        impacts.append(record)

    return impacts


def check_betrayal_conditions(state: GameState) -> Optional[str]:
    """检查是否触发背叛/兵变/暗杀"""
    for mid, minister in state.ministers.items():
        e = minister.emotion
        h = minister.hidden

        # 野心家兵变：野心 > 80 且 满意度 < 30
        if h.hidden_trait == "野心家" and e.ambition > 80 and e.satisfaction < 30:
            return f"betrayal_{mid}"

        # 暗奸暗杀：恐惧 > 90（被逼急了）或 全体忠诚 < 30
        if h.hidden_trait == "暗奸" and e.fear > 90:
            return f"assassinate_{mid}"

    # 全体忠诚度检查
    all_loyalties = [m.emotion.loyalty for m in state.ministers.values()]
    if all_loyalties and max(all_loyalties) < 30:
        return "mass_betrayal"

    return None
