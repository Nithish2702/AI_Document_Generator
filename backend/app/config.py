"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase (Database + Storage)
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str
    DATABASE_URL: str
    
    # Google Gemini (LLM)
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-pro"
    
    # Application
    SECRET_KEY: str
    DEBUG: bool
    
    # File Storage - Local directories
    VECTOR_STORE_DIR: str
    UPLOAD_DIR: str = "./storage/uploads"
    GENERATED_DIR: str = "./storage/generated"
    
    # CORS
    ALLOWED_ORIGINS: str
    
    # Embedding
    EMBEDDING_MODEL: str
    EMBEDDING_DIMENSION: int
    
    # Server
    HOST: str
    PORT: int
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()
