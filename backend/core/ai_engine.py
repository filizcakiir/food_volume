# -*- coding: utf-8 -*-
"""
AI Engine - Model Loading and Management
Lazy loading pattern with singleton for efficient memory usage
"""
import os
import torch
import pandas as pd
from tensorflow.keras.models import load_model as keras_load_model
import logging

# Import U2NET from ml_models
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_models.u2net import U2NETP

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Singleton class to manage AI models with lazy loading.
    Models are loaded once and cached for subsequent requests.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not ModelManager._initialized:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.food_model = None
            self.u2net_model = None
            self.midas_model = None
            self.midas_transforms = None
            self.calories_df = None
            self.class_names = self._get_class_names()
            ModelManager._initialized = True
            logger.info(f"ModelManager initialized on device: {self.device}")

    @staticmethod
    def _get_class_names():
        """101 food class names"""
        return ['apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
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

    def load_food_classification_model(self):
        """Load ResNet50-based food classification model"""
        if self.food_model is not None:
            return self.food_model

        try:
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                      'weights', 'model_trained_101class.hdf5')
            logger.info(f"Loading food classification model from {model_path}")
            self.food_model = keras_load_model(model_path)
            logger.info(" Food classification model loaded successfully")
            return self.food_model
        except Exception as e:
            logger.error(f"Failed to load food classification model: {str(e)}")
            raise

    def load_u2net_model(self):
        """Load U2NET segmentation model"""
        if self.u2net_model is not None:
            return self.u2net_model

        try:
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                      'weights', 'u2netp.pth')
            logger.info(f"Loading U2NET model from {model_path}")
            self.u2net_model = U2NETP(3, 1)
            self.u2net_model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.u2net_model.to(self.device)
            self.u2net_model.eval()
            logger.info(" U2NET segmentation model loaded successfully")
            return self.u2net_model
        except Exception as e:
            logger.error(f"Failed to load U2NET model: {str(e)}")
            raise

    def load_midas_model(self):
        """Load MiDaS depth estimation model"""
        if self.midas_model is not None and self.midas_transforms is not None:
            return self.midas_model, self.midas_transforms

        try:
            logger.info("Loading MiDaS depth estimation model from torch hub...")
            self.midas_model = torch.hub.load("intel-isl/MiDaS", "DPT_Large",
                                              trust_repo=True, verbose=False)
            self.midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms",
                                                    trust_repo=True, verbose=False).dpt_transform
            self.midas_model.eval().to(self.device)
            logger.info(" MiDaS depth model loaded successfully")
            return self.midas_model, self.midas_transforms
        except Exception as e:
            logger.error(f"Failed to load MiDaS model: {str(e)}")
            raise

    def load_calories_data(self):
        """Load calorie database"""
        if self.calories_df is not None:
            return self.calories_df

        try:
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                    'weights', 'calories_per_101class_100g.csv')
            logger.info(f"Loading calorie data from {csv_path}")
            self.calories_df = pd.read_csv(csv_path)
            logger.info(" Calorie data loaded successfully")
            return self.calories_df
        except Exception as e:
            logger.error(f"Failed to load calorie data: {str(e)}")
            raise

    def ensure_all_models_loaded(self):
        """Load all models at once (lazy loading)"""
        logger.info("= Loading all AI models...")
        self.load_food_classification_model()
        self.load_u2net_model()
        self.load_midas_model()
        self.load_calories_data()
        logger.info("All models loaded successfully!")

    def get_calorie_for_food(self, food_class, weight_grams):
        """
        Calculate calories for given food and weight

        Args:
            food_class (str): Food class name
            weight_grams (float): Weight in grams

        Returns:
            float: Calories
        """
        if self.calories_df is None:
            self.load_calories_data()

        try:
            row = self.calories_df[self.calories_df['label'] == food_class]
            if row.empty:
                logger.warning(f"No calorie data for {food_class}, using default")
                return weight_grams * 2.5  # Default: 250 kcal per 100g

            calories_per_100g = row['calories'].values[0]
            total_calories = (weight_grams / 100) * calories_per_100g
            return round(total_calories, 1)
        except Exception as e:
            logger.error(f"Error calculating calories: {str(e)}")
            return weight_grams * 2.5  # Fallback

    def get_nutrition_for_food(self, food_class, weight_grams):
        """
        Calculate full nutrition (calories, protein, carbs, fat) for given food and weight

        Args:
            food_class (str): Food class name
            weight_grams (float): Weight in grams

        Returns:
            dict: Nutrition values (calories, protein, carbs, fat)
        """
        if self.calories_df is None:
            self.load_calories_data()

        try:
            row = self.calories_df[self.calories_df['label'] == food_class]
            if row.empty:
                logger.warning(f"No nutrition data for {food_class}, using defaults")
                # Defaults for unknown food
                return {
                    'calories': round(weight_grams * 2.5, 1),
                    'protein': round(weight_grams * 0.15, 1),
                    'carbs': round(weight_grams * 0.30, 1),
                    'fat': round(weight_grams * 0.10, 1)
                }

            # Get values per 100g
            calories_per_100g = row['calories'].values[0]
            protein_per_100g = row['protein'].values[0]
            carbs_per_100g = row['carbs'].values[0]
            fat_per_100g = row['fat'].values[0]

            # Calculate for actual weight
            ratio = weight_grams / 100

            return {
                'calories': round(calories_per_100g * ratio, 1),
                'protein': round(protein_per_100g * ratio, 1),
                'carbs': round(carbs_per_100g * ratio, 1),
                'fat': round(fat_per_100g * ratio, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating nutrition: {str(e)}")
            # Fallback
            return {
                'calories': round(weight_grams * 2.5, 1),
                'protein': round(weight_grams * 0.15, 1),
                'carbs': round(weight_grams * 0.30, 1),
                'fat': round(weight_grams * 0.10, 1)
            }


# Global instance
_model_manager = None


def get_model_manager():
    """Get singleton instance of ModelManager"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
