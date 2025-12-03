"""
Database Models
"""
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance (app.py'de initialize edilecek)
db = SQLAlchemy()

# Modelleri import et
from .user import User, UserProfile
from .history import PredictionHistory, DailyLog
from .notification import Notification, Achievement, UserAchievement, DailyStreak, NotificationPreference

__all__ = [
    'db',
    'User',
    'UserProfile',
    'PredictionHistory',
    'DailyLog',
    'Notification',
    'Achievement',
    'UserAchievement',
    'DailyStreak',
    'NotificationPreference'
]
