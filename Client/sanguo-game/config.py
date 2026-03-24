"""全局配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 无论从哪个目录启动，都能找到项目根目录的 .env
_BASE_DIR = Path(__file__).parent
load_dotenv(_BASE_DIR / ".env")

# Venus OpenAPI
_secret_id = os.getenv("ENV_VENUS_OPENAPI_SECRET_ID", "")
if not _secret_id:
    raise RuntimeError(
        "\n\n❌ 未配置 ENV_VENUS_OPENAPI_SECRET_ID！\n"
        f"请在 {_BASE_DIR / '.env'} 中写入：\n"
        "ENV_VENUS_OPENAPI_SECRET_ID=你的SecretID\n"
    )
VENUS_TOKEN: str = _secret_id + "@1"
VENUS_URL: str = "http://v2.open.venus.oa.com/llmproxy/chat/completions"

# 模型配置
MINISTER_MODEL: str = "qwen3.5-35b-a3b"
NARRATOR_MODEL: str = "qwen3.5-35b-a3b"
PARSER_MODEL:   str = "qwen3.5-35b-a3b"

# 游戏参数
MAX_HISTORY_ROUNDS: int = 10
SAVE_DIR: str = "saves"
DEFAULT_SAVE_FILE: str = "saves/gamestate.json"

# FastAPI
CORS_ORIGINS: list = ["*"]
