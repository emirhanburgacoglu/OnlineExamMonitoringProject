# C:\Projelerim\OnlineExamMonitoringProject\audio_analyzer\run_audio.py

import pyaudio
import numpy as np
import time
import torch
from pyannote.audio.pipelines import SpeakerDiarization
import logging
import json

# --- HUGGING FACE TOKEN'INIZI BURAYA YAPIŞTIRIN ---
HF_TOKEN = "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"
# --- ---

# --- Loglama Kurulumu ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename='audio_events.log',
    filemode='a',
    encoding='utf-8'
)

# --- Model Kurulumu ---
try:
    pipeline = SpeakerDiarization.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=HF_TOKEN) # Not: 'use_auth_token' değil, güncel parametre 'token'
    
    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
        print("Ses analizi için GPU kullanılıyor (Hızlı).")
    else:
        print("Ses analizi için CPU kullanılıyor (Başlangıçta yavaş olabilir).")
    PIPELINE_OK = True
except Exception as e:
    # İzinlerin alınmadığı durumlar için detaylı hata mesajı
    if "403 Client Error" in str(e) or "gated repo" in str(e):
        print("\n!!! ERİŞİM HATASI !!!")
        print("Kullanmak istediğiniz pyannote modeli korumalıdır.")
        print("Lütfen aşağıdaki 3 linki ziyaret edip kullanım koşullarını kabul edin:")
        print("1. https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("2. https://huggingface.co/pyannote/segmentation-3.0")
        print("3. https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb")
        print("-" * 50)
    else:
        print(f"HATA: pyannote modeli yüklenemedi. Token'ınızı veya internet bağlantınızı kontrol edin. Hata: {e}")
    PIPELINE_OK = False

def start_audio_analysis():
    if not PIPELINE_OK:
        print("Ses analizi modeli yüklenemediği için ses modülü başlatılamıyor.")
        return

    RATE = 16000
    CHUNK_DURATION_SEC = 3.0 # Her 3 saniyede bir analiz et
    CHUNK_SAMPLES = int(RATE * CHUNK_DURATION_SEC)
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                    input=True, frames_per_buffer=CHUNK_SAMPLES)
    
    print("\nSes Analizi Başladı. İkinci Ses Tespiti Aktif.")
    last_event_time = 0

    try:
        while True:
            data = stream.read(CHUNK_SAMPLES, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            waveform = torch.from_numpy(audio_data).unsqueeze(0)
            
            try:
                # Modeli çalıştır ve konuşmacı günlüğünü çıkar
                diarization = pipeline({"waveform": waveform, "sample_rate": RATE})
                
                # Tespit edilen benzersiz konuşmacı sayısını say
                speakers = set(track for segment, track, label in diarization.itertracks(yield_label=True))
                num_speakers = len(speakers)
                
                # Eğer 1'den fazla konuşmacı varsa...
                if num_speakers > 1:
                    # Aynı olayı art arda loglamamak için 10 saniye bekle
                    if (time.time() - last_event_time > 10):
                        event_data = {
                            "timestamp": time.time(),
                            "event": f"Birden Fazla Konusmaci Algilandi ({num_speakers} kisi)",
                            "suspicion_score": 0.95
                        }
                        # Olayı log dosyasına kaydet ve terminale yaz
                        logging.info(json.dumps(event_data, ensure_ascii=False))
                        print(f"\n--- SES LOG: {event_data['event']} ---")
                        
                        last_event_time = time.time()
                        
            except Exception as e:
                pass

    except KeyboardInterrupt:
        print("\nSes analizi bitti.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    start_audio_analysis()