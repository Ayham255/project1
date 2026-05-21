import cv2
import time
import os
from app import config
from app.cameras import open_camera, read_frame, release_all
from app.detector import YoloDetector
from app.distance import estimate_distance, get_direction
from app.speech import SpeechEngine
import threading
from app.translations import translate_label
from app import web_dashboard

def main():
    print("Starting Vision + Voice AI Assistant...")
    
    speech_engine = SpeechEngine(cooldown_seconds=config.SPEECH_COOLDOWN_SECONDS)
    
    # --- Arduino Setup ---
    arduino = None
    if config.USE_ARDUINO:
        from app.arduino_reader import ArduinoReader
        arduino = ArduinoReader(
            port=config.ARDUINO_PORT,
            baud_rate=config.ARDUINO_BAUD_RATE
        )

    # --- Telegram Bot Setup ---
    telegram = None
    if config.USE_TELEGRAM:
        from app.telegram_bot import TelegramBot
        telegram = TelegramBot(
            token=config.TELEGRAM_BOT_TOKEN,
            send_interval=config.TELEGRAM_SEND_INTERVAL
        )
        if arduino:
            telegram.set_arduino_reader(arduino)

    # --- Fall Detection Callback ---
    def on_fall_detected(fall_info):
        """Called when Arduino detects a fall."""
        name = fall_info.get("person_name", "شخص")
        speech_engine.speak(f"تحذير! سقوط {name}! يرجى المساعدة!")
        if telegram:
            telegram.send_fall_alert(fall_info)

    if arduino:
        arduino.set_on_fall(on_fall_detected)
        arduino.start()

    if telegram:
        telegram.start()
        telegram.broadcast("🟢 *النظام يعمل الآن!*\nأرسل /help لعرض الأوامر.")
    
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

    # --- Pothole Detector Setup ---
    pothole_det = None
    if config.USE_POTHOLE_DETECTION:
        from app.pothole_detector import PotholeDetector
        pothole_det = PotholeDetector(
            api_key=config.POTHOLE_ROBOFLOW_API_KEY,
            model_id=config.POTHOLE_ROBOFLOW_MODEL_ID,
            confidence_threshold=config.POTHOLE_CONFIDENCE,
            snapshot_cooldown=config.POTHOLE_SNAPSHOT_COOLDOWN,
        )
        if pothole_det.is_ready():
            print("Pothole Detector: Ready.")
        else:
            print("Pothole Detector: Model not loaded – feature disabled.")
            pothole_det = None
    
    # Start Web Dashboard
    print(f"Starting Web Dashboard on port {config.WEB_PORT}...")
    web_dashboard.system_state["status"] = "running"
    web_dashboard.system_state["cameras_active"] = len(cameras)
    web_dashboard.system_state["pothole_model_loaded"] = (pothole_det is not None)
    threading.Thread(target=web_dashboard.run_server, daemon=True).start()
    
    # State for async pothole detection
    pothole_state = {"is_inferencing": False, "last_annotated": None}
    
    try:
        while True:
            for idx, cap in enumerate(cameras):
                ret, frame = read_frame(cap)
                if not ret:
                    continue
                
                if idx == 0:
                    # Run YOLO Object detection on Camera 0
                    detections = detector.detect(frame)
                    
                    detected_labels = set()
                    
                    # Draw detections and estimate distance
                    for det in detections:
                        label_eng = det.get("label", "object")
                        label_ar = translate_label(label_eng)
                        conf = det.get("confidence", 0.0)
                        bbox = det.get("bbox", [0, 0, 0, 0])
                        
                        x1, y1, x2, y2 = map(int, bbox)
                        
                        direction = get_direction(bbox, frame.shape[1])
                        distance_msg = estimate_distance(det)
                        
                        # Add label and its relative direction in Arabic
                        detected_labels.add(f"{label_ar} {direction}")
                        
                        # Draw bbox
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        text = f"{label_eng} ({conf:.2f})"
                        cv2.putText(frame, text, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Generate speech message for all unique detected objects
                    if detected_labels:
                        objects_str = " و ".join(detected_labels)
                        speech_text = f"أرى {objects_str}."
                        speech_engine.speak(speech_text)
                        
                        # Send detection to Telegram
                        if telegram:
                            telegram.update_detection(speech_text)
                    
                    # Update Web Dashboard frame with YOLO feed
                    web_dashboard.latest_frame = frame.copy()
                
                elif idx == 1:
                    # --- Pothole detection pass on Camera 1 (Async) ---
                    if pothole_det:
                        if not pothole_state["is_inferencing"]:
                            pothole_state["is_inferencing"] = True
                            
                            def pothole_task(f):
                                try:
                                    annotated, pothole_hits = pothole_det.process_frame(f)
                                    pothole_state["last_annotated"] = annotated
                                    if pothole_hits:
                                        web_dashboard.system_state["pothole_detections"] = pothole_det.get_stats()["total_detections"]
                                        speech_engine.speak("تحذير! حفرة في الطريق!")
                                        # Intermittent buzzer + vibration alert on Arduino
                                        if arduino:
                                            arduino.pothole_alert()
                                        if telegram:
                                            best = max(pothole_hits, key=lambda d: d['confidence'])
                                            snap = best.get('_snapshot_path', '')
                                            telegram.broadcast(
                                                f"🕳️ *تنبيه حفرة!*\n"
                                                f"الثقة: *{best['confidence']:.0%}*\n"
                                                f"⏰ {time.strftime('%H:%M:%S')}"
                                            )
                                            # Send snapshot image if saved
                                            if snap and os.path.exists(snap):
                                                telegram.broadcast_photo(snap)
                                finally:
                                    pothole_state["is_inferencing"] = False
                            
                            # Run inference in background to prevent lag
                            threading.Thread(target=pothole_task, args=(frame.copy(),), daemon=True).start()
                        
                        # Display the latest annotated frame if available, otherwise show the raw frame
                        if pothole_state["last_annotated"] is not None:
                            frame = pothole_state["last_annotated"]
                
                # Display the frame if requested
                if config.DISPLAY_ON_JETSON:
                    try:
                        window_name = "YOLO (Cam 0)" if idx == 0 else "Pothole (Cam 1)"
                        cv2.imshow(window_name, frame)
                    except cv2.error:
                        # GTK backend not available (running headless/SSH)
                        config.DISPLAY_ON_JETSON = False
                        print("Display not available (headless mode). Running without GUI.")
            
            # Only check for ESC key if display is active
            if config.DISPLAY_ON_JETSON:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    print("ESC pressed. Exiting...")
                    break
            else:
                time.sleep(0.01)  # Small delay to avoid CPU spin
                
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")
    finally:
        print("Cleaning up resources...")
        release_all(cameras)
        if config.DISPLAY_ON_JETSON:
            cv2.destroyAllWindows()
        if arduino:
            arduino.stop()
        if telegram:
            telegram.broadcast("🔴 *النظام توقف.*")
            time.sleep(1)
            telegram.stop()

if __name__ == "__main__":
    main()
