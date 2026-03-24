"""朝会状态机"""
from typing import Optional


COURT_PHASES = [
    "idle",          # 待机，等待上朝
    "kai_chao",      # 鸣鞭入殿（自动播放）
    "bingzou",       # 禀奏：三臣依次汇报
    "yishi",         # 议事：玩家自由对话
    "nizhi",         # 拟旨：玩家下令，大臣确认
    "tui_chao",      # 退朝礼仪
    "world_update",  # 后端世界结算
    "week_report",   # 周报展示
]

PHASE_TRANSITIONS = {
    "idle":         "kai_chao",
    "kai_chao":     "bingzou",
    "bingzou":      "yishi",
    "yishi":        "nizhi",
    "nizhi":        "tui_chao",
    "tui_chao":     "world_update",
    "world_update": "week_report",
    "week_report":  "idle",
}

PHASE_DISPLAY = {
    "idle":         "待机",
    "kai_chao":     "鸣鞭入殿",
    "bingzou":      "禀奏",
    "yishi":        "议事",
    "nizhi":        "拟旨",
    "tui_chao":     "退朝",
    "world_update": "世界推进",
    "week_report":  "周报",
}


def next_phase(current: str) -> str:
    return PHASE_TRANSITIONS.get(current, "idle")


def can_chat(phase: str) -> bool:
    """只有议事阶段允许自由对话"""
    return phase == "yishi"


def can_decree(phase: str) -> bool:
    """拟旨阶段才能下旨"""
    return phase == "nizhi"
