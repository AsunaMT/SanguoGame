"""快速验证所有模块导入是否正常"""
import sys
sys.path.insert(0, '.')

try:
    from game.state import GameState, Minister, ConquestProgress, ImpactRecord
    print("OK: game.state")
except Exception as e:
    print(f"FAIL: game.state - {e}")

try:
    from game.ministers import MINISTER_CANDIDATES, build_minister, CANDIDATE_MAP
    print(f"OK: game.ministers - {len(MINISTER_CANDIDATES)} candidates")
    m = build_minister(MINISTER_CANDIDATES[0]["id"])
    print(f"  Built: {m.name}, hidden_trait={m.hidden.hidden_trait}, stats.wuli={m.stats.wuli}")
except Exception as e:
    print(f"FAIL: game.ministers - {e}")

try:
    from game.court import next_phase, get_random_scene_event, PHASE_DISPLAY
    print(f"OK: game.court - phases: {list(PHASE_DISPLAY.keys())}")
except Exception as e:
    print(f"FAIL: game.court - {e}")

try:
    from game.map_data import build_initial_territories, build_initial_diplomacy, TERRITORY_POSITIONS
    territories = build_initial_territories()
    print(f"OK: game.map_data - {len(territories)} territories")
except Exception as e:
    print(f"FAIL: game.map_data - {e}")

try:
    from game.world import process_week
    print("OK: game.world")
except Exception as e:
    print(f"FAIL: game.world - {e}")

try:
    from ai.minister_agent import MinisterAgent, calculate_speech_impact, check_betrayal_conditions
    print("OK: ai.minister_agent")
except Exception as e:
    print(f"FAIL: ai.minister_agent - {e}")

try:
    from ai.world_narrator import parse_orders, narrate_week
    print("OK: ai.world_narrator")
except Exception as e:
    print(f"FAIL: ai.world_narrator - {e}")

try:
    from api.routes_court import router as court_router
    print("OK: api.routes_court")
except Exception as e:
    print(f"FAIL: api.routes_court - {e}")

try:
    from api.routes_setup import router as setup_router
    print("OK: api.routes_setup")
except Exception as e:
    print(f"FAIL: api.routes_setup - {e}")

try:
    from api.routes_world import router as world_router
    print("OK: api.routes_world")
except Exception as e:
    print(f"FAIL: api.routes_world - {e}")

try:
    from api.routes_menu import router as menu_router
    print("OK: api.routes_menu")
except Exception as e:
    print(f"FAIL: api.routes_menu - {e}")

print("\n--- All imports tested ---")
