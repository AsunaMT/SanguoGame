"""朝堂状态机 v2.0 — 7步朝堂流程"""
from typing import Optional, List, Dict


# ─── 新朝堂阶段 ──────────────────────────────────────────────
# idle → opening → intel → group_discuss → private_meet → decision → impact → world_update → idle
COURT_PHASES = [
    "idle",             # 待机，等待上朝
    "opening",          # 开朝（旁白描述 + 随机场景事件）
    "intel",            # 情报汇报（各方势力动态 + 大臣禀奏）
    "group_discuss",    # 群议环节（玩家发言 → 所有大臣依次回应）
    "private_meet",     # 密谋环节（玩家可选择单独召见某大臣私聊）
    "decision",         # 决策环节（玩家做出最终决定/下旨）
    "impact",           # 影响结算（展示每个大臣的状态变化）
    "world_update",     # 天下局势更新（地图 + 进度条变化）
]

PHASE_TRANSITIONS = {
    "idle":           "opening",
    "opening":        "intel",
    "intel":          "group_discuss",
    "group_discuss":  "private_meet",
    "private_meet":   "decision",
    "decision":       "impact",
    "impact":         "world_update",
    "world_update":   "idle",
}

PHASE_DISPLAY = {
    "idle":           "待机",
    "opening":        "开朝",
    "intel":          "情报",
    "group_discuss":  "群议",
    "private_meet":   "密谋",
    "decision":       "决策",
    "impact":         "结算",
    "world_update":   "天下大势",
}

# 旧阶段 → 新阶段映射（v1 兼容）
LEGACY_PHASE_MAP = {
    "kai_chao":     "opening",
    "bingzou":      "intel",
    "yishi":        "group_discuss",
    "nizhi":        "decision",
    "tui_chao":     "impact",
    "week_report":  "world_update",
}


def normalize_phase(phase: str) -> str:
    """将旧版阶段名映射为新版"""
    return LEGACY_PHASE_MAP.get(phase, phase)


def next_phase(current: str) -> str:
    """返回下一个阶段"""
    current = normalize_phase(current)
    return PHASE_TRANSITIONS.get(current, "idle")


def can_group_chat(phase: str) -> bool:
    """群议阶段允许群聊"""
    return normalize_phase(phase) == "group_discuss"


def can_private_chat(phase: str) -> bool:
    """密谋阶段允许私聊"""
    return normalize_phase(phase) == "private_meet"


def can_decree(phase: str) -> bool:
    """决策阶段才能下旨"""
    return normalize_phase(phase) == "decision"


def can_skip_to_decision(phase: str) -> bool:
    """群议和密谋阶段都可以跳到决策"""
    p = normalize_phase(phase)
    return p in ("group_discuss", "private_meet")


# ─── 随机场景事件池 ──────────────────────────────────────────
SCENE_EVENTS = [
    {
        "id": "tea_spill",
        "description": "{minister_name}不小心打翻了面前的茶杯，茶水洒了一地。",
        "hint": "也许{minister_name}心里有事，才会如此失态…",
        "weight": 15,
        "emotion_effects": {"target": "fear+5"},
    },
    {
        "id": "whisper_caught",
        "description": "你注意到{minister_a}和{minister_b}在低声私语，看到你望过来，他们立刻停了下来。",
        "hint": "他们在聊什么？是正常交流，还是在密谋什么？",
        "weight": 12,
        "emotion_effects": {},
    },
    {
        "id": "urgent_report",
        "description": "殿外突然传来急促的脚步声——一名信使跌跌撞撞地冲进来：「报——边关急报！」",
        "hint": "各位大臣的反应值得观察。",
        "weight": 10,
        "emotion_effects": {"all": "fear+5"},
    },
    {
        "id": "doze_off",
        "description": "{minister_name}似乎有些困倦，眼皮不断打架，差点在朝会上打起盹来。",
        "hint": "也许昨晚{minister_name}在忙什么别的事…",
        "weight": 10,
        "emotion_effects": {"target": "satisfaction-5"},
    },
    {
        "id": "vase_fall",
        "description": "不知谁碰了一下，殿角的一个花瓶「砰」地倒在地上摔碎了。{minister_name}离花瓶最近…",
        "hint": "是意外，还是有人故意制造混乱？",
        "weight": 8,
        "emotion_effects": {},
    },
    {
        "id": "anonymous_letter",
        "description": "侍卫在龙案上发现一封没有署名的信。信中暗示朝中有人暗通敌国…",
        "hint": "这封信是谁写的？信中所言是否属实？",
        "weight": 5,
        "emotion_effects": {"all": "fear+10"},
    },
    {
        "id": "sudden_kneel",
        "description": "{minister_name}突然跪倒在地：「主公，臣有一事不得不说！」",
        "hint": "是真的有要事禀报，还是被逼无奈？",
        "weight": 7,
        "emotion_effects": {"target": "fear+15"},
    },
    {
        "id": "envoy_arrives",
        "description": "宫门突然来报：有外邦使者求见！来的是{faction_name}的人。",
        "hint": "在这个时候来访，是和是战？",
        "weight": 8,
        "emotion_effects": {},
    },
]


def get_random_scene_event(ministers: Dict, diplomacy: Dict) -> Optional[Dict]:
    """随机选取一个场景事件并填充参数"""
    import random

    # 30%概率不触发事件
    if random.random() < 0.30:
        return None

    weights = [e["weight"] for e in SCENE_EVENTS]
    event_template = random.choices(SCENE_EVENTS, weights=weights, k=1)[0]
    event = dict(event_template)

    minister_ids = list(ministers.keys())
    if not minister_ids:
        return None

    # 填充占位符
    random_minister = random.choice(minister_ids)
    event["description"] = event["description"].replace(
        "{minister_name}", ministers[random_minister].name
    )
    event["hint"] = event["hint"].replace(
        "{minister_name}", ministers[random_minister].name
    )
    event["affected_minister"] = random_minister

    # 双人事件
    if "{minister_a}" in event["description"] and len(minister_ids) >= 2:
        pair = random.sample(minister_ids, 2)
        event["description"] = event["description"].replace(
            "{minister_a}", ministers[pair[0]].name
        ).replace(
            "{minister_b}", ministers[pair[1]].name
        )
        event["hint"] = event["hint"].replace(
            "{minister_a}", ministers[pair[0]].name
        ).replace(
            "{minister_b}", ministers[pair[1]].name
        )

    # 外交事件
    if "{faction_name}" in event["description"]:
        faction_names = {"cao_cao": "曹操", "liu_bei": "刘备", "sun_quan": "孙权"}
        faction_keys = list(diplomacy.keys())
        if faction_keys:
            fk = random.choice(faction_keys)
            fname = faction_names.get(fk, fk)
            event["description"] = event["description"].replace("{faction_name}", fname)
            event["hint"] = event["hint"].replace("{faction_name}", fname)

    return event
