# app/agents/graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict
import operator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.models.yolo_detector import PavementDetector
from app.models.pci_calculator import calculate_pci_score, generate_recommendations
from app.core.aws_bedrock import get_bedrock_client
from app.agents.tools import (
    get_defect_statistics,
    get_repair_cost_breakdown,
    get_priority_repairs,
    get_timeline_estimate,
    execute_sql_query,  # ← Add this
    analyze_query_intent  # ← Add this
)
from app.config import settings

# Define State
class AssessmentState(TypedDict):
    """State for assessment workflow"""
    # Input
    image_path: str
    
    # Detection results
    detections: List[Dict]
    annotated_image_path: str
    
    # PCI calculation
    pci_score: float
    condition: str
    
    # AI analysis
    analysis: str
    recommendations: List[str]
    
    # Messages for chat
    messages: Annotated[List, operator.add]
    
    # Error handling
    error: str

# Node functions
def detect_defects(state: AssessmentState) -> AssessmentState:
    """
    Node 1: Run YOLO detection on image
    """
    print("🔍 Running YOLO detection...")
    
    try:
        # Initialize detector
        detector = PavementDetector()
        
        # Run detection
        result = detector.detect(state["image_path"])
        
        print(f"   Found {result['total_defects']} defects")
        
        return {
            **state,
            "detections": result["detections"],
            "annotated_image_path": result.get("annotated_image_path", ""),
            "error": ""
        }
    
    except Exception as e:
        print(f"   ❌ Error in detection: {e}")
        return {
            **state,
            "detections": [],
            "annotated_image_path": "",
            "error": f"Detection failed: {str(e)}"
        }

def calculate_pci(state: AssessmentState) -> AssessmentState:
    """
    Node 2: Calculate PCI score from detections
    """
    print("📊 Calculating PCI score...")
    
    try:
        # Calculate PCI
        pci_result = calculate_pci_score(state["detections"])
        
        # Generate recommendations
        recommendations = generate_recommendations(
            pci_result["pci_score"],
            state["detections"]
        )
        
        print(f"   PCI Score: {pci_result['pci_score']}")
        print(f"   Condition: {pci_result['condition']}")
        
        return {
            **state,
            "pci_score": pci_result["pci_score"],
            "condition": pci_result["condition"],
            "recommendations": recommendations,
            "error": ""
        }
    
    except Exception as e:
        print(f"   ❌ Error in PCI calculation: {e}")
        return {
            **state,
            "pci_score": 0.0,
            "condition": "Unknown",
            "recommendations": [],
            "error": f"PCI calculation failed: {str(e)}"
        }

def analyze_with_ai(state: AssessmentState) -> AssessmentState:
    """
    Node 3: Analyze results with AWS Bedrock (Claude)
    """
    print("🤖 Analyzing with AI...")
    
    try:
        # Get Bedrock client
        bedrock = get_bedrock_client()
        
        # Analyze pavement
        analysis = bedrock.analyze_pavement(
            pci_score=state["pci_score"],
            detections=state["detections"]
        )
        
        print(f"   ✅ AI analysis complete")
        
        return {
            **state,
            "analysis": analysis,
            "error": ""
        }
    
    except Exception as e:
        print(f"   ⚠️  AI analysis skipped: {e}")
        # Fallback to rule-based analysis
        analysis = generate_fallback_analysis(
            state["pci_score"],
            state["detections"]
        )
        
        return {
            **state,
            "analysis": analysis,
            "error": ""
        }

def generate_fallback_analysis(pci_score: float, detections: List[Dict]) -> str:
    """
    Fallback analysis if AI is unavailable
    """
    analysis = f"**Pavement Assessment Report**\n\n"
    analysis += f"**Overall Condition:** PCI Score {pci_score}/100 - "
    
    if pci_score >= 85:
        analysis += "Excellent\n"
    elif pci_score >= 70:
        analysis += "Very Good\n"
    elif pci_score >= 55:
        analysis += "Good\n"
    elif pci_score >= 40:
        analysis += "Fair - Maintenance needed\n"
    else:
        analysis += "Poor - Urgent action required\n"
    
    analysis += f"\n**Defects Detected:** {len(detections)}\n\n"
    
    # Critical issues
    critical = [d for d in detections if d['severity'] == 'critical']
    if critical:
        analysis += f"**⚠️ CRITICAL ISSUES:** {len(critical)} critical defect(s) detected\n"
        for det in critical[:3]:
            analysis += f"  - {det['type']} at ({det['bbox']['x']}, {det['bbox']['y']})\n"
        analysis += "\n"
    
    # Recommendations
    analysis += "**Recommended Actions:**\n"
    if pci_score < 40:
        analysis += "  1. Immediate safety assessment required\n"
        analysis += "  2. Major rehabilitation within 30 days\n"
        analysis += "  3. Consider full reconstruction\n"
    elif pci_score < 70:
        analysis += "  1. Schedule corrective maintenance\n"
        analysis += "  2. Address high-severity defects within 60 days\n"
        analysis += "  3. Plan for re-assessment in 3 months\n"
    else:
        analysis += "  1. Routine preventive maintenance\n"
        analysis += "  2. Monitor condition quarterly\n"
        analysis += "  3. Address minor defects during next cycle\n"
    
    return analysis

# Create workflow graph
def create_assessment_graph():
    """
    Create LangGraph workflow for pavement assessment
    """
    # Initialize graph
    workflow = StateGraph(AssessmentState)
    
    # Add nodes
    workflow.add_node("detect", detect_defects)
    workflow.add_node("calculate_pci", calculate_pci)
    workflow.add_node("analyze", analyze_with_ai)
    
    # Define edges (workflow)
    workflow.set_entry_point("detect")
    workflow.add_edge("detect", "calculate_pci")
    workflow.add_edge("calculate_pci", "analyze")
    workflow.add_edge("analyze", END)
    
    # Compile graph
    return workflow.compile()

# Create graph instance
assessment_graph = create_assessment_graph()

# Chat agent state
class ChatState(TypedDict):
    """State for chat workflow"""
    # Assessment context
    assessment_id: str
    pci_score: float
    condition: str
    detections: List[Dict]
    
    # Conversation
    messages: Annotated[List, operator.add]
    user_question: str
    
    # SQL query capability
    needs_sql_query: bool  # ← Add this
    sql_query: str  # ← Add this
    sql_results: str  # ← Add this
    
    # Response
    response: str

# Add new node for SQL query detection
def detect_sql_intent(state: ChatState) -> ChatState:
    """
    Detect if user question needs SQL query
    """
    needs_sql = analyze_query_intent(state['user_question'])
    
    return {
        **state,
        'needs_sql_query': needs_sql,
        'sql_query': '',
        'sql_results': ''
    }

# Add new node for SQL generation
def generate_sql_query(state: ChatState) -> ChatState:
    """
    Generate SQL query using AI
    """
    if not state['needs_sql_query']:
        return state
    
    try:
        from app.core.aws_bedrock import get_bedrock_client
        
        bedrock = get_bedrock_client()
        
        # Database schema context
        schema_context = """
        Database Schema:
        
        assessments table:
        - id (INTEGER)
        - assessment_id (TEXT)
        - pci_score (REAL)
        - condition (TEXT)
        - location (TEXT)
        - created_at (DATETIME)
        
        defects table:
        - id (INTEGER)
        - assessment_id (INTEGER, FK to assessments)
        - defect_type (TEXT)
        - severity (TEXT)
        - confidence (REAL)
        - area_pixels (REAL)
        
        Example queries:
        - Show assessments with PCI below 60:
          SELECT * FROM assessments WHERE pci_score < 60
        
        - Count defects by type:
          SELECT defect_type, COUNT(*) as count FROM defects GROUP BY defect_type
        
        - Find critical defects:
          SELECT * FROM defects WHERE severity = 'critical'
        """
        
        prompt = f"""You are a SQL expert. Generate a SQL query for this question.

{schema_context}

User Question: {state['user_question']}

Generate ONLY the SQL query, no explanation. Use SELECT only (no INSERT/UPDATE/DELETE).
Return just the SQL query text."""

        from langchain_core.messages import HumanMessage
        
        sql_query = bedrock.invoke([HumanMessage(content=prompt)])
        
        # Clean up query
        sql_query = sql_query.strip()
        if sql_query.startswith('```sql'):
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        print(f"   Generated SQL: {sql_query}")
        
        return {
            **state,
            'sql_query': sql_query
        }
        
    except Exception as e:
        print(f"   SQL generation failed: {e}")
        return {
            **state,
            'needs_sql_query': False
        }

# Add new node for SQL execution
def execute_sql(state: ChatState) -> ChatState:
    """
    Execute generated SQL query
    """
    if not state['needs_sql_query'] or not state['sql_query']:
        return state
    
    try:
        results = execute_sql_query(
            state['sql_query'],
            settings.database_url
        )
        
        return {
            **state,
            'sql_results': results
        }
        
    except Exception as e:
        return {
            **state,
            'sql_results': f"❌ Query execution failed: {str(e)}"
        }

def answer_question(state: ChatState) -> ChatState:
    """
    Answer user question about assessment using AI
    """
    print(f"💬 Answering: {state['user_question']}")
    
    try:
        # Get Bedrock client
        bedrock = get_bedrock_client()
        
        # Build context
        context = {
            'pci_score': state['pci_score'],
            'condition': state['condition'],
            'detections': state['detections']
        }
        
        # Add SQL results if available
        if state.get('sql_results'):
            context['sql_results'] = state['sql_results']
        
        # Get answer
        answer = bedrock.answer_question(
            question=state['user_question'],
            assessment_context=context,
            chat_history=state.get('messages', [])
        )
        
        # If SQL was used, mention it
        if state.get('sql_query') and state.get('sql_results'):
            answer = f"**SQL Query:**\n```sql\n{state['sql_query']}\n```\n\n{state['sql_results']}\n\n**Analysis:**\n{answer}"
        
        print("   ✅ Answer generated")
        
        return {
            **state,
            "response": answer,
            "messages": state.get('messages', []) + [
                HumanMessage(content=state['user_question']),
                AIMessage(content=answer)
            ]
        }
    except Exception as e:
        print(f"   ⚠️  Using fallback response: {e}")
        # Fallback to tool-based answer
        answer = generate_tool_based_answer(state)
        
        return {
            **state,
            "response": answer,
            "messages": state.get('messages', []) + [
                HumanMessage(content=state['user_question']),
                AIMessage(content=answer)
            ]
        }

def generate_tool_based_answer(state: ChatState) -> str:
    """
    Generate answer using tools when AI is unavailable
    """
    question = state['user_question'].lower()
    
    # Route to appropriate tool
    if any(word in question for word in ['cost', 'price', 'budget', 'expense']):
        return get_repair_cost_breakdown(state['detections'])
    
    elif any(word in question for word in ['priority', 'urgent', 'critical', 'first']):
        return get_priority_repairs(state['detections'])
    
    elif any(word in question for word in ['when', 'timeline', 'schedule', 'time']):
        return get_timeline_estimate(state['pci_score'], state['detections'])
    
    elif any(word in question for word in ['statistics', 'stats', 'summary', 'overview']):
        return get_defect_statistics(state['detections'])
    
    else:
        # General response
        return f"""Based on the assessment:
        
**PCI Score:** {state['pci_score']}/100 ({state['condition']})
**Total Defects:** {len(state['detections'])}

For specific information, you can ask about:
- Repair costs and budget
- Priority repairs
- Timeline and schedule
- Defect statistics

What would you like to know?"""

# Create chat graph

# Update create_chat_graph to include SQL nodes
def create_chat_graph():
    """Create LangGraph workflow for chat with SQL capability"""
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("detect_sql", detect_sql_intent)
    workflow.add_node("generate_sql", generate_sql_query)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("answer", answer_question)
    
    # Define edges
    workflow.set_entry_point("detect_sql")
    
    # Conditional routing
    def should_generate_sql(state: ChatState):
        return "generate_sql" if state.get('needs_sql_query') else "answer"
    
    workflow.add_conditional_edges(
        "detect_sql",
        should_generate_sql,
        {
            "generate_sql": "generate_sql",
            "answer": "answer"
        }
    )
    
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "answer")
    workflow.add_edge("answer", END)
    
    return workflow.compile()

# Create chat graph instance
chat_graph = create_chat_graph()