import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Camera failed")
        break

    cv2.imwrite("camera_test.jpg", frame)
    print("Saved test image: camera_test.jpg")
    break

cap.release()