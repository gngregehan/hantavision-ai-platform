# HantaVision AI Clinical Imaging Platform

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/gngregehan/hantavision-ai-platform)

Profesyonel, yapay zeka destekli Hantavirüs ilişki analizi için React + FastAPI tabanlı medikal görüntü işleme platformu.

## Özellikler

- React/Vite tabanlı modern medikal dashboard
- JWT ile giriş/kayıt, admin paneli ve analiz geçmişi
- Güvenli dosya yükleme, format/size doğrulama ve görüntü kalite kontrolü
- Çok aşamalı model orkestrasyonu: görsel türü sınıflandırma, medikal analiz, kemirgen tespiti, mikroskop/doku analizi, Hantavirüs ilişki sınıflandırması, ROI açıklanabilirlik
- Görsel türü, Hantavirüs sonucu, güven skoru, güvenilirlik, kalite, risk seviyesi, uyarılar ve PDF rapor çıktısı
- Esnek veritabanı katmanı: SQLite/PostgreSQL veya Firebase Cloud Firestore
- Docker destekli dağıtım yapısı

## Güvenlik ve Klinik Not

Bu sistem tıbbi karar destek platformu olarak tasarlanmıştır. Üretilen sonuçlar kesin tıbbi teşhis değildir ve uzman değerlendirmesi gerektirir.

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

Dağıtımdan önce `.env` veya Render ortam değişkenlerinde `SECRET_KEY`, admin parolası ve CORS alanları değiştirilmelidir.

## Veritabanı

Varsayılan yerel kullanım SQLite ile çalışır. Render dağıtımı `DATABASE_BACKEND=auto` kullanır: Firebase servis hesabı verilmediyse Render PostgreSQL ile devam eder, `FIREBASE_SERVICE_ACCOUNT_JSON` eklenince Firestore'a geçer.

Firebase Cloud Firestore kullanmak için:

1. Firebase Console'da bir proje açın ve Cloud Firestore'u etkinleştirin.
2. Project settings > Service accounts bölümünden yeni private key JSON dosyası üretin.
3. Render `hantavision-ai-api` servisinde şu environment variable değerlerini girin:

```bash
DATABASE_BACKEND=auto
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_JSON={...service-account-json...}
FIREBASE_COLLECTION_PREFIX=hantavision_
```

`FIREBASE_SERVICE_ACCOUNT_JSON` ham JSON veya base64 encode edilmiş JSON olabilir. `DATABASE_BACKEND=firebase` kullanılırsa servis hesabı zorunludur; `auto` kullanılırsa servis hesabı yokken Postgres yedek olarak çalışır.

## Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:8080`
- API: `http://localhost:8000`
- API dokümantasyonu: `http://localhost:8000/docs`

## Render Deployment

Repo kökünde `render.yaml` bulunur. Render butonu üç kaynak oluşturur:

- `hantavision-ai-api`: FastAPI Docker web service
- `hantavision-ai-frontend`: Vite static site
- `hantavision-ai-db`: PostgreSQL veritabanı

Firebase servis hesabı Render env'e eklenene kadar canlı ortam PostgreSQL kullanır. Firebase bilgileri eklendiğinde kullanıcılar, analiz kayıtları ve admin özetleri Cloud Firestore koleksiyonlarına yazılır.

Deploy bağlantısı: https://render.com/deploy?repo=https://github.com/gngregehan/hantavision-ai-platform

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
