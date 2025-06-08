from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "SBEKMS Backend API"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv('DEBUG') == 'True'
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Triplestore Settings
    TRIPLESTORE_URL: str = "http://localhost:7200"
    TRIPLESTORE_REPOSITORY: str = "sbekms"
    TRIPLESTORE_USERNAME: Optional[str] = None
    TRIPLESTORE_PASSWORD: Optional[str] = None
    
    # File Upload Settings
    UPLOAD_DIR: str = "data/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".py", ".js", ".ts", ".java", ".cpp", ".c", ".jsx", ".tsx",
        ".md", ".txt", ".rst", ".json", ".yml", ".yaml", ".toml",
        ".css", ".scss", ".svg", ".png", ".jpg", ".jpeg"
    ]
    
    # Ontology Settings
    ONTOLOGY_PATH: str = "data/ontologies/skms_ontology.owl"
    WDO_NAMESPACE: str = "http://purl.example.org/web_dev_km_bfo#"
    INSTANCE_NAMESPACE: str = "http://sbekms.example.org/instances/"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True) 