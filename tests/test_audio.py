import os
import sys

def test_audio():
    print("Testing audio output...")
    text_to_speak = "Audio test is working"
    
    try:
        import pyttsx3
        print("Using pyttsx3 for TTS...")
        engine = pyttsx3.init()
        engine.say(text_to_speak)
        engine.runAndWait()
        print("Audio test via pyttsx3 completed.")
        return
    except ImportError:
        print("pyttsx3 not found. Falling back to espeak...")
    except Exception as e:
        print(f"pyttsx3 error: {e}. Falling back to espeak...")
        
    # Fallback to espeak
    try:
        # We check if espeak is installed first
        status = os.system("which espeak > /dev/null")
        if status == 0:
            print("Using espeak for TTS...")
            os.system(f"espeak -ven+m3 '{text_to_speak}'")
            print("Audio test via espeak completed.")
        else:
            print("espeak is not installed.")
            print("Fallback 2: using speaker-test...")
            os.system("speaker-test -t sine -f 440 -l 1")
            print("Audio test via speaker-test completed.")
    except Exception as e:
        print(f"Failed to play audio: {e}")

if __name__ == "__main__":
    test_audio()
