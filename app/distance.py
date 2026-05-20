def estimate_distance(detection):
    """
    Estimates the distance to a detected object.
    
    NOTE: Real distance estimation requires either:
    1. Stereo camera calibration (using disparity maps between two cameras)
    2. A depth camera (RealSense, ZED, etc.)
    3. An ultrasonic or LiDAR sensor
    4. Known real-world object dimensions (focal length * real_height / object_height_in_pixels)
    
    For now, this is a placeholder function.
    """
    label = detection.get("label", "object")
    if label == "person":
        return "على بعد حوالي مترين"
    return "مسافة غير معروفة"

def get_direction(bbox, frame_width):
    """
    Returns the relative direction of the object based on its bounding box center.
    """
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2
    
    third = frame_width / 3
    if center_x < third:
        return "على يسارك"
    elif center_x > 2 * third:
        return "على يمينك"
    else:
        return "أمامك"
