import cv2
import mediapipe as mp
import json
import math
import time
import threading
import pyttsx3
from datetime import datetime

# Initialize the text-to-speech engine
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # Speed of speech
except Exception as e:
    print(f"Warning: Could not initialize speech engine: {e}")
    # Create a dummy engine that just prints instead
    class DummyEngine:
        def say(self, text):
            print(f"Speech: {text}")
        def runAndWait(self):
            pass
    engine = DummyEngine()

# Lock for thread-safe voice feedback
voice_lock = threading.Lock()
last_feedback_time = {}  # Track when feedback was last given for each joint

# Load pose database
try:
    with open('pose_database.json', 'r') as f:
        pose_database = json.load(f)
    print(f"Loaded {len(pose_database)} poses from database")
except FileNotFoundError:
    print("Error: pose_database.json not found")
    pose_database = {}

# MediaPipe setup
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
drawing_spec = mp_drawing.DrawingSpec(thickness=2, circle_radius=1)

# Calculate angle between three points
def calculate_angle(a, b, c):
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle

# Extract angles from landmarks
def extract_angles(landmarks):
    def get_coords(index):
        return [landmarks[index].x, landmarks[index].y]

    joints = {
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

    angles = {}
    for name, (a, b, c) in joints.items():
        angles[name] = calculate_angle(get_coords(a), get_coords(b), get_coords(c))

    return angles

# Compare angles between current pose and stored pose
def classify_pose(current_angles):
    min_diff = float('inf')
    best_match = None
    confidence = 0
    
    for pose_name, data in pose_database.items():
        total_diff = 0
        joint_count = 0
        
        for joint, angle in data["angles"].items():
            if joint in current_angles:
                total_diff += abs(current_angles[joint] - angle)
                joint_count += 1
                
        if joint_count > 0:
            avg_diff = total_diff / joint_count
            if avg_diff < min_diff:
                min_diff = avg_diff
                best_match = pose_name
                confidence = max(0, 100 - avg_diff)  # Simple confidence calculation
    
    return best_match, confidence

# Get corrections with severity levels
def get_corrections(current_angles, reference_angles):
    corrections = []
    for joint, ref_angle in reference_angles.items():
        if joint in current_angles:
            diff = abs(current_angles[joint] - ref_angle)
            
            # Define severity levels
            if diff > 30:
                severity = "major"
            elif diff > 15:
                severity = "moderate"
            else:
                severity = "minor"
                
            if diff > 10:  # Only suggest corrections for noticeable differences
                direction = "higher" if current_angles[joint] < ref_angle else "lower"
                human_joint = joint.replace('_', ' ')
                corrections.append({
                    "joint": joint,
                    "human_joint": human_joint,
                    "diff": diff,
                    "direction": direction,
                    "severity": severity,
                    "message": f"Adjust your {human_joint} — make it {direction}. Off by {diff:.1f} degrees."
                })
    
    # Sort by severity
    return sorted(corrections, key=lambda x: x["diff"], reverse=True)

# Speak feedback in a separate thread to avoid blocking
def speak_feedback(message):
    def speak_worker():
        with voice_lock:
            engine.say(message)
            engine.runAndWait()
    
    threading.Thread(target=speak_worker).start()

# Start webcam pose detection
def start_pose_correction(target_pose=None):
    cap = cv2.VideoCapture(0)
    
    # Increase resolution if camera supports it
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # If target pose is provided, validate it exists
    if target_pose and target_pose not in pose_database:
        print(f"Warning: Target pose '{target_pose}' not found in database")
        target_pose = None
    
    current_pose = None
    hold_start_time = None
    hold_duration = 0
    feedback_cooldown = 3  # seconds between feedback for the same joint
    
    with mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7) as pose:
        print("Starting yoga pose correction...")
        print("Press 'q' to quit, 'p' to toggle target pose mode")
        
        # If no target pose, speak available poses
        if not target_pose:
            available_poses = list(pose_database.keys())
            pose_list = ", ".join(p.replace("_", " ") for p in available_poses[:5])
            speak_feedback(f"Available poses include {pose_list} and others")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
            
            # Flip the frame horizontally for a mirror effect
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB and process with MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)
            
            # Draw pose landmarks
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=drawing_spec
                )
                
                # Calculate angles and classify pose
                landmarks = results.pose_landmarks.landmark
                angles = extract_angles(landmarks)
                
                if target_pose:
                    # Practice mode: focus on the target pose
                    predicted_pose, confidence = target_pose, 0
                    reference_angles = pose_database[target_pose]["angles"]
                    corrections = get_corrections(angles, reference_angles)
                    
                    # Calculate average alignment with target pose
                    total_diff = sum(c["diff"] for c in corrections)
                    confidence = max(0, 100 - (total_diff / len(corrections) if corrections else 0))
                else:
                    # Detection mode: identify the closest pose
                    predicted_pose, confidence = classify_pose(angles)
                    if predicted_pose:
                        reference_angles = pose_database[predicted_pose]["angles"]
                        corrections = get_corrections(angles, reference_angles)
                    else:
                        corrections = []
                
                # Update pose tracking for hold time
                if predicted_pose != current_pose:
                    current_pose = predicted_pose
                    hold_start_time = time.time()
                    hold_duration = 0
                    speak_feedback(f"I see {current_pose.replace('_', ' ')}")
                else:
                    hold_duration = time.time() - hold_start_time
                
                # Display pose and confidence
                pose_display = predicted_pose.replace("_", " ") if predicted_pose else "Unknown"
                cv2.putText(frame, f'Pose: {pose_display}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(frame, f'Confidence: {confidence:.1f}%', (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(frame, f'Hold: {hold_duration:.1f}s', (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Display corrections with color-coded severity
                for i, correction in enumerate(corrections[:3]):  # Show top 3 corrections
                    severity = correction["severity"]
                    color = (0, 0, 255) if severity == "major" else (0, 165, 255) if severity == "moderate" else (0, 255, 255)
                    cv2.putText(frame, correction["message"], (10, 120 + i * 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Provide voice feedback for the most important correction
                current_time = time.time()
                if corrections and confidence < 90:
                    # Choose the most severe correction
                    worst_correction = corrections[0]
                    joint = worst_correction["joint"]
                    
                    # Check if we haven't given feedback for this joint recently
                    if joint not in last_feedback_time or (current_time - last_feedback_time[joint]) > feedback_cooldown:
                        feedback_msg = f"{worst_correction['human_joint']} should be {worst_correction['direction']}"
                        speak_feedback(feedback_msg)
                        last_feedback_time[joint] = current_time
                
                # Give positive reinforcement for good alignment
                if hold_duration > 3 and confidence > 85 and not corrections:
                    if hold_duration % 5 < 0.1:  # Every ~5 seconds
                        speak_feedback("Good job maintaining the pose")
            else:
                cv2.putText(frame, "No pose detected", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Display mode information
            mode_text = f"Mode: {'Practice - ' + target_pose.replace('_', ' ') if target_pose else 'Detection'}"
            cv2.putText(frame, mode_text, (10, frame.shape[0] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show the frame
            cv2.imshow('Yoga Pose Correction', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('p'):
                # Toggle practice mode
                if target_pose:
                    target_pose = None
                    speak_feedback("Switched to detection mode")
                else:
                    # Select first pose in database
                    target_pose = next(iter(pose_database.keys()))
                    speak_feedback(f"Practice mode: {target_pose.replace('_', ' ')}")
            elif key == ord('n') and target_pose:
                # Cycle to next pose
                poses = list(pose_database.keys())
                current_idx = poses.index(target_pose)
                target_pose = poses[(current_idx + 1) % len(poses)]
                speak_feedback(f"Now practicing {target_pose.replace('_', ' ')}")
            
    cap.release()
    cv2.destroyAllWindows()
    print("Yoga pose correction ended.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Yoga Pose Correction System')
    parser.add_argument('--pose', type=str, help='Target pose to practice')
    args = parser.parse_args()
    
    # Print available poses for reference
    print("Available poses:")
    for i, pose in enumerate(pose_database.keys()):
        print(f"{i+1}. {pose.replace('_', ' ')}")
    
    # Start the system
    start_pose_correction(args.pose)