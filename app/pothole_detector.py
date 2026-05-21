"""
Pothole Detector Module.

Uses a custom YOLO model (best.pt) to detect road potholes in real-time.
When a pothole is detected:
  - Bounding box with confidence is drawn on the frame.
  - A red "⚠ POTHOLE DETECTED" overlay is shown.
  - The frame is saved as a snapshot.
  - The detection is logged to a CSV file.

Compatible with Jetson Nano and standard laptop environments.
"""

import cv2
import os
import time
import csv
import threading
from datetime import datetime


# Directories for snapshots and logs
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(_BASE_DIR, "..", "pothole_snapshots")
LOG_DIR = os.path.join(_BASE_DIR, "..", "pothole_logs")
LOG_FILE = os.path.join(LOG_DIR, "detections.csv")


class PotholeDetector:
    """
    Detects potholes using a custom-trained YOLO model.

    Args:
        api_key: Roboflow API Key.
        model_id: Roboflow model ID (e.g., "pothole-project/1").
        confidence_threshold: Minimum confidence to consider a detection valid.
        snapshot_cooldown: Seconds between saving consecutive snapshots.
    """

    def __init__(self, api_key="", model_id="pothole-vhmow/2", confidence_threshold=0.5,
                 snapshot_cooldown=5):
        self.api_key = api_key
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self.snapshot_cooldown = snapshot_cooldown
        self.model = None
        self._last_snapshot_time = 0
        self._detection_count = 0
        self._lock = threading.Lock()

        # Create output directories
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)

        # Initialize CSV log with header if it doesn't exist
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "confidence", "x1", "y1", "x2", "y2",
                    "snapshot_path"
                ])

        # Load YOLO model
        self._load_model()

    def _load_model(self):
        """Initialize the Roboflow Inference Client."""
        if not self.api_key or self.api_key == "YOUR_ROBOFLOW_API_KEY":
            print("Pothole Detector: Roboflow API Key not set. Please update config.py.")
            return

        try:
            from inference_sdk import InferenceHTTPClient
            self.model = InferenceHTTPClient(
                api_url="https://serverless.roboflow.com",
                api_key=self.api_key
            )
            print(f"Pothole Detector: Roboflow Client initialized for model '{self.model_id}'")
        except ImportError:
            print("Pothole Detector: inference-sdk not installed. "
                  "Install with: pip install inference-sdk")
        except Exception as e:
            print(f"Pothole Detector: Failed to initialize client - {e}")
            self.model = None

    def is_ready(self):
        """Check if the model is loaded and ready."""
        return self.model is not None

    def detect(self, frame):
        """
        Run pothole detection on a frame using Roboflow.

        Returns:
            list of dicts: Each dict has 'label', 'confidence', 'bbox'.
        """
        if self.model is None:
            return []

        detections = []
        try:
            # OPTIMIZATION: Resize the frame to reduce payload size over the network
            # This makes the API request much faster and reduces lag.
            original_h, original_w = frame.shape[:2]
            inference_size = 320 # Ultra-small size for ultra-fast network upload
            small_frame = cv2.resize(frame, (inference_size, inference_size))

            # Use inference-sdk directly on the scaled numpy frame
            result = self.model.infer(small_frame, model_id=self.model_id)
            detections_raw = result.get("predictions", [])
            
            # Calculate scale ratios to map bounding boxes back to original size
            scale_x = original_w / inference_size
            scale_y = original_h / inference_size
            
            for pred in detections_raw:
                conf = pred.get("confidence", 0)
                if conf < self.confidence_threshold:
                    continue

                # Get coordinates from the small frame and scale them up
                x = pred["x"] * scale_x
                y = pred["y"] * scale_y
                w = pred["width"] * scale_x
                h = pred["height"] * scale_y
                
                x1 = int(x - w / 2)
                y1 = int(y - h / 2)
                x2 = int(x + w / 2)
                y2 = int(y + h / 2)
                
                label = pred.get("class", "pothole")

                detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                })
        except Exception as e:
            print(f"Pothole Detector: Inference failed - {e}")

        return detections

    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and warning overlay on the frame.

        Args:
            frame: The BGR image (numpy array).
            detections: List of detection dicts from detect().

        Returns:
            The annotated frame (modified in-place).
        """
        for det in detections:
            conf = det["confidence"]
            x1, y1, x2, y2 = map(int, det["bbox"])
            label = det.get("label", "pothole")

            # Red bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # Label with confidence
            text = f"{label} {conf:.0%}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            (tw, th), _ = cv2.getTextSize(text, font, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw, y1), (0, 0, 255), -1)
            cv2.putText(frame, text, (x1, y1 - 4), font, 0.6, (255, 255, 255), 2)

        # Warning banner at the top of the frame
        if detections:
            h, w = frame.shape[:2]
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 40), (0, 0, 200), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            warning = "!! POTHOLE DETECTED !!"
            cv2.putText(frame, warning, (w // 2 - 130, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def process_frame(self, frame):
        """
        Full pipeline: detect → draw → snapshot → log.

        Args:
            frame: The BGR image (numpy array).

        Returns:
            tuple: (annotated_frame, detections_list)
        """
        detections = self.detect(frame)
        annotated = self.draw_detections(frame, detections)

        if detections:
            self._save_snapshot_if_ready(annotated, detections)
            self._log_detections(detections)

        return annotated, detections

    def _save_snapshot_if_ready(self, frame, detections):
        """Save a snapshot image (respects cooldown to avoid flooding disk)."""
        now = time.time()
        if (now - self._last_snapshot_time) < self.snapshot_cooldown:
            return

        self._last_snapshot_time = now
        self._detection_count += 1

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pothole_{timestamp}_{self._detection_count}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)

        threading.Thread(
            target=self._write_image, args=(filepath, frame.copy()),
            daemon=True
        ).start()

        # Update the latest snapshot path for the first detection
        with self._lock:
            detections[0]["_snapshot_path"] = filepath

    @staticmethod
    def _write_image(path, frame):
        """Write image to disk in a background thread."""
        try:
            cv2.imwrite(path, frame)
            print(f"Pothole Detector: Snapshot saved → {path}")
        except Exception as e:
            print(f"Pothole Detector: Failed to save snapshot - {e}")

    def _log_detections(self, detections):
        """Append detections to the CSV log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(LOG_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                for det in detections:
                    snap = det.get("_snapshot_path", "")
                    x1, y1, x2, y2 = det["bbox"]
                    writer.writerow([
                        timestamp,
                        f"{det['confidence']:.4f}",
                        int(x1), int(y1), int(x2), int(y2),
                        snap,
                    ])
        except Exception as e:
            print(f"Pothole Detector: Failed to write log - {e}")

    def get_stats(self):
        """Return basic stats dict for the dashboard."""
        with self._lock:
            return {
                "model_loaded": self.model is not None,
                "total_detections": self._detection_count,
                "confidence_threshold": self.confidence_threshold,
            }
