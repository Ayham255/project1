#!/bin/bash
echo "=============================="
echo "   SYSTEM CHECK SCRIPT"
echo "=============================="

echo "[1] Date & Hostname"
date
hostname
echo ""

echo "[2] Current User"
whoami
echo ""

echo "[3] Python & Pip Versions"
python3 --version
pip --version
echo ""

echo "[4] OS Info"
cat /etc/os-release | head -n 3
echo ""

echo "[5] /dev/video Devices"
ls -l /dev/video* 2>/dev/null || echo "No video devices found in /dev/"
echo ""

echo "[6] v4l2-ctl Camera List"
v4l2-ctl --list-devices 2>/dev/null || echo "v4l2-ctl not found"
echo ""

echo "[7] USB Devices"
lsusb
echo ""

echo "[8] Audio Cards (aplay -l)"
aplay -l 2>/dev/null || echo "aplay not found"
echo ""

echo "[9] PulseAudio Sinks"
pactl list short sinks 2>/dev/null || echo "pactl not found"
echo ""

echo "[10] NVIDIA/CUDA Info"
nvcc --version 2>/dev/null || echo "nvcc not found in path"
dpkg -l | grep -i nvidia 2>/dev/null || echo "nvidia packages not checked"
echo ""

echo "System Check Complete."
