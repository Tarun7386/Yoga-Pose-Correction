import cv2
import mediapipe as mp
import json
import math
# from scripts.geometry import calculate_angle, extract_angles

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from geometry import calculate_angle, extract_angles

# Load your pose database
with open('pose_database.json', 'r') as f:
    pose_database = json.load(f)

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Compare angles between current pose and stored pose
def classify_pose(current_angles):
    min_diff = float('inf')
    best_match = None
    for pose_name, data in pose_database.items():
        total_diff = 0
        for joint, angle in data["angles"].items():
            if joint in current_angles:
                total_diff += abs(current_angles[joint] - angle)
        if total_diff < min_diff:
            min_diff = total_diff
            best_match = pose_name
    return best_match

# Suggest corrections
def get_corrections(current_angles, reference_angles):
    corrections = []
    for joint, ref_angle in reference_angles.items():
        if joint in current_angles:
            diff = abs(current_angles[joint] - ref_angle)
            if diff > 15:  # Tolerance threshold
                direction = "higher" if current_angles[joint] < ref_angle else "lower"
                corrections.append(f"Adjust your {joint.replace('_', ' ')} — make it {direction}.")
    return corrections

# Start webcam pose detection
cap = cv2.VideoCapture(0)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    print("Starting webcam... Press 'q' to quit.")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            angles = extract_angles(landmarks)

            predicted_pose = classify_pose(angles)
            corrections = get_corrections(angles, pose_database[predicted_pose]["angles"])

            # Display on screen
            cv2.putText(frame, f'Pose: {predicted_pose}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            for i, correction in enumerate(corrections[:3]):  # Show top 3 corrections
                cv2.putText(frame, correction, (10, 60 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Draw pose
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        else:
            cv2.putText(frame, "No pose detected.", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow('Yoga Pose Correction', frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print("Webcam closed.")