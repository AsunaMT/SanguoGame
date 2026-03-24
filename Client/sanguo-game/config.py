"""全局配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 无论从哪个目录启动，都能找到项目根目录的 .env
_BASE_DIR = Path(__file__).parent
load_dotenv(_BASE_DIR / ".env")

# Gemini API
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "\n\n❌ 未配置 GEMINI_API_KEY！\n"
        f"请在 {_BASE_DIR / '.env'} 中写入：\n"
        "GEMINI_API_KEY=AIza你的key\n"
        "免费申请：https://aistudio.google.com/apikey\n"
    )

# 模型配置（Gemini 2.0 Flash 免费额度充足）
MINISTER_MODEL: str = "gemini-2.0-flash"
NARRATOR_MODEL: str = "gemini-2.0-flash"
PARSER_MODEL:   str = "gemini-2.0-flash"

# 游戏参数
MAX_HISTORY_ROUNDS: int = 10
SAVE_DIR: str = "saves"
DEFAULT_SAVE_FILE: str = "saves/gamestate.json"

# FastAPI
CORS_ORIGINS: list = ["*"]
