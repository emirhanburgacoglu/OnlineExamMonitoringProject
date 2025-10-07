# Online Exam Monitoring Project - Kod Yapısı ve Mimarisi

Bu belge, `OnlineExamMonitoringProject` projesinin klasör ve dosya yapısını, her bir bileşenin sorumluluğunu ve aralarındaki ilişkiyi açıklamaktadır. Projeye yeni katılan geliştiriciler için bir başlangıç rehberi niteliğindedir.

---

## 🏛️ Yüksek Seviye Mimari

Proje, iki ana bağımsız servisten oluşan bir **mikroservis mimarisi** üzerine kurulmuştur:

1.  **`analyzer-python`**: Görüntü ve ses verilerini işleyen, yapay zekâ tabanlı analiz motoru.
2.  **`dashboard-dotnet`**: Analiz sonuçlarını gösteren, öğretmenlerin kullandığı web tabanlı arayüz.

Bu iki servis, bir API aracılığıyla ve gerçek zamanlı mesajlaşma protokolleri (WebSocket/SignalR) üzerinden iletişim kurar.

---

## 📂 Klasör ve Dosya Açıklamaları

### 📁 `analyzer-python/`
Bu klasör, projenin Python ile yazılmış analiz motorunu içerir. Tüm yapay zekâ mantığı, veri işleme ve API bu servis tarafından yönetilir.

-   **`app/`**: Analiz mantığının çekirdeğini barındırır. Bu klasördeki modüller, ham veriyi alıp anlamlı çıktılara dönüştürür.
    -   **`__init__.py`**: Bu klasörün bir Python paketi olarak tanınmasını sağlar.
    -   **`video_analysis.py`**: Gelen video karelerinden yüz tespiti, baş pozu tahmini, bakış yönü analizi ve duygu tanıma gibi görsel işlemleri yapar. Kullandığı kütüphaneler: `OpenCV`, `Mediapipe`, `DeepFace`.
    -   **`audio_analysis.py`**: Gelen ses parçalarından konuşma aktivitesi (VAD), çoklu konuşmacı tespiti (diarization) ve arka plan gürültüsü analizi gibi ses işlemlerini yapar. Kullandığı kütüphaneler: `webrtcvad`, `pyannote.audio`.
    -   **`fusion.py`**: Video ve ses analiz modüllerinden gelen ham sonuçları alır. Bu sonuçları bir skorlama mantığı ile birleştirerek (`score = w1*gaze + w2*speakers...`) şüpheli bir "olay" olup olmadığına karar verir.
-   **`api/`**: Analiz servisinin dış dünya ile iletişim kurduğu web arayüzünü (API) içerir.
    -   **`main.py`**: `FastAPI` veya `Flask` kullanılarak yazılmış API endpoint'lerini barındırır. İstemcilerden (öğrencinin tarayıcısı) gelen video/ses verilerini kabul eder ve bunları `app/` içindeki ilgili analiz modüllerine yönlendirir.
-   **`run.py`**: Python web sunucusunu (örn: Uvicorn, Gunicorn) başlatan ana script. Projeyi çalıştırmak için `python run.py` komutu kullanılır.
-   **`requirements.txt`**: Bu Python projesinin çalışması için gereken tüm kütüphanelerin ( `opencv-python`, `fastapi`, `mediapipe` vb.) listesi. `pip install -r requirements.txt` ile kurulur.
-   **`venv/`**: *[Git tarafından takip edilmez]* Bu projeye özel Python sanal ortamının dosyalarını içerir.

---

### 📁 `dashboard-dotnet/`
Bu klasör, ASP.NET Core ile geliştirilen ve öğretmenler tarafından kullanılan web tabanlı kontrol panelini içerir.

-   **`Controllers/`**: Gelen HTTP isteklerini işleyen ve `View`'lara veri gönderen C# sınıflarını içerir. (MVC deseni için)
-   **`Models/`**: Veritabanı tablolarını temsil eden C# sınıflarını (`POCO` - Plain Old CLR Object) barındırır.
    -   **`User.cs`, `Session.cs`, `Event.cs`, `Clip.cs`**: Veritabanındaki `users`, `sessions`, `events` ve `clips` tablolarının kod karşılıklarıdır.
-   **`Data/`**: Veritabanı erişim katmanını içerir.
    -   **`AppDbContext.cs`**: Entity Framework Core için veritabanı bağlantısını ve tablo ilişkilerini yöneten ana context sınıfı.
-   **`Pages/` (veya `Views/`)**: Kullanıcının gördüğü HTML, Razor veya Blazor bileşenlerini içerir.
-   **`Dashboard.sln`**: Visual Studio için projenin ana "solution" dosyası.
-   **`appsettings.json`**: Veritabanı bağlantı dizgisi, API anahtarları gibi yapılandırma ayarlarını içerir.

---

### 📁 `database/`
Veritabanı ile ilgili statik dosyaları ve script'leri barındırır.

-   **`schema.sql`**: Proje için gerekli tüm veritabanı tablolarını (`users`, `sessions`, `events` vb.) oluşturan SQL script'i. Temiz bir veritabanı kurulumu için kullanılır.
-   **`seed.sql`**: Geliştirme ve test aşamasında kullanılmak üzere veritabanına örnek veriler (test kullanıcıları, sahte oturumlar vb.) ekleyen SQL script'i.

---

### 📁 `docs/`
Proje ile ilgili teknik dokümantasyonları içerir.

-   **`database-design.md`**: Veritabanı şemasının ER (Entity-Relationship) diyagramını, tablo açıklamalarını ve alanların ne anlama geldiğini detaylandıran doküman.

---
