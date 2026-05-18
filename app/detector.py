import cv2

class DummyDetector:
    def __init__(self):
        print("Initialized Dummy Detector. No AI model loaded.")
        
    def detect(self, frame):
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        bbox = [center_x - 100, center_y - 150, center_x + 100, center_y + 150]
        return [{"label": "person", "confidence": 0.95, "bbox": bbox}]

class YoloDetector:
    def __init__(self, model_path="yolov8n.pt"):
        print(f"Loading YOLO model from {model_path}...")
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            print("YOLO model loaded successfully!")
        except ImportError:
            print("Error: ultralytics is not installed. Falling back to DummyDetector.")
            self.model = None

    def detect(self, frame):
        if self.model is None:
            return []
            
        results = self.model(frame, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # get coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                # get confidence
                conf = box.conf[0].item()
                # get class label
                cls_id = int(box.cls[0].item())
                label = self.model.names[cls_id]
                
                # Only keep detections with confidence > 0.5
                if conf > 0.5:
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "bbox": [x1, y1, x2, y2]
                    })
                    
        return detections
