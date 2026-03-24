"""世界模拟引擎 — 每周结算逻辑"""
from __future__ import annotations
import random
from typing import List, Dict, Any, Tuple

from game.state import GameState, WeekResult, Territory
from game.events import HISTORY_EVENTS, EVENT_MAP
from game.buffs import BUFF_MAP


# ─── 命令动作定义 ─────────────────────────────────────────────
ACTION_COSTS: Dict[str, Dict[str, int]] = {
    "train_troops": {"food": 200, "gold": 100},
    "recruit": {"gold": 300, "food": 100},
    "diplomacy_gift": {"gold": 500},
    "build_farm": {"gold": 400},
    "build_walls": {"gold": 600},
    "spy": {"gold": 200},
    "rest": {},
}


def apply_orders(state: GameState, structured_orders: List[Dict]) -> List[str]:
    """执行玩家命令，返回结果描述列表"""
    results = []
    r = state.resources
    for order in structured_orders:
        action = order.get("action", "")
        amount = order.get("amount", 0)
        cost = ACTION_COSTS.get(action, {})

        # 检查资源是否足够
        enough = all(
            getattr(r, res, 0) >= cost.get(res, 0)
            for res in cost
        )
        if not enough:
            results.append(f"【命令失败】{action}：资源不足")
            continue

        # 扣除资源
        for res, val in cost.items():
            setattr(r, res, getattr(r, res) - val)

        # 执行效果
        if action == "train_troops":
            r.troops += amount or 1000
            results.append(f"训练兵马{amount or 1000}，军备充实")
        elif action == "recruit":
            r.troops += amount or 500
            results.append(f"征募士卒{amount or 500}，兵力增加")
        elif action == "diplomacy_gift":
            target = order.get("target", "")
            if target in state.diplomacy:
                state.diplomacy[target].relation = min(100, state.diplomacy[target].relation + 15)
                results.append(f"馈赠{target}，关系改善")
        elif action == "build_farm":
            r.food += 800
            results.append("开垦农田，增产粮食")
        elif action == "build_walls":
            results.append("修筑城防，工事加固")
        elif action == "spy":
            results.append("遣派细作，刺探情报")
        elif action == "rest":
            r.food += 200
            results.append("休养生息，民心渐安")

    return results


def check_events(state: GameState) -> List[Dict[str, Any]]:
    """检查本周是否触发历史事件"""
    triggered = []
    for event in HISTORY_EVENTS:
        if event["id"] in state.history_log:
            continue
        if state.turn == event["trigger_turn"]:
            triggered.append(event)
            state.history_log.append(event["id"])

            # 确定结果
            outcome = event["default_outcome"]
            modifiers = event.get("player_modifiers", {})

            # 检查玩家行为modifier
            for mod_key, mod_val in modifiers.items():
                if mod_key.startswith("alliance_"):
                    faction = mod_key.replace("alliance_", "")
                    rel = state.diplomacy.get(faction)
                    if rel and rel.alliance:
                        outcome = mod_val
                        break

            # 应用领土变化
            changes = event.get("territory_changes", {}).get(outcome, [])
            for change in changes:
                for t in state.territories:
                    if t.id == change["territory"]:
                        t.owner = change["new_owner"]
                        break

    return triggered


def simulate_npcs(state: GameState) -> List[str]:
    """NPC诸侯简化行动决策"""
    actions = []
    player_power = state.resources.troops + state.resources.prestige * 100

    # 曹操策略：若玩家弱小，可能骚扰边境
    cao_rel = state.diplomacy.get("cao_cao")
    if cao_rel and not cao_rel.alliance:
        if player_power < 15000 and random.random() < 0.3:
            actions.append("曹操遣将南探，边境稍有摩擦")
            cao_rel.relation = max(-100, cao_rel.relation - 5)
        elif player_power > 50000 and random.random() < 0.2:
            actions.append("曹操遣使通好，似有结盟之意")
            cao_rel.relation = min(100, cao_rel.relation + 10)

    # 刘备策略：随历史进程
    liu_rel = state.diplomacy.get("liu_bei")
    if liu_rel and random.random() < 0.2:
        if liu_rel.relation > 30:
            actions.append("刘备遣简雍来访，共叙汉室复兴之志")
        else:
            actions.append("刘备忙于整军备战，无暇顾及")

    # 孙权策略
    sun_rel = state.diplomacy.get("sun_quan")
    if sun_rel and random.random() < 0.15:
        if sun_rel.alliance:
            actions.append("孙权水师巡江，联盟稳固")
        else:
            actions.append("江东细作西望，孙权似在观察局势")

    return actions


def update_resources(state: GameState) -> Dict[str, int]:
    """每周资源自然增减，返回变化量"""
    r = state.resources
    delta = {}

    # 税收
    tax_base = sum(t.population for t in state.territories if t.owner == "player")
    tax_income = int(tax_base * 0.002)  # 基础税率

    # buff加成
    for bid in state.buffs:
        buff = BUFF_MAP.get(bid)
        if buff:
            fx = buff["effects"]
            if "tax_bonus" in fx:
                tax_income = int(tax_income * (1 + fx["tax_bonus"]))
            if "gold_per_week" in fx:
                tax_income += fx["gold_per_week"]

    r.gold += tax_income
    delta["gold"] = tax_income

    # 军粮消耗
    food_consume = max(100, r.troops // 10)
    for bid in state.buffs:
        buff = BUFF_MAP.get(bid)
        if buff and "food_consume_reduce" in buff["effects"]:
            food_consume = int(food_consume * (1 - buff["effects"]["food_consume_reduce"]))

    r.food = max(0, r.food - food_consume)
    delta["food"] = -food_consume

    # 人口增长
    pop_growth_rate = 0.02
    for bid in state.buffs:
        buff = BUFF_MAP.get(bid)
        if buff and "pop_growth" in buff["effects"]:
            pop_growth_rate += buff["effects"]["pop_growth"]

    for t in state.territories:
        if t.owner == "player":
            growth = int(t.population * pop_growth_rate)
            t.population += growth

    # 声望自然衰减（少量）
    r.prestige = max(0, r.prestige - 1)

    return delta


def generate_date(turn: int) -> str:
    """根据周数生成日期文字"""
    year = 208 + (turn - 1) // 12
    month = ((turn - 1) % 12) + 1
    season_map = {
        1: "春", 2: "春", 3: "春",
        4: "夏", 5: "夏", 6: "夏",
        7: "秋", 8: "秋", 9: "秋",
        10: "冬", 11: "冬", 12: "冬",
    }
    return f"公元{year}年{season_map[month]}（{month}月）"


def process_week(state: GameState, orders: List[Dict]) -> Tuple[WeekResult, List[str]]:
    """
    执行一周结算。
    返回 (WeekResult, order_results)
    """
    # 1. 执行玩家命令
    order_results = apply_orders(state, orders)

    # 2. 检查触发历史事件
    triggered_events = check_events(state)
    triggered_titles = [e["title"] for e in triggered_events]

    # 3. NPC行动
    npc_actions = simulate_npcs(state)

    # 4. 资源自然增减
    delta = update_resources(state)

    # 5. 推进时间
    state.turn += 1
    state.date = generate_date(state.turn)
    state.week_orders = []

    # 6. 构建周报摘要（旁白AI将进一步润色）
    summary_parts = []
    if triggered_titles:
        summary_parts.append("【历史大事】" + "；".join(triggered_titles))
    if npc_actions:
        summary_parts.append("【天下动态】" + "；".join(npc_actions))
    if order_results:
        summary_parts.append("【我方动向】" + "；".join(order_results))
    summary_parts.append(
        f"【资源变化】金粮{delta.get('gold', 0):+d}，军粮{delta.get('food', 0):+d}"
    )

    raw_report = "\n".join(summary_parts)

    result = WeekResult(
        turn=state.turn - 1,
        report=raw_report,
        events=triggered_titles,
        resource_delta=delta,
    )
    return result, order_results
