import asyncio
import sys
from game.state import GameState, init_game_state
from game.ministers import DEFAULT_MINISTERS
from ai.minister_agent import MinisterAgent

async def test_minister_bingzou():
    """测试大臣禀报功能"""
    try:
        print("初始化游戏状态...")
        state = init_game_state(
            ruler_name="刘备",
            ministers_data=DEFAULT_MINISTERS
        )
        print(f"游戏状态初始化成功")
        print(f"大臣数量: {len(state.ministers)}")
        
        for mid, minister in state.ministers.items():
            print(f"  - {minister.name} ({mid})")
        
        # 测试第一位大臣禀报
        print("\n测试内政大臣禀报...")
        agent = MinisterAgent(state.ministers["internal"], state)
        reply = await agent.bingzou()
        
        print(f"\n禀报内容:\n{reply}")
        print("\n测试成功！")
        
    except Exception as e:
        print(f"\n测试失败: {type(e).__name__}")
        print(f"错误信息: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minister_bingzou())
