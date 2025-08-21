# app/config.py
import os
from typing import List, Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Evolution API
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    EVOLUTION_INSTANCE: str = os.getenv("EVOLUTION_INSTANCE", "bd-specialist")
    
    # External Services
    STT_SERVICE_URL: str = os.getenv("STT_SERVICE_URL", "http://localhost:8001/v1")
    TTS_SERVICE_URL: str = os.getenv("TTS_SERVICE_URL", "http://localhost:8002/api/tts")
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")  # openrouter, openai, gemini
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Default LLM Models
    DEFAULT_LLM_MODEL: str = "google/gemini-pro"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Database Configurations
    # MySQL
    MYSQL_HOST: Optional[str] = os.getenv("MYSQL_HOST")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER: Optional[str] = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: Optional[str] = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE: Optional[str] = os.getenv("MYSQL_DATABASE")
    
    # PostgreSQL
    POSTGRES_HOST: Optional[str] = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DATABASE: Optional[str] = os.getenv("POSTGRES_DATABASE")
    
    # Supabase
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Oracle
    ORACLE_HOST: Optional[str] = os.getenv("ORACLE_HOST")
    ORACLE_PORT: int = int(os.getenv("ORACLE_PORT", 1521))
    ORACLE_USER: Optional[str] = os.getenv("ORACLE_USER")
    ORACLE_PASSWORD: Optional[str] = os.getenv("ORACLE_PASSWORD")
    ORACLE_SERVICE_NAME: Optional[str] = os.getenv("ORACLE_SERVICE_NAME")
    
    # SQL Server
    SQLSERVER_HOST: Optional[str] = os.getenv("SQLSERVER_HOST")
    SQLSERVER_PORT: int = int(os.getenv("SQLSERVER_PORT", 1433))
    SQLSERVER_USER: Optional[str] = os.getenv("SQLSERVER_USER")
    SQLSERVER_PASSWORD: Optional[str] = os.getenv("SQLSERVER_PASSWORD")
    SQLSERVER_DATABASE: Optional[str] = os.getenv("SQLSERVER_DATABASE")
    
    # Security Settings
    MAX_QUERY_EXECUTION_TIME: int = 30  # seconds
    ALLOWED_OPERATIONS: List[str] = ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]
    RESTRICTED_OPERATIONS: List[str] = ["INSERT", "UPDATE", "CREATE", "ALTER"]
    FORBIDDEN_OPERATIONS: List[str] = ["DELETE", "DROP", "TRUNCATE"]
    
    # Audio Settings
    MAX_AUDIO_SIZE_MB: int = 25
    SUPPORTED_AUDIO_FORMATS: List[str] = [".mp3", ".wav", ".ogg", ".m4a"]
    
    # TTS Settings
    DEFAULT_VOICE: str = "pt_BR-faber-medium"
    TTS_SPEED: float = 1.0
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
