# Central configuration for the Vision + Voice AI Assistant

CAMERA_0_INDEX = 0
CAMERA_1_INDEX = 1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 15

DISPLAY_ON_JETSON = True
WEB_PORT = 8000
SPEECH_COOLDOWN_SECONDS = 5

USE_AI_DETECTION = True  # AI is now integrated
USE_TWO_CAMERAS = False

# --- Arduino Settings ---
USE_ARDUINO = True
ARDUINO_PORT = None         # None = auto-detect, or set e.g. "/dev/ttyUSB0"
ARDUINO_BAUD_RATE = 115200

# --- Telegram Bot Settings ---
USE_TELEGRAM = True
TELEGRAM_BOT_TOKEN = "8977103710:AAFKAJWXzUqTbLMo8nEWXuPdDESkb861bMc"
TELEGRAM_SEND_INTERVAL = 0  # 0 to disable auto sensor updates (only send on collision)
