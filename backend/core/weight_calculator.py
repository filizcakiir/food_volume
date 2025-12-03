# -*- coding: utf-8 -*-
"""
Weight Calculator - Estimate food weight from mask and food class
Simplified version with smart portion estimation
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Food portion weights (grams) by size
FOOD_PORTIONS = {
    'baklava': {'small': 80, 'medium': 140, 'large': 200},
    'apple_pie': {'small': 90, 'medium': 130, 'large': 180},
    'pizza': {'small': 150, 'medium': 250, 'large': 400},
    'cheesecake': {'small': 70, 'medium': 110, 'large': 150},
    'chocolate_cake': {'small': 80, 'medium': 120, 'large': 170},
    'hamburger': {'small': 120, 'medium': 180, 'large': 250},
    'french_fries': {'small': 60, 'medium': 100, 'large': 150},
    'lasagna': {'small': 180, 'medium': 250, 'large': 350},
    'spaghetti_bolognese': {'small': 200, 'medium': 300, 'large': 450},
    'ice_cream': {'small': 50, 'medium': 80, 'large': 120},
    'chicken_wings': {'small': 80, 'medium': 120, 'large': 180},
    'steak': {'small': 120, 'medium': 200, 'large': 300},
    'default': {'small': 80, 'medium': 130, 'large': 200}
}


class WeightCalculator:
    """Calculate food weight from segmentation mask and food class"""

    def __init__(self):
        self.portions = FOOD_PORTIONS

    def estimate_portion_size(self, mask_area, mask_width, mask_height):
        """
        Estimate portion size (small/medium/large) based on mask dimensions

        Args:
            mask_area (int): Area in pixels
            mask_width (int): Width in pixels
            mask_height (int): Height in pixels

        Returns:
            str: Portion size ('small', 'medium', 'large')
        """
        # Normalize by image size (assuming 640x480 typical image)
        normalized_area = mask_area / (640 * 480)

        # Simple heuristic based on area
        if normalized_area < 0.15:
            return 'small'
        elif normalized_area < 0.35:
            return 'medium'
        else:
            return 'large'

    def calculate_weight(self, food_class, mask_area, mask_width, mask_height):
        """
        Calculate estimated weight in grams

        Args:
            food_class (str): Food class name
            mask_area (int): Mask area in pixels
            mask_width (int): Mask width in pixels
            mask_height (int): Mask height in pixels

        Returns:
            tuple: (estimated_weight, portion_size)
        """
        try:
            # Determine portion size
            portion_size = self.estimate_portion_size(mask_area, mask_width, mask_height)

            # Get portion weights for this food class
            if food_class in self.portions:
                portion_weights = self.portions[food_class]
            else:
                logger.warning(f"No portion data for {food_class}, using default")
                portion_weights = self.portions['default']

            # Get weight for estimated portion size
            estimated_weight = portion_weights[portion_size]

            # Apply minor adjustment based on actual area
            # (within +/- 20% of portion weight)
            normalized_area = mask_area / (640 * 480)
            area_factor = max(0.8, min(1.2, normalized_area * 3))
            adjusted_weight = round(estimated_weight * area_factor)

            logger.info(f"Weight estimated: {food_class} = {adjusted_weight}g ({portion_size})")
            return adjusted_weight, portion_size

        except Exception as e:
            logger.error(f"Error calculating weight: {str(e)}")
            # Fallback to medium default
            return 130, 'medium'

    def calculate_weight_simple(self, food_class, mask_area):
        """
        Simplified weight calculation using only mask area

        Args:
            food_class (str): Food class name
            mask_area (int): Mask area in pixels

        Returns:
            int: Estimated weight in grams
        """
        # Use mask area ratio for simple estimation
        mask_width = int(np.sqrt(mask_area))
        mask_height = int(np.sqrt(mask_area))
        weight, _ = self.calculate_weight(food_class, mask_area, mask_width, mask_height)
        return weight


def estimate_food_weight(food_class, mask_area, mask_width=None, mask_height=None):
    """
    Convenience function to estimate food weight

    Args:
        food_class (str): Food class name
        mask_area (int): Mask area in pixels
        mask_width (int, optional): Mask width
        mask_height (int, optional): Mask height

    Returns:
        int: Estimated weight in grams
    """
    calculator = WeightCalculator()

    if mask_width is None or mask_height is None:
        return calculator.calculate_weight_simple(food_class, mask_area)
    else:
        weight, _ = calculator.calculate_weight(food_class, mask_area, mask_width, mask_height)
        return weight
