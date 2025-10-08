"""
Configuración principal de la aplicación SAVI
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Aplicación
    APP_NAME: str = "SAVI API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Base de datos
    DATABASE_URL: str = "sqlite:///./savi.db"
    
    # Seguridad
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Zona horaria
    TIMEZONE: str = "America/Mexico_City"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte CORS_ORIGINS string a lista"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
