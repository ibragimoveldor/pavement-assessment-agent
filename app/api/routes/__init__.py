# app/api/routes/__init__.py
from .analyze import router as analyze_router
from .chat import router as chat_router

__all__ = ['analyze_router', 'chat_router']