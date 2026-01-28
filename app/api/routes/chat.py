# app/api/routes/chat.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.database import get_db
from app.database import crud
from app.agents.graph import chat_graph

router = APIRouter()

# Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    assessment_id: str
    question: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    messages: List[ChatMessage]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assessment(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat about a specific pavement assessment
    
    **Features:**
    - Answer questions about PCI score, defects, costs
    - Provide repair recommendations
    - Explain technical details
    - Multi-turn conversation support
    """
    
    # Get assessment from database
    assessment = crud.get_assessment(db, request.assessment_id)
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Create or use existing session
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get chat history
    chat_history = crud.get_chat_history(db, session_id)
    
    # Convert to LangChain messages
    from langchain_core.messages import HumanMessage, AIMessage
    messages = []
    for msg in chat_history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
    
    print(f"\n💬 Chat - Session: {session_id[:8]}...")
    print(f"   Question: {request.question}")
    
    try:
        # Prepare detections
        detections = [
            {
                'type': d.defect_type,
                'severity': d.severity,
                'confidence': d.confidence,
                'bbox': d.bbox,
                'area_pixels': d.area_pixels
            } for d in assessment.defects
        ]
        
        # Run chat graph
        result = chat_graph.invoke({
            "assessment_id": request.assessment_id,
            "pci_score": assessment.pci_score,
            "condition": assessment.condition,
            "detections": detections,
            "messages": messages,
            "user_question": request.question,
            "response": ""
        })
        
        # Save messages to database
        crud.add_chat_message(
            db=db,
            assessment_id=assessment.id,
            session_id=session_id,
            role="user",
            content=request.question
        )
        
        crud.add_chat_message(
            db=db,
            assessment_id=assessment.id,
            session_id=session_id,
            role="assistant",
            content=result["response"]
        )
        
        print(f"   ✅ Response generated")
        
        # Build response
        response_messages = [
            ChatMessage(
                role="user" if isinstance(msg, HumanMessage) else "assistant",
                content=msg.content
            ) for msg in result.get("messages", [])
        ]
        
        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            messages=response_messages
        )
        
    except Exception as e:
        print(f"   ❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get chat history for a session"""
    
    messages = crud.get_chat_history(db, session_id)
    
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            } for msg in messages
        ]
    }