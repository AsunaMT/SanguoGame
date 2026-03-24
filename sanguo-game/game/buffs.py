"""起始Buff系统"""
from typing import List, Dict, Any

STARTER_BUFFS: List[Dict[str, Any]] = [
    {
        "id": "ren_de",
        "name": "仁德之名",
        "desc": "百姓拥戴，外交声望+20，每周人口增长+5%",
        "effects": {"prestige": 20, "pop_growth": 0.05},
    },
    {
        "id": "jing_bing",
        "name": "精兵猛将",
        "desc": "麾下精锐，初始兵力×1.5，训练效率+20%",
        "effects": {"troops_mult": 1.5, "train_efficiency": 0.2},
    },
    {
        "id": "qian_liang",
        "name": "钱粮充足",
        "desc": "仓廪实，初始金粮×1.5",
        "effects": {"gold_mult": 1.5, "food_mult": 1.5},
    },
    {
        "id": "di_li",
        "name": "地利之便",
        "desc": "险要地形，防御+30%，敌方攻城消耗+50%",
        "effects": {"defense_bonus": 0.3, "siege_cost_enemy": 0.5},
    },
    {
        "id": "mou_shi",
        "name": "谋士云集",
        "desc": "人才鼎盛，大臣智谋建议更准确，可额外查看一条情报",
        "effects": {"intel_bonus": 1},
    },
    {
        "id": "min_xin",
        "name": "民心所向",
        "desc": "民心归附，每周税收+15%，叛乱概率-50%",
        "effects": {"tax_bonus": 0.15, "rebellion_reduce": 0.5},
    },
    {
        "id": "shang_dao",
        "name": "商道兴旺",
        "desc": "贸易发达，每周额外收入+200金",
        "effects": {"gold_per_week": 200},
    },
    {
        "id": "tian_shi",
        "name": "天时眷顾",
        "desc": "本回合历史大事对你有利，赤壁后势力格局对玩家更友好",
        "effects": {"event_modifier": "favorable"},
    },
]

BUFF_MAP: Dict[str, Dict[str, Any]] = {b["id"]: b for b in STARTER_BUFFS}


def apply_buffs(resources_dict: dict, buff_ids: List[str]) -> dict:
    """将已选择的buff效果应用到资源初始值上"""
    r = dict(resources_dict)
    for bid in buff_ids:
        buff = BUFF_MAP.get(bid)
        if not buff:
            continue
        fx = buff["effects"]
        if "prestige" in fx:
            r["prestige"] = min(100, r.get("prestige", 30) + fx["prestige"])
        if "troops_mult" in fx:
            r["troops"] = int(r.get("troops", 10000) * fx["troops_mult"])
        if "gold_mult" in fx:
            r["gold"] = int(r.get("gold", 1000) * fx["gold_mult"])
        if "food_mult" in fx:
            r["food"] = int(r.get("food", 5000) * fx["food_mult"])
    return r
