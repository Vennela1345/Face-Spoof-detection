
import cv2
import mediapipe as mp
import numpy as np
from tkinter import Tk, filedialog
import math

# Initialize MediaPipe
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# EAR landmark indices
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# EAR calculation
def calculate_ear(landmarks, eye_points, w, h):
    p1 = np.array([landmarks[eye_points[1]].x * w, landmarks[eye_points[1]].y * h])
    p2 = np.array([landmarks[eye_points[2]].x * w, landmarks[eye_points[2]].y * h])
    p3 = np.array([landmarks[eye_points[5]].x * w, landmarks[eye_points[5]].y * h])
    p4 = np.array([landmarks[eye_points[4]].x * w, landmarks[eye_points[4]].y * h])
    p0 = np.array([landmarks[eye_points[0]].x * w, landmarks[eye_points[0]].y * h])
    p5 = np.array([landmarks[eye_points[3]].x * w, landmarks[eye_points[3]].y * h])
    vertical1 = np.linalg.norm(p2 - p4)
    vertical2 = np.linalg.norm(p1 - p3)
    horizontal = np.linalg.norm(p0 - p5)
    return (vertical1 + vertical2) / (2.0 * horizontal)

# Head pose estimation
def estimate_head_movement(landmarks, w, h):
    image_points = np.array([
        (landmarks[33].x * w, landmarks[33].y * h),
        (landmarks[263].x * w, landmarks[263].y * h),
        (landmarks[1].x * w, landmarks[1].y * h),
        (landmarks[61].x * w, landmarks[61].y * h),
        (landmarks[291].x * w, landmarks[291].y * h)
    ], dtype="double")
    model_points = np.array([
        (-30.0, 0.0, 0.0),
        (30.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (-25.0, -30.0, 0.0),
        (25.0, -30.0, 0.0)
    ])
    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([[focal_length, 0, center[0]],
                              [0, focal_length, center[1]],
                              [0, 0, 1]], dtype="double")
    dist_coeffs = np.zeros((4, 1))
    success, rotation_vector, _ = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )
    if not success:
        return None
    rotation_mat, _ = cv2.Rodrigues(rotation_vector)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_mat)
    return angles

# State dict
def get_initial_state():
    return {
        'blink_threshold': 0.25,
        'closed_frames': 0,
        'closed_threshold': 3,
        'blink_count': 0,
        'head_movement_count': 0,
        'prev_pitch': None,
        'prev_yaw': None,
        'angle_threshold': 10
    }

# Frame processor
def process_frame(frame, state, face_mesh):
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    label = "Spoof"
    color = (0, 0, 255)
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                frame, face_landmarks, mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1))
            landmarks = face_landmarks.landmark
            left_ear = calculate_ear(landmarks, LEFT_EYE, w, h)
            right_ear = calculate_ear(landmarks, RIGHT_EYE, w, h)
            ear = (left_ear + right_ear) / 2
            if ear < state['blink_threshold']:
                state['closed_frames'] += 1
            else:
                if state['closed_frames'] >= state['closed_threshold']:
                    state['blink_count'] += 1
                state['closed_frames'] = 0
            angles = estimate_head_movement(landmarks, w, h)
            if angles:
                pitch, yaw, _ = angles
                if state['prev_pitch'] is not None:
                    if abs(pitch - state['prev_pitch']) > state['angle_threshold'] or abs(yaw - state['prev_yaw']) > state['angle_threshold']:
                        state['head_movement_count'] += 1
                state['prev_pitch'] = pitch
                state['prev_yaw'] = yaw
            if state['blink_count'] > 0 or state['head_movement_count'] > 0:
                label = "Real"
                color = (0, 255, 0)
    else:
        cv2.putText(frame, "No face detected", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
    cv2.putText(frame, f"{label}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    cv2.putText(frame, f"Blinks: {state['blink_count']}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Head Moves: {state['head_movement_count']}", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return frame

# Image upload

def upload_and_process_image():
    Tk().withdraw()
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if not path:
        return
    image = cv2.imread(path)
    with mp_face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True) as static_face_mesh:
        state = get_initial_state()
        processed = process_frame(image, state, static_face_mesh)
        while True:
            cv2.imshow("Image Detection", processed)
            if cv2.waitKey(1) & 0xFF != 255:
                break
        cv2.destroyWindow("Image Detection")

# Video upload

def upload_and_process_video():
    Tk().withdraw()
    path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
    if not path:
        return
    cap = cv2.VideoCapture(path)
    with mp_face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=True) as video_face_mesh:
        state = get_initial_state()
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            processed = process_frame(frame, state, video_face_mesh)
            cv2.imshow("Video Detection", processed)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyWindow("Video Detection")

# Webcam

def webcam_mode():
    cap = cv2.VideoCapture(0)
    state = get_initial_state()
    with mp_face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=True) as face_mesh:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            processed = process_frame(frame, state, face_mesh)
            cv2.putText(processed, "Press 'i'=Image, 'v'=Video, 's'=Stop", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("Webcam Spoof Detection", processed)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                break
            elif key == ord('i'):
                upload_and_process_image()
            elif key == ord('v'):
                upload_and_process_video()
    cap.release()
    cv2.destroyAllWindows()

# Start
if __name__ == "__main__":
    webcam_mode()