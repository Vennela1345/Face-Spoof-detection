import threading
import time
import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import cv2
import spoof_detect  # Your detection logic file

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        User.objects.create_user(username=username, password=password)
        return redirect('login')
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('detect_choice')
    return render(request, 'login.html')

def detect_choice_view(request):
    return render(request, 'detect_choice.html')


# ---------- LIVE DETECTION --------------
def start_live_detection():
    start_time = time.time()
    cap = cv2.VideoCapture(0)
    state = spoof_detect.get_initial_state()

    with spoof_detect.mp_face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=True) as face_mesh:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            processed = spoof_detect.process_frame(frame, state, face_mesh)
            cv2.imshow("Live Detection", processed)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if time.time() - start_time > 30:
                break

    cap.release()
    cv2.destroyAllWindows()
    save_detection_result(state)

def live_detect_view(request):
    thread = threading.Thread(target=start_live_detection)
    thread.start()
    return render(request, 'detection_running.html')


# ---------- IMAGE DETECTION --------------
def image_detect_view(request):
    if request.method == 'POST' and request.FILES['image']:
        image_file = request.FILES['image']
        fs = FileSystemStorage(location='media/uploaded_files/')
        filename = fs.save(image_file.name, image_file)
        file_path = os.path.join('media/uploaded_files/', filename)

        frame = cv2.imread(file_path)
        state = spoof_detect.get_initial_state()

        with spoof_detect.mp_face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True) as face_mesh:
            spoof_detect.process_frame(frame, state, face_mesh)

        save_detection_result(state)
        return redirect('result')
    return HttpResponse("Upload failed")


# ---------- VIDEO DETECTION --------------
def video_detect_view(request):
    if request.method == 'POST' and request.FILES['video']:
        video_file = request.FILES['video']
        fs = FileSystemStorage(location='media/uploaded_files/')
        filename = fs.save(video_file.name, video_file)
        file_path = os.path.join('media/uploaded_files/', filename)

        cap = cv2.VideoCapture(file_path)
        state = spoof_detect.get_initial_state()

        with spoof_detect.mp_face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=True) as face_mesh:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                spoof_detect.process_frame(frame, state, face_mesh)

        cap.release()
        save_detection_result(state)
        return redirect('result')
    return HttpResponse("Upload failed")


# ---------- RESULT DISPLAY --------------
def result_view(request):
    try:
        with open("detection_result.txt", "r") as f:
            result = f.read()
    except:
        result = "No result"
    return render(request, 'result.html', {'result': result})


# ---------- LOGOUT --------------
def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- Save Result --------------
def save_detection_result(state):
    if state['blink_count'] > 0 or state['head_movement_count'] > 0:
        result = "REAL"
    else:
        result = "SPOOF"
    with open("detection_result.txt", "w") as f:
        f.write(result)
