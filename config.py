import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Discord
    TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "")
    GUILD_ID: str = os.getenv("GUILD_ID", "")
    SELFBOT_TOKEN: str = os.getenv("SELFBOT_TOKEN", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # API
    API_PORT: int = int(os.getenv("API_PORT", "3000"))
    API_ENABLED: bool = os.getenv("API_ENABLED", "false").lower() == "true"
    API_KEY: str = os.getenv("API_KEY", "")

    # App
    NODE_ENV: str = os.getenv("NODE_ENV", "development")
    OWNER_IDS: list[str] = [
        i.strip() for i in os.getenv("OWNER_IDS", "").split(",") if i.strip()
    ]
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "debug")

    # Whitelist
    WHITELIST_ENABLED: bool = os.getenv("WHITELIST_ENABLED", "true").lower() == "true"

    @property
    def is_dev(self) -> bool:
        return self.NODE_ENV == "development"

    @property
    def is_owner(self) -> str:
        return self.OWNER_IDS[0] if self.OWNER_IDS else ""


config = Config()
