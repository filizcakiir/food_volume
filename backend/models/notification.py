# -*- coding: utf-8 -*-
"""
GastronomGoz - Notification and Achievement Models

This module contains database models for:
- Notifications (in-app, email, push)
- User achievements (badges, milestones)
- Daily streaks (consecutive days tracking)
"""

from datetime import datetime, date
from . import db


class Notification(db.Model):
    """
    Notification model for user notifications

    Types:
    - achievement: User earned a badge/achievement
    - reminder: Daily goal reminder
    - weekly_summary: Weekly calorie summary
    - goal_reached: Daily calorie goal reached
    - streak: Streak milestone (7 days, 30 days, etc.)
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Notification details
    type = db.Column(db.String(50), nullable=False, index=True)  # achievement, reminder, etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)

    # Additional data (JSON format for flexibility)
    data = db.Column(db.JSON, nullable=True)  # e.g., {"achievement_id": 1, "badge": "7_day_streak"}

    # Status
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    # Delivery channels
    sent_in_app = db.Column(db.Boolean, default=True, nullable=False)
    sent_email = db.Column(db.Boolean, default=False, nullable=False)
    sent_push = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Notification id={self.id} type={self.type} user={self.user_id}>'


class Achievement(db.Model):
    """
    Achievement definitions

    Predefined achievements that users can earn:
    - first_prediction: First food prediction
    - 7_day_streak: 7 consecutive days of logging
    - 30_day_streak: 30 consecutive days
    - 100_predictions: 100 total predictions
    - goal_week: Hit daily goal 7 days in a row
    - healthy_eater: Log 30 salads
    - etc.
    """
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)

    # Achievement details
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., "7_day_streak"
    name = db.Column(db.String(100), nullable=False)  # e.g., "Week Warrior"
    description = db.Column(db.Text, nullable=False)  # e.g., "Log food for 7 consecutive days"

    # Badge info
    icon = db.Column(db.String(100), nullable=True)  # Icon name or URL
    category = db.Column(db.String(50), nullable=True)  # streak, prediction, goal, food

    # Requirements
    requirement_type = db.Column(db.String(50), nullable=False)  # streak, count, goal_days
    requirement_value = db.Column(db.Integer, nullable=False)  # e.g., 7 for 7_day_streak

    # Points/rewards
    points = db.Column(db.Integer, default=10, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'points': self.points
        }

    def __repr__(self):
        return f'<Achievement code={self.code} name={self.name}>'


class UserAchievement(db.Model):
    """
    User's earned achievements

    Tracks which achievements a user has unlocked and when
    """
    __tablename__ = 'user_achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)

    # When earned
    earned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Progress when earned (optional)
    progress_value = db.Column(db.Integer, nullable=True)  # e.g., user had 7 days streak

    # Unique constraint: user can only earn each achievement once
    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
    )

    # Relationships
    achievement = db.relationship('Achievement', backref='user_achievements', lazy=True)

    def to_dict(self, include_achievement=True):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'progress_value': self.progress_value
        }

        if include_achievement and self.achievement:
            data['achievement'] = self.achievement.to_dict()

        return data

    def __repr__(self):
        return f'<UserAchievement user={self.user_id} achievement={self.achievement_id}>'


class DailyStreak(db.Model):
    """
    Daily streak tracking

    Tracks consecutive days a user has logged food predictions.
    Updates every day when user makes a prediction.
    """
    __tablename__ = 'daily_streaks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)

    # Current streak
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)

    # Last activity
    last_activity_date = db.Column(db.Date, nullable=True, index=True)

    # Total stats
    total_active_days = db.Column(db.Integer, default=0, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_or_create(cls, user_id):
        """Get or create streak for user"""
        streak = cls.query.filter_by(user_id=user_id).first()
        if not streak:
            streak = cls(user_id=user_id)
            db.session.add(streak)
            db.session.commit()
        return streak

    def update_streak(self, activity_date=None):
        """
        Update streak when user logs food

        Args:
            activity_date: Date of activity (default: today)

        Returns:
            dict: Information about streak update (new_streak, milestone_reached)
        """
        if activity_date is None:
            activity_date = date.today()

        result = {
            'previous_streak': self.current_streak,
            'new_streak': self.current_streak,
            'milestone_reached': None,
            'streak_broken': False
        }

        # First time logging
        if self.last_activity_date is None:
            self.current_streak = 1
            self.longest_streak = 1
            self.total_active_days = 1
            self.last_activity_date = activity_date
            result['new_streak'] = 1

        # Same day - no change
        elif self.last_activity_date == activity_date:
            result['new_streak'] = self.current_streak

        # Consecutive day
        elif (activity_date - self.last_activity_date).days == 1:
            self.current_streak += 1
            self.total_active_days += 1
            self.last_activity_date = activity_date

            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak

            result['new_streak'] = self.current_streak

            # Check for milestones
            if self.current_streak in [3, 7, 14, 30, 60, 90, 180, 365]:
                result['milestone_reached'] = self.current_streak

        # Streak broken (more than 1 day gap)
        else:
            result['streak_broken'] = True
            result['previous_streak'] = self.current_streak
            self.current_streak = 1
            self.total_active_days += 1
            self.last_activity_date = activity_date
            result['new_streak'] = 1

        db.session.commit()
        return result

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'total_active_days': self.total_active_days
        }

    def __repr__(self):
        return f'<DailyStreak user={self.user_id} current={self.current_streak} longest={self.longest_streak}>'


class NotificationPreference(db.Model):
    """
    User notification preferences

    Controls which notifications the user wants to receive and through which channels
    """
    __tablename__ = 'notification_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)

    # Channel preferences
    enable_email = db.Column(db.Boolean, default=True, nullable=False)
    enable_push = db.Column(db.Boolean, default=True, nullable=False)
    enable_in_app = db.Column(db.Boolean, default=True, nullable=False)

    # Notification type preferences
    notify_achievements = db.Column(db.Boolean, default=True, nullable=False)
    notify_daily_reminder = db.Column(db.Boolean, default=True, nullable=False)
    notify_weekly_summary = db.Column(db.Boolean, default=True, nullable=False)
    notify_goal_reached = db.Column(db.Boolean, default=True, nullable=False)
    notify_streak_milestone = db.Column(db.Boolean, default=True, nullable=False)

    # Timing preferences
    daily_reminder_time = db.Column(db.Time, nullable=True)  # e.g., 20:00 for 8 PM
    weekly_summary_day = db.Column(db.Integer, nullable=True)  # 0=Monday, 6=Sunday

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_or_create(cls, user_id):
        """Get or create preferences for user"""
        prefs = cls.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = cls(user_id=user_id)
            db.session.add(prefs)
            db.session.commit()
        return prefs

    def should_send(self, notification_type, channel):
        """
        Check if notification should be sent

        Args:
            notification_type: Type of notification (achievement, reminder, etc.)
            channel: Delivery channel (email, push, in_app)

        Returns:
            bool: True if notification should be sent
        """
        # Check channel enabled
        if channel == 'email' and not self.enable_email:
            return False
        if channel == 'push' and not self.enable_push:
            return False
        if channel == 'in_app' and not self.enable_in_app:
            return False

        # Check notification type enabled
        type_map = {
            'achievement': self.notify_achievements,
            'reminder': self.notify_daily_reminder,
            'weekly_summary': self.notify_weekly_summary,
            'goal_reached': self.notify_goal_reached,
            'streak': self.notify_streak_milestone
        }

        return type_map.get(notification_type, True)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'enable_email': self.enable_email,
            'enable_push': self.enable_push,
            'enable_in_app': self.enable_in_app,
            'notify_achievements': self.notify_achievements,
            'notify_daily_reminder': self.notify_daily_reminder,
            'notify_weekly_summary': self.notify_weekly_summary,
            'notify_goal_reached': self.notify_goal_reached,
            'notify_streak_milestone': self.notify_streak_milestone,
            'daily_reminder_time': self.daily_reminder_time.isoformat() if self.daily_reminder_time else None,
            'weekly_summary_day': self.weekly_summary_day
        }

    def __repr__(self):
        return f'<NotificationPreference user={self.user_id}>'
