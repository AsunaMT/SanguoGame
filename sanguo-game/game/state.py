"""游戏状态数据模型（Pydantic）"""
from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ─── 资源 ────────────────────────────────────────────────────
class Resources(BaseModel):
    gold: int = 1000          # 钱粮
    food: int = 5000          # 军粮
    troops: int = 10000       # 兵力
    population: int = 50000   # 人口
    prestige: int = 30        # 声望（0-100）


# ─── 领土 ────────────────────────────────────────────────────
class Territory(BaseModel):
    id: str
    name: str
    owner: str                # player / cao_cao / liu_bei / sun_quan / neutral
    troops: int = 0
    population: int = 10000
    tax_rate: float = 0.1


# ─── 外交 ────────────────────────────────────────────────────
class DiplomacyRelation(BaseModel):
    target: str
    relation: int = 0         # -100(死敌) ~ 100(同盟)
    alliance: bool = False
    last_event: str = ""


# ─── 大臣人格 ─────────────────────────────────────────────────
class MinisterPersonality(BaseModel):
    traits: List[str] = []
    speech_style: str = ""
    values: List[str] = []
    dislikes: List[str] = []


# ─── 大臣 ────────────────────────────────────────────────────
class Minister(BaseModel):
    id: str
    name: str
    courtesy_name: str
    role: str                 # internal / military / diplomacy
    personality: MinisterPersonality
    background: str = ""
    special_ability: str = ""
    ability_effect: Dict = Field(default_factory=dict)
    loyalty: int = 80
    conversation_history: List[Dict] = Field(default_factory=list)
    history_summary: str = ""   # 早期对话的滚动摘要


# ─── 游戏状态 ─────────────────────────────────────────────────
class GameState(BaseModel):
    turn: int = 1
    date: str = "公元208年秋"
    ruler_name: str = "主公"
    buffs: List[str] = Field(default_factory=list)
    resources: Resources = Field(default_factory=Resources)
    territories: List[Territory] = Field(default_factory=list)
    diplomacy: Dict[str, DiplomacyRelation] = Field(default_factory=dict)
    ministers: Dict[str, Minister] = Field(default_factory=dict)
    court_phase: str = "idle"   # idle/kai_chao/bingzou/yishi/nizhi/tui_chao/world_update/week_report
    history_log: List[str] = Field(default_factory=list)
    week_orders: List[str] = Field(default_factory=list)
    week_reports: Dict[str, str] = Field(default_factory=dict)


# ─── 周结算结果 ───────────────────────────────────────────────
class WeekResult(BaseModel):
    turn: int
    report: str
    events: List[str] = Field(default_factory=list)
    resource_delta: Dict = Field(default_factory=dict)
    territory_changes: List[Dict] = Field(default_factory=list)
