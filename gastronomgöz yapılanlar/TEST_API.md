# API Test Komutları

## 1️⃣ Register (Yeni Kullanıcı Kaydı)

```bash
curl -X POST http://localhost:5001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "filiz@example.com",
    "password": "test12345",
    "name": "Filiz Çakır"
  }' | python3 -m json.tool
```

## 2️⃣ Login (Giriş Yap)

```bash
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "filiz@example.com",
    "password": "test12345"
  }' | python3 -m json.tool
```

## 3️⃣ Sunucu Durumunu Kontrol Et

```bash
curl http://localhost:5001/ | python3 -m json.tool
```

## 4️⃣ Health Check

```bash
curl http://localhost:5001/health | python3 -m json.tool
```

---

## Not:
- Sunucu çalışıyor olmalı (port 5001)
- Her komutu yeni bir terminal penceresinde çalıştırabilirsin
- Yanıtlar JSON formatında gelecek
