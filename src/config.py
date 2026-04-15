from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class DBSettings(BaseModel):
    DATABASE_URL: str
    ECHO: bool = False

    USER: str
    PASSWORD: str


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "src" / "certs" / "private.pem"
    public_key_path: Path = BASE_DIR / "src" / "certs" / "public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 43_200


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    api_v1_prefix: str = "/api/v1"

    db: DBSettings
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()
