from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELE_BOT_TOKEN: str
    TELE_API_APP_ID: str
    TELE_API_APP_HASH: str


settings = Settings(_env_file=".env")