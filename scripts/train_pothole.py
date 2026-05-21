import os
import yaml
from ultralytics import YOLO

dataset_path = "/home/mahdi/.cache/kagglehub/datasets/mahyeks/pothrgbd-rgb-and-depth-images-of-potholes/versions/1/PUBLIC POTHOLE DATASET"

# Create dataset.yaml for YOLO
yaml_content = {
    "path": dataset_path,
    "train": "images",
    "val": "images",
    "nc": 1,
    "names": {0: "pothole"}
}

yaml_path = os.path.join(dataset_path, "dataset.yaml")
with open(yaml_path, "w") as f:
    yaml.dump(yaml_content, f, sort_keys=False)

print(f"Created {yaml_path}")

# Load a pretrained YOLOv8 Nano model (fastest)
print("Loading YOLOv8n model...")
model = YOLO("yolov8n.pt")

# Train the model
print("Starting training...")
results = model.train(
    data=yaml_path,
    epochs=15,          # 15 epochs is enough for a good initial result on 1000 images
    imgsz=640,
    batch=8,           # Small batch to save Jetson GPU memory
    project="runs/detect",
    name="pothole_model"
)

print("\n" + "="*50)
print("🎯 Training complete!")
print("Your new Pothole model is saved at: runs/detect/pothole_model/weights/best.pt")
print("="*50 + "\n")
