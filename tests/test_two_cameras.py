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

def test_two_cameras(idx0=0, idx1=1):
    print(f"Testing cameras {idx0} and {idx1} together...")
    
    pipe0 = gstreamer_pipeline(sensor_id=idx0)
    pipe1 = gstreamer_pipeline(sensor_id=idx1)
    
    cap0 = cv2.VideoCapture(pipe0, cv2.CAP_GSTREAMER)
    cap1 = cv2.VideoCapture(pipe1, cv2.CAP_GSTREAMER)
    
    cam0_ok = cap0.isOpened()
    cam1_ok = cap1.isOpened()
    
    if not cam0_ok:
        print(f"Warning: Could not open camera {idx0}")
    if not cam1_ok:
        print(f"Warning: Could not open camera {idx1}")
        
    if not cam0_ok and not cam1_ok:
        print("Error: No cameras could be opened.")
        return
        
    print("Press ESC to close.")
    
    try:
        while True:
            if cam0_ok:
                ret0, frame0 = cap0.read()
                if ret0:
                    cv2.imshow(f"Camera {idx0}", frame0)
                else:
                    print(f"Failed to read from camera {idx0}")
                    
            if cam1_ok:
                ret1, frame1 = cap1.read()
                if ret1:
                    cv2.imshow(f"Camera {idx1}", frame1)
                else:
                    print(f"Failed to read from camera {idx1}")
                    
            key = cv2.waitKey(1) & 0xFF
            if key == 27: # ESC
                break
    finally:
        if cam0_ok:
            cap0.release()
        if cam1_ok:
            cap1.release()
        cv2.destroyAllWindows()
        print("Dual camera test complete.")

if __name__ == "__main__":
    test_two_cameras(0, 1)
