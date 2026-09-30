import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "AgriGraph API"
    VERSION: str = "1.0.0"
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "agrigraph_db")
    USE_MOCK_FALLBACK: bool = True
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

settings = Settings()
