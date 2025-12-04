# C:\Projelerim\OnlineExamMonitoringProject\audio_analyzer\run_audio.py
import os
import time
import json
import logging
import numpy as np
import torch
import pyaudio

from huggingface_hub import login
from pyannote.audio import Pipeline  # Önemli: v3 ile uyumlu

# --- HF Token (lütfen .env ya da ortam değişkeni kullanın) ---
HF_TOKEN = os.getenv("HUGGINGFACE_HUB_TOKEN")  # Ortam değişkeni
# login'ı da güvenli tutalım:
if HF_TOKEN:
    login(token=HF_TOKEN)

# --- Loglama ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename='audio_events.log',
    filemode='a',
    encoding='utf-8'
)

# --- Model Kurulumu ---
PIPELINE_OK = False
try:
    # token/use_auth_token farklı sürümlere göre değiştiği için esnek yaklaşım:
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=HF_TOKEN  # yeni API
        )
    except TypeError:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HF_TOKEN  # eski API
        )

    if torch.cuda.is_available():
        pipeline.to("cuda")  # v3 ile uyumlu kullanım
        print("Ses analizi için GPU kullanılıyor (Hızlı).")
    else:
        print("Ses analizi için CPU kullanılıyor (Başlangıçta yavaş olabilir).")

    PIPELINE_OK = True

except Exception as e:
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

def start_audio_analysis():
    if not PIPELINE_OK:
        print("Ses analizi modeli yüklenemediği için ses modülü başlatılamıyor.")
        return

    RATE = 16000
    CHUNK_DURATION_SEC = 3.0  # Her 3 saniyede bir analiz
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
            waveform = torch.from_numpy(audio_data).unsqueeze(0)  # (1, num_samples)

            try:
                diarization = pipeline({"waveform": waveform, "sample_rate": RATE})

                # Daha sağlam: unique label sayısı
                num_speakers = len(diarization.labels())

                if num_speakers > 1 and (time.time() - last_event_time > 10):
                    event_data = {
                        "timestamp": time.time(),
                        "event": f"Birden Fazla Konusmaci Algilandi ({num_speakers} kisi)",
                        "suspicion_score": 0.95
                    }
                    logging.info(json.dumps(event_data, ensure_ascii=False))
                    print(f"\n--- SES LOG: {event_data['event']} ---")
                    last_event_time = time.time()

            except Exception:
                # Sessizce devam et ama istersen debug için burayı loglayabilirsin
                pass

    except KeyboardInterrupt:
        print("\nSes analizi bitti.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    start_audio_analysis()