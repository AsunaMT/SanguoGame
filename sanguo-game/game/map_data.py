"""地图 / 领土基础数据"""
from typing import List, Dict, Any
from game.state import Territory, DiplomacyRelation

# 三国地图初始领土分配（简化版，围绕赤壁前夕）
INITIAL_TERRITORIES: List[Dict[str, Any]] = [
    # 玩家初始领土
    {"id": "player_start", "name": "零陵", "owner": "player", "troops": 3000, "population": 20000, "tax_rate": 0.1},

    # 曹操势力（北方/中原）
    {"id": "xu_du", "name": "许都", "owner": "cao_cao", "troops": 80000, "population": 300000, "tax_rate": 0.15},
    {"id": "jingzhou_bei", "name": "南阳", "owner": "cao_cao", "troops": 30000, "population": 80000, "tax_rate": 0.12},
    {"id": "wan_cheng", "name": "宛城", "owner": "cao_cao", "troops": 15000, "population": 50000, "tax_rate": 0.12},
    {"id": "ye_cheng", "name": "邺城", "owner": "cao_cao", "troops": 40000, "population": 120000, "tax_rate": 0.13},

    # 刘备势力（荆州）
    {"id": "xinye", "name": "新野", "owner": "liu_bei", "troops": 8000, "population": 30000, "tax_rate": 0.08},
    {"id": "fangling", "name": "樊城", "owner": "liu_bei", "troops": 5000, "population": 20000, "tax_rate": 0.08},

    # 孙权势力（江东）
    {"id": "jiankang", "name": "建业", "owner": "sun_quan", "troops": 50000, "population": 150000, "tax_rate": 0.12},
    {"id": "柴桑", "name": "柴桑", "owner": "sun_quan", "troops": 20000, "population": 60000, "tax_rate": 0.10},
    {"id": "jiujiang", "name": "寻阳", "owner": "sun_quan", "troops": 10000, "population": 40000, "tax_rate": 0.10},

    # 刘表势力（即将被曹操整合）
    {"id": "xiangyang", "name": "襄阳", "owner": "liu_biao", "troops": 20000, "population": 80000, "tax_rate": 0.10},
    {"id": "jiangling", "name": "江陵", "owner": "liu_biao", "troops": 12000, "population": 50000, "tax_rate": 0.10},

    # 中立/待取
    {"id": "changsha", "name": "长沙", "owner": "neutral", "troops": 5000, "population": 30000, "tax_rate": 0.08},
    {"id": "guiyang", "name": "桂阳", "owner": "neutral", "troops": 3000, "population": 20000, "tax_rate": 0.08},
    {"id": "wuling", "name": "武陵", "owner": "neutral", "troops": 2000, "population": 15000, "tax_rate": 0.07},
]

# 初始外交关系
INITIAL_DIPLOMACY: Dict[str, Dict[str, Any]] = {
    "cao_cao": {"target": "cao_cao", "relation": -20, "alliance": False, "last_event": "曹操南下，天下震动"},
    "liu_bei": {"target": "liu_bei", "relation": 10, "alliance": False, "last_event": "刘备驻扎新野，招揽人才"},
    "sun_quan": {"target": "sun_quan", "relation": 0, "alliance": False, "last_event": "孙权据守江东"},
    "liu_biao": {"target": "liu_biao", "relation": 20, "alliance": False, "last_event": "刘表荆州，与我相邻"},
}

# 势力显示名称
FACTION_NAMES: Dict[str, str] = {
    "player": "玩家",
    "cao_cao": "曹操",
    "liu_bei": "刘备",
    "sun_quan": "孙权",
    "liu_biao": "刘表",
    "neutral": "中立",
}


def build_initial_territories() -> List[Territory]:
    return [Territory(**t) for t in INITIAL_TERRITORIES]


def build_initial_diplomacy() -> Dict[str, DiplomacyRelation]:
    return {k: DiplomacyRelation(**v) for k, v in INITIAL_DIPLOMACY.items()}
