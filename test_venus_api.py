import asyncio
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MINISTER_MODEL

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

async def test_api_call():
    try:
        # 模拟同步调用
        print("测试同步调用...")
        response = client.chat.completions.create(
            model=MINISTER_MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print(f"同步调用成功: {response.choices[0].message.content}")
        
        # 模拟异步调用（代码中的方式）
        print("\n测试异步调用...")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=MINISTER_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
        )
        print(f"异步调用成功: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_call())
