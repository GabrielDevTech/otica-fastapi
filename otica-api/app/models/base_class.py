"""Classe base para models."""
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class BaseModel(Base):
    """Classe base abstrata para models com campos comuns."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

