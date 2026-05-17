import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_PRO_MODEL: str = "deepseek-chat"
    DEEPSEEK_FLASH_MODEL: str = "deepseek-chat"  # Flash uses same base, differentiated by max_tokens/temperature
    DEEPSEEK_API_BASE_URL: str = "https://api.deepseek.com"

    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_MODEL: str = "qwen-plus"
    QWEN_API_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "ai_music.db")
    OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


settings = Settings()
