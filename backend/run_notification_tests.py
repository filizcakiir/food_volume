#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test runner for notification tests
Runs tests without pytest to avoid import issues
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Now we can import
from flask import Flask
from flask_jwt_extended import create_access_token
import json
from datetime import date, timedelta

from app import create_app
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
    StreakService
)


def run_tests():
    """Run all notification API tests"""

    print("=" * 70)
    print("GastronomGoz - Notification API Tests")
    print("=" * 70)
    print()

    # Create test app
    app = create_app('development')  # Use development for testing
    app.config['TESTING'] = True

    passed = 0
    failed = 0

    with app.app_context():
        # Drop and recreate tables
        db.drop_all()
        db.create_all()

        # Initialize achievements
        AchievementService.initialize_achievements()

        # Create test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # Create access token
        token = create_access_token(identity=user_id)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        client = app.test_client()

        # ============================================================================
        # TEST 1: List notifications (empty)
        # ============================================================================
        print("TEST 1: List notifications when empty")
        try:
            response = client.get('/api/notifications', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data['success'] is True
            assert len(data['data']['notifications']) == 0
            assert data['data']['total_count'] == 0

            print("✅ PASSED: Empty notification list")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 2: Create and list notifications
        # ============================================================================
        print("TEST 2: Create and list notifications")
        try:
            # Create 3 notifications
            for i in range(3):
                NotificationService.create_notification(
                    user_id=user_id,
                    notification_type='achievement',
                    title=f'Achievement {i}',
                    message=f'Test message {i}'
                )

            response = client.get('/api/notifications', headers=headers)
            data = json.loads(response.data)

            assert len(data['data']['notifications']) == 3
            assert data['data']['total_count'] == 3
            assert data['data']['unread_count'] == 3

            print("✅ PASSED: Created and listed 3 notifications")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 3: Mark notification as read
        # ============================================================================
        print("TEST 3: Mark notification as read")
        try:
            notif_id = data['data']['notifications'][0]['id']

            response = client.post(f'/api/notifications/{notif_id}/read', headers=headers)
            assert response.status_code == 200

            # Check it's read
            notif = Notification.query.get(notif_id)
            assert notif.is_read is True

            print("✅ PASSED: Marked notification as read")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 4: Mark all as read
        # ============================================================================
        print("TEST 4: Mark all notifications as read")
        try:
            response = client.post('/api/notifications/read-all', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert data['data']['count'] >= 2  # At least 2 were unread

            # Verify
            response = client.get('/api/notifications/unread', headers=headers)
            data = json.loads(response.data)
            assert data['data']['unread_count'] == 0

            print("✅ PASSED: Marked all notifications as read")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 5: List all achievements
        # ============================================================================
        print("TEST 5: List all available achievements")
        try:
            response = client.get('/api/achievements', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert len(data['data']['achievements']) >= 8  # Default achievements

            print(f"✅ PASSED: Listed {len(data['data']['achievements'])} achievements")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 6: User achievements (empty)
        # ============================================================================
        print("TEST 6: Get user achievements (should be empty)")
        try:
            response = client.get('/api/achievements/user', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert data['data']['total_earned'] == 0
            assert data['data']['total_points'] == 0

            print("✅ PASSED: User has no achievements initially")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 7: Auto-award first prediction achievement
        # ============================================================================
        print("TEST 7: Auto-award first prediction achievement")
        try:
            # Create prediction
            prediction = PredictionHistory(
                user_id=user_id,
                food_class='pizza',
                calories=300.0,
                estimated_grams=100.0,
                confidence=0.95,
                meal_type='lunch',
                image_url='/static/uploads/test.jpg'
            )
            db.session.add(prediction)
            db.session.commit()

            # Check achievements
            AchievementService.check_and_award_achievements(user_id, context='prediction')

            # Verify
            response = client.get('/api/achievements/user', headers=headers)
            data = json.loads(response.data)

            assert data['data']['total_earned'] >= 1
            codes = [a['achievement']['code'] for a in data['data']['achievements']]
            assert 'first_prediction' in codes

            print("✅ PASSED: First prediction achievement awarded")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 8: Get streak (initial)
        # ============================================================================
        print("TEST 8: Get initial streak")
        try:
            response = client.get('/api/streak', headers=headers)
            data = json.loads(response.data)

            assert response.status_code == 200
            assert data['data']['current_streak'] == 0
            assert data['data']['longest_streak'] == 0

            print("✅ PASSED: Initial streak is 0")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 9: Update streak
        # ============================================================================
        print("TEST 9: Update streak for 3 consecutive days")
        try:
            today = date.today()

            # Simulate 3 consecutive days
            for i in range(3):
                activity_date = today - timedelta(days=2-i)
                StreakService.update_user_streak(user_id, activity_date)

            # Check streak
            response = client.get('/api/streak', headers=headers)
            data = json.loads(response.data)

            assert data['data']['current_streak'] == 3
            assert data['data']['longest_streak'] == 3
            assert data['data']['total_active_days'] == 3

            print("✅ PASSED: 3-day streak created")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 10: Streak achievement
        # ============================================================================
        print("TEST 10: Check 3-day streak achievement")
        try:
            # Check achievements
            AchievementService.check_and_award_achievements(user_id, context='streak')

            response = client.get('/api/achievements/user', headers=headers)
            data = json.loads(response.data)

            codes = [a['achievement']['code'] for a in data['data']['achievements']]
            assert '3_day_streak' in codes

            print("✅ PASSED: 3-day streak achievement awarded")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 11: Notification preferences
        # ============================================================================
        print("TEST 11: Get and update notification preferences")
        try:
            # Get default preferences
            response = client.get('/api/preferences/notifications', headers=headers)
            data = json.loads(response.data)

            assert data['data']['enable_email'] is True
            assert data['data']['enable_push'] is True

            # Update preferences
            update_data = {
                'enable_email': False,
                'notify_achievements': False
            }

            response = client.put(
                '/api/preferences/notifications',
                headers=headers,
                data=json.dumps(update_data)
            )
            data = json.loads(response.data)

            assert data['data']['enable_email'] is False
            assert data['data']['notify_achievements'] is False

            print("✅ PASSED: Notification preferences updated")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

        # ============================================================================
        # TEST 12: Streak broken
        # ============================================================================
        print("TEST 12: Test streak broken scenario")
        try:
            today = date.today()

            # Skip 5 days and log today (should break streak)
            result = StreakService.update_user_streak(user_id, today)

            assert result['streak_broken'] is True
            assert result['previous_streak'] == 3
            assert result['new_streak'] == 1

            # Check streak
            response = client.get('/api/streak', headers=headers)
            data = json.loads(response.data)

            assert data['data']['current_streak'] == 1
            assert data['data']['longest_streak'] == 3  # Longest remains

            print("✅ PASSED: Streak broken correctly")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        print()

    # ============================================================================
    # Summary
    # ============================================================================
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    print(f"Success Rate: {100 * passed / (passed + failed):.1f}%")
    print("=" * 70)

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
