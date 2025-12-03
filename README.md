# GastronomGöz: Akıllı Yemek Tanıma ve Kalori Hesaplama Sistemi

GastronomGöz, bir yemeğin fotoğrafından türünü tanıyan, derinlik ve segmentasyon analizleriyle hacmini hesaplayan ve tahmini kalori değerini çıkaran bir web tabanlı yapay zeka sistemidir. Kullanıcının yüklediği görsel analiz edilir ve yemek türü, ağırlık ve kalori bilgisi sunulur.

## 💡 Temel Özellikler

* 🍽️ **101 Sınıflı Yemek Tanıma (ResNet50)**
* 🔍 **U-2-Net ile Segmentasyon**
* 🌍 **MiDaS (DPT\_Large) ile Derinlik Haritaları ve Hacim Hesaplama**
* 📊 **Kalori Tahmini** (`gram x kalori/100g`)
* 📃 Web arayüzü (Flask)

---

## 🤖 Kullanılan Teknolojiler

* Python 3.10+
* TensorFlow / Keras
* OpenCV, NumPy, Pandas, Matplotlib
* Flask (sunucu)
* U-2-Net (segmentasyon modeli)
* MiDaS (depth estimation - hacim tahmini)
* ResNet50 (yemek tanıma)

---

## 🎓 Model Eğitimi (ResNet50)

### Veri Seti:

* **Food-101** (train/test ayrılımıyla)
* 101 sınıfa ait yemek görselleri

### Eğitim Özeti:

* 🔄 Önceden eğitilmiş `ResNet50` modeli (ImageNet)
* ✔️ GlobalAveragePooling + Dense(128) + Dropout(0.2) + Dense(101) katman yapısı
* **Optimizer:** SGD (lr=0.0001, momentum=0.9)
* **Loss:** Categorical Crossentropy
* **Callback:** `ModelCheckpoint`, `CSVLogger`
* Model çıktısı: `model_trained_101class.hdf5`

### Eğitim Kodu Özeti:

```python
resnet50 = ResNet50(weights='imagenet', include_top=False)
x = resnet50.output
x = GlobalAveragePooling2D()(x)
x = Dense(128,activation='relu')(x)
x = Dropout(0.2)(x)
predictions = Dense(101, activation='softmax')(x)
model = Model(inputs=resnet50.input, outputs=predictions)
```

---

## 📚 Proje Yapısı

```bash
food_volume/
├── app.py                      # Flask uygulaması
├── data_loader.py              # RescaleT, ToTensorLab vb. sınıflar
├── model/
│   └── u2net.py                # U2NETP modeli
├── static/
│   ├── uploads/               # Kullanıcının yüklediği görseller ve maskeler
│   └── css/, js/ (opsiyonel)
├── templates/
│   └── main.html               # Web arayüzü
├── best_model_101class.keras     # En iyi ağırlıklar
├── model_trained_101class.hdf5  # Final model
└── calories_per_100g.csv         # Kalori verisi (label, weight, calories)
```

---

## 💡 Kurulum

### Ortam Kurulumu (Windows)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Gerekli Modelleri Yükleyin:

* [U-2-Net](https://github.com/xuebinqin/U-2-Net)
* [MiDaS (DPT\_Large)](https://github.com/isl-org/MiDaS)

---

## 📂 Uygulamayı Başlatmak

```bash
python app.py
```

Tarayıcıdan: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📷 Görsel Örnek

* Segmentasyon ile tespit edilen yemek maskesi
* Hacim tahmini sonucu gram ve kalori bilgisi

![donut](static/uploads/mask_donut.png)

---

## 📍 Katkıda Bulunma

Projeye katkıda bulunmak isterseniz pull request gönderebilir veya sorunları bildirebilirsiniz.

---

## 📜 Lisans

MIT License ile sunulmuştur.
