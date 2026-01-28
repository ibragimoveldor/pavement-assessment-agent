# Pavement Assessment AI Agent

AI-powered pavement condition assessment using YOLO, LangGraph, and AWS Bedrock.


## Features
- Custom YOLO model for pavement defect detection
- PCI scoring following ASTM D6433 standards
- LangGraph multi-step agent workflows
- AWS Bedrock (Claude) for AI analysis
- Text-to-SQL conversational interface

## Tech Stack
- LangChain, LangGraph
- AWS Bedrock (Claude 3.5 Sonnet)
- FastAPI
- Custom YOLOv8 model
- SQLite


## Architecture
┌─────────────────────────────────────────────────────────────────┐
│                    PAVEMENT ASSESSMENT AI AGENT                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  ┌────────────────┐              ┌─────────────────────────┐   │
│  │  Gradio UI     │              │   FastAPI Swagger       │   │
│  │  (Port 7860)   │              │   (Port 8000/docs)      │   │
│  └────────┬───────┘              └───────────┬─────────────┘   │
└───────────┼──────────────────────────────────┼──────────────────┘
            │                                   │
            └───────────────┬───────────────────┘
                            │ HTTP/REST
┌───────────────────────────▼──────────────────────────────────────┐
│                      FASTAPI BACKEND                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    API ENDPOINTS                            │ │
│  │  POST /api/v1/analyze    │  POST /api/v1/chat             │ │
│  │  GET  /api/v1/assessment │  GET  /api/v1/uploads          │ │
│  └─────────────────────┬────────────────────────────────────┘ │
└────────────────────────┼──────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌─────────▼────────────┐
│  ANALYZE ROUTE  │            │    CHAT ROUTE        │
│  (Image Upload) │            │ (Conversational Q&A) │
└────────┬────────┘            └─────────┬────────────┘
         │                               │
         │                               │
┌────────▼───────────────────────────────▼──────────────────────┐
│                   LANGGRAPH ORCHESTRATION                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │           ASSESSMENT WORKFLOW (StateGraph)                │ │
│  │                                                            │ │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐          │ │
│  │   │  Node 1  │ ──▶│  Node 2  │ ──▶│  Node 3  │          │ │
│  │   │  DETECT  │    │   PCI    │    │ ANALYZE  │          │ │
│  │   │ DEFECTS  │    │  SCORE   │    │  w/ AI   │          │ │
│  │   └────┬─────┘    └────┬─────┘    └────┬─────┘          │ │
│  │        │               │               │                 │ │
│  │        │               │               │                 │ │
│  │   ┌────▼───────────────▼───────────────▼──────┐         │ │
│  │   │         SHARED STATE                       │         │ │
│  │   │  • image_path                              │         │ │
│  │   │  • detections                              │         │ │
│  │   │  • pci_score                               │         │ │
│  │   │  • analysis                                │         │ │
│  │   │  • recommendations                         │         │ │
│  │   └────────────────────────────────────────────┘         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              CHAT WORKFLOW (StateGraph)                   │ │
│  │                                                            │ │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐          │ │
│  │   │ Detect   │ ──▶│ Generate │ ──▶│  Answer  │          │ │
│  │   │SQL Intent│    │   SQL    │    │ Question │          │ │
│  │   └──────────┘    └──────────┘    └──────────┘          │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌───────▼──────────┐
│   YOLO MODEL    │  │  PCI CALCULATOR │  │  AWS BEDROCK     │
│                 │  │                 │  │                  │
│ • YOLOv8 Custom │  │ • ASTM D6433    │  │ • Claude 3.5     │
│ • 4 Defect      │  │ • Deduct Logic  │  │   Sonnet         │
│   Classes       │  │ • Severity      │  │ • AI Analysis    │
│ • Confidence    │  │   Rules         │  │ • Text-to-SQL    │
│ • Bounding Box  │  │ • Cost Estimate │  │ • Reasoning      │
│                 │  │ • Timeline      │  │                  │
└─────────────────┘  └─────────────────┘  └──────────────────┘
         │
         │
┌────────▼──────────────────────────────────────────────────────┐
│                    DATA LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   SQLite     │  │  File System │  │   Agent Tools    │   │
│  │              │  │              │  │                  │   │
│  │ • assessments│  │ • uploads/   │  │ • Statistics     │   │
│  │ • defects    │  │ • annotated/ │  │ • Cost Breakdown │   │
│  │ • chat_msgs  │  │              │  │ • Priorities     │   │
│  └──────────────┘  └──────────────┘  │ • Timeline       │   │
│                                       └──────────────────┘   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  ┌──────────────────────┐         ┌──────────────────────┐    │
│  │    AWS BEDROCK       │         │   AWS IAM            │    │
│  │  (us-east-1)         │         │  (Credentials)       │    │
│  └──────────────────────┘         └──────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
---

**This project demonstrates:**
- Multi-step agent reasoning
- Computer vision integration
- Cloud LLM deployment
- Production API design
