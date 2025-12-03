import tensorflow as tf
import matplotlib.image as img
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import collections
from shutil import copy
import pandas as pd
from shutil import copytree, rmtree
import tensorflow.keras.backend as K
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt
import numpy as np
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import subprocess
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

os.chdir('C:/Users/filiz/Desktop/KAGGLE/input/food-101/')

def check_extracted_folder():
    print(os.listdir('food-101/'))
    

check_extracted_folder()

# food-101/images dizinindeki dosyaları kontrol etme
def list_image_files():
    image_files = os.listdir('food-101/images')
    print(image_files)

# Fonksiyonu çağırarak görselleri listeleme
list_image_files()

# food-101/meta dizinindeki dosyaları kontrol etme
def list_meta_files():
    meta_files = os.listdir('food-101/meta')
    print(meta_files)

# Fonksiyonu çağırarak meta verilerini listeleme
list_meta_files()

# Dosyayı aç ve ilk 10 satırı oku
with open('food-101/meta/train.txt', 'r') as file:
    # İlk 10 satırı oku
    for _ in range(10):
        print(file.readline().strip())  # Her satırı ekrana yazdır


# classes.txt dosyasını okuma
with open('food-101/meta/classes.txt', 'r') as file:
    # İlk 10 satırı oku
    for _ in range(10):
        line = file.readline()
        print(line.strip())  # Satırı yazdır, strip() ile boşlukları temiz4le

# Visualize the data, showing one image per class from 101 classes
rows = 17
cols = 6
fig, ax = plt.subplots(rows, cols, figsize=(25,25))
fig.suptitle("Showing one random image from each class", y=1.05, fontsize=24) # Adding  y=1.05, fontsize=24 helped me fix the suptitle overlapping with axes issue
data_dir = "food-101/images/"
foods_sorted = sorted(os.listdir(data_dir))
food_id = 0
for i in range(rows):
  for j in range(cols):
    try:
      food_selected = foods_sorted[food_id] 
      food_id += 1
    except:
      break
    if food_selected == '.DS_Store':
        continue
    food_selected_images = os.listdir(os.path.join(data_dir,food_selected)) # returns the list of all files present in each food category
    food_selected_random = np.random.choice(food_selected_images) # picks one food item from the list as choice, takes a list and returns one random item
    img = plt.imread(os.path.join(data_dir,food_selected, food_selected_random))
    ax[i][j].imshow(img)
    ax[i][j].set_title(food_selected, pad = 10)
    
plt.setp(ax, xticks=[],yticks=[])
plt.tight_layout()
#plt.show()  # Görselleştirmeyi gösterir
# https://matplotlib.org/users/tight_layout_guide.html

# Veri setini belirli klasörlere ayırma fonksiyonu
def prepare_data(filepath, src, dest):
    classes_images = defaultdict(list)
    with open(filepath, 'r') as txt:
        paths = [read.strip() for read in txt.readlines()]
        for p in paths:
            food = p.split('/')
            classes_images[food[0]].append(food[1] + '.jpg')

    for food in classes_images.keys():
        print("\nCopying images into", food)
        if not os.path.exists(os.path.join(dest, food)):
            os.makedirs(os.path.join(dest, food))
        for i in classes_images[food]:
            copy(os.path.join(src, food, i), os.path.join(dest, food, i))
    print("Copying Done!")


# Train klasörünü hazırlama
if not os.path.exists('train'):
    print("Creating train data...")
    prepare_data('food-101/meta/train.txt', 'food-101/images', 'train')
else:
    print("Train data already exists. Skipping preparation.")

# Çalışma dizinini yazdırma
print("Çalışma dizini:", os.getcwd())

# Test klasörünü hazırlama
if not os.path.exists('test'):
    print("Creating test data...")
    prepare_data('food-101/meta/test.txt', 'food-101/images', 'test')
else:
    print("Test data already exists. Skipping preparation.")

def count_files_in_directory(directory):
    file_count = 0
    for root, dirs, files in os.walk(directory):
        file_count += len(files)
    return file_count

# Train klasöründeki toplam dosya sayısını kontrol edin
print("Total number of samples in train folder:", count_files_in_directory('train'))

# Test klasöründeki toplam dosya sayısını kontrol edin
print("Total number of samples in test folder:", count_files_in_directory('test'))

if '.DS_Store' in foods_sorted:
    foods_sorted.remove('.DS_Store')

foods_sorted

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
nb_train_samples = 2250 #75750
nb_validation_samples = 750 #25250
batch_size = 16

train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True)

test_datagen = ImageDataGenerator(rescale=1. / 255)

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
        history_path = 'C:/Users/filiz/Desktop/KAGGLE/working/history_101class.log'
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
    K.clear_session()  # Bellek temizliği
    resnet50 = ResNet50(weights='imagenet', include_top=False)
    x = resnet50.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128,activation='relu')(x)
    x = Dropout(0.2)(x)

    predictions = Dense(101,kernel_regularizer=regularizers.l2(0.005), activation='softmax')(x)

    model = Model(inputs=resnet50.input, outputs=predictions)
    model.compile(optimizer=SGD(learning_rate=0.0001, momentum=0.9), loss='categorical_crossentropy', metrics=['accuracy'])
    from tensorflow.keras.callbacks import ModelCheckpoint

    checkpointer = ModelCheckpoint(filepath='C:/Users/filiz/Desktop/KAGGLE/working/best_model_101class.keras', verbose=1, save_best_only=True)

    csv_logger = CSVLogger('C:/Users/filiz/Desktop/KAGGLE/working/history_101class.log')

    history = model.fit(
        train_generator,
        steps_per_epoch=nb_train_samples // batch_size,
        validation_data=validation_generator,
        validation_steps=nb_validation_samples // batch_size,
        epochs=30,
        verbose=1,
        callbacks=[csv_logger, checkpointer],
    )


     # Eğitimi tamamladıktan sonra modeli kaydet
    model.save(model_path)
    print("Eğitim tamamlandı ve model kaydedildi.")
    
# Grafikleri çizen fonksiyonlar
def plot_accuracy(history, title="Model Accuracy"):
    if history is None:
        print("Uyarı: History verisi bulunamadı.")
        return
    plt.title(title)
    plt.plot(history['accuracy'])
    plt.plot(history['val_accuracy'])
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train Accuracy', 'Validation Accuracy'], loc='best')
    plt.show()

def plot_loss(history, title="Model Loss"):
    if history is None:
        print("Uyarı: History verisi bulunamadı.")
        return
    plt.title(title)
    plt.plot(history['loss'])
    plt.plot(history['val_loss'])
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train Loss', 'Validation Loss'], loc='best')
    plt.show()

# History varsa çizim yap
if history:
    plot_accuracy(history, 'FOOD101-ResNet50')
    plot_loss(history, 'FOOD101-ResNet50')
    
    
# Kalori veri setini yükle
calories_df = pd.read_csv('C:/Users/filiz/Desktop/KAGGLE/calories_per_101class_100g.csv')

# Test görseli yolu
test_image_path = 'C:/Users/filiz/Desktop/KAGGLE/working/test_101/tiramisu/1016527.jpg'

# Görseli yükleyip ön işleme yapıyoruz
img_width, img_height = 224, 224
img = image.load_img(test_image_path, target_size=(img_width, img_height))
img_array = image.img_to_array(img)  # Görseli numpy array formatına çevir
img_array = np.expand_dims(img_array, axis=0)  # 4D tensor (batch, height, width, channels) haline getir
img_array = img_array / 255.0  # Normalizasyon (0-1 arası)

# Modelle tahmin yap
predictions = model.predict(img_array)

# Modelin sınıfları
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
predicted_class = class_names[np.argmax(predictions)]  # Tahmin edilen sınıf
predicted_probability = np.max(predictions)  # Tahmin edilen sınıfın olasılığı

# Kalori değerini getir
calorie_value = calories_df.loc[calories_df['Food'] == predicted_class, 'Calories_per_100g'].values

# Sonuçları yazdır
print(f"Tahmin edilen yemek: {predicted_class}")
print(f"Tahmin edilen olasılık: {predicted_probability:.2f}")

# Eğer kalori bilgisi varsa ekrana yaz
if len(calorie_value) > 0:
    calorie_text = f"{calorie_value[0]} kcal (100g)"
    print(f"100 gram başına kalori: {calorie_text}")
else:
    calorie_text = "Kalori bilgisi bulunamadı!"

# Görseli göster
plt.imshow(img)
plt.title(f"Predicted: {predicted_class} ({predicted_probability:.2f})\n{calorie_text}")
plt.axis('off')
plt.show()