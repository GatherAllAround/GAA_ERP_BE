from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/gaa_db"

    # Kakao OAuth
    kakao_client_id: str = ""
    kakao_redirect_uri: str = ""
    kakao_client_secret: str = ""

    # JWT
    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7일

    model_config = {"env_file": ".env"}


settings = Settings()
