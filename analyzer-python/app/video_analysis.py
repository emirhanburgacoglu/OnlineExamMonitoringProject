# app/video_analysis.py

import cv2
import mediapipe as mp
import numpy as np
import math

# Mediapipe'in çizim yardımcılarını ve yüz ağı modelini hazırlayalım
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

def start_camera_feed():
    """
    Kamerayı açar, canlı görüntü üzerinde baş pozisyonunu analiz eder (sağ/sol/merkez)
    ve sonucu ekranda gösterir. 'q' tuşuna basıldığında çıkar.
    """
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Hata: Kamera başlatılamadı.")
        return

    print("Kamera başlatıldı. Baş pozisyonu analizi aktif. Çıkmak için 'q' tuşuna basın.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)
        # Performans için görüntüyü BGR'dan RGB'ye çevir ve işlenemez yap
        frame.flags.writeable = False
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = face_mesh.process(rgb_frame)

        # Çizim için görüntüyü tekrar yazılabilir yap
        frame.flags.writeable = True

        img_h, img_w, img_c = frame.shape
        face_3d = []
        face_2d = []
        direction_text = "Yuz Kadraj Disinda" # Varsayılan durum

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Baş pozisyonunu tahmin etmek için kullanılacak kilit noktalar
                # Burun ucu, çene, sol gözün sol köşesi, sağ gözün sağ köşesi, sol ağız köşesi, sağ ağız köşesi
                for idx, lm in enumerate(face_landmarks.landmark):
                    if idx in [33, 263, 1, 61, 291, 199]:
                        # Görüntüdeki 2D koordinatlar
                        x, y = int(lm.x * img_w), int(lm.y * img_h)
                        face_2d.append([x, y])
                        # Modeldeki 3D koordinatlar
                        face_3d.append([x, y, lm.z])
                
                if len(face_2d) == 6 and len(face_3d) == 6:
                    face_2d = np.array(face_2d, dtype=np.float64)
                    face_3d = np.array(face_3d, dtype=np.float64)

                    # Kamera matrisi
                    focal_length = 1 * img_w
                    cam_matrix = np.array([[focal_length, 0, img_h / 2],
                                           [0, focal_length, img_w / 2],
                                           [0, 0, 1]])
                    dist_matrix = np.zeros((4, 1), dtype=np.float64)

                    # PnP Çözücüsü
                    success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)

                    # Rotasyon matrisini al
                    rmat, jac = cv2.Rodrigues(rot_vec)

                    # Açıları al
                    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

                    # Derece cinsinden açıları al
                    x = angles[0] * 360  # Pitch (Eğim)
                    y = angles[1] * 360  # Yaw (Sapma)
                    z = angles[2] * 360  # Roll (Yuvarlanma)

                    # Şüpheli durumu belirle (Yaw açısına göre)
                    if y < -10:
                        direction_text = "Sola Bakiyor"
                    elif y > 10:
                        direction_text = "Saga Bakiyor"
                    elif x < -10:
                        direction_text = "Asagi Bakiyor"
                    elif x > 10:
                        direction_text = "Yukari Bakiyor"
                    else:
                        direction_text = "Merkeze Bakiyor"
        
        # Ekrana durumu yazdır
        cv2.putText(frame, direction_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        # Görüntüyü göster
        cv2.imshow('Online Sınav - Baş Pozisyon Analizi', frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Kamera kapatıldı.")