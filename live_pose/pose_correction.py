import json
from scripts.geometry import calculate_angle

# Load the ideal database
with open("pose_database.json", "r") as f:
    pose_database = json.load(f)

# Set your joint angle pairs
angle_joints = {
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

# Helper to compute all angles from a landmark list
def extract_angles(landmarks):
    angles = {}
    for name, (a, b, c) in angle_joints.items():
        angles[name] = calculate_angle(landmarks[a], landmarks[b], landmarks[c])
    return angles

# Helper to compare with ideal and find the closest pose
def classify_pose(current_angles):
    best_match = None
    lowest_diff = float("inf")
    for pose_name, data in pose_database.items():
        ideal_angles = data["angles"]
        diff = sum(abs(current_angles[j] - ideal_angles.get(j, 0)) for j in current_angles)
        if diff < lowest_diff:
            lowest_diff = diff
            best_match = pose_name
    return best_match

# Helper to give feedback
def get_corrections(current_angles, ideal_angles, threshold=15):
    feedback = []
    for joint, current in current_angles.items():
        ideal = ideal_angles.get(joint)
        if ideal is None:
            continue
        if abs(current - ideal) > threshold:
            direction = "higher" if current < ideal else "lower"
            feedback.append(f"Adjust your {joint.replace('_', ' ')} — it should be {direction}.")
    return feedback
