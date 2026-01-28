# test_custom_model.py
import os
from pathlib import Path
from app.config import settings

print("="*60)
print("Custom Model Loading Debug")
print("="*60)

# Check .env file
print("\n1. Environment Variables:")
print(f"   YOLO_MODEL_PATH from .env: {os.getenv('YOLO_MODEL_PATH')}")
print(f"   Settings model path: {settings.yolo_model_path}")

# Check if path exists
model_path = settings.yolo_model_path
print(f"\n2. Model File Check:")
print(f"   Path: {model_path}")
print(f"   Exists: {os.path.exists(model_path)}")
print(f"   Is file: {os.path.isfile(model_path)}")

if os.path.exists(model_path):
    print(f"   File size: {os.path.getsize(model_path)} bytes")

# Try loading with YOLO
print(f"\n3. Attempting YOLO Load:")
try:
    from ultralytics import YOLO
    model = YOLO(model_path)
    print(f"   ✅ Model loaded successfully!")
    print(f"   Model classes: {model.names}")
    print(f"   Number of classes: {len(model.names)}")
except FileNotFoundError as e:
    print(f"   ❌ File not found: {e}")
except Exception as e:
    print(f"   ❌ Error loading: {e}")

# Check detector initialization
print(f"\n4. Detector Initialization:")
try:
    from app.models.yolo_detector import PavementDetector
    detector = PavementDetector()
    info = detector.get_model_info()
    print(f"   Model type: {info['model_type']}")
    print(f"   Is custom: {info['is_custom']}")
    print(f"   Classes: {info['classes']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("="*60)