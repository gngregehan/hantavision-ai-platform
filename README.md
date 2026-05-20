# HantaVision AI Clinical Imaging Platform

Profesyonel, yapay zeka destekli Hantavirüs ilişki analizi için React + FastAPI tabanlı medikal görüntü işleme platformu.

## Özellikler

- React/Vite tabanlı modern medikal dashboard
- JWT ile giriş/kayıt, admin paneli ve analiz geçmişi
- Güvenli dosya yükleme, format/size doğrulama ve görüntü kalite kontrolü
- Çok aşamalı model orkestrasyonu: görsel türü sınıflandırma, medikal analiz, kemirgen tespiti, mikroskop/doku analizi, Hantavirüs ilişki sınıflandırması, Grad-CAM/ROI açıklanabilirlik
- Görsel türü, Hantavirüs sonucu, güven skoru, güvenilirlik, kalite, risk seviyesi, uyarılar ve PDF rapor çıktısı
- SQLAlchemy veritabanı katmanı: lokal SQLite varsayılanı, Docker Compose ile PostgreSQL
- Docker destekli dağıtım yapısı

## Güvenlik ve Klinik Not

Bu sistem tıbbi karar destek platformu olarak tasarlanmıştır. Üretilen sonuçlar kesin tıbbi teşhis değildir ve uzman değerlendirmesi gerektirir.

Backend içinde bulunan `HantavirusPipeline`, üretim mimarisini bozmadan PyTorch/TensorFlow ağırlıklarıyla değiştirilebilecek model arayüzünü sağlar. Klinik üretim kullanımı için doğrulanmış veri setleri, regülasyon süreci, model validasyonu, izlenebilirlik ve güvenlik testleri tamamlanmalıdır.

## Yerel Çalıştırma

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Tarayıcı: `http://127.0.0.1:5173`

Varsayılan admin kullanıcısı:

- E-posta: `admin@hantavision.local`
- Parola: `ChangeMe!2026`

Dağıtımdan önce `.env` içinde `SECRET_KEY`, admin parolası ve CORS alanları değiştirilmelidir.

## Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:8080`
- API: `http://localhost:8000`
- API dokümantasyonu: `http://localhost:8000/docs`

## API Endpointleri

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/me`
- `POST /api/analyses`
- `GET /api/analyses`
- `GET /api/analyses/{analysis_id}`
- `GET /api/analyses/{analysis_id}/report.pdf`
- `GET /api/model-stack`
- `GET /api/admin/model-performance`
- `GET /api/admin/overview`

## Deployment

- Frontend: Vercel, Netlify veya statik Nginx container
- Backend: Render, Railway, AWS ECS veya Fly.io
- Veritabanı: PostgreSQL managed service
- Dosya depolama: Lokal volume, S3 uyumlu bucket veya hastane içi güvenli obje depolama

Üretim için önerilen ekler: HTTPS zorunluluğu, rate limit, audit log, antivirus scanning, DICOM desteği, PHI/PII maskeleme, model registry, model kartları ve klinik onay iş akışı.
