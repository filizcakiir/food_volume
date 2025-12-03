# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from models import db
from models.user import User, UserProfile
from schemas.user_schema import UserProfileSchema, UpdateGoalSchema

user_bp = Blueprint('user', __name__)
profile_schema = UserProfileSchema()
goal_schema = UpdateGoalSchema()


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        if not user.profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404

        return jsonify({
            'success': True,
            'data': {
                'profile': user.profile.to_dict()
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f'Get profile error: {str(e)}')
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile"""
    try:
        # Validate input
        try:
            data = profile_schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': err.messages
            }), 400

        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        if not user.profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404

        # Update profile fields
        profile = user.profile
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        db.session.commit()
        current_app.logger.info(f'Profile updated: user_id={current_user_id}')

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'profile': profile.to_dict()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Update profile error: {str(e)}')
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500


@user_bp.route('/goals', methods=['PUT'])
@jwt_required()
def update_goals():
    """Update user's daily calorie goal"""
    try:
        # Validate input
        try:
            data = goal_schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'details': err.messages
            }), 400

        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        if not user.profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404

        # Update goals
        profile = user.profile
        profile.daily_calorie_goal = data['daily_calorie_goal']

        if 'goal_type' in data and data['goal_type']:
            profile.goal_type = data['goal_type']

        db.session.commit()
        current_app.logger.info(f'Goals updated: user_id={current_user_id}, goal={data["daily_calorie_goal"]}')

        return jsonify({
            'success': True,
            'message': 'Goals updated successfully',
            'data': {
                'daily_calorie_goal': profile.daily_calorie_goal,
                'goal_type': profile.goal_type,
                'bmi': profile.calculate_bmi(),
                'bmr': profile.calculate_bmr(),
                'tdee': profile.calculate_tdee()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Update goals error: {str(e)}')
        return jsonify({'success': False, 'error': 'Failed to update goals'}), 500
