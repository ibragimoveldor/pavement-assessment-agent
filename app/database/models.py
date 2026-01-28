# app/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Assessment(Base):
    """Pavement assessment record"""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String(36), unique=True, index=True)
    image_path = Column(String(500))
    location = Column(String(200), nullable=True)
    pci_score = Column(Float)
    condition = Column(String(50))
    analysis = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    defects = relationship("Defect", back_populates="assessment", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="assessment", cascade="all, delete-orphan")

class Defect(Base):
    """Detected defect"""
    __tablename__ = "defects"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    defect_type = Column(String(50))
    severity = Column(String(20))
    confidence = Column(Float)
    bbox = Column(JSON)  # {x, y, width, height}
    area_pixels = Column(Float)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="defects")

class ChatMessage(Base):
    """Chat history"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    session_id = Column(String(36))
    role = Column(String(20))  # user, assistant, system
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="chat_messages")