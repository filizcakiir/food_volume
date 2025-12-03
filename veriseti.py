import tensorflow as tf                          # TensorFlow ile derin öğrenme modellerini oluşturmak ve çalıştırmak için
import matplotlib.image as img                    # Görüntüleri dosyadan okumak için
import matplotlib.pyplot as plt                   # Eğitim süresince grafik çizimleri için
import numpy as np                                # Sayısal işlemler, dizi yönetimi
from collections import defaultdict               # Anahtar-değer sayma gibi işlemler için
import collections                                # Ekstra koleksiyon yapıları (ör., deque) için
from shutil import copy, copytree, rmtree         # Dosya/klasör kopyalama ve silme
import tensorflow.keras.backend as K              # TensorFlow Keras backend fonksiyonları
from tensorflow.keras.models import load_model    # Önceden eğitilmiş modelleri yükleme
from tensorflow.keras.preprocessing import image  # Görüntü ön işleme araçları
import os                                         # İşletim sistemi ile dosya işlemleri
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'         # TensorFlow’un OneDNN optimizasyonlarını kapatmak için (bazı uyumluluk sorunları için)
import subprocess                                 # Komut satırı işlemleri (ör. dış script çalıştırmak için)
import random
import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras import regularizers
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
from tensorflow.keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D, GlobalAveragePooling2D, AveragePooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.regularizers import l2
from tensorflow import keras
from tensorflow.keras import models
import cv2

# Check if GPU is enabled
print(tf.__version__)
print(tf.test.gpu_device_name())

import os
import shutil
# Helper method to create train_101 and test_101 data samples
def dataset_mini(food_list, src, dest):
    if not os.path.exists(dest):  # Eğer klasör yoksa oluştur
        os.makedirs(dest)
        for food_item in food_list:
            print("Copying images into", food_item)
            copytree(os.path.join(src, food_item), os.path.join(dest, food_item))
    else:
        print(f"{dest} klasörü zaten mevcut, yeniden oluşturulmadı.")

# picking 101 food items and generating separate data folders for the same
food_list = ['apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare', 
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
src_train = 'train'
dest_train = 'C:/Users/filiz/Desktop/KAGGLE/working/train_101'
src_test = 'test'
dest_test = 'C:/Users/filiz/Desktop/KAGGLE/working/test_101'

print("Creating train data folder with new classes")
dataset_mini(food_list, src_train, dest_train)

import os

def count_files_and_dirs(path):
    total_count = sum([len(files) + len(dirs) for _, dirs, files in os.walk(path)])
    return total_count

total_samples = count_files_and_dirs(dest_train)

print("Total number of samples in train folder:", total_samples)


print("Creating test data folder with new classes")
dataset_mini(food_list, src_test, dest_test)

import os

def count_files_and_dirs(path):
    total_count = sum([len(files) + len(dirs) for _, dirs, files in os.walk(path)])
    return total_count

total_samples = count_files_and_dirs(dest_test)

print("Total number of samples in test folder:", total_samples)

from tensorflow.keras.applications.resnet50 import ResNet50

# Model dosyasının yolu
model_path = 'C:/Users/filiz/Desktop/KAGGLE/working/model_trained_101class.hdf5'

n_classes = 101
img_width, img_height = 224, 224
train_data_dir = 'C:/Users/filiz/Desktop/KAGGLE/working/train_101'
validation_data_dir = 'C:/Users/filiz/Desktop/KAGGLE/working/test_101'
nb_train_samples = 2250 #75750 # Toplam eğitim verisi örneği sayısı
nb_validation_samples = 750 #25250 # Doğrulama (test) örneği sayısı
batch_size = 16# Her eğitim adımında kaç örneğin modele verileceği

train_datagen = ImageDataGenerator(
    rescale=1. / 255,         # Piksel değerlerini [0,255] yerine [0,1] aralığına getirir
    shear_range=0.2,          # Rastgele kesme dönüşümü (shearing)
    zoom_range=0.2,           # Rastgele yakınlaştırma
    horizontal_flip=True)     # Görselleri yatay eksende çevirebilir (augmentation)

test_datagen = ImageDataGenerator(rescale=1. / 255)  # Doğrulama verisinde sadece normalize işlemi yapılır

train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical')

validation_generator = test_datagen.flow_from_directory(
    validation_data_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical')

# Modelin varlığını kontrol et
try:
    if os.path.exists(model_path):
        print("Model mevcut, eğitim yapılmayacak.")
        model = load_model(model_path)

        # Kayıtlı eğitim geçmişini yüklemeyi dene
        history_path = 'C:/Users/filiz/Desktop/KAGGLE/working/history_3class.log'
        if os.path.exists(history_path):
            history_df = pd.read_csv(history_path)
            history = {
                'accuracy': history_df['accuracy'].values,
                'val_accuracy': history_df['val_accuracy'].values,
                'loss': history_df['loss'].values,
                'val_loss': history_df['val_loss'].values
            }
        else:
            history = None  # Eğer kayıtlı history yoksa boş bırak
        
    else:
            raise FileNotFoundError
except FileNotFoundError:
    print("Model bulunamadı, eğitim yapılacak.")
    # Modeli sıfırdan oluştur
    resnet50 = ResNet50(weights='imagenet', include_top=False)
    x = resnet50.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128,activation='relu')(x)
    x = Dropout(0.2)(x)

    predictions = Dense(101,kernel_regularizer=regularizers.l2(0.005), activation='softmax')(x) # Önceden eğitilmiş gövde (son sınıflandırıcı katman yok)

    model = Model(inputs=resnet50.input, outputs=predictions)
    model.compile(optimizer=SGD(learning_rate=0.0001, momentum=0.9), loss='categorical_crossentropy', metrics=['accuracy'])
    #SGD: Öğrenme oranı düşük, momentumlu klasik stochastic gradient descent.
    #Kayıp fonksiyonu: Çok sınıflı sınıflandırmada yaygın olan categorical crossentropy.
    from tensorflow.keras.callbacks import ModelCheckpoint

    checkpointer = ModelCheckpoint(filepath='C:/Users/filiz/Desktop/KAGGLE/working/best_model_101class.keras', verbose=1, save_best_only=True)
    #ModelCheckpoint: Her epoch sonunda doğrulama başarımı en iyi olan modeli .keras dosyası olarak kaydeder.

    #CSVLogger: Her epoch sonunda loss, accuracy, val_loss, val_accuracy gibi metrikleri .log dosyasına yazar.
    csv_logger = CSVLogger('C:/Users/filiz/Desktop/KAGGLE/working/history_101class.log')

    history = model.fit(
        train_generator,
        steps_per_epoch=nb_train_samples // batch_size, #Kaç batch ile bir epoch tamamlanır. Örn: 2250 / 16 = 140
        validation_data=validation_generator,
        validation_steps=nb_validation_samples // batch_size,
        epochs=30,
        verbose=1,
        callbacks=[csv_logger, checkpointer],
    )


     # Eğitimi tamamladıktan sonra modeli kaydet
    model.save(model_path)
    print("Eğitim tamamlandı ve model kaydedildi.")
