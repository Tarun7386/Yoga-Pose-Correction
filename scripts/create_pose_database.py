import sys
import os
import json
sys.path.append(os.path.abspath(".."))  # 👈 this tells Python to go up one level

from scripts.geometry import calculate_angle
from tqdm import tqdm


# Load landmarks from file
with open("../pose_landmarks.json", "r") as f:
    pose_data = json.load(f)

pose_database = {}

# Define key joints to calculate angles between (triplets of landmark indices)
# Format: (name, point1, vertex_point, point2)
ANGLE_DEFINITIONS = {
    "left_elbow": [11, 13, 15],
    "right_elbow": [12, 14, 16],
    "left_shoulder": [13, 11, 23],
    "right_shoulder": [14, 12, 24],
    "left_hip": [11, 23, 25],
    "right_hip": [12, 24, 26],
    "left_knee": [23, 25, 27],
    "right_knee": [24, 26, 28],
    "left_ankle": [25, 27, 29],
    "right_ankle": [26, 28, 30],
}

for pose_name, entries in tqdm(pose_data.items(), desc="Processing poses"):
    all_angles = {k: [] for k in ANGLE_DEFINITIONS}

    for entry in entries:
        landmarks = entry["landmarks"]

        # Convert landmarks keys to int (some may be str)
        landmarks = {int(k): v for k, v in landmarks.items()}

        for angle_name, (a, b, c) in ANGLE_DEFINITIONS.items():
            if a in landmarks and b in landmarks and c in landmarks:
                angle = calculate_angle(landmarks[a], landmarks[b], landmarks[c])
                all_angles[angle_name].append(angle)

    # Average angles across all images for this pose
    avg_angles = {}
    for key, values in all_angles.items():
        if values:
            avg_angles[key] = sum(values) / len(values)

    pose_database[pose_name] = {
        "angles": avg_angles,
        "description": f"{pose_name} yoga pose",
        "instructions": [f"Focus on keeping your {joint} aligned." for joint in avg_angles.keys()]
    }

# Save to JSON
with open("../pose_database.json", "w") as f:
    json.dump(pose_database, f, indent=2)

print("Pose database created successfully.")
