# app/video_analysis.py

import cv2
import mediapipe as mp

# Mediapipe'in çizim yardımcılarını ve yüz ağı modelini hazırlayalım
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

def start_camera_feed():
    """
    Kamerayı açar, canlı görüntü üzerinde Mediapipe ile yüz ağı tespiti yapar
    ve sonucu ekranda gösterir. 'q' tuşuna basıldığında çıkar.
    """
    # Yüz ağı modelini, daha hassas çalışması için bazı parametrelerle başlatalım
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,  # Sadece tek bir yüzü tespit et
        refine_landmarks=True,  # Gözler ve dudaklar gibi alanlarda daha detaylı noktalar sağla
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Hata: Kamera başlatılamadı.")
        return

    print("Kamera başlatıldı. Yüz tespiti aktif. Çıkmak için 'q' tuşuna basın.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Görüntü alınamadı, döngü sonlandırılıyor.")
            break

        # Görüntüyü daha performanslı işlemek için yazılabilir değil olarak işaretle
        frame.flags.writeable = False
        # OpenCV BGR formatında okur, Mediapipe ise RGB bekler. Renk dönüşümü yapalım.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Görüntüyü işle ve yüz landmark'larını (işaret noktalarını) bul
        results = face_mesh.process(rgb_frame)

        # Görüntüyü tekrar yazılabilir yap
        frame.flags.writeable = True

        # Eğer bir yüz tespit edildiyse, landmark'ları çizdir
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Yüzdeki ağ bağlantılarını çizdiriyoruz
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1) # Yeşil, ince çizgiler
                )

        # İşlenmiş görüntüyü ekranda göster
        cv2.imshow('Online Sınav - Yüz Tespiti', frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    # Kaynakları serbest bırak
    face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Kamera kapatıldı.")