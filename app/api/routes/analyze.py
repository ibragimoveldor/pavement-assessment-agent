# app/api/routes/analyze.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import shutil
from pathlib import Path
import uuid

from app.database import get_db
from app.database import crud
from app.agents.graph import assessment_graph
from app.config import settings

router = APIRouter()

# Create upload directory
Path(settings.upload_dir).mkdir(exist_ok=True)

# Response models
class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class Defection(BaseModel):
    type: str
    severity: str
    confidence: float
    bbox: BoundingBox
    area_pixels: float

class AssessmentResponse(BaseModel):
    assessment_id: str
    pci_score: float
    condition: str
    total_defects: int
    detections: List[Defection]
    analysis: str
    recommendations: List[str]
    image_url: str
    annotated_image_url: Optional[str]

@router.post("/analyze", response_model=AssessmentResponse)
async def analyze_pavement(
    file: UploadFile = File(...),
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze pavement image and return PCI score with AI analysis
    
    **Process:**
    1. Upload image
    2. Run YOLO detection
    3. Calculate PCI score
    4. Generate AI analysis with AWS Bedrock
    5. Save to database
    6. Return results
    """
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique ID
    assessment_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_extension = Path(file.filename).suffix
    filename = f"{assessment_id}{file_extension}"
    file_path = Path(settings.upload_dir) / filename
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Processing Assessment: {assessment_id}")
    print(f"{'='*60}")
    
    try:
        # Run LangGraph workflow
        result = assessment_graph.invoke({
            "image_path": str(file_path),
            "detections": [],
            "annotated_image_path": "",
            "pci_score": 0.0,
            "condition": "",
            "analysis": "",
            "recommendations": [],
            "messages": [],
            "error": ""
        })
        
        # Check for errors
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Save to database
        assessment = crud.create_assessment(
            db=db,
            image_path=str(file_path),
            pci_score=result["pci_score"],
            condition=result["condition"],
            analysis=result["analysis"],
            location=location
        )
        
        # Save defects
        if result["detections"]:
            crud.add_defects(
                db=db,
                assessment_id=assessment.id,
                defects=result["detections"]
            )
        
        print(f"✅ Assessment complete: PCI {result['pci_score']}")
        print(f"{'='*60}\n")
        
        # Build response
        return AssessmentResponse(
            assessment_id=assessment.assessment_id,
            pci_score=result["pci_score"],
            condition=result["condition"],
            total_defects=len(result["detections"]),
            detections=[
                Defection(
                    type=d["type"],
                    severity=d["severity"],
                    confidence=d["confidence"],
                    bbox=BoundingBox(**d["bbox"]),
                    area_pixels=d["area_pixels"]
                ) for d in result["detections"]
            ],
            analysis=result["analysis"],
            recommendations=result["recommendations"],
            image_url=f"/uploads/{filename}",
            annotated_image_url=f"/api/v1/uploads/annotated/{assessment_id}_annotated.jpg"
 
                if result.get("annotated_image_path") else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Serve uploaded images"""
    file_path = Path(settings.upload_dir) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@router.get("/uploads/annotated/{filename}")
async def get_annotated_file(filename: str):
    """Serve annotated images"""
    file_path = Path(settings.upload_dir) / "annotated" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@router.get("/assessment/{assessment_id}")
async def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Get assessment by ID"""
    assessment = crud.get_assessment(db, assessment_id)
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return {
        "assessment_id": assessment.assessment_id,
        "pci_score": assessment.pci_score,
        "condition": assessment.condition,
        "analysis": assessment.analysis,
        "location": assessment.location,
        "created_at": assessment.created_at.isoformat(),
        "defects": [
            {
                "type": d.defect_type,
                "severity": d.severity,
                "confidence": d.confidence,
                "bbox": d.bbox
            } for d in assessment.defects
        ]
    }