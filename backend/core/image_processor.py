# -*- coding: utf-8 -*-
"""
Image Processor - Image preprocessing and prediction utilities
"""
import os
import cv2
import numpy as np
from PIL import Image
import torch
from torch.autograd import Variable
import torchvision.transforms as transforms
from tensorflow.keras.preprocessing import image as keras_image
import logging

# Import transforms from ml_models
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_models.data_loader import RescaleT, ToTensorLab

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing utilities for food recognition"""

    def __init__(self, device='cpu'):
        self.device = torch.device(device) if isinstance(device, str) else device

    def preprocess_for_classification(self, img_path):
        """
        Preprocess image for food classification model (ResNet50)

        Args:
            img_path (str): Path to image

        Returns:
            np.ndarray: Preprocessed image array (1, 224, 224, 3)
        """
        try:
            img = keras_image.load_img(img_path, target_size=(224, 224))
            img_array = keras_image.img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image for classification: {str(e)}")
            raise

    def predict_food_class(self, model, img_path, class_names):
        """
        Predict food class from image

        Args:
            model: Keras food classification model
            img_path (str): Path to image
            class_names (list): List of class names

        Returns:
            tuple: (predicted_class, confidence)
        """
        try:
            img_array = self.preprocess_for_classification(img_path)
            predictions = model.predict(img_array, verbose=0)[0]
            predicted_idx = np.argmax(predictions)
            predicted_class = class_names[predicted_idx]
            confidence = float(predictions[predicted_idx])
            return predicted_class, confidence
        except Exception as e:
            logger.error(f"Error predicting food class: {str(e)}")
            raise

    def generate_segmentation_mask(self, u2net_model, image_path):
        """
        Generate segmentation mask using U2NET

        Args:
            u2net_model: U2NET model
            image_path (str): Path to input image

        Returns:
            tuple: (mask array, binary_mask)
        """
        try:
            # Load and preprocess image
            image = np.array(Image.open(image_path).convert('RGB'))
            sample = {'imidx': 0, 'image': image, 'label': image}

            # Apply transformations
            transform = transforms.Compose([
                RescaleT(320),
                ToTensorLab(flag=0)
            ])
            sample = transform(sample)

            # Prepare tensor
            image_tensor = sample['image'].unsqueeze(0).float().to(self.device)

            # Forward pass
            with torch.no_grad():
                d1, *_ = u2net_model(Variable(image_tensor))
                pred = (d1[:, 0, :, :] - d1.min()) / (d1.max() - d1.min())
                mask = (pred.squeeze().cpu().data.numpy() * 255).astype(np.uint8)

            # Resize to original dimensions
            height, width = image.shape[:2]
            mask_resized = cv2.resize(mask, (width, height))
            _, binary_mask = cv2.threshold(mask_resized, 127, 255, cv2.THRESH_BINARY)

            return mask_resized, binary_mask

        except Exception as e:
            logger.error(f"Error generating segmentation mask: {str(e)}")
            raise

    def save_mask_visualization(self, image_path, mask, output_dir):
        """
        Save visualization of segmentation mask with contours

        Args:
            image_path (str): Original image path
            mask (np.ndarray): Binary mask
            output_dir (str): Output directory

        Returns:
            str: Output filename
        """
        try:
            # Load original image
            image = np.array(Image.open(image_path).convert('RGB'))

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw contours on image
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.drawContours(image_bgr, contours, -1, (0, 0, 255), 3)
            result_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            # Save result
            os.makedirs(output_dir, exist_ok=True)
            output_filename = f"mask_{os.path.basename(image_path)}"
            output_path = os.path.join(output_dir, output_filename)
            Image.fromarray(result_rgb).save(output_path)

            return output_filename

        except Exception as e:
            logger.error(f"Error saving mask visualization: {str(e)}")
            raise

    def calculate_mask_area(self, mask):
        """
        Calculate area of segmented object in pixels

        Args:
            mask (np.ndarray): Binary mask

        Returns:
            int: Area in pixels
        """
        return np.sum(mask > 0)

    def get_mask_dimensions(self, mask):
        """
        Get bounding box dimensions of mask

        Args:
            mask (np.ndarray): Binary mask

        Returns:
            tuple: (width, height) in pixels
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0, 0

        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        return w, h


def process_food_image(model_manager, image_path, output_dir):
    """
    Complete food image processing pipeline

    Args:
        model_manager: ModelManager instance
        image_path (str): Path to input image
        output_dir (str): Directory for output files

    Returns:
        dict: Processing results
    """
    try:
        processor = ImageProcessor(device=model_manager.device)

        # Load models
        food_model = model_manager.load_food_classification_model()
        u2net_model = model_manager.load_u2net_model()

        # Predict food class
        food_class, confidence = processor.predict_food_class(
            food_model, image_path, model_manager.class_names
        )

        # Generate segmentation mask
        mask, binary_mask = processor.generate_segmentation_mask(u2net_model, image_path)

        # Save visualization
        mask_filename = processor.save_mask_visualization(image_path, binary_mask, output_dir)

        # Calculate metrics
        mask_area = processor.calculate_mask_area(binary_mask)
        mask_width, mask_height = processor.get_mask_dimensions(binary_mask)

        return {
            'food_class': food_class,
            'confidence': confidence,
            'mask': binary_mask,
            'mask_filename': mask_filename,
            'mask_area': mask_area,
            'mask_width': mask_width,
            'mask_height': mask_height
        }

    except Exception as e:
        logger.error(f"Error in food image processing pipeline: {str(e)}")
        raise
