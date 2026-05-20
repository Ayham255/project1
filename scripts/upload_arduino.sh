#!/bin/bash
# Upload Arduino sketch to Arduino Nano
# Usage: ./scripts/upload_arduino.sh [PORT]
# Example: ./scripts/upload_arduino.sh /dev/ttyUSB0

export PATH="$HOME/.local/bin:$PATH"

SKETCH_DIR="arduino/sensor_sender"
FQBN="arduino:avr:nano"

# Auto-detect port or use argument
if [ -n "$1" ]; then
    PORT="$1"
else
    # Try common ports
    for p in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1; do
        if [ -e "$p" ]; then
            PORT="$p"
            break
        fi
    done
fi

if [ -z "$PORT" ]; then
    echo "❌ Arduino not found! Connect it via USB first."
    echo "Available ports:"
    arduino-cli board list
    exit 1
fi

echo "🔧 Compiling sketch..."
arduino-cli compile --fqbn "$FQBN" "$SKETCH_DIR"
if [ $? -ne 0 ]; then
    echo "❌ Compilation failed!"
    exit 1
fi

echo ""
echo "📤 Uploading to $PORT..."
arduino-cli upload --fqbn "$FQBN" --port "$PORT" "$SKETCH_DIR"
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Upload successful!"
    echo "Arduino is ready on $PORT"
else
    echo ""
    echo "❌ Upload failed!"
    echo "Try: sudo chmod 666 $PORT"
    echo "Or:  sudo usermod -a -G dialout $USER"
    exit 1
fi
