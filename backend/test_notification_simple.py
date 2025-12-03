#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple notification API test without full app dependencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_cors import CORS
import json
from datetime import date, timedelta

from models import db
from models.user import User
from models.history import PredictionHistory
from models.notification import (
    Notification,
    Achievement,
    UserAchievement,
    DailyStreak,
    NotificationPreference
)
from services.notification_service import (
    NotificationService,
    AchievementService,
    StreakService,
    mail
)
from api.notification import notification_bp


def create_test_app():
    """Create minimal test app"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database_dev.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    # Mail config (mock)
    app.config['MAIL_SERVER'] = 'localhost'
    app.config['MAIL_PORT'] = 25
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USERNAME'] = None
    app.config['MAIL_PASSWORD'] = None

    db.init_app(app)
    jwt = JWTManager(app)
    mail.init_app(app)
    CORS(app)

    # Register only notification blueprint
    app.register_blueprint(notification_bp, url_prefix='/api')

    return app


def run_tests():
    """Run notification API tests"""

    print("=" * 80)
    print("GastronomGoz - Notification API Tests (Simplified)")
    print("=" * 80)
    print()

    app = create_test_app()
    passed = 0
    failed = 0

    with app.app_context():
        # Ensure all models are imported before db.create_all()
        from models.history import PredictionHistory, DailyLog  # Import history models too

        # Create all tables if they don't exist
        db.create_all()

        # Create test user
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            user = User(name='Test User', email='test@example.com')
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()

        user_id = user.id

        # Initialize achievements if not exists
        if Achievement.query.count() == 0:
            AchievementService.initialize_achievements()

        # Create token (identity should be string for JWT)
        token = create_access_token(identity=str(user_id))
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        client = app.test_client()

        # ========================================================================
        # TEST 1: List notifications
        # ========================================================================
        print("TEST 1: List notifications")
        try:
            response = client.get('/api/notifications', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200, f"Status: {response.status_code}, Data: {data}"
            assert data['success'] is True, f"Response not successful: {data}"
            assert 'notifications' in data['data'], f"No 'notifications' in data: {data}"
            assert 'total_count' in data['data']
            assert 'unread_count' in data['data']

            print(f"✅ PASSED: Found {data['data']['total_count']} notifications")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()

        # ========================================================================
        # TEST 2: Get unread count
        # ========================================================================
        print("TEST 2: Get unread count")
        try:
            response = client.get('/api/notifications/unread', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert 'unread_count' in data['data']

            print(f"✅ PASSED: {data['data']['unread_count']} unread notifications")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 3: Create notification
        # ========================================================================
        print("TEST 3: Create notification")
        try:
            notif = NotificationService.create_notification(
                user_id=user_id,
                notification_type='achievement',
                title='Test Notification',
                message='This is a test notification',
                send_email=False,
                send_push=False
            )

            assert notif.id is not None
            assert notif.user_id == user_id
            assert notif.is_read is False

            print(f"✅ PASSED: Created notification ID {notif.id}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 4: Mark notification as read
        # ========================================================================
        print("TEST 4: Mark notification as read")
        try:
            # Get first unread notification
            unread = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).first()

            if unread:
                response = client.post(
                    f'/api/notifications/{unread.id}/read',
                    headers=headers
                )
                data = json.loads(response.data)

                assert response.status_code == 200
                assert data['success'] is True

                # Verify
                unread = Notification.query.get(unread.id)
                assert unread.is_read is True

                print("✅ PASSED: Notification marked as read")
                passed += 1
            else:
                print("⚠️  SKIPPED: No unread notifications")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 5: List all achievements
        # ========================================================================
        print("TEST 5: List all achievements")
        try:
            response = client.get('/api/achievements', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert len(data['data']['achievements']) >= 8

            print(f"✅ PASSED: {len(data['data']['achievements'])} achievements available")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 6: Get user achievements
        # ========================================================================
        print("TEST 6: Get user achievements")
        try:
            response = client.get('/api/achievements/user', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert 'achievements' in data['data']
            assert 'total_earned' in data['data']
            assert 'total_points' in data['data']

            print(f"✅ PASSED: User has {data['data']['total_earned']} achievements")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 7: Get streak
        # ========================================================================
        print("TEST 7: Get user streak")
        try:
            response = client.get('/api/streak', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert 'current_streak' in data['data']
            assert 'longest_streak' in data['data']
            assert 'total_active_days' in data['data']

            print(f"✅ PASSED: Current streak: {data['data']['current_streak']} days")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 8: Update streak
        # ========================================================================
        print("TEST 8: Update streak")
        try:
            today = date.today()
            result = StreakService.update_user_streak(user_id, today)

            assert 'new_streak' in result
            assert 'streak_broken' in result

            print(f"✅ PASSED: Streak updated to {result['new_streak']} days")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 9: Get notification preferences
        # ========================================================================
        print("TEST 9: Get notification preferences")
        try:
            response = client.get('/api/preferences/notifications', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert 'enable_email' in data['data']
            assert 'enable_push' in data['data']
            assert 'notify_achievements' in data['data']

            print("✅ PASSED: Preferences retrieved")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 10: Update preferences
        # ========================================================================
        print("TEST 10: Update notification preferences")
        try:
            update_data = {
                'enable_email': False,
                'notify_achievements': True
            }

            response = client.put(
                '/api/preferences/notifications',
                headers=headers,
                data=json.dumps(update_data)
            )
            data = json.loads(response.data)

            assert response.status_code == 200
            assert data['data']['enable_email'] is False
            assert data['data']['notify_achievements'] is True

            print("✅ PASSED: Preferences updated")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 11: Award achievement
        # ========================================================================
        print("TEST 11: Award achievement")
        try:
            achievement = Achievement.query.filter_by(code='first_prediction').first()
            if achievement:
                user_ach = AchievementService.award_achievement(
                    user_id,
                    achievement.id,
                    progress_value=1
                )

                assert user_ach is not None
                assert user_ach.user_id == user_id
                assert user_ach.achievement_id == achievement.id

                print(f"✅ PASSED: Achievement '{achievement.name}' awarded")
                passed += 1
            else:
                print("⚠️  SKIPPED: Achievement not found")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ========================================================================
        # TEST 12: Check auto-award achievements
        # ========================================================================
        print("TEST 12: Auto-award achievements")
        try:
            # Create a prediction if not exists
            pred_count = PredictionHistory.query.filter_by(user_id=user_id).count()
            if pred_count == 0:
                prediction = PredictionHistory(
                    user_id=user_id,
                    food_class='pizza',
                    calories=300.0,
                    estimated_grams=100.0,
                    confidence=0.95,
                    meal_type='lunch',
                    image_path='/static/test.jpg'
                )
                db.session.add(prediction)
                db.session.commit()

            # Check and award
            earned = AchievementService.check_and_award_achievements(
                user_id,
                context='prediction'
            )

            print(f"✅ PASSED: Auto-check completed ({len(earned)} new achievements)")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

    # ========================================================================
    # Summary
    # ========================================================================
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    if passed + failed > 0:
        print(f"Success Rate: {100 * passed / (passed + failed):.1f}%")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
