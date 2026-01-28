# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./pavement_assessment.db"
    
    # Application
    upload_dir: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    
    # YOLO
    yolo_model_path: str = "/home/e/SISTech/GPR/PCI_agent/app/models/model/KCL_code_and_model/model_v5_3003.pt"
    
    # API
    api_title: str = "Pavement Assessment AI Agent"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()