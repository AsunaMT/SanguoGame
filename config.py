"""全局配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 无论从哪个目录启动，都能找到项目根目录的 .env
_BASE_DIR = Path(__file__).parent
load_dotenv(_BASE_DIR / ".env")

# Venus API (腾讯内部)
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    raise RuntimeError(
        "\n\n❌ 未配置 VENUS_API_KEY！\n"
        f"请在 {_BASE_DIR / '.env'} 中写入：\n"
        "DEEPSEEK_API_KEY=你的Venus_Token\n"
    )

# 模型配置（使用 Venus Qwen）
MINISTER_MODEL: str = "qwen3.5-35b-a3b"
NARRATOR_MODEL: str = "qwen3.5-35b-a3b"
PARSER_MODEL:   str = "qwen3.5-35b-a3b"

# Venus API 配置
DEEPSEEK_BASE_URL: str = "http://v2.open.venus.oa.com/llmproxy"
DEEPSEEK_MAX_TOKENS: int = 2000
DEEPSEEK_TEMPERATURE: float = 0.8

# 游戏参数
MAX_HISTORY_ROUNDS: int = 10
SAVE_DIR: str = "saves"
DEFAULT_SAVE_FILE: str = "saves/gamestate.json"

# FastAPI
CORS_ORIGINS: list = ["*"]
