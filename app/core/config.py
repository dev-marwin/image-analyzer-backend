import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "images")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-4o-mini")
        self.thumbnail_size = int(os.getenv("THUMBNAIL_SIZE", "300"))
        self.max_tags = int(os.getenv("AI_TAG_COUNT", "8"))

    def validate(self) -> None:
        missing = []
        if not self.supabase_url or self.supabase_url.strip() == "":
            missing.append("SUPABASE_URL")
        if not self.supabase_service_key or self.supabase_service_key.strip() == "":
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if not self.supabase_anon_key or self.supabase_anon_key.strip() == "":
            missing.append("SUPABASE_ANON_KEY")
        if not self.openai_api_key or self.openai_api_key.strip() == "":
            missing.append("OPENAI_API_KEY")

        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file in the backend/ directory.\n"
                f"Current values: SUPABASE_URL={'set' if self.supabase_url else 'MISSING'}, "
                f"SUPABASE_SERVICE_ROLE_KEY={'set' if self.supabase_service_key else 'MISSING'}, "
                f"SUPABASE_ANON_KEY={'set' if self.supabase_anon_key else 'MISSING'}, "
                f"OPENAI_API_KEY={'set' if self.openai_api_key else 'MISSING'}"
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings

