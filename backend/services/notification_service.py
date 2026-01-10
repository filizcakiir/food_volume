# -*- coding: utf-8 -*-
"""
GastronomGoz - Notification Service

This service handles:
- Creating and sending notifications
- Email notifications
- Push notifications (future: Firebase/OneSignal)
- Achievement checking and awarding
- Streak updates
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, List
from flask import current_app, request
from flask_mail import Mail, Message

from models import db
from models.notification import (
    Notification,
    Achievement,
    UserAchievement,
    DailyStreak,
    NotificationPreference
)
from models.user import User

logger = logging.getLogger(__name__)

# Initialize Flask-Mail (will be configured in app.py)
mail = Mail()


def _get_user_lang(user_id: int) -> str:
    """Return user language; prefers profile language, then Accept-Language, else en."""
    # 1) User profile language (authoritative)
    user = User.query.get(user_id)
    if user and user.profile:
        pref = getattr(user.profile, 'language', None)
        if pref == 'tr':
            return 'tr'
        if pref == 'en':
            return 'en'

    # 2) Accept-Language header (fallback)
    try:
        accept_lang = (request.headers.get('Accept-Language', '') or '').lower()
        if accept_lang.startswith('tr'):
            return 'tr'
        if accept_lang.startswith('en'):
            return 'en'
    except Exception:
        pass

    # 3) Default
    return 'en'


def _localize_achievement(achievement: Achievement, lang: str) -> Dict[str, str]:
    """Return localized title/description for a given achievement."""
    translations = {
        'first_prediction': {
            'name_tr': 'İlk Adım',
            'desc_tr': 'İlk yemek tahminini yaptın'
        },
        '10_predictions': {
            'name_tr': 'Başlangıç',
            'desc_tr': '10 yemek tahmini yaptın'
        },
        '100_predictions': {
            'name_tr': 'Yüzyıl Kulübü',
            'desc_tr': '100 yemek tahmini yaptın'
        },
        '3_day_streak': {
            'name_tr': 'Alışkanlık Geliştirici',
            'desc_tr': '3 gün üst üste kayıt yaptın'
        },
        '7_day_streak': {
            'name_tr': 'Hafta Savaşçısı',
            'desc_tr': '7 gün üst üste kayıt yaptın'
        },
        '30_day_streak': {
            'name_tr': 'Aylık Usta',
            'desc_tr': '30 gün üst üste kayıt yaptın'
        },
        '7_days_goal': {
            'name_tr': 'Hedef Avcısı',
            'desc_tr': '7 gün üst üste günlük kalori hedefini tutturdun'
        },
        'healthy_week': {
            'name_tr': 'Sağlıklı Hafta',
            'desc_tr': 'Bir haftada 5 kez sebze/salata kaydettin'
        },
    }

    if lang == 'tr':
        tr = translations.get(achievement.code, {})
        name = tr.get('name_tr', achievement.name)
        desc = tr.get('desc_tr', achievement.description)
    else:
        name = achievement.name
        desc = achievement.description

    return {'name': name, 'description': desc}


class NotificationService:
    """
    Service for managing notifications

    Handles creation, delivery, and tracking of notifications
    """

    @staticmethod
    def create_notification(
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        send_email: bool = False,
        send_push: bool = False
    ) -> Notification:
        """
        Create a new notification

        Args:
            user_id: User ID
            notification_type: Type (achievement, reminder, etc.)
            title: Notification title
            message: Notification message
            data: Additional data (JSON)
            send_email: Send via email
            send_push: Send via push notification

        Returns:
            Notification: Created notification object
        """
        # Check user preferences
        prefs = NotificationPreference.get_or_create(user_id)

        # Determine which channels to use
        should_send_email = send_email and prefs.should_send(notification_type, 'email')
        should_send_push = send_push and prefs.should_send(notification_type, 'push')
        should_send_in_app = prefs.should_send(notification_type, 'in_app')

        # Create notification
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data,
            sent_in_app=should_send_in_app,
            sent_email=should_send_email,
            sent_push=should_send_push
        )

        db.session.add(notification)
        db.session.commit()

        # Send via channels
        if should_send_email:
            NotificationService._send_email(user_id, title, message)

        if should_send_push:
            NotificationService._send_push(user_id, title, message, data)

        logger.info(f"Notification created: user={user_id}, type={notification_type}")
        return notification

    @staticmethod
    def _send_email(user_id: int, title: str, message: str):
        """Send email notification"""
        try:
            user = User.query.get(user_id)
            if not user or not user.email:
                return

            msg = Message(
                subject=f"GastronomGoz - {title}",
                recipients=[user.email],
                body=message,
                html=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #4CAF50;">{title}</h2>
                            <p style="font-size: 16px; line-height: 1.6;">{message}</p>
                            <hr style="margin: 20px 0;">
                            <p style="color: #888; font-size: 12px;">
                                This is an automated message from GastronomGoz.
                                You can manage your notification preferences in the app.
                            </p>
                        </div>
                    </body>
                </html>
                """
            )

            mail.send(msg)
            logger.info(f"Email sent to user {user_id}: {title}")

        except Exception as e:
            logger.error(f"Error sending email to user {user_id}: {str(e)}")

    @staticmethod
    def _send_push(user_id: int, title: str, message: str, data: Optional[Dict] = None):
        """
        Send push notification

        Note: This is a placeholder. In production, integrate with:
        - Firebase Cloud Messaging (FCM) for mobile apps
        - OneSignal
        - Amazon SNS
        etc.
        """
        # TODO: Implement push notification with FCM/OneSignal
        logger.info(f"Push notification (placeholder): user={user_id}, title={title}")
        pass

    @staticmethod
    def get_user_notifications(
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get user's notifications

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications
            offset: Offset for pagination

        Returns:
            List of notifications
        """
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(
            Notification.created_at.desc()
        ).limit(limit).offset(offset).all()

        return notifications

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """
        Mark notification as read

        Args:
            notification_id: Notification ID
            user_id: User ID (for security)

        Returns:
            bool: Success
        """
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if notification:
            notification.mark_as_read()
            return True

        return False

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """
        Mark all notifications as read for user

        Args:
            user_id: User ID

        Returns:
            int: Number of notifications marked as read
        """
        count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })

        db.session.commit()
        return count


class AchievementService:
    """
    Service for managing achievements

    Handles checking and awarding achievements to users
    """

    @staticmethod
    def initialize_achievements():
        """
        Initialize default achievements in database

        Should be run once when setting up the app
        """
        default_achievements = [
            {
                'code': 'first_prediction',
                'name': 'First Step',
                'description': 'Made your first food prediction',
                'icon': 'star',
                'category': 'prediction',
                'requirement_type': 'count',
                'requirement_value': 1,
                'points': 10
            },
            {
                'code': '10_predictions',
                'name': 'Getting Started',
                'description': 'Made 10 food predictions',
                'icon': 'trophy',
                'category': 'prediction',
                'requirement_type': 'count',
                'requirement_value': 10,
                'points': 20
            },
            {
                'code': '100_predictions',
                'name': 'Century Club',
                'description': 'Made 100 food predictions',
                'icon': 'medal',
                'category': 'prediction',
                'requirement_type': 'count',
                'requirement_value': 100,
                'points': 100
            },
            {
                'code': '3_day_streak',
                'name': 'Habit Builder',
                'description': 'Logged food for 3 consecutive days',
                'icon': 'fire',
                'category': 'streak',
                'requirement_type': 'streak',
                'requirement_value': 3,
                'points': 15
            },
            {
                'code': '7_day_streak',
                'name': 'Week Warrior',
                'description': 'Logged food for 7 consecutive days',
                'icon': 'fire',
                'category': 'streak',
                'requirement_type': 'streak',
                'requirement_value': 7,
                'points': 30
            },
            {
                'code': '30_day_streak',
                'name': 'Monthly Master',
                'description': 'Logged food for 30 consecutive days',
                'icon': 'fire',
                'category': 'streak',
                'requirement_type': 'streak',
                'requirement_value': 30,
                'points': 100
            },
            {
                'code': '7_days_goal',
                'name': 'Goal Getter',
                'description': 'Hit your daily calorie goal for 7 consecutive days',
                'icon': 'target',
                'category': 'goal',
                'requirement_type': 'goal_days',
                'requirement_value': 7,
                'points': 50
            },
            {
                'code': 'healthy_week',
                'name': 'Healthy Week',
                'description': 'Logged vegetables or salads 5 times in a week',
                'icon': 'leaf',
                'category': 'food',
                'requirement_type': 'healthy_count',
                'requirement_value': 5,
                'points': 25
            }
        ]

        for ach_data in default_achievements:
            existing = Achievement.query.filter_by(code=ach_data['code']).first()
            if not existing:
                achievement = Achievement(**ach_data)
                db.session.add(achievement)

        db.session.commit()
        logger.info("Default achievements initialized")

    @staticmethod
    def check_and_award_achievements(user_id: int, context: str = 'prediction'):
        """
        Check if user earned any achievements

        Args:
            user_id: User ID
            context: Context of check (prediction, goal_reached, etc.)

        Returns:
            List of newly earned achievements
        """
        from models.history import PredictionHistory, DailyLog

        earned = []

        # Get user's existing achievements
        existing_codes = {
            ua.achievement.code
            for ua in UserAchievement.query.filter_by(user_id=user_id).all()
        }

        # Check prediction count achievements
        if context == 'prediction':
            prediction_count = PredictionHistory.query.filter_by(user_id=user_id).count()

            for code in ['first_prediction', '10_predictions', '100_predictions']:
                if code in existing_codes:
                    continue

                achievement = Achievement.query.filter_by(code=code).first()
                if achievement and prediction_count >= achievement.requirement_value:
                    earned_achievement = AchievementService.award_achievement(
                        user_id,
                        achievement.id,
                        prediction_count
                    )
                    earned.append(earned_achievement)

        # Check streak achievements
        if context in ['prediction', 'streak']:
            streak = DailyStreak.get_or_create(user_id)

            for code in ['3_day_streak', '7_day_streak', '30_day_streak']:
                if code in existing_codes:
                    continue

                achievement = Achievement.query.filter_by(code=code).first()
                if achievement and streak.current_streak >= achievement.requirement_value:
                    earned_achievement = AchievementService.award_achievement(
                        user_id,
                        achievement.id,
                        streak.current_streak
                    )
                    earned.append(earned_achievement)

        return earned

    @staticmethod
    def award_achievement(user_id: int, achievement_id: int, progress_value: Optional[int] = None) -> UserAchievement:
        """
        Award achievement to user

        Args:
            user_id: User ID
            achievement_id: Achievement ID
            progress_value: Optional progress value

        Returns:
            UserAchievement: Awarded achievement record
        """
        # Check if already earned
        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=achievement_id
        ).first()

        if existing:
            return existing

        # Award achievement
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
            progress_value=progress_value
        )

        db.session.add(user_achievement)
        db.session.commit()

        # Get achievement details
        achievement = Achievement.query.get(achievement_id)

        # Send notification
        lang = _get_user_lang(user_id)
        localized = _localize_achievement(achievement, lang)

        if lang == 'tr':
            title = f"Başarı Açıldı: {localized['name']}"
            message = f"Tebrikler! {localized['description']}"
        else:
            title = f'Achievement Unlocked: {localized["name"]}'
            message = f'Congratulations! {localized["description"]}'

        NotificationService.create_notification(
            user_id=user_id,
            notification_type='achievement',
            title=title,
            message=message,
            data={
                'achievement_id': achievement_id,
                'achievement_code': achievement.code,
                'points': achievement.points
            },
            send_email=True,
            send_push=True
        )

        logger.info(f"Achievement awarded: user={user_id}, achievement={achievement.code}")
        return user_achievement

    @staticmethod
    def get_user_achievements(user_id: int) -> List[UserAchievement]:
        """Get all achievements earned by user"""
        return UserAchievement.query.filter_by(user_id=user_id).order_by(
            UserAchievement.earned_at.desc()
        ).all()

    @staticmethod
    def get_available_achievements() -> List[Achievement]:
        """Get all available achievements"""
        return Achievement.query.order_by(Achievement.category, Achievement.points).all()


class StreakService:
    """
    Service for managing daily streaks
    """

    @staticmethod
    def update_user_streak(user_id: int, activity_date: Optional[date] = None) -> Dict:
        """
        Update user's daily streak

        Args:
            user_id: User ID
            activity_date: Date of activity (default: today)

        Returns:
            dict: Streak update information
        """
        streak = DailyStreak.get_or_create(user_id)
        result = streak.update_streak(activity_date)

        # Check for streak achievements
        if result.get('milestone_reached'):
            AchievementService.check_and_award_achievements(user_id, context='streak')

            # Send streak milestone notification
            milestone = result['milestone_reached']
            lang = _get_user_lang(user_id)
            if lang == 'tr':
                title = f'{milestone} Günlük Seri!'
                message = f'{milestone} gündür üst üste kayıt yapıyorsun, devam!'
            else:
                title = f'{milestone} Day Streak!'
                message = f'Amazing! You\'ve logged food for {milestone} consecutive days. Keep it up!'

            NotificationService.create_notification(
                user_id=user_id,
                notification_type='streak',
                title=title,
                message=message,
                data={'streak': milestone},
                send_email=True,
                send_push=True
            )

        # Send notification if streak broken
        elif result.get('streak_broken') and result['previous_streak'] >= 3:
            lang = _get_user_lang(user_id)
            if lang == 'tr':
                title = 'Seri Bozuldu'
                message = f"{result['previous_streak']} günlük serin sona erdi. Bugün yeniden başlayabilirsin!"
            else:
                title = 'Streak Broken'
                message = f'Your {result["previous_streak"]} day streak has ended. Start a new one today!'

            NotificationService.create_notification(
                user_id=user_id,
                notification_type='streak',
                title=title,
                message=message,
                data={'previous_streak': result['previous_streak']},
                send_email=False,
                send_push=True
            )

        return result

    @staticmethod
    def get_user_streak(user_id: int) -> DailyStreak:
        """Get user's streak information"""
        return DailyStreak.get_or_create(user_id)
