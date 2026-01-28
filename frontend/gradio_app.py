# frontend/gradio_app.py
"""
Gradio Frontend for Pavement Assessment AI Agent
"""

import gradio as gr
import requests
from PIL import Image
import io
import os
from datetime import datetime

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# Session state
current_assessment_id = None
current_session_id = None

def analyze_image(image):
    """Upload and analyze pavement image"""
    global current_assessment_id, current_session_id
    
    if image is None:
        return None, "⚠️ Please upload an image first.", None, [], ""
    
    logs = f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting analysis...\n"
    
    try:
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Uploading image to API...\n"
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        files = {"file": ("image.jpg", img_byte_arr, "image/jpeg")}
        
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 🔗 Calling FastAPI endpoint: {API_URL}/analyze\n"
        
        response = requests.post(f"{API_URL}/analyze", files=files)
        
        if response.status_code != 200:
            logs += f"[{datetime.now().strftime('%H:%M:%S')}] ❌ API Error: {response.status_code}\n"
            return None, f"❌ Error: {response.text}", None, [], logs
        
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] ✅ API response received\n"
        
        result = response.json()
        
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Step 1: YOLO Detection - Found {result['total_defects']} defects\n"
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Step 2: PCI Calculation - Score: {result['pci_score']}\n"
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Step 3: AI Analysis (AWS Bedrock)\n"
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 💾 Step 4: Saving to database\n"
        
        current_assessment_id = result['assessment_id']
        current_session_id = None
        
        # Format results
        results_text = f"""
# 📊 Assessment Results

**PCI Score:** {result['pci_score']}/100 ({result['condition']})  
**Total Defects:** {result['total_defects']}

## 🤖 AI Analysis
{result['analysis']}

## 📋 Recommendations
"""
        for i, rec in enumerate(result.get('recommendations', []), 1):
            results_text += f"{i}. {rec}\n"
        
        # Load annotated image
        annotated_img = None
        if result.get('annotated_image_url'):
            try:
                logs += f"[{datetime.now().strftime('%H:%M:%S')}] 🎨 Loading annotated image...\n"
                img_response = requests.get(f"http://localhost:8000{result['annotated_image_url']}")
                if img_response.status_code == 200:
                    annotated_img = Image.open(io.BytesIO(img_response.content))
                    logs += f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Annotated image loaded\n"
            except:
                pass
        
        chat_history = [
            {"role": "assistant", "content": f"✅ Assessment complete! PCI Score: {result['pci_score']} ({result['condition']}). Ask me anything!"}
        ]
        
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Analysis complete!\n"
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] Assessment ID: {current_assessment_id}\n"
        
        return current_assessment_id, results_text, annotated_img, chat_history, logs
        
    except Exception as e:
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)}\n"
        return None, f"❌ Error: {str(e)}", None, [], logs

def chat_with_assessment(message, chat_history, current_logs):
    """Chat about the assessment"""
    global current_assessment_id, current_session_id
    
    logs = current_logs + f"\n[{datetime.now().strftime('%H:%M:%S')}] 💬 User question: {message}\n"
    
    if not current_assessment_id:
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": "⚠️ Please analyze an image first."})
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No assessment available\n"
        return "", chat_history, logs
    
    if not message.strip():
        return "", chat_history, logs
    
    try:
        chat_history.append({"role": "user", "content": message})
        
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 🔗 Calling chat API...\n"
        
        payload = {
            "assessment_id": current_assessment_id,
            "question": message,
            "session_id": current_session_id
        }
        
        response = requests.post(f"{API_URL}/chat", json=payload)
        
        if response.status_code != 200:
            logs += f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Chat API error\n"
            chat_history.append({"role": "assistant", "content": f"❌ Error: {response.text}"})
            return "", chat_history, logs
        
        result = response.json()
        current_session_id = result['session_id']
        
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Agent processing question...\n"
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 LangGraph workflow executing\n"
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Response generated\n"
        
        chat_history.append({"role": "assistant", "content": result['response']})
        
        return "", chat_history, logs
        
    except Exception as e:
        logs += f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)}\n"
        chat_history.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
        return "", chat_history, logs

def clear_chat():
    """Clear chat"""
    global current_session_id
    current_session_id = None
    return []

# Create Interface
with gr.Blocks(title="Pavement Assessment AI Agent") as demo:
    
    gr.Markdown("""
    # 🛣️ Pavement Assessment AI Agent
    ### AI-powered pavement condition analysis using YOLO, LangGraph, and AWS Bedrock
    
    Upload a pavement image to get instant PCI scoring, defect detection, and AI-powered recommendations.
    """)
    
    assessment_id_state = gr.State(None)
    logs_state = gr.State("")
    
    with gr.Row():
        # Left Column - Analysis (Wider)
        with gr.Column(scale=2):
            gr.Markdown("### 📤 Upload & Analyze")
            
            image_input = gr.Image(
                type="pil",
                label="Pavement Image",
                height=250,
                sources=["upload", "clipboard"]
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
                height=250
            )
        
        # Right Column - Chat + Logs
        with gr.Column(scale=1):
            gr.Markdown("### 💬 Chat")
            
            chatbot = gr.Chatbot(
                label="AI Assistant",
                height=400
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about results...",
                    label="Question",
                    scale=4,
                    lines=1
                )
                send_btn = gr.Button("Send", scale=1, variant="primary")
            
            clear_btn = gr.Button("Clear Chat", size="sm")
            
            gr.Markdown("### 💡 Examples")
            
            with gr.Column():
                ex1 = gr.Button("Urgent repairs?", size="sm")
                ex2 = gr.Button("Cost estimate?", size="sm")
                ex3 = gr.Button("Timeline?", size="sm")
                ex4 = gr.Button("Safety concerns?", size="sm")
            
            # Collapsible Logs Section
            with gr.Accordion("📋 Agent Workflow Logs", open=False):
                logs_output = gr.Textbox(
                    label="",
                    value="No logs yet. Run an analysis to see workflow steps.",
                    lines=10,
                    max_lines=15,
                    show_label=False,
                    interactive=False,
                    elem_classes="monospace"
                )
    
    gr.Markdown("---\n**Stack:** YOLO | AWS Bedrock | LangGraph | FastAPI")
    
    # Events
    analyze_btn.click(
        fn=analyze_image,
        inputs=[image_input],
        outputs=[assessment_id_state, results_output, annotated_image, chatbot, logs_output]
    )
    
    send_btn.click(
        fn=chat_with_assessment,
        inputs=[msg_input, chatbot, logs_output],
        outputs=[msg_input, chatbot, logs_output]
    )
    
    msg_input.submit(
        fn=chat_with_assessment,
        inputs=[msg_input, chatbot, logs_output],
        outputs=[msg_input, chatbot, logs_output]
    )
    
    clear_btn.click(fn=clear_chat, outputs=[chatbot])
    
    ex1.click(lambda: "What's the most urgent repair?", outputs=[msg_input])
    ex2.click(lambda: "How much will this cost?", outputs=[msg_input])
    ex3.click(lambda: "When should repairs be done?", outputs=[msg_input])
    ex4.click(lambda: "Is this road safe?", outputs=[msg_input])

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Gradio Frontend Starting")
    print("="*60)
    print(f"API: {API_URL}")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
