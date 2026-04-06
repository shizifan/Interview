from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/ai_interviewer.db"
    UPLOAD_DIR: str = "./uploads"
    LOG_DIR: str = "./logs"
    AI_SERVICE_MODE: str = "mock"  # "mock" | "real"

    # LLM (Qwen3-235B, OpenAI-compatible)
    LLM_API_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "Qwen3-235B"
    LLM_TIMEOUT: int = 60
    LLM_MAX_TOKENS: int = 2048

    # OCR / Vision (Qwen2-VL-72B, OpenAI Vision-compatible)
    OCR_API_URL: str = ""
    OCR_API_KEY: str = ""
    OCR_MODEL: str = "Qwen2-VL-72B"
    OCR_TIMEOUT: int = 30

    # DashScope (ASR + TTS)
    DASHSCOPE_API_KEY: str = ""
    ASR_MODEL: str = "paraformer-v2"
    TTS_MODEL: str = "cosyvoice-v2"
    TTS_VOICE: str = "longxiaochun"
    TTS_FORMAT: str = "wav"

    MAX_DAILY_INTERVIEWS: int = 3
    MAX_FOLLOW_UP_COUNT: int = 2
    ANSWER_TIMEOUT_SECONDS: int = 30
    INTERVIEW_RECOVERY_HOURS: int = 24
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
