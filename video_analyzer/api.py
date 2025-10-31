# C:\Projelerim\OnlineExamMonitoringProject\video_analyzer\api.py

import cv2
import mediapipe as mp
import time
import threading
from fastapi import FastAPI
# --- YENİ EKLENEN SATIR ---
from fastapi.middleware.cors import CORSMiddleware
# --- ---

# FastAPI uygulamasını oluştur
app = FastAPI()

# --- YENİ BÖLÜM: CORS AYARLARI ---
# .NET projenizin çalıştığı adresi buraya ekliyoruz.
origins = [
    "http://localhost:5018", # SİZİN .NET PROJE ADRESİNİZ
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Sadece bu adreslerden gelen isteklere izin ver
    allow_credentials=True,
    allow_methods=["*"], # Tüm metotlara (GET, POST vb.) izin ver
    allow_headers=["*"], # Tüm başlıklara izin ver
)
# --- CORS AYARLARI SONU ---


# Global Değişken: Analiz Sonucunu Saklamak İçin
latest_event = {
    "timestamp": time.time(),
    "event": "Sistem Başlatılıyor...",
    "suspicion_score": 0.0
}

# --- Göz Takibi Mantığı (Değişiklik yok) ---
def video_analysis_thread():
    global latest_event
    
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Hata: Video kamera başlatılamadı.")
        return

    gaze_timer_start = None
    GAZE_THRESHOLD_SECONDS = 3.5
    
    HORIZONTAL_LOWER_THRESHOLD = 0.30
    HORIZONTAL_UPPER_THRESHOLD = 0.56
    VERTICAL_LOWER_THRESHOLD = 0.32
    VERTICAL_UPPER_THRESHOLD = 0.55

    last_event_time = 0

    while True:
        success, frame = cap.read()
        if not success:
            time.sleep(0.1)
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        suspicious = False
        status_text = "Merkeze Bakiyor"
        is_looking_away = False

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            h_left_eye_width = landmarks[133].x - landmarks[33].x
            h_left_ratio = (landmarks[473].x - landmarks[33].x) / h_left_eye_width if h_left_eye_width != 0 else 0.5
            h_right_eye_width = landmarks[263].x - landmarks[362].x
            h_right_ratio = (landmarks[468].x - landmarks[362].x) / h_right_eye_width if h_right_eye_width != 0 else 0.5
            avg_horizontal_ratio = (h_left_ratio + h_right_ratio) / 2.0

            v_left_eye_height = landmarks[145].y - landmarks[159].y
            v_left_ratio = (landmarks[473].y - landmarks[159].y) / v_left_eye_height if v_left_eye_height != 0 else 0.5
            v_right_eye_height = landmarks[374].y - landmarks[386].y
            v_right_ratio = (landmarks[468].y - landmarks[386].y) / v_right_eye_height if v_right_eye_height != 0 else 0.5
            avg_vertical_ratio = (v_left_ratio + v_right_ratio) / 2.0

            if avg_horizontal_ratio < HORIZONTAL_LOWER_THRESHOLD:
                is_looking_away, status_text = True, "Saga Bakiyor"
            elif avg_horizontal_ratio > HORIZONTAL_UPPER_THRESHOLD:
                is_looking_away, status_text = True, "Sola Bakiyor"
            elif avg_vertical_ratio < VERTICAL_LOWER_THRESHOLD:
                is_looking_away, status_text = True, "Yukari Bakiyor"
            elif avg_vertical_ratio > VERTICAL_UPPER_THRESHOLD:
                is_looking_away, status_text = True, "Asagi Bakiyor"
                
        else:
            suspicious, status_text = True, "Yuz Kadraj Disinda"

        if is_looking_away:
            if gaze_timer_start is None: gaze_timer_start = time.time()
            if time.time() - gaze_timer_start > GAZE_THRESHOLD_SECONDS:
                suspicious = True
        else:
            gaze_timer_start = None
        
        current_time = time.time()
        
        if suspicious and (current_time - last_event_time > 5):
            latest_event = {"timestamp": current_time, "event": status_text, "suspicion_score": 0.8}
            print(f"API Guncellendi: {status_text}")
            last_event_time = current_time
        elif not is_looking_away and not suspicious:
            if latest_event["event"] != "NORMAL":
                 latest_event = {"timestamp": current_time, "event": "NORMAL", "suspicion_score": 0.0}
                 print(f"API Guncellendi: NORMAL")
                 last_event_time = current_time

        time.sleep(0.01)

@app.get("/")
def read_root():
    return {"mesaj": "Video Analiz API'si Aktif"}

@app.get("/latest_event")
def get_latest_event():
    return latest_event

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=video_analysis_thread, daemon=True)
    thread.start()
    print("Video analiz thread'i arkaplanda başlatıldı.")