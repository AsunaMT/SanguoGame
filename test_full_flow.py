import asyncio
from game.state import GameState, Resources
from game.ministers import MINISTER_CANDIDATES, build_minister, CANDIDATE_MAP
from game.map_data import build_initial_territories, build_initial_diplomacy
from ai.minister_agent import MinisterAgent

async def test_full_chat_flow():
    """完整测试聊天流程"""
    try:
        print("1. 初始化游戏状态...")
        state = GameState(
            ruler_name="刘备",
            resources=Resources(),
            territories=build_initial_territories(),
            diplomacy=build_initial_diplomacy(),
            ministers={
                "internal": build_minister("chen_bowen"),
                "military": build_minister("zhao_tianlie"),
                "diplomacy": build_minister("su_wenjing")
            },
        )
        print(f"   游戏状态初始化成功")
        print(f"   大臣: {list(state.ministers.keys())}")
        
        print("\n2. 创建大臣代理...")
        agent = MinisterAgent(state.ministers["internal"], state)
        print(f"   代理创建成功")
        
        print("\n3. 测试大臣禀报...")
        reply = await agent.bingzou()
        print(f"   禀报成功！")
        print(f"   内容长度: {len(reply)} 字符")
        print(f"   内容: {reply[:100]}...")
        
        print("\n4. 测试议事对话...")
        reply = await agent.respond("你好", phase="yishi")
        print(f"   对话成功！")
        print(f"   响应长度: {len(reply)} 字符")
        print(f"   内容: {reply[:100]}...")
        
        print("\n所有测试通过！")
        
    except Exception as e:
        print(f"\n错误: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_chat_flow())
