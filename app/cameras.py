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
        "video/x-raw, format=(string)BGR ! appsink drop=true max-buffers=1"
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

def open_camera(index, width, height, fps):
    """
    Attempts to open a Jetson CSI camera using GStreamer.
    """
    pipeline = gstreamer_pipeline(
        sensor_id=index,
        display_width=width,
        display_height=height,
        framerate=30 # Using 30 as it's a stable capture framerate for IMX219
    )
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {index} with GStreamer.")
        return None
    
    # We do not set CAP_PROP here because GStreamer pipeline string already handles resolution and framerate
    return cap

def read_frame(cap):
    """
    Reads a single frame from the camera.
    Returns (success, frame).
    """
    if cap is None or not cap.isOpened():
        return False, None
    return cap.read()

def release_all(cameras):
    """
    Releases all camera objects provided in the list.
    """
    for cap in cameras:
        if cap is not None and cap.isOpened():
            cap.release()
