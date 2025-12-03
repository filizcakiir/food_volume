# -*- coding: utf-8 -*-
"""
GastronomGoz - Notification API Tests

Bu dosya notification, achievement ve streak API'lerini test eder.

Test Coverage:
1. Notification API Tests
   - Bildirim listeleme
   - Okunmamış bildirim sayısı
   - Bildirimi okundu işaretleme
   - Tüm bildirimleri okundu işaretleme

2. Achievement API Tests
   - Tüm başarıları listeleme
   - Kullanıcının başarılarını getirme
   - Başarı başlatma
   - Otomatik başarı kazanma

3. Streak API Tests
   - Streak bilgisi getirme
   - Streak güncelleme
   - Milestone bildirimleri

4. Notification Preferences Tests
   - Tercihleri getirme
   - Tercihleri güncelleme
   - Tercih bazlı bildirim filtreleme
"""

import pytest
import json
from datetime import datetime, date, timedelta
from flask import Flask
from flask_jwt_extended import create_access_token

from app import create_app
from models import db
from models.user import User
from models.history import PredictionHistory, DailyLog
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


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create and configure test app"""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'

    with app.app_context():
        db.create_all()
        # Initialize achievements
        AchievementService.initialize_achievements()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    """Create authenticated headers for test user"""
    with app.app_context():
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        # Create access token
        token = create_access_token(identity=user_id)

        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }, user_id


# ============================================================================
# 1. Notification API Tests
# ============================================================================

def test_list_notifications_empty(client, auth_headers):
    """Test: Bildirim yokken boş liste dönmeli"""
    headers, user_id = auth_headers

    response = client.get('/api/notifications', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['data']['notifications']) == 0
    assert data['data']['total_count'] == 0
    assert data['data']['unread_count'] == 0


def test_create_and_list_notifications(client, auth_headers, app):
    """Test: Bildirim oluşturma ve listeleme"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create 3 notifications
        for i in range(3):
            NotificationService.create_notification(
                user_id=user_id,
                notification_type='achievement',
                title=f'Achievement {i}',
                message=f'You earned achievement {i}',
                data={'achievement_id': i}
            )

    response = client.get('/api/notifications', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['data']['notifications']) == 3
    assert data['data']['total_count'] == 3
    assert data['data']['unread_count'] == 3


def test_list_notifications_unread_only(client, auth_headers, app):
    """Test: Sadece okunmamış bildirimleri getirme"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create 5 notifications
        for i in range(5):
            notif = NotificationService.create_notification(
                user_id=user_id,
                notification_type='reminder',
                title=f'Reminder {i}',
                message=f'This is reminder {i}'
            )

            # Mark first 2 as read
            if i < 2:
                notif.mark_as_read()

    # Get all notifications
    response = client.get('/api/notifications', headers=headers)
    data = json.loads(response.data)
    assert len(data['data']['notifications']) == 5
    assert data['data']['unread_count'] == 3

    # Get unread only
    response = client.get('/api/notifications?unread_only=true', headers=headers)
    data = json.loads(response.data)
    assert len(data['data']['notifications']) == 3
    assert all(not n['is_read'] for n in data['data']['notifications'])


def test_get_unread_count(client, auth_headers, app):
    """Test: Okunmamış bildirim sayısını getirme"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create 7 notifications
        for i in range(7):
            notif = NotificationService.create_notification(
                user_id=user_id,
                notification_type='streak',
                title='Streak',
                message='Streak message'
            )

            # Mark 3 as read
            if i < 3:
                notif.mark_as_read()

    response = client.get('/api/notifications/unread', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['data']['unread_count'] == 4


def test_mark_notification_read(client, auth_headers, app):
    """Test: Tek bildirimi okundu olarak işaretleme"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create notification
        notif = NotificationService.create_notification(
            user_id=user_id,
            notification_type='achievement',
            title='Test',
            message='Test message'
        )
        notif_id = notif.id

    # Mark as read
    response = client.post(f'/api/notifications/{notif_id}/read', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Verify it's read
    with app.app_context():
        notif = Notification.query.get(notif_id)
        assert notif.is_read is True
        assert notif.read_at is not None


def test_mark_all_notifications_read(client, auth_headers, app):
    """Test: Tüm bildirimleri okundu olarak işaretleme"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create 5 notifications (all unread)
        for i in range(5):
            NotificationService.create_notification(
                user_id=user_id,
                notification_type='reminder',
                title=f'Reminder {i}',
                message=f'Message {i}'
            )

    # Verify all unread
    response = client.get('/api/notifications/unread', headers=headers)
    data = json.loads(response.data)
    assert data['data']['unread_count'] == 5

    # Mark all as read
    response = client.post('/api/notifications/read-all', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['data']['count'] == 5

    # Verify all are read now
    response = client.get('/api/notifications/unread', headers=headers)
    data = json.loads(response.data)
    assert data['data']['unread_count'] == 0


def test_notification_pagination(client, auth_headers, app):
    """Test: Bildirim sayfalama"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create 50 notifications
        for i in range(50):
            NotificationService.create_notification(
                user_id=user_id,
                notification_type='reminder',
                title=f'Notification {i}',
                message=f'Message {i}'
            )

    # Get first page (default 50)
    response = client.get('/api/notifications?limit=20&offset=0', headers=headers)
    data = json.loads(response.data)
    assert len(data['data']['notifications']) == 20

    # Get second page
    response = client.get('/api/notifications?limit=20&offset=20', headers=headers)
    data = json.loads(response.data)
    assert len(data['data']['notifications']) == 20

    # Get third page
    response = client.get('/api/notifications?limit=20&offset=40', headers=headers)
    data = json.loads(response.data)
    assert len(data['data']['notifications']) == 10


# ============================================================================
# 2. Achievement API Tests
# ============================================================================

def test_list_all_achievements(client, auth_headers, app):
    """Test: Tüm mevcut başarıları listeleme"""
    headers, user_id = auth_headers

    response = client.get('/api/achievements', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Should have default achievements (8 tanesi AchievementService'de tanımlı)
    achievements = data['data']['achievements']
    assert len(achievements) >= 8

    # Check structure
    ach = achievements[0]
    assert 'id' in ach
    assert 'code' in ach
    assert 'name' in ach
    assert 'description' in ach
    assert 'points' in ach


def test_get_user_achievements_empty(client, auth_headers):
    """Test: Kullanıcının başarısı yokken boş liste dönmeli"""
    headers, user_id = auth_headers

    response = client.get('/api/achievements/user', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['data']['achievements']) == 0
    assert data['data']['total_earned'] == 0
    assert data['data']['total_points'] == 0


def test_award_achievement_and_list(client, auth_headers, app):
    """Test: Başarı verme ve listeleme"""
    headers, user_id = auth_headers

    with app.app_context():
        # Get first_prediction achievement
        achievement = Achievement.query.filter_by(code='first_prediction').first()
        assert achievement is not None

        # Award it
        AchievementService.award_achievement(user_id, achievement.id, progress_value=1)

    # Get user achievements
    response = client.get('/api/achievements/user', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['data']['achievements']) == 1
    assert data['data']['total_earned'] == 1
    assert data['data']['total_points'] == 10  # first_prediction is 10 points


def test_auto_award_first_prediction(client, auth_headers, app):
    """Test: İlk tahmin yapınca otomatik başarı kazanma"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create first prediction
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

    # Should have first_prediction achievement
    response = client.get('/api/achievements/user', headers=headers)
    data = json.loads(response.data)

    assert len(data['data']['achievements']) >= 1
    codes = [a['achievement']['code'] for a in data['data']['achievements']]
    assert 'first_prediction' in codes


def test_auto_award_10_predictions(client, auth_headers, app):
    """Test: 10 tahmin yapınca başarı kazanma"""
    headers, user_id = auth_headers

    with app.app_context():
        # Create 10 predictions
        for i in range(10):
            prediction = PredictionHistory(
                user_id=user_id,
                food_class='pizza',
                calories=300.0,
                estimated_grams=100.0,
                confidence=0.95,
                meal_type='lunch',
                image_url=f'/static/uploads/test{i}.jpg'
            )
            db.session.add(prediction)
        db.session.commit()

        # Check achievements
        AchievementService.check_and_award_achievements(user_id, context='prediction')

    # Should have both first_prediction and 10_predictions
    response = client.get('/api/achievements/user', headers=headers)
    data = json.loads(response.data)

    codes = [a['achievement']['code'] for a in data['data']['achievements']]
    assert 'first_prediction' in codes
    assert '10_predictions' in codes


def test_no_duplicate_achievements(client, auth_headers, app):
    """Test: Aynı başarı iki kez verilmemeli"""
    headers, user_id = auth_headers

    with app.app_context():
        achievement = Achievement.query.filter_by(code='first_prediction').first()

        # Award twice
        AchievementService.award_achievement(user_id, achievement.id)
        AchievementService.award_achievement(user_id, achievement.id)

    # Should only have 1
    response = client.get('/api/achievements/user', headers=headers)
    data = json.loads(response.data)
    assert data['data']['total_earned'] == 1


# ============================================================================
# 3. Streak API Tests
# ============================================================================

def test_get_streak_initial(client, auth_headers):
    """Test: İlk streak bilgisi getirme"""
    headers, user_id = auth_headers

    response = client.get('/api/streak', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    streak = data['data']
    assert streak['current_streak'] == 0
    assert streak['longest_streak'] == 0
    assert streak['total_active_days'] == 0


def test_streak_first_day(client, auth_headers, app):
    """Test: İlk gün streak güncelleme"""
    headers, user_id = auth_headers

    with app.app_context():
        # Update streak for today
        result = StreakService.update_user_streak(user_id)

        assert result['new_streak'] == 1
        assert result['milestone_reached'] is None
        assert result['streak_broken'] is False

    # Get streak
    response = client.get('/api/streak', headers=headers)
    data = json.loads(response.data)

    assert data['data']['current_streak'] == 1
    assert data['data']['longest_streak'] == 1
    assert data['data']['total_active_days'] == 1


def test_streak_consecutive_days(client, auth_headers, app):
    """Test: Ardışık günler streak"""
    headers, user_id = auth_headers

    with app.app_context():
        today = date.today()

        # Simulate 7 consecutive days
        for i in range(7):
            activity_date = today - timedelta(days=6-i)
            StreakService.update_user_streak(user_id, activity_date)

    # Get streak
    response = client.get('/api/streak', headers=headers)
    data = json.loads(response.data)

    assert data['data']['current_streak'] == 7
    assert data['data']['longest_streak'] == 7
    assert data['data']['total_active_days'] == 7


def test_streak_milestone_3_days(client, auth_headers, app):
    """Test: 3 günlük milestone"""
    headers, user_id = auth_headers

    with app.app_context():
        today = date.today()

        # Day 1, 2
        for i in range(2):
            activity_date = today - timedelta(days=2-i)
            StreakService.update_user_streak(user_id, activity_date)

        # Day 3 - should trigger milestone
        result = StreakService.update_user_streak(user_id, today)

        assert result['new_streak'] == 3
        assert result['milestone_reached'] == 3


def test_streak_broken(client, auth_headers, app):
    """Test: Streak kırılması"""
    headers, user_id = auth_headers

    with app.app_context():
        today = date.today()

        # Build 5 day streak
        for i in range(5):
            activity_date = today - timedelta(days=10-i)  # 10 days ago to 6 days ago
            StreakService.update_user_streak(user_id, activity_date)

        # Skip days and restart today (should break streak)
        result = StreakService.update_user_streak(user_id, today)

        assert result['streak_broken'] is True
        assert result['previous_streak'] == 5
        assert result['new_streak'] == 1

    # Get streak
    response = client.get('/api/streak', headers=headers)
    data = json.loads(response.data)

    assert data['data']['current_streak'] == 1
    assert data['data']['longest_streak'] == 5  # Longest remains
    assert data['data']['total_active_days'] == 6  # 5 + 1


def test_streak_same_day_no_change(client, auth_headers, app):
    """Test: Aynı gün içinde birden fazla aktivite - streak değişmemeli"""
    headers, user_id = auth_headers

    with app.app_context():
        today = date.today()

        # First activity today
        result1 = StreakService.update_user_streak(user_id, today)
        assert result1['new_streak'] == 1

        # Second activity same day
        result2 = StreakService.update_user_streak(user_id, today)
        assert result2['new_streak'] == 1  # No change

    response = client.get('/api/streak', headers=headers)
    data = json.loads(response.data)
    assert data['data']['current_streak'] == 1
    assert data['data']['total_active_days'] == 1  # Only 1 day


def test_streak_achievement_integration(client, auth_headers, app):
    """Test: Streak milestone ile başarı kazanma entegrasyonu"""
    headers, user_id = auth_headers

    with app.app_context():
        today = date.today()

        # Build 7 day streak
        for i in range(7):
            activity_date = today - timedelta(days=6-i)
            StreakService.update_user_streak(user_id, activity_date)

        # Check achievements
        AchievementService.check_and_award_achievements(user_id, context='streak')

    # Should have 3_day_streak and 7_day_streak
    response = client.get('/api/achievements/user', headers=headers)
    data = json.loads(response.data)

    codes = [a['achievement']['code'] for a in data['data']['achievements']]
    assert '3_day_streak' in codes
    assert '7_day_streak' in codes


# ============================================================================
# 4. Notification Preferences Tests
# ============================================================================

def test_get_default_preferences(client, auth_headers):
    """Test: Varsayılan tercihleri getirme"""
    headers, user_id = auth_headers

    response = client.get('/api/preferences/notifications', headers=headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    prefs = data['data']
    # All should be true by default
    assert prefs['enable_email'] is True
    assert prefs['enable_push'] is True
    assert prefs['enable_in_app'] is True
    assert prefs['notify_achievements'] is True
    assert prefs['notify_daily_reminder'] is True


def test_update_preferences(client, auth_headers):
    """Test: Tercihleri güncelleme"""
    headers, user_id = auth_headers

    # Update preferences
    update_data = {
        'enable_email': False,
        'enable_push': True,
        'notify_achievements': True,
        'notify_daily_reminder': False
    }

    response = client.put(
        '/api/preferences/notifications',
        headers=headers,
        data=json.dumps(update_data)
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    prefs = data['data']
    assert prefs['enable_email'] is False
    assert prefs['enable_push'] is True
    assert prefs['notify_achievements'] is True
    assert prefs['notify_daily_reminder'] is False


def test_preferences_affect_notifications(client, auth_headers, app):
    """Test: Tercihler bildirimleri etkilemeli"""
    headers, user_id = auth_headers

    with app.app_context():
        # Update preferences - disable achievements
        prefs = NotificationPreference.get_or_create(user_id)
        prefs.notify_achievements = False
        prefs.enable_in_app = False
        db.session.commit()

        # Try to create achievement notification
        notif = NotificationService.create_notification(
            user_id=user_id,
            notification_type='achievement',
            title='Test Achievement',
            message='Test message',
            send_email=True,
            send_push=True
        )

        # Should not be sent in-app
        assert notif.sent_in_app is False


def test_update_reminder_time(client, auth_headers):
    """Test: Hatırlatma saatini güncelleme"""
    headers, user_id = auth_headers

    update_data = {
        'daily_reminder_time': '20:00:00',
        'weekly_summary_day': 0  # Monday
    }

    response = client.put(
        '/api/preferences/notifications',
        headers=headers,
        data=json.dumps(update_data)
    )

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['data']['daily_reminder_time'] == '20:00:00'
    assert data['data']['weekly_summary_day'] == 0


# ============================================================================
# 5. Integration Tests
# ============================================================================

def test_full_user_journey(client, auth_headers, app):
    """Test: Tam kullanıcı yolculuğu - tahmin -> streak -> başarı -> bildirim"""
    headers, user_id = auth_headers

    with app.app_context():
        # Step 1: User makes first prediction
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

        # Step 2: Update streak
        StreakService.update_user_streak(user_id)

        # Step 3: Check and award achievements
        AchievementService.check_and_award_achievements(user_id, context='prediction')
        AchievementService.check_and_award_achievements(user_id, context='streak')

    # Verify streak
    response = client.get('/api/streak', headers=headers)
    data = json.loads(response.data)
    assert data['data']['current_streak'] == 1

    # Verify achievements
    response = client.get('/api/achievements/user', headers=headers)
    data = json.loads(response.data)
    assert data['data']['total_earned'] >= 1

    # Verify notifications (achievement notification should be created)
    response = client.get('/api/notifications', headers=headers)
    data = json.loads(response.data)
    assert data['data']['total_count'] >= 1

    # Should have achievement notification
    notif_types = [n['type'] for n in data['data']['notifications']]
    assert 'achievement' in notif_types


def test_7_day_streak_milestone_notification(client, auth_headers, app):
    """Test: 7 günlük streak milestone bildirimi"""
    headers, user_id = auth_headers

    with app.app_context():
        today = date.today()

        # Build 7 day streak
        for i in range(7):
            activity_date = today - timedelta(days=6-i)
            StreakService.update_user_streak(user_id, activity_date)

    # Should have streak notification
    response = client.get('/api/notifications', headers=headers)
    data = json.loads(response.data)

    notifs = data['data']['notifications']
    streak_notifs = [n for n in notifs if n['type'] == 'streak']

    # Should have 3-day and 7-day milestone notifications
    assert len(streak_notifs) >= 2


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
