# -*- coding: utf-8 -*-
"""
GastronomGoz - Prediction History Management API

This module provides RESTful API endpoints for managing user food prediction history.

API Endpoints:
- GET    /api/history              - List all predictions with pagination and filters
- GET    /api/history/<id>         - Get single prediction details
- PATCH  /api/history/<id>         - Update prediction information
- DELETE /api/history/<id>         - Delete prediction
- GET    /api/daily-log            - Get today's daily log summary
- GET    /api/daily-log/date       - Get specific date's summary
- GET    /api/daily-log/week       - Get this week's summary
- GET    /api/daily-log/month      - Get this month's summary
- GET    /api/stats/favorites      - List favorite foods
- GET    /api/stats/top-foods      - List most consumed foods
- GET    /api/stats/meal-distribution - Get meal distribution
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta, date
from sqlalchemy import func, desc, and_, or_
import logging

from models import db
from models.history import PredictionHistory, DailyLog
from models.user import User
from schemas.history_schema import (
    UpdatePredictionSchema,
    HistoryFilterSchema,
    DateRangeSchema
)
from services.notification_service import AchievementService, StreakService
from flask import g

# Blueprint creation
history_bp = Blueprint('history', __name__)

# Logger setup
logger = logging.getLogger(__name__)

# Schema instances
update_prediction_schema = UpdatePredictionSchema()
history_filter_schema = HistoryFilterSchema()
date_range_schema = DateRangeSchema()


# ============================================================================
# Helper Functions
# ============================================================================

def success_response(data, message="Success", status=200):
    """Return success response"""
    return jsonify({
        'success': True,
        'message': message,
        'data': data
    }), status


def error_response(message, status=400):
    """Return error response"""
    return jsonify({
        'success': False,
        'error': message
    }), status


def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)


# ============================================================================
# Prediction History Endpoints
# ============================================================================

@history_bp.route('/history', methods=['GET'])
@jwt_required()
def list_predictions():
    """
    GET /api/history - List all predictions with pagination and filtering

    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - meal_type: Filter by meal type (breakfast, lunch, dinner, snack)
    - food_class: Filter by food name
    - is_favorite: Filter favorite items (true/false)
    - start_date: Start date filter (YYYY-MM-DD)
    - end_date: End date filter (YYYY-MM-DD)
    - min_calories: Minimum calories filter
    - max_calories: Maximum calories filter
    - sort_by: Sort field (created_at, calories, confidence, food_class)
    - sort_order: Sort direction (asc, desc)
    """
    try:
        filters = history_filter_schema.load(request.args)
    except ValidationError as err:
        return error_response(err.messages, 400)

    user_id = get_jwt_identity()
    # Default: show only saved items (meal_type set). To include drafts, pass include_unsaved=true
    include_unsaved = request.args.get('include_unsaved', 'false').lower() == 'true'
    query = PredictionHistory.query.filter_by(user_id=user_id)
    if not include_unsaved:
        query = query.filter(PredictionHistory.meal_type.isnot(None))

    # Apply filters
    if filters.get('meal_type'):
        query = query.filter_by(meal_type=filters['meal_type'])

    if filters.get('food_class'):
        query = query.filter(PredictionHistory.food_class.ilike(f"%{filters['food_class']}%"))

    if filters.get('is_favorite') is not None:
        query = query.filter_by(is_favorite=filters['is_favorite'])

    if filters.get('start_date'):
        query = query.filter(PredictionHistory.created_at >= filters['start_date'])

    if filters.get('end_date'):
        end_datetime = datetime.combine(filters['end_date'], datetime.max.time())
        query = query.filter(PredictionHistory.created_at <= end_datetime)

    if filters.get('min_calories') is not None:
        query = query.filter(PredictionHistory.calories >= filters['min_calories'])

    if filters.get('max_calories') is not None:
        query = query.filter(PredictionHistory.calories <= filters['max_calories'])

    # Apply sorting
    sort_by = filters.get('sort_by', 'created_at')
    sort_order = filters.get('sort_order', 'desc')

    if sort_order == 'desc':
        query = query.order_by(desc(getattr(PredictionHistory, sort_by)))
    else:
        query = query.order_by(getattr(PredictionHistory, sort_by))

    # Pagination
    page = filters.get('page', 1)
    per_page = filters.get('per_page', 20)

    paginated = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    predictions = [p.to_dict() for p in paginated.items]

    return success_response({
        'predictions': predictions,
        'pagination': {
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total_items': paginated.total,
            'total_pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    }, "Predictions retrieved successfully")


@history_bp.route('/history/<int:prediction_id>', methods=['GET'])
@jwt_required()
def get_prediction(prediction_id):
    """
    GET /api/history/<id> - Get single prediction details
    """
    user_id = get_jwt_identity()

    prediction = PredictionHistory.query.filter_by(
        id=prediction_id,
        user_id=user_id
    ).first()

    if not prediction:
        return error_response("Prediction not found", 404)

    return success_response(
        prediction.to_dict(),
        "Prediction retrieved successfully"
    )


@history_bp.route('/history/<int:prediction_id>', methods=['PATCH'])
@jwt_required()
def update_prediction(prediction_id):
    """
    PATCH /api/history/<id> - Update prediction information
    """
    try:
        data = update_prediction_schema.load(request.json or {})
    except ValidationError as err:
        return error_response(err.messages, 400)

    user_id = get_jwt_identity()

    prediction = PredictionHistory.query.filter_by(
        id=prediction_id,
        user_id=user_id
    ).first()

    if not prediction:
        return error_response("Prediction not found", 404)

    # Update fields
    if 'user_note' in data:
        prediction.user_note = data['user_note']

    if 'meal_type' in data:
        old_meal_type = prediction.meal_type
        new_meal_type = data['meal_type']

        # Update daily log if meal_type changes
        if old_meal_type != new_meal_type:
            daily_log = DailyLog.get_or_create(
                user_id=user_id,
                target_date=prediction.created_at.date()
            )

            # If this is the first time adding meal_type, increment totals
            if old_meal_type is None and new_meal_type is not None:
                daily_log.total_calories += prediction.calories
                daily_log.total_meals += 1

                # Trigger achievements/streak for newly saved meals
                try:
                    AchievementService.check_and_award_achievements(
                        user_id,
                        context='prediction'
                    )
                    StreakService.update_user_streak(
                        user_id,
                        activity_date=prediction.created_at.date()
                    )
                    g.streak_updated = True
                except Exception as notify_err:
                    logger.warning(f"Notification/streak trigger failed: {notify_err}")

            # Remove calories from old meal_type
            if old_meal_type == 'breakfast':
                daily_log.breakfast_calories -= prediction.calories
            elif old_meal_type == 'lunch':
                daily_log.lunch_calories -= prediction.calories
            elif old_meal_type == 'dinner':
                daily_log.dinner_calories -= prediction.calories
            elif old_meal_type == 'snack':
                daily_log.snack_calories -= prediction.calories

            # Add calories to new meal_type
            if new_meal_type == 'breakfast':
                daily_log.breakfast_calories += prediction.calories
            elif new_meal_type == 'lunch':
                daily_log.lunch_calories += prediction.calories
            elif new_meal_type == 'dinner':
                daily_log.dinner_calories += prediction.calories
            elif new_meal_type == 'snack':
                daily_log.snack_calories += prediction.calories

        prediction.meal_type = new_meal_type

    if 'is_favorite' in data:
        prediction.is_favorite = data['is_favorite']

    try:
        db.session.commit()
        logger.info(f"Prediction {prediction_id} updated by user {user_id}")
        return success_response(
            prediction.to_dict(),
            "Prediction updated successfully"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating prediction {prediction_id}: {str(e)}")
        return error_response("Error updating prediction", 500)


@history_bp.route('/history/<int:prediction_id>', methods=['DELETE'])
@jwt_required()
def delete_prediction(prediction_id):
    """
    DELETE /api/history/<id> - Delete prediction
    """
    user_id = get_jwt_identity()

    prediction = PredictionHistory.query.filter_by(
        id=prediction_id,
        user_id=user_id
    ).first()

    if not prediction:
        return error_response("Prediction not found", 404)

    try:
        daily_log = DailyLog.query.filter_by(
            user_id=user_id,
            date=prediction.created_at.date()
        ).first()

        if daily_log:
            daily_log.total_calories -= prediction.calories
            daily_log.total_meals -= 1

            if prediction.meal_type == 'breakfast':
                daily_log.breakfast_calories -= prediction.calories
            elif prediction.meal_type == 'lunch':
                daily_log.lunch_calories -= prediction.calories
            elif prediction.meal_type == 'dinner':
                daily_log.dinner_calories -= prediction.calories
            elif prediction.meal_type == 'snack':
                daily_log.snack_calories -= prediction.calories

            # Prevent negative values
            daily_log.total_calories = max(0, daily_log.total_calories)
            daily_log.total_meals = max(0, daily_log.total_meals)
            daily_log.breakfast_calories = max(0, daily_log.breakfast_calories)
            daily_log.lunch_calories = max(0, daily_log.lunch_calories)
            daily_log.dinner_calories = max(0, daily_log.dinner_calories)
            daily_log.snack_calories = max(0, daily_log.snack_calories)

        db.session.delete(prediction)
        db.session.commit()

        logger.info(f"Prediction {prediction_id} deleted by user {user_id}")
        return success_response(
            {'deleted_id': prediction_id},
            "Prediction deleted successfully"
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting prediction {prediction_id}: {str(e)}")
        return error_response("Error deleting prediction", 500)


# ============================================================================
# Daily Log Endpoints
# ============================================================================

@history_bp.route('/daily-log', methods=['GET'])
@jwt_required()
def get_daily_log():
    """
    GET /api/daily-log - Get today's or specific date's daily log summary
    """
    try:
        params = date_range_schema.load(request.args)
    except ValidationError as err:
        return error_response(err.messages, 400)

    user_id = get_jwt_identity()
    target_date = params.get('date', date.today())

    daily_log = DailyLog.get_or_create(user_id, target_date)

    user = get_current_user()
    if user and user.profile and user.profile.daily_calorie_goal:
        daily_log.daily_goal = user.profile.daily_calorie_goal
        db.session.commit()

    # Calculate total protein/carbs/fat from predictions
    from sqlalchemy import func
    from datetime import datetime, timedelta

    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    # Only include saved meals (meal_type set); otherwise taslaklar da sayılıyor
    macros = db.session.query(
        func.sum(PredictionHistory.calories).label('total_cals'),
        func.sum(func.coalesce(PredictionHistory.protein, 0)).label('total_protein'),
        func.sum(func.coalesce(PredictionHistory.carbs, 0)).label('total_carbs'),
        func.sum(func.coalesce(PredictionHistory.fat, 0)).label('total_fat')
    ).filter(
        PredictionHistory.user_id == user_id,
        PredictionHistory.created_at >= start_of_day,
        PredictionHistory.created_at < end_of_day,
        PredictionHistory.meal_type.isnot(None)
    ).first()

    # Add macros to response
    log_dict = daily_log.to_dict()
    log_dict['protein'] = round(macros.total_protein or 0, 1)
    log_dict['carbs'] = round(macros.total_carbs or 0, 1)
    log_dict['fat'] = round(macros.total_fat or 0, 1)

    return success_response(
        log_dict,
        "Daily log retrieved successfully"
    )


@history_bp.route('/daily-log/week', methods=['GET'])
@jwt_required()
def get_weekly_log():
    """
    GET /api/daily-log/week - Get this week's daily log summary (last 7 days)
    """
    user_id = get_jwt_identity()

    end_date = date.today()
    start_date = end_date - timedelta(days=6)

    logs = DailyLog.query.filter(
        DailyLog.user_id == user_id,
        DailyLog.date >= start_date,
        DailyLog.date <= end_date
    ).order_by(DailyLog.date).all()

    existing_dates = {log.date for log in logs}
    all_logs = []

    current_date = start_date
    while current_date <= end_date:
        if current_date in existing_dates:
            log = next(l for l in logs if l.date == current_date)
            all_logs.append(log.to_dict())
        else:
            all_logs.append({
                'date': current_date.isoformat(),
                'total_calories': 0.0,
                'total_meals': 0,
                'breakfast_calories': 0.0,
                'lunch_calories': 0.0,
                'dinner_calories': 0.0,
                'snack_calories': 0.0,
                'daily_goal': None,
                'goal_achieved': False,
                'progress_percentage': 0
            })
        current_date += timedelta(days=1)

    total_calories = sum(log['total_calories'] for log in all_logs)
    total_meals = sum(log['total_meals'] for log in all_logs)
    average_calories = round(total_calories / 7, 1) if total_calories > 0 else 0

    return success_response({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'days': all_logs,
        'summary': {
            'total_calories': round(total_calories, 1),
            'average_daily_calories': average_calories,
            'total_meals': total_meals
        }
    }, "Weekly log retrieved successfully")


@history_bp.route('/daily-log/month', methods=['GET'])
@jwt_required()
def get_monthly_log():
    """
    GET /api/daily-log/month - Get this month's daily log summary (last 30 days)
    """
    user_id = get_jwt_identity()

    end_date = date.today()
    start_date = end_date - timedelta(days=29)

    logs = DailyLog.query.filter(
        DailyLog.user_id == user_id,
        DailyLog.date >= start_date,
        DailyLog.date <= end_date
    ).order_by(DailyLog.date).all()

    logs_dict = {log.date: log.to_dict() for log in logs}
    all_logs = []

    current_date = start_date
    while current_date <= end_date:
        if current_date in logs_dict:
            all_logs.append(logs_dict[current_date])
        else:
            all_logs.append({
                'date': current_date.isoformat(),
                'total_calories': 0.0,
                'total_meals': 0,
                'breakfast_calories': 0.0,
                'lunch_calories': 0.0,
                'dinner_calories': 0.0,
                'snack_calories': 0.0,
                'daily_goal': None,
                'goal_achieved': False,
                'progress_percentage': 0
            })
        current_date += timedelta(days=1)

    total_calories = sum(log['total_calories'] for log in all_logs)
    total_meals = sum(log['total_meals'] for log in all_logs)
    days_logged = sum(1 for log in all_logs if log['total_meals'] > 0)
    average_calories = round(total_calories / 30, 1) if total_calories > 0 else 0

    return success_response({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'days': all_logs,
        'summary': {
            'total_calories': round(total_calories, 1),
            'average_daily_calories': average_calories,
            'total_meals': total_meals,
            'days_logged': days_logged
        }
    }, "Monthly log retrieved successfully")


# ============================================================================
# Statistics and Analytics Endpoints
# ============================================================================

@history_bp.route('/stats/favorites', methods=['GET'])
@jwt_required()
def get_favorite_foods():
    """
    GET /api/stats/favorites - List favorite foods
    """
    user_id = get_jwt_identity()

    favorites = PredictionHistory.query.filter_by(
        user_id=user_id,
        is_favorite=True
    ).order_by(desc(PredictionHistory.created_at)).all()

    return success_response({
        'favorites': [f.to_dict() for f in favorites],
        'count': len(favorites)
    }, "Favorite foods retrieved successfully")


@history_bp.route('/stats/top-foods', methods=['GET'])
@jwt_required()
def get_top_foods():
    """
    GET /api/stats/top-foods - List most consumed foods
    """
    user_id = get_jwt_identity()

    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 10, type=int)

    start_date = datetime.utcnow() - timedelta(days=days)

    top_foods = db.session.query(
        PredictionHistory.food_class,
        func.count(PredictionHistory.id).label('count'),
        func.sum(PredictionHistory.calories).label('total_calories'),
        func.avg(PredictionHistory.calories).label('average_calories')
    ).filter(
        PredictionHistory.user_id == user_id,
        PredictionHistory.created_at >= start_date
    ).group_by(
        PredictionHistory.food_class
    ).order_by(
        desc('count')
    ).limit(limit).all()

    foods = [
        {
            'food_class': food.food_class,
            'count': food.count,
            'total_calories': round(food.total_calories, 1),
            'average_calories': round(food.average_calories, 1)
        }
        for food in top_foods
    ]

    return success_response({
        'foods': foods,
        'period_days': days
    }, "Top foods retrieved successfully")


@history_bp.route('/stats/meal-distribution', methods=['GET'])
@jwt_required()
def get_meal_distribution():
    """
    GET /api/stats/meal-distribution - Get meal distribution
    """
    user_id = get_jwt_identity()

    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    meal_stats = db.session.query(
        PredictionHistory.meal_type,
        func.count(PredictionHistory.id).label('count'),
        func.sum(PredictionHistory.calories).label('total_calories')
    ).filter(
        PredictionHistory.user_id == user_id,
        PredictionHistory.created_at >= start_date,
        PredictionHistory.meal_type.isnot(None)
    ).group_by(
        PredictionHistory.meal_type
    ).all()

    total_meals = sum(stat.count for stat in meal_stats)
    total_calories = sum(stat.total_calories for stat in meal_stats)

    distribution = {}
    for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
        stat = next((s for s in meal_stats if s.meal_type == meal_type), None)
        if stat:
            count = stat.count
            calories = stat.total_calories
            percentage = round((count / total_meals * 100), 1) if total_meals > 0 else 0
        else:
            count = 0
            calories = 0.0
            percentage = 0.0

        distribution[meal_type] = {
            'count': count,
            'total_calories': round(calories, 1),
            'percentage': percentage
        }

    return success_response({
        'distribution': distribution,
        'total_meals': total_meals,
        'total_calories': round(total_calories, 1),
        'period_days': days
    }, "Meal distribution retrieved successfully")
