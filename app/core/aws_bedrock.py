# app/core/aws_bedrock.py
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import Optional, List, Dict
import boto3
from botocore.config import Config
from app.config import settings
import os

class BedrockClient:
    """
    AWS Bedrock client for Claude AI
    """
    
    def __init__(self):
        """Initialize Bedrock client"""
        
        # Configure boto3
        self.config = Config(
            region_name=settings.aws_region,
            signature_version='v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        # Initialize Bedrock Runtime client
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.aws_region,
            config=self.config,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        
        # Initialize LangChain ChatBedrock
        self.llm = ChatBedrock(
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            client=self.bedrock_client,
            model_kwargs={
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 2048
            }
        )
        
        print("✅ AWS Bedrock client initialized")
        print(f"   Region: {settings.aws_region}")
        print(f"   Model: Claude 3.5 Sonnet")
    
    def invoke(self, messages: List, **kwargs) -> str:
        """
        Invoke Claude with messages
        
        Args:
            messages: List of message dicts or LangChain messages
            **kwargs: Additional model parameters
            
        Returns:
            Model response as string
        """
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def analyze_pavement(
        self, 
        pci_score: float,
        detections: List[Dict],
        image_description: Optional[str] = None
    ) -> str:
        """
        Analyze pavement assessment results
        
        Args:
            pci_score: PCI score (0-100)
            detections: List of detected defects
            image_description: Optional description of image
            
        Returns:
            Analysis text
        """
        # Build context
        defect_summary = self._format_detections(detections)
        
        prompt = f"""You are a pavement engineering expert. Analyze this road assessment:

**PCI Score:** {pci_score}/100

**Detected Defects:**
{defect_summary}

Provide a professional assessment including:
1. Overall pavement condition interpretation
2. Critical issues that need immediate attention
3. Recommended maintenance actions with priority levels
4. Estimated timeline for repairs
5. Safety considerations

Be specific, technical, and actionable."""

        messages = [HumanMessage(content=prompt)]
        return self.invoke(messages)
    
    def answer_question(
        self,
        question: str,
        assessment_context: Dict,
        chat_history: Optional[List] = None
    ) -> str:
        """
        Answer user question about assessment
        
        Args:
            question: User's question
            assessment_context: Dict with PCI, defects, analysis
            chat_history: Previous chat messages
            
        Returns:
            Answer text
        """
        # Build system context
        system_prompt = f"""You are a pavement engineering assistant helping users understand road assessment results.

**Current Assessment:**
- PCI Score: {assessment_context.get('pci_score', 'N/A')}
- Condition: {assessment_context.get('condition', 'N/A')}
- Total Defects: {len(assessment_context.get('detections', []))}

**Defect Details:**
{self._format_detections(assessment_context.get('detections', []))}

Answer the user's question clearly and professionally. Use specific data from the assessment.
If asked about costs, provide estimates based on defect types and severity.
If asked about timelines, prioritize based on severity."""

        messages = [SystemMessage(content=system_prompt)]
        
        # Add chat history
        if chat_history:
            messages.extend(chat_history[-10:])  # Last 10 messages
        
        # Add current question
        messages.append(HumanMessage(content=question))
        
        return self.invoke(messages)
    
    def _format_detections(self, detections: List[Dict]) -> str:
        """Format detections for prompt"""
        if not detections:
            return "No defects detected"
        
        formatted = []
        for i, det in enumerate(detections, 1):
            formatted.append(
                f"{i}. {det['type'].upper()} - "
                f"Severity: {det['severity']}, "
                f"Confidence: {det['confidence']:.2f}, "
                f"Location: ({det['bbox']['x']}, {det['bbox']['y']}), "
                f"Size: {det['bbox']['width']}x{det['bbox']['height']}px"
            )
        
        return "\n".join(formatted)
    
    def test_connection(self) -> bool:
        """Test Bedrock connection"""
        try:
            response = self.invoke([HumanMessage(content="Hello, respond with OK")])
            return "ok" in response.lower()
        except Exception as e:
            print(f"❌ Bedrock connection test failed: {e}")
            return False

# Global instance
_bedrock_client = None

def get_bedrock_client() -> BedrockClient:
    """Get or create Bedrock client singleton"""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client