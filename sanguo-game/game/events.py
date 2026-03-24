"""三国历史事件时间线"""
from typing import List, Dict, Any

HISTORY_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "liu_biao_death",
        "trigger_turn": 3,
        "title": "刘表病逝",
        "description": "荆州牧刘表病逝，其子刘琮继位，荆州人心惶惶。曹操大军随即南下。",
        "default_outcome": "cao_take_jingzhou",
        "player_modifiers": {
            # 若玩家已与刘表结盟，可选择协助刘琮或坐观
            "alliance_liu_biao": "assist_liuzong_choice",
        },
        "territory_changes": {
            "cao_take_jingzhou": [
                {"territory": "xiangyang", "new_owner": "cao_cao"},
            ]
        },
    },
    {
        "id": "chibi_battle",
        "trigger_turn": 8,
        "title": "赤壁之战",
        "description": "曹操率大军顺江东下，孙刘联军以火攻大破曹军于赤壁，曹操北撤。",
        "default_outcome": "sun_liu_win",
        "player_modifiers": {
            "alliance_sun_quan": "stronger_sun_liu",
            "alliance_cao_cao": "with_cao_army",
            "neutral": "watch_and_profit",
        },
        "territory_changes": {
            "sun_liu_win": [
                {"territory": "jiangling", "new_owner": "liu_bei"},
                {"territory": "柴桑", "new_owner": "sun_quan"},
            ],
            "with_cao_army": [
                {"territory": "jiangling", "new_owner": "cao_cao"},
            ],
        },
    },
    {
        "id": "liu_bei_jingzhou",
        "trigger_turn": 10,
        "title": "刘备借荆州",
        "description": "刘备向孙权借得荆州诸郡，势力大涨，开始谋取益州。",
        "default_outcome": "liu_bei_expands",
        "player_modifiers": {},
        "territory_changes": {
            "liu_bei_expands": [
                {"territory": "changsha", "new_owner": "liu_bei"},
            ]
        },
    },
    {
        "id": "liu_bei_yi_zhou",
        "trigger_turn": 20,
        "title": "刘备取益州",
        "description": "刘备趁益州内乱，夺取成都，益州牧刘璋投降。",
        "default_outcome": "liu_bei_shu",
        "player_modifiers": {},
        "territory_changes": {
            "liu_bei_shu": []   # 益州地图外，不影响荆州板块
        },
    },
    {
        "id": "guan_yu_northern",
        "trigger_turn": 30,
        "title": "关羽北伐，水淹七军",
        "description": "关羽率荆州军北伐，擒于禁、斩庞德，威震华夏，曹操几欲迁都。",
        "default_outcome": "guan_yu_peak",
        "player_modifiers": {
            "alliance_liu_bei": "assist_northern_expedition",
        },
        "territory_changes": {
            "guan_yu_peak": [
                {"territory": "wan_cheng", "new_owner": "liu_bei"},
            ]
        },
    },
    {
        "id": "jing_zhou_fall",
        "trigger_turn": 32,
        "title": "吕蒙白衣渡江，荆州易主",
        "description": "孙权遣吕蒙偷袭荆州，关羽腹背受敌，败走麦城，荆州归吴。",
        "default_outcome": "jingzhou_to_sun",
        "player_modifiers": {
            "alliance_sun_quan": "warned_in_advance",
            "alliance_liu_bei": "defend_jingzhou_failed",
        },
        "territory_changes": {
            "jingzhou_to_sun": [
                {"territory": "jiangling", "new_owner": "sun_quan"},
                {"territory": "fangling", "new_owner": "sun_quan"},
            ]
        },
    },
    {
        "id": "yi_ling_battle",
        "trigger_turn": 38,
        "title": "夷陵之战",
        "description": "刘备为报荆州之仇，亲率大军伐吴，陆逊火烧连营，蜀军大败。",
        "default_outcome": "shu_defeated",
        "player_modifiers": {
            "alliance_liu_bei": "join_shu_army",
            "alliance_sun_quan": "join_wu_defense",
        },
        "territory_changes": {},
    },
]

EVENT_MAP: Dict[str, Dict[str, Any]] = {e["id"]: e for e in HISTORY_EVENTS}
