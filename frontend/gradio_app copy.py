# frontend/gradio_app.py
"""
Gradio Frontend for Pavement Assessment AI Agent
"""

import gradio as gr
import requests
from PIL import Image
import io
import os

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# Session state
current_assessment_id = None
current_session_id = None

def analyze_image(image):
    """
    Upload and analyze pavement image
    """
    global current_assessment_id, current_session_id
    
    if image is None:
        return None, "Please upload an image first.", None, []
    
    try:
        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        # Call API
        files = {"file": ("image.jpg", img_byte_arr, "image/jpeg")}
        response = requests.post(f"{API_URL}/analyze", files=files)
        
        if response.status_code != 200:
            return None, f"❌ Error: {response.text}", None, []
        
        result = response.json()
        
        # Store assessment ID for chat
        current_assessment_id = result['assessment_id']
        current_session_id = None  # Reset session
        
        # Format results
        results_text = f"""
# 📊 Assessment Results

## Overall Condition
**PCI Score:** {result['pci_score']}/100  
**Rating:** {result['condition']}

## Defects Detected
**Total Defects:** {result['total_defects']}

"""
        
        # Add defect breakdown
        if result['total_defects'] > 0:
            defect_types = {}
            severity_counts = {}
            
            for defect in result['detections']:
                dtype = defect['type']
                severity = defect['severity']
                
                defect_types[dtype] = defect_types.get(dtype, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            results_text += "### By Type:\n"
            for dtype, count in sorted(defect_types.items(), key=lambda x: x[1], reverse=True):
                results_text += f"- **{dtype}**: {count}\n"
            
            results_text += "\n### By Severity:\n"
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in severity_counts:
                    results_text += f"- **{severity.upper()}**: {severity_counts[severity]}\n"
        
        # Add AI analysis
        results_text += f"\n## 🤖 AI Analysis\n\n{result['analysis']}\n"
        
        # Add recommendations
        if result['recommendations']:
            results_text += "\n## 📋 Recommendations\n\n"
            for i, rec in enumerate(result['recommendations'], 1):
                results_text += f"{i}. {rec}\n"
        
        # Load annotated image if available
        annotated_img = None
        if result.get('annotated_image_url'):
            try:
                img_response = requests.get(f"http://localhost:8000{result['annotated_image_url']}")
                if img_response.status_code == 200:
                    annotated_img = Image.open(io.BytesIO(img_response.content))
            except:
                pass
        
        # Initialize chat with welcome message (Gradio 6.0 format)
        chat_history = [
            {
                "role": "assistant",
                "content": f"Assessment complete! PCI Score: {result['pci_score']} ({result['condition']}). Ask me anything about the results!"
            }
        ]
        
        return current_assessment_id, results_text, annotated_img, chat_history
        
    except Exception as e:
        return None, f"❌ Error: {str(e)}\n\nMake sure FastAPI backend is running:\nuvicorn app.main:app --reload", None, []

def chat_with_assessment(message, chat_history):
    """
    Chat about the assessment (Gradio 6.0 format)
    """
    global current_assessment_id, current_session_id
    
    if not current_assessment_id:
        # Add error message
        chat_history.append({
            "role": "user",
            "content": message
        })
        chat_history.append({
            "role": "assistant",
            "content": "⚠️ Please analyze an image first before asking questions."
        })
        return "", chat_history
    
    if not message.strip():
        return "", chat_history
    
    try:
        # Add user message to history
        chat_history.append({
            "role": "user",
            "content": message
        })
        
        # Call chat API
        payload = {
            "assessment_id": current_assessment_id,
            "question": message,
            "session_id": current_session_id
        }
        
        response = requests.post(f"{API_URL}/chat", json=payload)
        
        if response.status_code != 200:
            chat_history.append({
                "role": "assistant",
                "content": f"❌ Error: {response.text}"
            })
            return "", chat_history
        
        result = response.json()
        
        # Update session ID
        current_session_id = result['session_id']
        
        # Add assistant response
        chat_history.append({
            "role": "assistant",
            "content": result['response']
        })
        
        return "", chat_history
        
    except Exception as e:
        chat_history.append({
            "role": "assistant",
            "content": f"❌ Error: {str(e)}"
        })
        return "", chat_history

def clear_chat():
    """Clear chat and reset session"""
    global current_session_id
    current_session_id = None
    return []

def set_example_question(question):
    """Set example question in input box"""
    return question

# Create Gradio Interface
with gr.Blocks(title="Pavement Assessment AI Agent") as demo:
    
    # Header
    gr.Markdown("""
    # 🛣️ Pavement Assessment AI Agent
    ### AI-powered pavement condition analysis using YOLO, LangGraph, and AWS Bedrock
    
    **Upload a pavement image** to get instant PCI scoring, defect detection, and AI-powered recommendations.
    Then **chat with AI** to ask questions about the assessment.
    """)
    
    # Hidden state for assessment ID
    assessment_id_state = gr.State(None)
    
    with gr.Row():
        # Left Column - Image Analysis
        with gr.Column(scale=1):
            gr.Markdown("### 1️⃣ Upload & Analyze")
            
            image_input = gr.Image(
                type="pil",
                label="Pavement Image",
                height=300
            )
            
            analyze_btn = gr.Button(
                "🔍 Analyze Pavement",
                variant="primary",
                size="lg"
            )
            
            gr.Markdown("### 📊 Results")
            
            results_output = gr.Markdown(
                value="Upload an image and click 'Analyze Pavement' to get started."
            )
            
            gr.Markdown("### 🎯 Detected Defects")
            
            annotated_image = gr.Image(
                label="Annotated Image",
                height=300
            )
        
        # Right Column - Chat Interface
        with gr.Column(scale=1):
            gr.Markdown("### 2️⃣ Ask Questions")
            
            chatbot = gr.Chatbot(
                label="AI Assistant",
                height=400,
                #type="messages"  # Gradio 6.0: explicit type
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about costs, repairs, timelines, etc...",
                    label="Your Question",
                    scale=4,
                    lines=1
                )
                send_btn = gr.Button("📤 Send", scale=1, variant="primary")
            
            clear_btn = gr.Button("🔄 Clear Chat", size="sm")
            
            # Example questions
            gr.Markdown("### 💡 Example Questions")
            
            with gr.Row():
                ex1 = gr.Button("What's the most urgent repair?", size="sm")
                ex2 = gr.Button("How much will repairs cost?", size="sm")
            
            with gr.Row():
                ex3 = gr.Button("What caused these defects?", size="sm")
                ex4 = gr.Button("When should repairs be done?", size="sm")
            
            with gr.Row():
                ex5 = gr.Button("Is this road safe?", size="sm")
                ex6 = gr.Button("Show defect priorities", size="sm")
    
    # Footer
    gr.Markdown("""
    ---
    **Technology Stack:** YOLO Detection | AWS Bedrock (Claude) | LangGraph | FastAPI | SQLite
    
    **Note:** Make sure FastAPI backend is running: `uvicorn app.main:app --reload`
    """)
    
    # Event handlers
    analyze_btn.click(
        fn=analyze_image,
        inputs=[image_input],
        outputs=[assessment_id_state, results_output, annotated_image, chatbot]
    )
    
    send_btn.click(
        fn=chat_with_assessment,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )
    
    msg_input.submit(
        fn=chat_with_assessment,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )
    
    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot]
    )
    
    # Example question buttons
    ex1.click(fn=lambda: "What's the most urgent repair?", outputs=[msg_input])
    ex2.click(fn=lambda: "How much will repairs cost?", outputs=[msg_input])
    ex3.click(fn=lambda: "What caused these defects?", outputs=[msg_input])
    ex4.click(fn=lambda: "When should repairs be done?", outputs=[msg_input])
    ex5.click(fn=lambda: "Is this road safe to use?", outputs=[msg_input])
    ex6.click(fn=lambda: "Show me the priority repairs", outputs=[msg_input])

# Launch app
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Gradio Frontend")
    print("="*60)
    print(f"API URL: {API_URL}")
    print("Make sure FastAPI is running on http://localhost:8000")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft()
    )