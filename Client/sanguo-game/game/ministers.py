"""大臣系统 — 候选人池 & 人格定义"""
from typing import List, Dict, Any
from game.state import Minister, MinisterPersonality

# ─── 候选大臣数据 ─────────────────────────────────────────────
MINISTER_CANDIDATES: List[Dict[str, Any]] = [
    # 内政方向
    {
        "id": "chen_bowen",
        "name": "陈伯文",
        "courtesy_name": "仲达",
        "role": "internal",
        "personality": {
            "traits": ["老成持重", "精于算计", "沉默寡言"],
            "speech_style": "言简意赅，多用数字佐证，偶引古语，语气平稳不失威重",
            "values": ["稳健", "民生", "仓廪充实"],
            "dislikes": ["冒进", "穷兵黩武", "空谈"],
        },
        "background": "曾任县令二十年，治绩卓著，户籍清明，粮税从无亏空。不善辞令，但处事稳妥，深得百姓信赖。",
        "special_ability": "精打细算：每周税收+10%，治下叛乱概率-30%",
        "ability_effect": {"tax_bonus": 0.10, "rebellion_reduce": 0.30},
    },
    {
        "id": "lin_xiaoshuang",
        "name": "林晓霜",
        "courtesy_name": "清源",
        "role": "internal",
        "personality": {
            "traits": ["温和务实", "体恤民情", "细心周到"],
            "speech_style": "语调柔和，措辞亲切，善用比喻，常以百姓疾苦作论据",
            "values": ["民本", "仁政", "休养生息"],
            "dislikes": ["苛政", "横征暴敛", "轻启战端"],
        },
        "background": "寒门出身，幼时亲历饥荒，深知民间疾苦。以一手农桑之策令流民归附，声名渐著。",
        "special_ability": "抚民安邦：每周人口增长+8%，军粮消耗-10%",
        "ability_effect": {"pop_growth": 0.08, "food_consume_reduce": 0.10},
    },
    # 军事方向
    {
        "id": "zhao_tianlie",
        "name": "赵天烈",
        "courtesy_name": "奉先",
        "role": "military",
        "personality": {
            "traits": ["刚烈勇猛", "令行禁止", "嫉恶如仇"],
            "speech_style": "语气铿锵，直言无忌，善用军旅比喻，有时过于直白",
            "values": ["忠勇", "铁律", "开疆拓土"],
            "dislikes": ["怯懦", "优柔寡断", "偷安享乐"],
        },
        "background": "西凉旧将，身经百战，曾率五百骑击溃敌方万人。治军严明，麾下无有不从。",
        "special_ability": "铁血雄师：军队战斗力+20%，但粮草消耗+15%",
        "ability_effect": {"combat_bonus": 0.20, "food_consume_extra": 0.15},
    },
    {
        "id": "han_shouyi",
        "name": "韩守义",
        "courtesy_name": "信之",
        "role": "military",
        "personality": {
            "traits": ["稳重谨慎", "深谋远虑", "不骄不躁"],
            "speech_style": "条理清晰，多用推演，喜引兵法，语气沉稳，偶显迂腐",
            "values": ["审时度势", "以守待攻", "知己知彼"],
            "dislikes": ["鲁莽冒进", "赌国运"],
        },
        "background": "兵法世家出身，熟读孙吴，精于守城布阵。其父曾守一城三年不失，韩守义青出于蓝。",
        "special_ability": "坚壁清野：防御+25%，可预判敌方行动方向",
        "ability_effect": {"defense_bonus": 0.25, "intel_enemy_moves": True},
    },
    # 外交方向
    {
        "id": "su_wenjing",
        "name": "苏文镜",
        "courtesy_name": "长卿",
        "role": "diplomacy",
        "personality": {
            "traits": ["机智圆滑", "能言善辩", "洞察人心"],
            "speech_style": "口若悬河，善用典故，语中常藏深意，笑里不失算计",
            "values": ["实用", "利益为先", "灵活变通"],
            "dislikes": ["迂腐固执", "因小失大"],
        },
        "background": "游学天下十余载，遍识诸侯幕僚，曾凭三寸不烂之舌使两国罢兵。善于纵横捭阖。",
        "special_ability": "纵横之术：结盟成功率+30%，可刺探敌方情报",
        "ability_effect": {"alliance_chance": 0.30, "can_spy": True},
    },
    {
        "id": "fang_zhengyan",
        "name": "方正言",
        "courtesy_name": "直卿",
        "role": "diplomacy",
        "personality": {
            "traits": ["正直刚烈", "恪守礼仪", "一诺千金"],
            "speech_style": "字正腔圆，引经据典，措辞庄重，绝无虚言，但有时失于迂阔",
            "values": ["忠义", "礼法", "汉室正统"],
            "dislikes": ["阴谋诡计", "背信弃义", "僭越礼制"],
        },
        "background": "汉室忠臣之后，自幼习礼，以信义闻名于诸侯。曾拒曹操厚礼而不仕，清名远播。",
        "special_ability": "清名高义：声望+20%，但无法使用间谍手段",
        "ability_effect": {"prestige_bonus": 0.20, "no_spy": True},
    },
]

CANDIDATE_MAP: Dict[str, Dict[str, Any]] = {c["id"]: c for c in MINISTER_CANDIDATES}


def build_minister(candidate_id: str) -> Minister:
    """从候选人数据构建 Minister 对象"""
    data = CANDIDATE_MAP[candidate_id]
    return Minister(
        id=data["id"],
        name=data["name"],
        courtesy_name=data["courtesy_name"],
        role=data["role"],
        personality=MinisterPersonality(**data["personality"]),
        background=data["background"],
        special_ability=data["special_ability"],
        ability_effect=data["ability_effect"],
    )


ROLE_NAMES: Dict[str, str] = {
    "internal": "内政大臣",
    "military": "军事大臣",
    "diplomacy": "外交大臣",
}
