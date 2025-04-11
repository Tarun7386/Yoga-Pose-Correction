# Yoga Pose Correction System

This system provides real-time feedback for yoga poses using computer vision and voice guidance.

## Features

- Real-time pose detection using webcam
- Comparison with reference poses from database
- Visual feedback with pose identification
- Voice feedback for pose corrections
- Graphical user interface for pose selection
- Practice mode for specific poses
- Auto-detection mode for free practice

## Requirements

- Python 3.7+
- Webcam
- The following Python packages:
  - opencv-python
  - mediapipe
  - pyttsx3
  - numpy

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### GUI Application

Start the graphical user interface:

```
python yoga_training_app.py
```

This will launch a window where you can:
- Browse available yoga poses
- View pose descriptions and instructions
- Choose a specific pose to practice
- Start auto-detection mode

### Command Line Usage

You can also use the pose correction system directly:

```
python yoga_pose_corrector.py [--pose POSE_NAME]
```

Options:
- `--pose POSE_NAME`: Specify a target pose to practice (optional)

### Controls:
- Press 'q' to quit
- Press 'p' to toggle between practice mode and detection mode
- Press 'n' to cycle to the next pose (in practice mode)

## How It Works

1. The system captures video from your webcam
2. MediaPipe's pose detection identifies key body landmarks
3. Joint angles are calculated from these landmarks
4. These angles are compared to reference poses in the database
5. The system provides visual and voice feedback on your pose

## Customizing Poses

The system uses `pose_database.json` to store reference poses. You can add your own poses:

1. Capture images of the pose
2. Use the scripts in the `scripts` folder to process these images
3. Add the generated angles to your database

## Folder Structure

- `yoga_training_app.py`: Main GUI application
- `yoga_pose_corrector.py`: Core pose detection and correction logic
- `pose_database.json`: Reference poses data
- `scripts/`: Utility scripts for database creation
- `requirements.txt`: Required Python packages

## Future Improvements

- Add support for pose sequences/flows
- Improve accuracy of pose detection
- Add progress tracking
- Add video recording and playback
- Mobile app version

## License

This project is licensed under the MIT License - see the LICENSE file for details.