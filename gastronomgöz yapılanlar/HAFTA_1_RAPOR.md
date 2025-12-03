# GastronomGöz - Hafta 1 İlerleme Raporu

**Öğrenci:** Filiz Çakır
**Tarih:** 9 Kasım 2025
**Proje:** GastronomGöz - AI Tabanlı Yemek Tanıma ve Kalori Hesaplama Sistemi

---

## 📋 Bu Hafta Yapılanlar

### 1. Backend Altyapısı Kurulumu ✅

**Oluşturulan Klasör Yapısı:**
```
backend/
├── api/              # API endpoint'leri
│   ├── auth.py       # Kimlik doğrulama
│   ├── user.py       # Kullanıcı işlemleri
│   ├── prediction.py # AI tahmin endpoint'leri
│   └── history.py    # Geçmiş kayıtları
├── models/           # Database modelleri
│   ├── user.py       # Kullanıcı ve profil modelleri
│   └── history.py    # Tahmin geçmişi modelleri
├── schemas/          # Validasyon şemaları
├── middleware/       # Error handler'lar
├── utils/            # Yardımcı fonksiyonlar
├── ml_models/        # AI model dosyaları
├── core/             # AI model wrapper'ları
├── static/           # Statik dosyalar
└── migrations/       # Database migration'ları
```

**Toplam:** 33 Python dosyası oluşturuldu

---

### 2. Database Tasarımı ve Oluşturulması ✅

**Oluşturulan Tablolar:**

#### `users` Tablosu
- Kullanıcı kimlik doğrulama bilgileri
- Email, şifre (hash'lenmiş), isim
- Hesap durumu (aktif/pasif)
- Oluşturma ve güncelleme tarihleri

#### `user_profiles` Tablosu
- Kullanıcı profil bilgileri
- Boy, kilo, yaş, cinsiyet
- Aktivite seviyesi
- Günlük kalori hedefi
- Hedef tipi (kilo ver/al/koru)
- Dil ve birim tercihleri
- **Otomatik hesaplamalar:** BMI, BMR, TDEE (Harris-Benedict formülü)

#### `prediction_history` Tablosu
- AI tahmin kayıtları
- Yemek sınıfı, güven skoru
- Tahmini gram ve kalori
- Görsel ve mask dosya yolları
- Model versiyonu, işlem süresi
- Öğün tipi (kahvaltı/öğle/akşam/atıştırmalık)
- Kullanıcı notları, favori işareti

#### `daily_logs` Tablosu
- Günlük özet istatistikleri
- Toplam kalori ve öğün sayısı
- Öğün bazında kalori dağılımı
- Günlük hedef ve başarı durumu

**İlişkiler:**
- User → UserProfile (1-to-1)
- User → PredictionHistory (1-to-many)
- User → DailyLog (1-to-many)

---

### 3. Authentication API Endpoint'leri ✅

**Geliştirilen Endpoint'ler:**

#### POST `/auth/register`
- Yeni kullanıcı kaydı
- Email, şifre ve isim doğrulaması
- Otomatik profil oluşturma
- JWT access ve refresh token üretimi
- **Şifre güvenliği:** pbkdf2:sha256 hash algoritması

**Doğrulama Kuralları:**
- Email geçerli format olmalı
- Şifre minimum 6 karakter, en az 1 harf içermeli
- İsim minimum 2, maksimum 100 karakter

#### POST `/auth/login`
- Kullanıcı girişi
- Email ve şifre doğrulaması
- Hesap aktiflik kontrolü
- Yeni JWT token üretimi

#### POST `/auth/refresh`
- Access token yenileme
- Refresh token ile yeni access token alma

#### GET `/auth/me`
- Mevcut kullanıcı bilgilerini getirme
- JWT korumalı endpoint

#### POST `/auth/logout`
- Kullanıcı çıkışı
- Log kaydı

---

### 4. Teknoloji Stack'i

**Backend Framework:**
- Flask 3.1.0
- Flask-SQLAlchemy 3.1.1 (ORM)
- Flask-JWT-Extended 4.6.0 (Authentication)
- Flask-CORS 4.0.0 (Mobile app desteği)
- Flask-Migrate 4.0.5 (Database versiyonlama)

**Validation:**
- Marshmallow 3.20.1 (Request/response validation)

**Database:**
- SQLite (Development)
- Migration desteği ile PostgreSQL'e geçiş hazır

**AI/ML (Hazır, henüz entegre değil):**
- PyTorch 2.3.1
- TensorFlow-macos 2.16.1
- torchvision 0.18.1

**Güvenlik:**
- Werkzeug password hashing
- JWT token-based authentication
- CORS yapılandırması

---

### 5. API Testleri - Postman ✅

**Test Edilen Endpoint'ler:**

#### Register Endpoint Testi
- **Method:** POST
- **URL:** http://localhost:5001/auth/register
- **Status:** 201 Created ✅
- **Response:** Kullanıcı bilgileri, access_token, refresh_token

#### Login Endpoint Testi
- **Method:** POST
- **URL:** http://localhost:5001/auth/login
- **Status:** 200 OK ✅
- **Response:** Kullanıcı bilgileri, access_token, refresh_token

**Test Sonuçları:**
- ✅ Kullanıcı kaydı başarılı
- ✅ Kullanıcı girişi başarılı
- ✅ Token üretimi çalışıyor
- ✅ Profil otomatik oluşturuluyor
- ✅ Validasyon kuralları çalışıyor
- ✅ Error handling düzgün çalışıyor

---

## 📊 İstatistikler

- **Oluşturulan dosya sayısı:** 33
- **Database tablosu:** 4
- **API endpoint:** 5 (2'si test edildi)
- **Toplam kod satırı:** ~1500+
- **Test edilen kullanıcı:** 3

---

## 🎯 Gelecek Hafta Planı (Hafta 2)

### Öncelikli Görevler:

1. **User Profile API Endpoint'leri**
   - GET `/api/user/profile` - Profil bilgilerini getir
   - PUT `/api/user/profile` - Profil güncelle
   - PATCH `/api/user/profile/goal` - Kalori hedefi güncelle

2. **CORS Yapılandırması**
   - Mobile app için CORS ayarları
   - Security headers
   - Rate limiting

3. **JWT Protected Endpoints Düzeltmesi**
   - `/auth/me` endpoint'inin düzgün çalışması
   - Token validation sorunlarının giderilmesi

4. **API Dokümantasyonu**
   - Endpoint listesi
   - Request/response örnekleri
   - Error code'ları

---

## 🔧 Teknik Detaylar

### Database Schema
```python
# User Model
class User(db.Model):
    id = Integer (Primary Key)
    email = String(120) (Unique, Indexed)
    password_hash = String(256)
    name = String(100)
    is_active = Boolean (Default: True)
    created_at = DateTime
    updated_at = DateTime

# UserProfile Model
class UserProfile(db.Model):
    id = Integer (Primary Key)
    user_id = Integer (Foreign Key -> users.id)
    height = Float (cm)
    weight = Float (kg)
    age = Integer
    gender = String(10)
    activity_level = String(20)
    daily_calorie_goal = Integer
    # ... diğer alanlar

    # Otomatik hesaplamalar
    calculate_bmi() -> Float
    calculate_bmr() -> Float (Harris-Benedict)
    calculate_tdee() -> Float
```

### API Response Format
```json
{
  "success": true/false,
  "message": "Success message",
  "data": {
    "user": {...},
    "access_token": "...",
    "refresh_token": "..."
  },
  "error": "Error message (sadece hata durumunda)"
}
```

---

## 📝 Notlar

- Development server port 5001'de çalışıyor (5000 AirPlay tarafından kullanılıyor)
- Auto-reload devre dışı (JWT token tutarlılığı için)
- Database migration sistemi hazır
- Mevcut AI modelleri (ResNet50, U²-Net, MiDaS) backend/ml_models/ altında
- Mobile app (Flutter) için CORS yapılandırması tamamlandı

---

## 🎓 Öğrenilen Teknolojiler

1. Flask App Factory Pattern
2. SQLAlchemy ORM ve ilişkiler
3. JWT Authentication (Access + Refresh token)
4. Marshmallow validation
5. Flask-Migrate ile database versioning
6. RESTful API tasarımı
7. Error handling ve logging
8. Password hashing ve güvenlik

---

**Hazırlayan:** Filiz Çakır
**Tarih:** 9 Kasım 2025
