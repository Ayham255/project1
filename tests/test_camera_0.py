import cv2

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=640,
    display_height=480,
    framerate=30,
    flip_method=2,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def test_camera(index=0):
    print(f"Testing camera {index} with GStreamer...")
    pipeline = gstreamer_pipeline(sensor_id=index)
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print(f"Warning: GStreamer pipeline failed for camera {index}. Falling back to standard V4L2...")
        cap = cv2.VideoCapture(index)
        
    if not cap.isOpened():
        print(f"Error: Cannot open camera {index} with any method.")
        return
        
    print(f"Successfully opened camera {index}. Press ESC to close.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break
                
            cv2.imshow(f"Camera {index} Test", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27: # ESC
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"Camera {index} test complete.")

if __name__ == "__main__":
    test_camera(0)
