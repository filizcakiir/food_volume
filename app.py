# ─── Flask ve Web İlgili Kütüphaneler ────────────────────────────────────────────
from flask import Flask, render_template, request, redirect, url_for, jsonify
"""
 Flask: mikro web çatısı. 
 render_template: HTML şablonlarını render etmek için.
 request: HTTP isteğindeki form/veri içeriğine erişmek için.
 redirect, url_for: yönlendirme işlemleri için.
 jsonify: Python objesini JSON’a çevirmek için."""

# ─── Sistem, UUID ve Görüntü İşleme ───────────────────────────────────────────────
import os            # Dosya ve klasör işlemleri için
import uuid          # Evrensel benzersiz kimlik (ör. yüklenen dosyalara isim vermek için)
import cv2           # OpenCV: görüntü işleme fonksiyonları
import numpy as np   # Sayısal işlemler, dizi (array) yapıları
from PIL import Image  # Python Imaging Library: ek görüntü manipülasyonları

# ─── Makine Öğrenmesi ve Derin Öğrenme ──────────────────────────────────────────
import torch                         # PyTorch: segmentasyon için
import torchvision.transforms as transforms  # - transforms: görüntüleri modele uygun formata dönüştürmek için (normalize, resize, tensor dönüşümü vb.)
from torch.autograd import Variable  # GPU/CPU üzerinde tensörleri sarmak ve gradyan hesaplamak için
import pandas as pd                  # Veri analizi; kalori tablolarını okumak için
# TensorFlow/Keras: sınıflandırma modeli yükleme ve görüntü ön işleme
from tensorflow.keras.models import load_model  
from tensorflow.keras.preprocessing import image as keras_image

# ─── Proje İçi Modüller ─────────────────────────────────────────────────────────
from model.u2net import U2NETP       # U²-Net segmentasyon modelinin “light” versiyonu
from data_loader import RescaleT, ToTensorLab  
# - RescaleT, ToTensorLab: MiDaS derinlik ve segmentasyon maskesi ön işlem araçları

# ─── Hata Ayıklama ve Loglama ───────────────────────────────────────────────────
import logging       # Log seviyesini ayarlamak ve hata kayıtları tutmak için
import traceback     # Hata oluştuğunda ayrıntılı yığın (stack) izleme bilgisi almak için

# Logging seviyesini ayarla
logging.getLogger('tensorflow').setLevel(logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads' # - static/uploads: kullanıcıdan gelen dosyalar burada saklanacak.
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # - exist_ok=True: klasör zaten varsa hata fırlatma.

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") # - CUDA varsa GPU kullanımına geç, yoksa CPU’da çalış.

# --- YEMEK SINIFLARI (101 sınıf) ---
class_names = ['apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare', 
    'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito', 
    'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake', 
    'ceviche', 'cheese_plate', 'cheesecake', 'chicken_curry', 'chicken_quesadilla', 
    'chicken_wings', 'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder', 
    'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame', 'cup_cakes', 
    'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict', 'escargots', 
    'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras', 'french_fries', 
    'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice', 'frozen_yogurt', 
    'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich', 'grilled_salmon', 
    'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup', 'hot_dog', 'huevos_rancheros', 
    'hummus', 'ice_cream', 'lasagna', 'lobster_bisque', 'lobster_roll_sandwich', 
    'macaroni_and_cheese', 'macarons', 'miso_soup', 'mussels', 'nachos', 'omelette', 
    'onion_rings', 'oysters', 'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck', 
    'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib', 'pulled_pork_sandwich', 'ramen', 
    'ravioli', 'red_velvet_cake', 'risotto', 'samosa', 'sashimi', 'scallops', 'seaweed_salad', 
    'shrimp_and_grits', 'spaghetti_bolognese', 'spaghetti_carbonara', 'spring_rolls', 
    'steak', 'strawberry_shortcake', 'sushi', 'tacos', 'takoyaki', 'tiramisu', 'tuna_tartare', 
    'waffles']

# Gerçekçi porsiyon ağırlıkları - araştırma verilerine göre güncellenmiş
FOOD_PORTIONS = {
    'baklava': {
        'small': 80,    # 2 dilim
        'medium': 140,  # 3-4 dilim 
        'large': 200    # 5-6 dilim
    },
    'apple_pie': {
        'small': 90,
        'medium': 130,
        'large': 180
    },
    'pizza': {
        'small': 150,   # 1 dilim
        'medium': 250,  # 2 dilim
        'large': 400    # 3+ dilim
    },
    'cheesecake': {
        'small': 70,
        'medium': 110,
        'large': 150
    },
    'chocolate_cake': {
        'small': 80,
        'medium': 120,
        'large': 170
    },
    'hamburger': {
        'small': 120,
        'medium': 180,
        'large': 250
    },
    'french_fries': {
        'small': 60,
        'medium': 100,
        'large': 150
    },
    'lasagna': {
        'small': 180,
        'medium': 250,
        'large': 350
    },
    'spaghetti_bolognese': {
        'small': 200,
        'medium': 300,
        'large': 450
    },
    'ice_cream': {
        'small': 50,
        'medium': 80,
        'large': 120
    },
    'chicken_wings': {
        'small': 80,    # 3-4 kanat
        'medium': 120,  # 5-6 kanat
        'large': 180    # 7+ kanat
    },
    'steak': {
        'small': 120,
        'medium': 200,
        'large': 300
    },
    'default': {
        'small': 80,
        'medium': 130,
        'large': 200
    }
}
# - Küçük/orta/büyük porsiyonlarda tipik ağırlık değerleri (gram cinsinden).
# - Eğer yemek ismi FOOD_PORTIONS’da yoksa 'default' kullanılır.

# Yemek türlerine göre tipik yükseklik/kalınlık profilleri (cm)
# “thin/medium/thick” = “ince/orta/kalın”
FOOD_HEIGHT_PROFILES = {
    'baklava': {'thin': 1.5, 'medium': 2.5, 'thick': 4.0},      # Baklava katmanları
    'pizza': {'thin': 1.0, 'medium': 2.0, 'thick': 3.5},       # Pizza kalınlığı
    'lasagna': {'thin': 3.0, 'medium': 5.0, 'thick': 7.0},     # Lasagna katmanları
    'cake': {'thin': 2.0, 'medium': 4.0, 'thick': 6.0},        # Pasta dilimi
    'hamburger': {'thin': 4.0, 'medium': 6.0, 'thick': 9.0},   # Hamburger yüksekliği
    'steak': {'thin': 1.5, 'medium': 2.5, 'thick': 4.0},       # Et kalınlığı
    'ice_cream': {'thin': 2.0, 'medium': 4.0, 'thick': 6.0},   # Dondurma yüksekliği
    'soup': {'thin': 1.0, 'medium': 2.0, 'thick': 3.0},        # Çorba derinliği
    'default': {'thin': 1.5, 'medium': 3.0, 'thick': 5.0}      # Genel yemekler
}
# - Hacim hesabı için yemeklerin kalınlık/derinlik profilleri (cm).
# - Thin/medium/thick seçenekleri, modelin size tahminiyle eşlenir.


# ─── Global Model ve Veri Değişkenleri ───────
food_model     = None  # Keras sınıflandırma modeli
calories_df    = None  # Kalori CSV tablosu (pandas DataFrame)
u2net_model    = None  # U²-Net segmentasyon modeli
midas          = None  # MiDaS derinlik tahmin modeli
midas_transforms = None  # Derinlik ön işleme pipeline’ı

def ensure_models_loaded():
    """Modellerin yüklendiğinden emin ol - gerçek lazy loading.
    İlk web'de resim yüklendiğinde tüm modelleri ve verileri yükler, sonrasında tekrar yükleme yapmaz."""
    global food_model, calories_df, u2net_model, midas, midas_transforms

    # Henüz yüklenmemiş (None) herhangi bir model/df varsa, yüklemeyi başlat
    if (food_model is None or calories_df is None or 
        u2net_model is None or midas is None or midas_transforms is None):

        print("🔄 Modeller ilk kez yükleniyor... (Bu işlem sadece bir kez yapılır)")

        # 1) Sınıflandırma modeli
        if food_model is None:
            print("📊 Yemek sınıflandırma modeli yükleniyor...")
            food_model = load_model("./weights/model_trained_101class.hdf5")

            print("✅ Yemek modeli yüklendi")
        # 2) Kalori tablosu
        if calories_df is None:
            print("📋 Kalori verileri yükleniyor...")
            calories_df = pd.read_csv("./weights/calories_per_101class_100g.csv")
            print("✅ Kalori verileri yüklendi")
        # 3) U²-Net segmentasyon modeli
        if u2net_model is None:
            print("🎯 U2NET segmentasyon modeli yükleniyor...")
            u2net_model = U2NETP(3, 1)
            u2net_model.load_state_dict(torch.load("./weights/u2netp.pth", map_location=device))
            u2net_model.to(device)
            u2net_model.eval()
            print("✅ U2NET modeli yüklendi")
        # 4) MiDaS derinlik tahmin modeli
        if midas is None:
            print("🌊 MiDaS derinlik modeli yükleniyor...")
            # Torch Hub’dan DPT_Large modelini indir ve yükle
            midas = torch.hub.load("intel-isl/MiDaS", "DPT_Large", trust_repo=True, verbose=False)
            # Derinlik ön işleme pipeline’ını hazırla
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True, verbose=False).dpt_transform
            midas.eval().to(device)
            print("✅ MiDaS modeli yüklendi")

        print("🎉 Tüm modeller başarıyla yüklendi!")

def save_output(image_path, output_dir):
    """U2NET ile segmentasyon"""
    """
    Verilen görüntü yolu için:
    1) U²-Net ile segmentasyon maskesi üret,
    2) Maskeyi çizdir,
    3) Sonucu output_dir içine kaydet,
    4) (mask dizisi, kaydedilen dosya adı) döndür.
    """
    global u2net_model
    
    image = np.array(Image.open(image_path).convert('RGB'))# 1) Görüntüyü oku ve RGB dizisine dönüştür
    # 2) Modelin istediği formata getirmek için dict hazırla
    sample = {'imidx': 0, 'image': image, 'label': image}
    transform_ = transforms.Compose([
        RescaleT(320),      # Yeniden ölçek - kısa kenar = 320 px
        ToTensorLab(flag=0) # RGB ve lab renk uzayında tensöre dönüştür
    ])
    sample = transform_(sample)
    # 3) Batch boyutunu ekle ve cihaza gönder
    image_tensor = sample['image'].unsqueeze(0).float().to(device)

    # 4) Forward geçiş (gradyan hesaplamayı kapat)
    with torch.no_grad():
        d1, *_ = u2net_model(Variable(image_tensor))
        # Çıktıyı 0–1 aralığına normalize et
        pred = (d1[:, 0, :, :] - d1.min()) / (d1.max() - d1.min())
        mask = (pred.squeeze().cpu().data.numpy() * 255).astype(np.uint8)

    # 5) Maskeyi orijinal boyuta geri ölçekle ve ikili hale getir
    height, width = image.shape[:2]
    mask_resized = cv2.resize(mask, (width, height))
    _, binary_mask = cv2.threshold(mask_resized, 127, 255, cv2.THRESH_BINARY)
    # 6) Konturları bul ve orijinal görüntü üzerinde çiz
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.drawContours(image_bgr, contours, -1, (0, 0, 255), 3)# 4. Konturları[kırmızı] orijinal görselin üzerine çiz
    result_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    # 7) Output klasörünü oluştur (eğer yoksa) ve resmi kaydet
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"mask_{os.path.basename(image_path)}"
    output_path = os.path.join(output_dir, output_filename)
    Image.fromarray(result_rgb).save(output_path)

    # 8) Mask dizisini ve dosya adını döndür
    return mask, output_filename

def predict_food(img_path):
    """Yemek türü tahmini"""
    """
    Verilen görüntü için sınıf tahmini yap:
    1) Keras modeline uygun boyuta getir,
    2) Normalize et,
    3) Modelin predict() metodunu çağır,
    4) En yüksek olasılık ve sınıf ismini döndür.
    """
    global food_model
    
    # 1) Görüntüyü 224×224 olarak yükle
    img = keras_image.load_img(img_path, target_size=(224, 224))
    # 2) Diziye çevir ve normalize et
    img_array = keras_image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    # 3) Tahmini al (verbose=0: sessizlik modu)
    pred = food_model.predict(img_array, verbose=0)[0]
    # 4) En olası sınıfın adı ve olasılığını döndür
    return class_names[np.argmax(pred)], pred[np.argmax(pred)]

def calculate_smart_portion_weight(img_path, mask, food_class):
    """
    Akıllı porsiyon ağırlık hesaplama:
    - Segmentasyon maskesine ve yemek sınıfına bakarak porsiyon ağırlığını tahmin eder.
    """
    
    # Görsel ve maske analizi
    img = cv2.imread(img_path)
    height, width = img.shape[:2] # Görüntü yüksekliği ve genişliği (piksel)
    
    # Maskeyi orijinal boyuta getir
    mask_resized = cv2.resize(mask, (width, height))
    binary_mask = mask_resized > 128 # Eşikleme: piksel değeri 128'den büyükse yemek bölgesi
    
    # Segment alanını hesapla
    food_pixels = np.sum(binary_mask)            
    total_pixels = height * width                
    area_ratio = food_pixels / total_pixels # Yemek bölgesi oranı (0–1). Örneğin 0.2 ise görüntünün %20’si yemek.
    
    print(f"Debug: {food_class} - Area ratio: {area_ratio:.3f}, Food pixels: {food_pixels}")
    
    # Kontur analizi: yemek şeklinin karmaşıklığını ölçmek için
    contours, _ = cv2.findContours(
        mask_resized.astype(np.uint8),            # 0–255 aralığında uint8 maske
        cv2.RETR_EXTERNAL,                        # Yalnızca dış konturlar
        cv2.CHAIN_APPROX_SIMPLE                   # Kontur basitleştirme yöntemi
    )
    
    # En büyük konturu seç ve alan / bounding-box oranı ile çevresellik hesapla
    if contours:
        main_contour = max(contours, key=cv2.contourArea)#En geniş alana sahip kontur (genelde yemek parçasının sınırı).
        contour_area = cv2.contourArea(main_contour) # Konturun kapladığı alan (piksel²).
        
        # Konturun bounding-box’u
        x, y, w, h = cv2.boundingRect(main_contour)
        bbox_area = w * h #Kontur etrafına çizilen dikdörtgenin alanı.
        fill_ratio = contour_area / bbox_area if bbox_area > 0 else 0 #Konturun ne kadar “dolu” olduğunu gösterir
        
        # Konturun çevresi uzunluğu ve yuvarlaklık (circularity)
        perimeter = cv2.arcLength(main_contour, True)
        #circularity: Şeklin ne kadar yuvarlak olduğunu ölçer. (4π·area)/(perimeter²) — 1’e yakınsa tam daire.
        circularity = 4 * np.pi * contour_area / (perimeter * perimeter) if perimeter > 0 else 0
    else:
        # Kontur bulunamazsa varsayılan değerler
        fill_ratio = 0.7
        circularity = 0.5
    
    print(f"Debug: Fill ratio: {fill_ratio:.3f}, Circularity: {circularity:.3f}")
    
    # Porsiyon boyutu belirleme - yemek türüne özel eşikler
    if food_class in ['baklava', 'apple_pie', 'cheesecake', 'chocolate_cake']:
        # Tatlılar için özel eşikler (genelde küçük tabakta servis)
        if area_ratio > 0.25:
            size_category = 'large'
        elif area_ratio > 0.12:
            size_category = 'medium'
        else:
            size_category = 'small'
    elif food_class in ['pizza', 'lasagna', 'spaghetti_bolognese']:
        # Büyük yemekler için farklı eşikler
        if area_ratio > 0.35:
            size_category = 'large'
        elif area_ratio > 0.18:
            size_category = 'medium'
        else:
            size_category = 'small'
    elif food_class in ['french_fries', 'ice_cream']:
        # Hacimli ama hafif yemekler
        if area_ratio > 0.30:
            size_category = 'large'
        elif area_ratio > 0.15:
            size_category = 'medium'
        else:
            size_category = 'small'
    else:
        # Genel kategoriler
        if area_ratio > 0.28:
            size_category = 'large'
        elif area_ratio > 0.14:
            size_category = 'medium'
        else:
            size_category = 'small'
    
    # Temel ağırlığı al
    #FOOD_PORTIONS: Önceden tanımlı küçük/orta/büyük porsiyon ağırlıkları (gram).
    portions = FOOD_PORTIONS.get(food_class, FOOD_PORTIONS['default'])
    base_weight = portions[size_category]#base_weight: Seçilen kategoriye (small/medium/large) karşılık gelen temel gramaj.
    
    """shape_multiplier: Porsiyonun “doluluk” ve “yuvarlaklık” özelliklerine göre ağırlık düzeltmesi.
    Çok dolu/yuvarlaksa biraz artır, çok parçalı/düzensizse ayarla."""
    shape_multiplier = 1.0
    
    # Fill ratio düzeltmesi - dolu/boş alan oranı
    if fill_ratio > 0.8:  # Çok dolu şekil
        shape_multiplier *= 1.1
    elif fill_ratio < 0.5:  # Boşluklu şekil
        shape_multiplier *= 0.9
    
    # Circularity düzeltmesi - yuvarlak/düzensiz şekil
    if circularity > 0.7:  # Yuvarlak (pizza, pasta tabağı)
        shape_multiplier *= 1.05
    elif circularity < 0.3:  # Çok düzensiz (parçalı yemek)
        shape_multiplier *= 1.15
    
    # food_corrections: Her yemeğe özgü yoğunluk/kalite katsayısı (ör. baklava 1.1, dondurma 0.8).
    food_corrections = {
        'baklava': 1.1,      # Baklava yoğun ve kalorili
        'cheesecake': 1.0,   # Cheesecake normal
        'chocolate_cake': 1.05,  # Çikolatalı pasta biraz ağır
        'apple_pie': 0.95,   # Apple pie biraz daha hafif
        'pizza': 1.0,        # Pizza normal
        'hamburger': 0.95,   # Hamburger biraz kompakt
        'french_fries': 0.85, # Patates hacimli ama hafif
        'ice_cream': 0.8,    # Dondurma çok hafif
        'chicken_wings': 1.1, # Kanatlar kemikli ama et yoğun
        'steak': 1.0,        # Steak normal et yoğunluğu
        'lasagna': 1.05,     # Lasagna katmanlı ve ağır
        'spaghetti_bolognese': 1.0,  # Makarna normal
    }
    
    final_multiplier = food_corrections.get(food_class, 1.0)#Yemek Türüne Özel Düzeltme
    final_weight = base_weight * shape_multiplier * final_multiplier
    
    print(f"Debug: Base: {base_weight}g, Shape mult: {shape_multiplier:.2f}, Food mult: {final_multiplier:.2f}, Final: {final_weight:.1f}g")
    
    # Mantıklı sınırlar içinde tut
    min_reasonable = 30   # Minimum 30 gram
    max_reasonable = 600  # Maximum 600 gram (çok büyük porsiyon)
    
    final_weight = max(min_reasonable, min(final_weight, max_reasonable))
    
    return round(final_weight, 0)

def calculate_midas_hybrid_weight(img_path, mask, food_class):
    """MiDaS + Alan analizi hibrit ağırlık hesaplama"""
    global midas, midas_transforms
    
    # Görsel yükleme ve ön işleme
    img = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)# OpenCV ile BGR formatında okunan görüntüyü RGB’ye çeviriyoruz:
    height, width = img_rgb.shape[:2]
    
    # MiDaS için görsel boyutunu optimize et (384x384 optimal)
    target_size = 384
    # scale_factor: Görüntünün uzun kenarını target_size’a sığdırmak için ölçek faktörü
    scale_factor = target_size / max(height, width)
    new_height = int(height * scale_factor)
    new_width = int(width * scale_factor)
    img_resized = cv2.resize(img_rgb, (new_width, new_height)) # Yeniden boyutlandırılmış görüntü
    
    # MiDaS ile derinlik haritası oluştur
    input_tensor = midas_transforms(img_resized).to(device)
    with torch.no_grad():
        # Tek adımlık derinlik tahmini
        depth_prediction = midas(input_tensor)
        # Çıktıyı orijinal (yeni) boyuta yeniden örnekleyip NumPy dizisine çevir
        depth_map = torch.nn.functional.interpolate(
            depth_prediction.unsqueeze(1),
            size=(new_height, new_width),
            mode="bicubic",
            align_corners=False
        ).squeeze().cpu().numpy()
    # `depth_map`: Piksel başına “yakınlık” bilgisini veren 2D float dizisi
    
    # Maskeyi MiDaS boyutuna uyarla
    mask_resized = cv2.resize(mask, (new_width, new_height))
    binary_mask = mask_resized > 128
    
    # Segment alanını hesapla
    food_pixels = np.sum(binary_mask)
    total_pixels = new_height * new_width
    area_ratio = food_pixels / total_pixels# `area_ratio`: 0–1 arası değer, yemek bölgesinin tüm görüntüye oranı
    
    # MiDaS derinlik haritasını normalize et (0-1 arası)
    if depth_map.max() > depth_map.min():
        # MiDaS çıktısını ters çevir (küçük değer = yakın/yüksek)
        depth_normalized = 1.0 - ((depth_map - depth_map.min()) / (depth_map.max() - depth_map.min()))
    else:
        depth_normalized = np.ones_like(depth_map) * 0.5
    
    # Maske boyunca sadece yemek bölgesinin derinlik değerleri
    masked_depth = depth_normalized * binary_mask
    
    # Eğer maskede hiç pixel yoksa (food_pixels=0), orta porsiyon döndür
    if food_pixels == 0:
        return FOOD_PORTIONS.get(food_class, FOOD_PORTIONS['default'])['medium']
    
    # Derinlik istatistikleri
    valid_depth_values = masked_depth[binary_mask]
    avg_depth = np.mean(valid_depth_values)# `avg_depth`: Ortalama “yükseklik” tahmini
    max_depth = np.max(valid_depth_values)# `max_depth`: En derin (en yakın) nokta
    depth_std = np.std(valid_depth_values)# `depth_std`: Derinlik varyansı, yüzey pürüzlülüğü/kademeliliği
    
    print(f"Debug: {food_class}")
    print(f"  Area ratio: {area_ratio:.3f}")
    print(f"  Avg depth: {avg_depth:.3f}, Max depth: {max_depth:.3f}, Std: {depth_std:.3f}")
    
    # 1. ALAN BAZLI PORSİYON BOYUTU BELİRLEME
    if food_class in ['baklava', 'apple_pie', 'cheesecake', 'chocolate_cake']:
        # Tatlılar için özel eşikler
        if area_ratio > 0.25:
            area_size = 'large'
        elif area_ratio > 0.12:
            area_size = 'medium'
        else:
            area_size = 'small'
    elif food_class in ['pizza', 'lasagna', 'spaghetti_bolognese']:
        # Büyük yemekler için özel eşikler
        if area_ratio > 0.35:
            area_size = 'large'
        elif area_ratio > 0.18:
            area_size = 'medium'
        else:
            area_size = 'small'
    else:
        # Genel kategoriler için özel eşikler
        if area_ratio > 0.28:
            area_size = 'large'
        elif area_ratio > 0.14:
            area_size = 'medium'
        else:
            area_size = 'small'
    
    # 2. MiDaS DERINLIK BAZLI KALINLIK/YÜKSEKLIK ANALİZİ
    height_profile = FOOD_HEIGHT_PROFILES.get(food_class, FOOD_HEIGHT_PROFILES['default'])
    
    # Derinlik değerine göre kalınlık kategorisi
    if avg_depth > 0.7:  # Yüksek derinlik = kalın/yüksek yemek
        depth_category = 'thick'
        depth_multiplier = 1.3
    elif avg_depth > 0.4:  # Orta derinlik
        depth_category = 'medium'
        depth_multiplier = 1.0
    else:  # Düşük derinlik = ince/düz yemek
        depth_category = 'thin'
        depth_multiplier = 0.7
    
    # Derinlik varyansı - yemek pürüzlülüğü/katmanlılığı
    if depth_std > 0.08:  # Yüksek varyans = katmanlı/pürüzlü
        texture_multiplier = 1.15  # Katmanlı yemekler daha ağır
    elif depth_std > 0.04:  # Orta varyans
        texture_multiplier = 1.0
    else:  # Düz yüzey
        texture_multiplier = 0.9
    
    print(f"  Area size: {area_size}, Depth category: {depth_category}")
    print(f"  Depth mult: {depth_multiplier:.2f}, Texture mult: {texture_multiplier:.2f}")
    
    # 3. HİBRİT AĞIRLIK HESAPLAMA
    # Temel porsiyon ağırlığı (alan bazlı)
    portions = FOOD_PORTIONS.get(food_class, FOOD_PORTIONS['default'])
    base_weight = portions[area_size] # `base_weight`: Alan bazlı small/medium/large gramajı
    
    # MiDaS ile Derinlik ve pürüzlülük düzeltmesiyle yeni ağırlık
    depth_adjusted_weight = base_weight * depth_multiplier * texture_multiplier
    
    # 4. YEMEK TÜRÜNE ÖZEL SON DÜZELTMELERİ
    food_specific_corrections = {
        'baklava': 1.1,      # Baklava yoğun ve şekerli
        'cheesecake': 1.05,  # Cheesecake yoğun
        'chocolate_cake': 1.1,  # Çikolatalı pasta ağır
        'apple_pie': 0.95,   # Apple pie daha hafif
        'pizza': 1.0,        # Pizza normal
        'hamburger': 0.95,   # Hamburger kompakt
        'french_fries': 0.8, # Patates hacimli ama hafif
        'ice_cream': 0.7,    # Dondurma çok hafif
        'chicken_wings': 1.1, # Kanatlar et yoğun
        'steak': 1.0,        # Steak normal
        'lasagna': 1.1,      # Lasagna ağır ve katmanlı
        'spaghetti_bolognese': 1.0,
        'soup': 1.2,         # Çorba sıvı ağır
    }
    
    # Yemek türü düzeltmesi
    food_correction = food_specific_corrections.get(food_class, 1.0)
    
    # Derinlik tabanlı ek düzeltmeler
    if food_class in ['baklava', 'lasagna'] and depth_category == 'thick':
        # Katmanlı yemekler kalınsa daha da ağır
        food_correction *= 1.15
    elif food_class in ['pizza'] and depth_category == 'thin':
        # İnce pizza daha hafif
        food_correction *= 0.9
    
    # Final hesaplama
    final_weight = depth_adjusted_weight * food_correction
    
    print(f"  Base: {base_weight}g → Depth adj: {depth_adjusted_weight:.1f}g → Final: {final_weight:.1f}g")
    
    # Makul sınırlar (max, min sınırlama)
    min_weight = 25
    max_weight = 800
    final_weight = max(min_weight, min(final_weight, max_weight))
    
    # En yakın tam sayıya (gram) yuvarla ve döndür
    return round(final_weight, 0)

def calculate_optimized_weight(img_path, mask, food_class):
    """Optimize edilmiş ağırlık hesaplaması - MiDaS + gerçekçi porsiyon tahmini"""
    global midas, midas_transforms
    
    # Görsel analizi
    img = cv2.imread(img_path)# BGR formatta oku
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)# RGB’ye çevir
    height, width = img_rgb.shape[:2]# Görüntü boyutları
    
    # Maskeyi orijinal boyuta getir
    mask_resized = cv2.resize(mask, (width, height))
    binary_mask = mask_resized > 128
    
    # Segment alanını hesapla
    food_pixels = np.sum(binary_mask)# Yemek pikselleri sayısı
    total_pixels = height * width                     # Toplam piksel sayısı
    area_ratio   = food_pixels / total_pixels         # Alana oran (0–1)
    
    # MiDaS için görsel boyutunu optimize et
    target_size = 384
    scale_factor = target_size / max(height, width)
    new_height = int(height * scale_factor)
    new_width = int(width * scale_factor)
    img_resized = cv2.resize(img_rgb, (new_width, new_height))
    
    # MiDaS ile derinlik haritası
    input_tensor = midas_transforms(img_resized).to(device)
    with torch.no_grad():
        depth_prediction = midas(input_tensor)
        depth_map = torch.nn.functional.interpolate(
            depth_prediction.unsqueeze(1),
            size=(new_height, new_width),
            mode="bicubic",
            align_corners=False,
        ).squeeze().cpu().numpy()
    
    # Maskeyi MiDaS boyutuna uyarla
    mask_midas = cv2.resize(mask, (new_width, new_height))
    binary_mask_midas = mask_midas > 128
    
    # Derinlik analizi
    if depth_map.max() > depth_map.min():
        depth_normalized = 1.0 - ((depth_map - depth_map.min()) / (depth_map.max() - depth_map.min()))
    else:
        depth_normalized = np.ones_like(depth_map) * 0.5
    
    # Maskelenmiş derinlik
    masked_depth = depth_normalized * binary_mask_midas
    food_pixels_midas = np.sum(binary_mask_midas)
    
    if food_pixels_midas > 0:
        avg_depth = np.mean(masked_depth[binary_mask_midas])
        depth_variance = np.var(masked_depth[binary_mask_midas])
    else:
        avg_depth = 0.5
        depth_variance = 0.0
    
    print(f"Debug: {food_class}")
    print(f"  Area ratio: {area_ratio:.3f}")
    print(f"  Avg depth: {avg_depth:.3f}, Depth var: {depth_variance:.3f}")
    
    # BASİT VE ETKİLİ HESAPLAMA YÖNTEMİ
    
    # 1. Temel porsiyon ağırlığı (yemek türüne göre)
    base_weights = {
        'baklava': 155,      # 4 dilim için gerçekçi ağırlık
        'cheesecake': 110,   # Orta porsiyon
        'chocolate_cake': 125,
        'apple_pie': 130,
        'pizza': 280,        # 2-3 dilim
        'hamburger': 200,
        'french_fries': 110,
        'lasagna': 260,
        'spaghetti_bolognese': 320,
        'ice_cream': 85,
        'chicken_wings': 140,
        'steak': 210,
        'default': 150
    }
    
    base_weight = base_weights.get(food_class, base_weights['default'])
    
    # 2. Alan bazlı düzeltme (basit ve güvenilir)
    if area_ratio > 0.30:      # Çok büyük porsiyon
        area_multiplier = 1.4
    elif area_ratio > 0.20:    # Büyük porsiyon
        area_multiplier = 1.2
    elif area_ratio > 0.12:    # Normal porsiyon
        area_multiplier = 1.0
    elif area_ratio > 0.06:    # Küçük porsiyon
        area_multiplier = 0.8
    else:                      # Çok küçük
        area_multiplier = 0.6
    
    # 3. MiDaS derinlik düzeltmesi (basitleştirilmiş)
    if avg_depth > 0.65:       # Kalın/yüksek yemek
        depth_multiplier = 1.2
    elif avg_depth > 0.35:     # Normal kalınlık
        depth_multiplier = 1.0
    else:                      # İnce yemek
        depth_multiplier = 0.85
    
    # 4. Doku/katman düzeltmesi
    if depth_variance > 0.06:  # Katmanlı/pürüzlü (baklava, lasagna gibi)
        texture_multiplier = 1.1
    else:                      # Düz yüzey
        texture_multiplier = 1.0
    
    # Özel ayarlama: Baklava gibi yoğun, katmanlı yiyecekler ince görünse bile ağırlığını daha iyi korumalı
    if food_class == 'baklava' and texture_multiplier > 1.0: # Eğer baklava ve katmanlıysa
        if avg_depth < 0.35: # ve MiDaS'a göre "ince" kategorisindeyse (normalde 0.85 derinlik çarpanı alır)
            # "İncelik" nedeniyle uygulanan ağırlık azaltma etkisini hafifletmek için derinlik çarpanını yükselt.
            # Orijinal "ince" çarpanı 0.85 idi, bunu 0.95'e çekerek daha makul bir tahmin sağlıyoruz.
            depth_multiplier = 0.95 
    
    # 5. Yemek türü özel düzeltmeleri
    food_corrections = {
        'baklava': 1.0,          # Baklava için özel düzeltme kaldırıldı
        'cheesecake': 1.0,
        'chocolate_cake': 1.0,
        'apple_pie': 0.95,
        'pizza': 1.0,
        'hamburger': 0.95,
        'french_fries': 0.9,     # Hafif ama hacimli
        'ice_cream': 0.8,        # Çok hafif
        'chicken_wings': 1.05,   # Et yoğun
        'steak': 1.0,
        'lasagna': 1.05,         # Ağır katmanlı
        'soup': 1.1,             # Sıvı ağır
    }
    
    food_correction = food_corrections.get(food_class, 1.0)
    
    # Final hesaplama
    #Agırlık (g)=Baz agırlık×alan katsayısı×derinlik katsayısı×doku katsayısı×yiyecek duzeltmesi
    calculated_weight = base_weight * area_multiplier * depth_multiplier * texture_multiplier * food_correction
    
    print(f"  Base: {base_weight}g")
    print(f"  Area mult: {area_multiplier:.2f}")
    print(f"  Depth mult: {depth_multiplier:.2f}")
    print(f"  Texture mult: {texture_multiplier:.2f}")
    print(f"  Food correction: {food_correction:.2f}")
    print(f"  Final: {calculated_weight:.1f}g")
    
    # Mantıklı sınırlar
    if food_class == 'baklava':
        min_weight, max_weight = 100, 250  # Baklava için özel sınır
    elif food_class in ['pizza', 'lasagna', 'spaghetti_bolognese']:
        min_weight, max_weight = 150, 500  # Büyük yemekler
    elif food_class in ['ice_cream', 'french_fries']:
        min_weight, max_weight = 40, 200   # Hafif yemekler
    else:
        min_weight, max_weight = 60, 400   # Genel sınırlar
    
    final_weight = max(min_weight, min(calculated_weight, max_weight))
    
    return round(final_weight, 0)

# Status endpoint - sadece basit kontrol
@app.route('/status')
def status():
    return jsonify({'status': 'ready'})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Modelleri sadece burada yükle (ilk resim yüklendiğinde)
            ensure_models_loaded()
            
            # Dosya kontrolü (Mac uyumlu)
            file = request.files.get('image') or request.form.get('image')

            if not file:
                print("⚠️ Dosya alınamadı (muhtemelen tarayıcı izinleri nedeniyle).")
                return render_template("main.html", error="Dosya yüklenemedi. Lütfen tekrar deneyin.")

            # Benzersiz dosya adı oluştur
            filename = f"{uuid.uuid4().hex}.jpg"
            file_path = os.path.join(UPLOAD_FOLDER, filename)

            # macOS’ta bazen file.stream kapalı gelir, bu nedenle try-except ekleyelim
            try:
                file.save(file_path)
            except Exception as e:
                print(f"❌ Dosya kaydedilemedi: {e}")
                return render_template("main.html", error="Dosya kaydedilemedi. Lütfen tekrar deneyin.")

            # Yemek türü tahmini
            predicted_class, prob = predict_food(file_path)

            # Segmentasyon
            mask, mask_filename = save_output(file_path, UPLOAD_FOLDER)

            # Optimized weight calculation
            estimated_grams = calculate_optimized_weight(file_path, mask, predicted_class)
            
            # Kalori hesaplama
            # Yalnızca 100g ağırlığındaki girdiyi filtreleyerek doğru kalori/100g değerini al
            cal_entry = calories_df[(calories_df['label'] == predicted_class) & (calories_df['weight'] == 100)]
            
            if not cal_entry.empty:
                calories_per_100g = cal_entry['calories'].values[0]
                # MiDaS + segmentasyon ile tahmin edilen gram ın kaloriye dönüştürülmesii.
                estimated_cal = (calories_per_100g / 100) * estimated_grams
            else:
                # 100g için giriş bulunamazsa, bulunan ilk girişi kullanmayı deneyebiliriz (riskli)
                # veya varsayılan bir değer atayabiliriz. Şimdilik 0 olarak bırakıyoruz.
                # Daha iyi bir yaklaşım, CSV'de her yiyecek için 100g girdisinin olmasını sağlamaktır.
                all_entries_for_food = calories_df[calories_df['label'] == predicted_class]
                if not all_entries_for_food.empty:
                    # Fallback: İlk bulduğun girdinin ağırlık ve kalorisini alıp 100g'a oranla
                    # Bu, CSV'de 100g girdisi olmayan durumlar için bir yedek mekanizmadır.
                    # Ancak CSV'nin her zaman 100g girdisi içermesi en sağlıklısıdır.
                    fallback_weight = all_entries_for_food['weight'].values[0]
                    fallback_calories = all_entries_for_food['calories'].values[0]
                    if fallback_weight > 0: # Ağırlık 0 olmamalı
                        calories_per_100g_fallback = (fallback_calories / fallback_weight) * 100
                        estimated_cal = (calories_per_100g_fallback / 100) * estimated_grams
                        print(f"Warning: No 100g entry for {predicted_class}. Using fallback: {fallback_calories}kcal/{fallback_weight}g.")
                    else:
                        estimated_cal = 0 # Geçersiz ağırlık
                        print(f"Warning: No 100g entry and invalid fallback weight for {predicted_class}.")
                else:
                    estimated_cal = 0 # Yiyecek için hiç giriş yok
                    print(f"Warning: No calorie data found for {predicted_class}.")


            return render_template("main.html", 
                                image=filename, 
                                mask=mask_filename,
                                label=predicted_class, 
                                prob=prob,
                                grams=estimated_grams, 
                                calories=estimated_cal)
        
        except Exception as e:
            print("🚨 HATA DETAYI 🚨")
            print(e)
            print(traceback.format_exc())
            return render_template("main.html", error="Bir hata oluştu, lütfen tekrar deneyin.")


    return render_template("main.html")

if __name__ == '__main__':
    print("🚀 Flask uygulaması başlatılıyor...")
    print("💡 Modeller ilk resim yüklendiğinde yüklenecek")
    print("🌐 Site anında hazır: http://127.0.0.1:5000")
    # load_models() satırını tamamen kaldır!
    app.run(debug=True, threaded=True, port=5000)