import math

def calculate_angle(a, b, c):
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle

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
