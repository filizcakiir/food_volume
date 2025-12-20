#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill script to update existing predictions with nutrition data
"""
from app import create_app
from models import db
from models.history import PredictionHistory
from core.ai_engine import get_model_manager

def backfill_nutrition():
    """Update all existing predictions with protein, carbs, fat values"""
    app = create_app('development')

    with app.app_context():
        # Get all predictions that don't have nutrition data
        predictions = PredictionHistory.query.filter(
            (PredictionHistory.protein == None) |
            (PredictionHistory.carbs == None) |
            (PredictionHistory.fat == None)
        ).all()

        if not predictions:
            print("No predictions need updating.")
            return

        print(f"Found {len(predictions)} predictions to update...")

        # Get model manager for nutrition calculations
        model_manager = get_model_manager()

        updated_count = 0
        for prediction in predictions:
            try:
                # Calculate nutrition based on food class and weight
                nutrition = model_manager.get_nutrition_for_food(
                    prediction.food_class,
                    prediction.estimated_grams
                )

                # Update the prediction
                prediction.protein = nutrition['protein']
                prediction.carbs = nutrition['carbs']
                prediction.fat = nutrition['fat']

                updated_count += 1

                if updated_count % 10 == 0:
                    print(f"Updated {updated_count}/{len(predictions)} predictions...")

            except Exception as e:
                print(f"Error updating prediction {prediction.id}: {e}")
                continue

        # Commit all changes
        db.session.commit()
        print(f"\nSuccessfully updated {updated_count} predictions with nutrition data!")

if __name__ == '__main__':
    backfill_nutrition()
