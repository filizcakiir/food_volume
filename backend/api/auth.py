# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from models import db
from models.user import User, UserProfile
from schemas.auth_schema import RegisterSchema, LoginSchema

auth_bp = Blueprint('auth', __name__)
register_schema = RegisterSchema()
login_schema = LoginSchema()

@auth_bp.route('/register', methods=['POST'])
def register():
    current_app.logger.info(f'Register request received: {request.json}')
    try:
        data = register_schema.load(request.json)
    except ValidationError as err:
        current_app.logger.error(f'Validation error: {err.messages}')
        return jsonify({'success': False, 'error': 'Validation error', 'details': err.messages}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    try:
        user = User(email=data['email'], name=data['name'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        current_app.logger.info(f'New user registered: {user.email}')
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify({'success': True, 'message': 'Registration successful', 'data': {'user': user.to_dict(), 'access_token': access_token, 'refresh_token': refresh_token}}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        return jsonify({'success': False, 'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'success': False, 'error': 'Validation error', 'details': err.messages}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
    if not user.is_active:
        return jsonify({'success': False, 'error': 'Account is disabled'}), 403
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    current_app.logger.info(f'User logged in: {user.email}')
    return jsonify({'success': True, 'message': 'Login successful', 'data': {'user': user.to_dict(), 'access_token': access_token, 'refresh_token': refresh_token}}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=str(current_user_id))
        return jsonify({'success': True, 'data': {'access_token': new_access_token}}), 200
    except Exception as e:
        current_app.logger.error(f'Token refresh error: {str(e)}')
        return jsonify({'success': False, 'error': 'Token refresh failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        return jsonify({'success': True, 'data': {'user': user.to_dict()}}), 200
    except Exception as e:
        current_app.logger.error(f'Get user error: {str(e)}')
        return jsonify({'success': False, 'error': 'Failed to get user'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = int(get_jwt_identity())
    current_app.logger.info(f'User logged out: user_id={current_user_id}')
    return jsonify({'success': True, 'message': 'Logout successful'}), 200
