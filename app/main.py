import cv2
import time
from app import config
from app.cameras import open_camera, read_frame, release_all
from app.detector import YoloDetector
from app.distance import estimate_distance, get_direction
from app.speech import SpeechEngine

def main():
    print("Starting Vision + Voice AI Assistant...")
    
    speech_engine = SpeechEngine(cooldown_seconds=config.SPEECH_COOLDOWN_SECONDS)
    
    cameras = []
    
    # Open Camera 0
    print(f"Opening Camera 0 (Index {config.CAMERA_0_INDEX})...")
    cap0 = open_camera(config.CAMERA_0_INDEX, config.FRAME_WIDTH, config.FRAME_HEIGHT, config.FPS)
    if cap0:
        cameras.append(cap0)
        
    # Open Camera 1 if requested
    if config.USE_TWO_CAMERAS:
        print(f"Opening Camera 1 (Index {config.CAMERA_1_INDEX})...")
        cap1 = open_camera(config.CAMERA_1_INDEX, config.FRAME_WIDTH, config.FRAME_HEIGHT, config.FPS)
        if cap1:
            cameras.append(cap1)
            
    if not cameras:
        print("Error: No cameras could be opened. Exiting.")
        return

    # Initialize YOLO detector AFTER opening cameras so NVMM buffers get memory first!
    detector = YoloDetector()
    
    try:
        while True:
            for idx, cap in enumerate(cameras):
                ret, frame = read_frame(cap)
                if not ret:
                    continue
                
                # Run detection
                detections = detector.detect(frame)
                
                detected_labels = set()
                
                # Draw detections and estimate distance
                for det in detections:
                    label = det.get("label", "object")
                    conf = det.get("confidence", 0.0)
                    bbox = det.get("bbox", [0, 0, 0, 0])
                    
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    direction = get_direction(bbox, frame.shape[1])
                    distance_msg = estimate_distance(det)
                    
                    # Add label and its relative direction
                    detected_labels.add(f"{label} {direction}")
                    
                    # Draw bbox
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    text = f"{label} {direction} ({conf:.2f})"
                    cv2.putText(frame, text, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Generate speech message for all unique detected objects
                if detected_labels:
                    objects_str = ", ".join(detected_labels)
                    speech_text = f"I see: {objects_str}."
                    speech_engine.speak(speech_text)
                
                # Display the frame if requested
                if config.DISPLAY_ON_JETSON:
                    window_name = f"Camera {idx}"
                    cv2.imshow(window_name, frame)
            
            # Exit on ESC key
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                print("ESC pressed. Exiting...")
                break
                
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")
    finally:
        print("Cleaning up resources...")
        release_all(cameras)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
