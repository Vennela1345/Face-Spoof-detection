# Face Spoof Detection Using Machine Learning

## 🔹 Project Overview
This project implements a **Face Spoof Detection (Anti-Spoofing) system** using **Machine Learning** and **Computer Vision**.  
It detects whether a face presented to a camera is **live** or a **spoof** (e.g., photo, video, or mask).

The system uses **MediaPipe** to detect facial landmarks and analyzes **blinks** and **head movements** to verify liveness.

---

## 🔹 Features
- Real-time face detection using webcam
- Spoof detection based on:
  - Eye blink patterns
  - Head movements (left, right, up, down)
- Image/video upload for testing spoof attacks
- Django-based web interface:
  - Login / Logout
  - Real-time webcam scan (20 seconds)
  - Authentication based on live face activity

---

## 🔹 Technology Stack
- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Django  
- **Machine Learning / Computer Vision:** Python, OpenCV, MediaPipe, NumPy, Pandas  
- **Other:** Pickle (.pkl) files for trained models

---

## 🔹 Installation

1. Clone the repository:
```bash
git clone https://github.com/<your-username>/face-spoof-detection.git
cd face-spoof-detection
