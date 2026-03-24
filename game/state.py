"""游戏状态数据模型 v2.0（Pydantic）"""
from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import random


# ─── 资源 ────────────────────────────────────────────────────
class Resources(BaseModel):
    gold: int = 1000
    food: int = 5000
    troops: int = 10000
    population: int = 50000
    prestige: int = 30


# ─── 领土 ────────────────────────────────────────────────────
class Territory(BaseModel):
    id: str
    name: str
    owner: str              # player / cao_cao / liu_bei / sun_quan / neutral ...
    troops: int = 0
    population: int = 10000
    tax_rate: float = 0.1
    defense: int = 50       # 城防值 0-100
    at_war: bool = False    # 是否处于战争中


# ─── 外交 ────────────────────────────────────────────────────
class DiplomacyRelation(BaseModel):
    target: str
    relation: int = 0       # -100(死敌) ~ 100(同盟)
    alliance: bool = False
    last_event: str = ""


# ─── 7维能力数值 ──────────────────────────────────────────────
class CharacterStats(BaseModel):
    """角色能力数值体系"""
    wuli: int = 50          # 武力 0-100: 战斗胜率、护驾
    zhili: int = 50         # 智力 0-100: 计策成功率、识破阴谋
    tongshuai: int = 50     # 统率 0-100: 带兵上限、士气
    koucai: int = 50        # 口才 0-100: 说服、外交谈判
    zhongcheng: int = 80    # 忠诚 0-100: 对玩家忠诚度（动态变化）
    yexin: int = 20         # 野心 0-100: 越高越可能叛变
    qinglian: int = 60      # 清廉 0-100: 国库收入、民心


# ─── 大臣隐藏特质系统（狼人杀核心）──────────────────────────────
class HiddenProfile(BaseModel):
    """大臣的隐藏面 - 玩家无法直接看到"""
    hidden_trait: str = "老实人"       # "暗奸" / "死忠" / "墙头草" / "野心家" / "老实人"
    hidden_agenda: str = ""             # 秘密目标描述
    deception_skill: int = 30           # 欺骗能力 0-100
    persuasion_skill: int = 50          # 说服能力 0-100
    allies: List[str] = Field(default_factory=list)    # 暗中结盟的大臣id
    enemies: List[str] = Field(default_factory=list)   # 敌对的大臣id


# ─── 大臣动态情绪状态 ─────────────────────────────────────────
class EmotionState(BaseModel):
    """实时变化的情绪数值"""
    loyalty: int = 75           # 忠诚度 0-100
    satisfaction: int = 60      # 满意度 0-100
    fear: int = 10              # 恐惧值 0-100
    ambition: int = 20          # 野心值 0-100
    suspicion: Dict[str, int] = Field(default_factory=dict)  # 对其他大臣的怀疑度


# ─── 大臣表面性格（玩家可见）──────────────────────────────────
class SurfacePersonality(BaseModel):
    """玩家可以感知到的性格"""
    surface_trait: str = ""     # "忠厚老实" / "刚正不阿" / "足智多谋" 等
    traits: List[str] = Field(default_factory=list)
    speech_style: str = ""
    values: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)


# ─── 大臣 v2.0 ──────────────────────────────────────────────
class Minister(BaseModel):
    id: str
    name: str
    courtesy_name: str
    role: str                   # internal / military / diplomacy
    position: str = ""          # 具体官职名 "丞相" / "将军" 等

    # 表面性格（玩家可见）
    personality: SurfacePersonality = Field(default_factory=SurfacePersonality)

    # 7维能力数值
    stats: CharacterStats = Field(default_factory=CharacterStats)

    # 隐藏特质（狼人杀核心）
    hidden: HiddenProfile = Field(default_factory=HiddenProfile)

    # 动态情绪
    emotion: EmotionState = Field(default_factory=EmotionState)

    # 基本信息
    background: str = ""
    special_ability: str = ""
    ability_effect: Dict = Field(default_factory=dict)

    # 行为记录（玩家可查看的公开记录）
    action_log: List[str] = Field(default_factory=list)

    # AI对话历史
    conversation_history: List[Dict] = Field(default_factory=list)
    history_summary: str = ""

    # 状态
    status: str = "active"      # active / captured / exiled / dead

    def clamp_emotion(self):
        """将所有情绪值限制在 0-100"""
        e = self.emotion
        e.loyalty = max(0, min(100, e.loyalty))
        e.satisfaction = max(0, min(100, e.satisfaction))
        e.fear = max(0, min(100, e.fear))
        e.ambition = max(0, min(100, e.ambition))


# ─── 场景事件 ────────────────────────────────────────────────
class SceneEvent(BaseModel):
    """随机场景事件"""
    id: str
    description: str
    hint: str = ""              # 给玩家的隐藏线索
    affected_ministers: List[str] = Field(default_factory=list)
    effects: Dict = Field(default_factory=dict)


# ─── 影响结算记录 ─────────────────────────────────────────────
class ImpactRecord(BaseModel):
    """单个大臣在一轮中的状态变化"""
    minister_id: str
    minister_name: str
    loyalty_delta: int = 0
    satisfaction_delta: int = 0
    fear_delta: int = 0
    ambition_delta: int = 0
    comment: str = ""           # AI生成的内心独白


# ─── 称霸进度 ────────────────────────────────────────────────
class ConquestProgress(BaseModel):
    """称霸天下进度"""
    total_provinces: int = 12
    owned_provinces: int = 1
    progress_percent: float = 0.0
    target_provinces: int = 12  # 需要占领多少州才算胜利

    def update(self, territories: List[Territory]):
        self.owned_provinces = sum(1 for t in territories if t.owner == "player")
        self.progress_percent = round(
            (self.owned_provinces / self.target_provinces) * 100, 1
        )


# ─── 游戏结局枚举 ────────────────────────────────────────────
class GameEnding(BaseModel):
    """游戏结局"""
    type: str = ""              # victory / death_age / betrayal / captured / assassinated
    description: str = ""
    turn: int = 0


# ─── 游戏状态 v2.0 ──────────────────────────────────────────
class GameState(BaseModel):
    # 基础信息
    turn: int = 1
    max_turns: int = 20         # 极速模式：20轮
    date: str = "公元208年秋"
    ruler_name: str = "主公"

    # 资源
    resources: Resources = Field(default_factory=Resources)

    # 领土 & 外交
    territories: List[Territory] = Field(default_factory=list)
    diplomacy: Dict[str, DiplomacyRelation] = Field(default_factory=dict)

    # 大臣（key = minister.id 而非 role）
    ministers: Dict[str, Minister] = Field(default_factory=dict)

    # 朝堂阶段
    court_phase: str = "idle"
    # idle → opening → intel → group_discuss → private_meet → decision → impact → world_update → idle

    # 称霸进度
    conquest: ConquestProgress = Field(default_factory=ConquestProgress)

    # 本轮数据
    current_scene_event: Optional[SceneEvent] = None
    current_impacts: List[ImpactRecord] = Field(default_factory=list)
    week_orders: List[str] = Field(default_factory=list)
    week_reports: Dict[str, str] = Field(default_factory=dict)

    # 历史
    history_log: List[str] = Field(default_factory=list)

    # 游戏结束
    game_over: bool = False
    ending: Optional[GameEnding] = None

    # 被俘状态
    is_captured: bool = False
    capture_turn: int = 0

    # v1 兼容（保留旧字段，避免存档加载报错）
    # court_phase 的旧值映射在 court.py 里处理


# ─── 周结算结果 ──────────────────────────────────────────────
class WeekResult(BaseModel):
    turn: int
    report: str
    events: List[str] = Field(default_factory=list)
    resource_delta: Dict = Field(default_factory=dict)
    territory_changes: List[Dict] = Field(default_factory=list)
    impacts: List[ImpactRecord] = Field(default_factory=list)
    conquest_progress: float = 0.0
