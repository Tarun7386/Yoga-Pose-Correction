# yoga-pose/scripts/extract_landmarks.py

import os
import cv2
import json
import mediapipe as mp

DATASET_DIR = "../dataset"
OUTPUT_FILE = "../pose_landmarks.json"

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True)
results_data = {}

# Loop through folders (poses)
for pose_name in os.listdir(DATASET_DIR):
    pose_folder = os.path.join(DATASET_DIR, pose_name)
    if not os.path.isdir(pose_folder):
        continue

    results_data[pose_name] = []

    for filename in os.listdir(pose_folder):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        
        image_path = os.path.join(pose_folder, filename)
        image = cv2.imread(image_path)
        if image is None:
            continue

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = pose.process(image_rgb)

        if result.pose_landmarks:
            landmarks = {}
            for i, lm in enumerate(result.pose_landmarks.landmark):
                landmarks[i] = (lm.x, lm.y, lm.visibility)
            
            results_data[pose_name].append({
                "image": filename,
                "landmarks": landmarks
            })

# Save all pose landmarks to a JSON file
with open(OUTPUT_FILE, 'w') as f:
    json.dump(results_data, f, indent=2)

print(f"Landmark extraction complete. Saved to {OUTPUT_FILE}")
