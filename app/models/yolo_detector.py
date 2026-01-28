# app/models/yolo_detector.py
from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import os

class PavementDetector:
    """
    YOLO-based pavement defect detector
    Supports both custom trained models and generic YOLO
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize YOLO detector"""
        
        # If no path provided, use from settings
        if model_path is None:
            from app.config import settings
            model_path = settings.yolo_model_path
        
        if model_path and os.path.exists(model_path):
            print(f"✅ Loading custom model: {model_path}")
            self.model = YOLO(model_path)
            self.is_custom = True
            
            # YOUR CUSTOM CLASSES - mapped from model
            self.defect_classes = {
                0: 'apothole',
                1: 'spalling',
                2: 'patching',
                3: 'rm'
            }
            
            print(f"   Loaded {len(self.defect_classes)} defect classes: {list(self.defect_classes.values())}")
            
        else:
            print(f"⚠️  Custom model not found: {model_path}")
            print("⚠️  Loading generic YOLOv8n model (demo mode)")
            self.model = YOLO('yolov8n.pt')
            self.is_custom = False
            self.defect_classes = None
    
    def detect(
        self, 
        image_path: str, 
        conf_threshold: float = 0.25,
        save_annotated: bool = True
    ) -> Dict:
        """Detect defects in pavement image"""
        
        results = self.model(image_path, conf=conf_threshold)
        
        detections = []
        
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls)
                
                if self.is_custom and self.defect_classes:
                    defect_type = self.defect_classes.get(cls_id, 'unknown')
                else:
                    defect_type = r.names[cls_id]
                
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                width = x2 - x1
                height = y2 - y1
                area = width * height
                
                detection = {
                    'type': defect_type,
                    'confidence': float(box.conf),
                    'bbox': {
                        'x': int(x1),
                        'y': int(y1),
                        'width': int(width),
                        'height': int(height)
                    },
                    'area_pixels': float(area),
                    'severity': self._calculate_severity(defect_type, area)
                }
                
                detections.append(detection)
        
        # Save annotated image
        annotated_path = None
        if save_annotated and len(results) > 0:
            annotated_path = self._save_annotated_image(results[0], image_path)
            
            if annotated_path and not Path(annotated_path).exists():
                print(f"   ⚠️ Annotated image not found: {annotated_path}")
                annotated_path = None
        
        return {
            'detections': detections,
            'total_defects': len(detections),
            'annotated_image_path': annotated_path
        }
    
    def _calculate_severity(self, defect_type: str, area: float) -> str:
        """Calculate severity for YOUR custom defect types"""
        
        if defect_type == 'apothole':
            if area > 15000:
                return 'critical'
            elif area > 8000:
                return 'high'
            elif area > 3000:
                return 'medium'
            else:
                return 'low'
        
        elif defect_type == 'spalling':
            if area > 12000:
                return 'high'
            elif area > 5000:
                return 'medium'
            else:
                return 'low'
        
        elif defect_type == 'patching':
            if area > 10000:
                return 'medium'
            else:
                return 'low'
        
        elif defect_type == 'rm':
            if area > 8000:
                return 'high'
            elif area > 4000:
                return 'medium'
            else:
                return 'low'
        
        else:
            # Default for unknown types
            if area > 8000:
                return 'medium'
            else:
                return 'low'
    
    def _save_annotated_image(self, result, original_path: str) -> str:
        """Save annotated image with bounding boxes"""
        
        annotated_dir = Path("uploads/annotated")
        annotated_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = Path(original_path).stem
        annotated_path = annotated_dir / f"{original_name}_annotated.jpg"
        
        annotated_img = result.plot()
        
        try:
            success = cv2.imwrite(str(annotated_path), annotated_img)
            
            if success:
                print(f"   ✅ Saved annotated image: {annotated_path}")
                return str(annotated_path)
            else:
                print(f"   ❌ Failed to save annotated image")
                return ""
                
        except Exception as e:
            print(f"   ❌ Error saving annotated image: {e}")
            return ""
    
    def get_model_info(self) -> Dict:
        """Get model metadata"""
        return {
            'is_custom': self.is_custom,
            'model_type': 'Custom Pavement YOLO' if self.is_custom else 'Generic YOLOv8n',
            'classes': list(self.defect_classes.values()) if self.defect_classes else 'COCO classes',
            'total_classes': len(self.defect_classes) if self.defect_classes else 80
        }