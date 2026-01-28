# app/database/crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models
import uuid

def create_assessment(
    db: Session,
    image_path: str,
    pci_score: float,
    condition: str,
    analysis: str,
    location: Optional[str] = None
) -> models.Assessment:
    """Create new assessment"""
    
    assessment = models.Assessment(
        assessment_id=str(uuid.uuid4()),
        image_path=image_path,
        location=location,
        pci_score=pci_score,
        condition=condition,
        analysis=analysis
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment

def add_defects(
    db: Session,
    assessment_id: int,
    defects: List[dict]
) -> List[models.Defect]:
    """Add defects to assessment"""
    
    defect_records = []
    for defect in defects:
        defect_record = models.Defect(
            assessment_id=assessment_id,
            defect_type=defect['type'],
            severity=defect['severity'],
            confidence=defect['confidence'],
            bbox=defect['bbox'],
            area_pixels=defect.get('area_pixels', 0)
        )
        db.add(defect_record)
        defect_records.append(defect_record)
    
    db.commit()
    return defect_records

def get_assessment(db: Session, assessment_id: str) -> Optional[models.Assessment]:
    """Get assessment by ID"""
    return db.query(models.Assessment).filter(
        models.Assessment.assessment_id == assessment_id
    ).first()

def add_chat_message(
    db: Session,
    assessment_id: int,
    session_id: str,
    role: str,
    content: str
) -> models.ChatMessage:
    """Add chat message"""
    
    message = models.ChatMessage(
        assessment_id=assessment_id,
        session_id=session_id,
        role=role,
        content=content
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_chat_history(
    db: Session,
    session_id: str,
    limit: int = 20
) -> List[models.ChatMessage]:
    """Get chat history for session"""
    return db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session_id
    ).order_by(models.ChatMessage.created_at).limit(limit).all()