# app/video_analysis.py

import cv2
import mediapipe as mp
import numpy as np
import time

def start_camera_feed():
    """
    Kamerayı açar, iki gözün ortalamasını alarak stabil göz takibi yapar.
    Şüpheli durum tespiti için daha toleranslı ikinci bir eşik kullanır.
    """
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(0)

    gaze_timer_start = None
    GAZE_THRESHOLD_SECONDS = 3.5
    suspicious = False

    # --- YENİ TOLERANS EŞİKLERİ ---
    # Zamanlayıcının başlaması için aşılması gereken, daha geniş aralık.
    # Bu değerlerle oynayarak hassasiyeti ayarlayabilirsin.
    SUSPICION_LOWER_THRESHOLD = 0.35
    SUSPICION_UPPER_THRESHOLD = 0.65
    
    # Ekranda yazının değişmesi için gereken hassas aralık.
    DISPLAY_LOWER_THRESHOLD = 0.4
    DISPLAY_UPPER_THRESHOLD = 0.6


    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)

        img_h, img_w, img_c = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        status_text = "Merkeze Bakiyor"
        is_looking_away = False
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            left_eye_width = landmarks[133].x - landmarks[33].x
            left_ratio = (landmarks[473].x - landmarks[33].x) / left_eye_width if left_eye_width != 0 else 0.5

            right_eye_width = landmarks[263].x - landmarks[362].x
            right_ratio = (landmarks[468].x - landmarks[362].x) / right_eye_width if right_eye_width != 0 else 0.5
            
            avg_ratio = (left_ratio + right_ratio) / 2.0

            # 1. Ekranda ne yazacağını belirle (Hassas Eşik)
            if avg_ratio < DISPLAY_LOWER_THRESHOLD:
                status_text = "Saga Bakiyor"
            elif avg_ratio > DISPLAY_UPPER_THRESHOLD:
                status_text = "Sola Bakiyor"

            # 2. Zamanlayıcının başlayıp başlamayacağını belirle (Toleranslı Eşik)
            if avg_ratio < SUSPICION_LOWER_THRESHOLD or avg_ratio > SUSPICION_UPPER_THRESHOLD:
                is_looking_away = True

            # Zamanlayıcı ve şüphe mantığı
            if is_looking_away:
                if gaze_timer_start is None:
                    gaze_timer_start = time.time()
                
                elapsed_time = time.time() - gaze_timer_start
                if elapsed_time > GAZE_THRESHOLD_SECONDS:
                    suspicious = True
            else:
                gaze_timer_start = None
                suspicious = False
        else:
            status_text = "Yuz Kadraj Disinda"
            suspicious = True

        if suspicious:
            cv2.putText(frame, "SUPHELI DURUM!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            cv2.putText(frame, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        cv2.imshow('ONLINE SINAV - SUPHELI DURUM TAKIBI', frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Kamera kapatıldı.")