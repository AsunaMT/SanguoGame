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
            "traits": ["老成持重", "精打细算", "话不多"],
            "speech_style": "说话简单直接，喜欢用数字说明问题，偶尔引用经验，语气稳重",
            "values": ["求稳", "民生", "仓库要满"],
            "dislikes": ["冒进", "打仗", "空谈"],
        },
        "background": "当了二十年县令，工作做得好，账目清楚，税收从来没缺过。不太会说话，但做事稳重，百姓很信任。",
        "special_ability": "精打细算：每周税收+10%，叛乱-30%",
        "ability_effect": {"tax_bonus": 0.10, "rebellion_reduce": 0.30},
    },
    {
        "id": "lin_xiaoshuang",
        "name": "林晓霜",
        "courtesy_name": "清源",
        "role": "internal",
        "personality": {
            "traits": ["温和务实", "关心百姓", "细心"],
            "speech_style": "语气亲切，用词简单，喜欢打比方，经常从百姓角度说事",
            "values": ["以民为本", "仁政", "休养生息"],
            "dislikes": ["苛捐杂税", "打仗", "随意开战"],
        },
        "background": "普通家庭出身，小时候经历过饥荒，知道老百姓的苦。用种地的办法让流民安顿下来，名气慢慢传开了。",
        "special_ability": "安抚百姓：每周人口增长+8%，军粮消耗-10%",
        "ability_effect": {"pop_growth": 0.08, "food_consume_reduce": 0.10},
    },
    # 军事方向
    {
        "id": "zhao_tianlie",
        "name": "赵天烈",
        "courtesy_name": "奉先",
        "role": "military",
        "personality": {
            "traits": ["勇猛", "纪律严明", "嫉恶如仇"],
            "speech_style": "说话干脆，直来直去，喜欢用打仗的例子，有时候太直",
            "values": ["忠诚", "铁的纪律", "开疆拓土"],
            "dislikes": ["胆小", "犹豫不决", "享乐"],
        },
        "background": "西凉的老将，打了一百多次仗，曾经带着五百骑兵打败敌人一万人。管军队严格，没人不听他的。",
        "special_ability": "铁血部队：战斗力+20%，但粮草消耗+15%",
        "ability_effect": {"combat_bonus": 0.20, "food_consume_extra": 0.15},
    },
    {
        "id": "han_shouyi",
        "name": "韩守义",
        "courtesy_name": "信之",
        "role": "military",
        "personality": {
            "traits": ["稳重", "看得远", "不骄不躁"],
            "speech_style": "条理清楚，喜欢推演，经常引用兵法，语气沉稳，有时有点啰嗦",
            "values": ["看清形势", "先防守后进攻", "了解敌人"],
            "dislikes": ["鲁莽", "赌博式行动"],
        },
        "background": "兵法世家，熟读兵书，擅长守城布阵。他爸爸曾经守一座城三年没被攻破，韩守义比他爸爸更强。",
        "special_ability": "防守专家：防御+25%，可以预判敌人动向",
        "ability_effect": {"defense_bonus": 0.25, "intel_enemy_moves": True},
    },
    # 外交方向
    {
        "id": "su_wenjing",
        "name": "苏文镜",
        "courtesy_name": "长卿",
        "role": "diplomacy",
        "personality": {
            "traits": ["圆滑", "能说", "会看人"],
            "speech_style": "说话流利，喜欢打比方，话里有话，笑着算计",
            "values": ["实用", "利益优先", "灵活"],
            "dislikes": ["死板", "因小失大"],
        },
        "background": "到处游学了十几年，认识很多诸侯的谋士，曾经凭一张嘴让两个国家停止打仗。善于搞外交。",
        "special_ability": "外交手段：结盟成功率+30%，可以刺探情报",
        "ability_effect": {"alliance_chance": 0.30, "can_spy": True},
    },
    {
        "id": "fang_zhengyan",
        "name": "方正言",
        "courtesy_name": "直卿",
        "role": "diplomacy",
        "personality": {
            "traits": ["正直", "讲礼仪", "守信用"],
            "speech_style": "说话认真，偶尔引经据典，用词正式，不说假话，但有时太死板",
            "values": ["忠义", "礼法", "汉室正统"],
            "dislikes": ["阴谋", "背叛", "不讲规矩"],
        },
        "background": "汉室忠臣的后代，从小就学礼仪，因为讲信用在各诸侯中很有名。曾经拒绝曹操的高官厚禄，名声很好。",
        "special_ability": "清名高义：声望+20%，但不能用间谍",
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
