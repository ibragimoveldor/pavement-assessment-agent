# app/core/__init__.py
from .aws_bedrock import BedrockClient, get_bedrock_client

__all__ = ['BedrockClient', 'get_bedrock_client']