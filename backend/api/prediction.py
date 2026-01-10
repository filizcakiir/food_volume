# -*- coding: utf-8 -*-
"""
Prediction API - Food recognition and calorie estimation
"""
import os
import time
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.history import PredictionHistory, DailyLog
from core.ai_engine import get_model_manager
from core.image_processor import process_food_image
from core.weight_calculator import estimate_food_weight
from services.notification_service import AchievementService, StreakService
from flask import g

prediction_bp = Blueprint('prediction', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@prediction_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Food recognition and calorie estimation endpoint

    Expects:
        - image: File upload
        - meal_type: Optional (breakfast, lunch, dinner, snack)

    Returns:
        - food_class: Recognized food
        - confidence: Prediction confidence
        - estimated_grams: Weight estimation
        - calories: Calorie estimation
        - image_url: Original image URL
        - mask_url: Segmentation mask URL
    """
    start_time = time.time()

    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Allowed: jpg, jpeg, png'
            }), 400

        # Get optional parameters
        meal_type = request.form.get('meal_type', None)
        user_note = request.form.get('note', None)

        # Get current user
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Save uploaded file
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)

        # Generate unique filename
        file_ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        image_path = os.path.join(upload_folder, unique_filename)
        file.save(image_path)

        current_app.logger.info(f"Image saved: {image_path}")

        # Get model manager
        model_manager = get_model_manager()

        # Ensure models are loaded (lazy loading)
        model_manager.ensure_all_models_loaded()

        # Process image
        current_app.logger.info("Processing image...")
        result = process_food_image(model_manager, image_path, upload_folder)

        # Estimate weight
        estimated_grams = estimate_food_weight(
            result['food_class'],
            result['mask_area'],
            result['mask_width'],
            result['mask_height']
        )

        # Calculate full nutrition (calories, protein, carbs, fat)
        nutrition = model_manager.get_nutrition_for_food(result['food_class'], estimated_grams)
        calories = nutrition['calories']

        # Save to database
        prediction = PredictionHistory(
            user_id=current_user_id,
            image_path=image_path,
            mask_path=os.path.join(upload_folder, result['mask_filename']),
            food_class=result['food_class'],
            confidence=result['confidence'],
            estimated_grams=estimated_grams,
            calories=calories,
            protein=nutrition['protein'],
            carbs=nutrition['carbs'],
            fat=nutrition['fat'],
            meal_type=meal_type,
            user_note=user_note,
            processing_time=time.time() - start_time
        )

        db.session.add(prediction)

        # Update daily log
        if meal_type:
            daily_log = DailyLog.get_or_create(current_user_id)
            if user.profile and user.profile.daily_calorie_goal:
                daily_log.daily_goal = user.profile.daily_calorie_goal
            daily_log.add_prediction(prediction)

        db.session.commit()

        current_app.logger.info(
            f"Prediction saved: {result['food_class']} "
            f"({estimated_grams}g, {calories} kcal)"
        )

        # Trigger achievements/streak only when a meal is actually saved
        if meal_type:
            try:
                AchievementService.check_and_award_achievements(
                    current_user_id,
                    context='prediction'
                )
                StreakService.update_user_streak(
                    current_user_id,
                    activity_date=prediction.created_at.date()
                )

                # Cache result for downstream UI (e.g., to reduce extra calls)
                g.streak_updated = True
            except Exception as notify_err:
                current_app.logger.warning(
                    f"Notification/streak trigger failed: {notify_err}"
                )

        # Return response
        return jsonify({
            'success': True,
            'message': 'Prediction successful',
            'data': {
                'id': prediction.id,
                'food_class': result['food_class'],
                'confidence': round(result['confidence'], 4),
                'estimated_grams': estimated_grams,
                'calories': calories,
                'protein': nutrition['protein'],
                'carbs': nutrition['carbs'],
                'fat': nutrition['fat'],
                'meal_type': meal_type,
                'image_url': f'/static/uploads/{unique_filename}',
                'mask_url': f'/static/uploads/{result["mask_filename"]}',
                'processing_time': round(time.time() - start_time, 2)
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Prediction failed',
            'details': str(e)
        }), 500


@prediction_bp.route('/food-classes', methods=['GET'])
def get_food_classes():
    """Get list of all supported food classes"""
    try:
        model_manager = get_model_manager()
        return jsonify({
            'success': True,
            'data': {
                'classes': model_manager.class_names,
                'count': len(model_manager.class_names)
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting food classes: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get food classes'}), 500
