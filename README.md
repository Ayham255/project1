# Vision + Voice AI Assistant (Rev.1)

A clean, modular AI vision and voice assistant built for a Jetson device with two cameras and a USB speaker.

## Project Goal
The goal of this project is to create an integrated pipeline that:
1. Reads from two connected cameras.
2. Runs AI object detection.
3. Estimates object distance.
4. Generates text descriptions (e.g., "Person detected...").
5. Converts text to speech and plays it through the audio output.
6. Displays the camera output on the Jetson monitor.

*Note: Dockerization will be added later after the application is fully stable.*

## Folder Structure
```
vision_voice_ai/
├── app/                  # Main application code (cameras, speech, detectors, logic)
├── tests/                # Individual test scripts for hardware verification
├── scripts/              # Bash scripts for running tests and the main app
├── models/               # (Future) Directory for YOLO/TensorRT models
├── data/                 # (Future) Data storage
├── logs/                 # (Future) Application logs
├── requirements-base.txt # Base safe Python requirements
└── requirements-ai.txt   # AI Python requirements (placeholder for now)
```

## Setup & Environment

To activate the Python virtual environment:
```bash
source venv/bin/activate
```

## How to Run System Check
We've provided a comprehensive script to check connected cameras, audio devices, OS, and CUDA availability:
```bash
./scripts/check_system.sh
```

## How to Run Tests

### Test Camera 0
```bash
source venv/bin/activate
DISPLAY=:0 python3 tests/test_camera_0.py
```

### Test Camera 1
```bash
source venv/bin/activate
DISPLAY=:0 python3 tests/test_camera_1.py
```

### Test Two Cameras Simultaneously
```bash
./scripts/run_camera_test.sh
```

### Test Audio Output
```bash
./scripts/run_audio_test.sh
```

## How to Run Main App

The main application integrates cameras, a dummy object detector, and the speech engine:
```bash
./scripts/run_app.sh
```
Press `ESC` on the display window to exit cleanly.
