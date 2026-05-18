import time
import os
import threading

class SpeechEngine:
    def __init__(self, cooldown_seconds=3):
        self.cooldown_seconds = cooldown_seconds
        self.last_spoken_time = 0.0
        self.last_message = ""

    def speak(self, text):
        # Print text before speaking
        print(f"Speaking: '{text}'")
        self.last_message = text
        
        current_time = time.time()
        if (current_time - self.last_spoken_time) < self.cooldown_seconds:
            print("Speech skipped due to cooldown.")
            return
            
        self.last_spoken_time = current_time
        
        # Run speech in a background thread so it doesn't freeze the camera feed
        threading.Thread(target=self._speak_task, args=(text,), daemon=True).start()

    def _speak_task(self, text):
        # Using spd-say directly via os.system is much more stable 
        # than pyttsx3 in multithreaded environments on Linux Jetson.
        os.system(f"spd-say '{text}'")
