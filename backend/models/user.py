# -*- coding: utf-8 -*-
from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    prediction_history = db.relationship('PredictionHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    daily_logs = db.relationship('DailyLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'email': self.email, 'name': self.name, 'is_active': self.is_active, 'created_at': self.created_at.isoformat() if self.created_at else None, 'profile': self.profile.to_dict() if self.profile else None}

    def __repr__(self):
        return f'<User {self.email}>'

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    activity_level = db.Column(db.String(20), default='moderate')
    daily_calorie_goal = db.Column(db.Integer, nullable=True)
    goal_type = db.Column(db.String(20), default='maintain')
    unit_system = db.Column(db.String(10), default='metric')
    language = db.Column(db.String(10), default='tr')
    notifications_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_bmi(self):
        if self.height and self.weight:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        return None

    def calculate_bmr(self):
        if not all([self.weight, self.height, self.age, self.gender]):
            return None
        if self.gender == 'male':
            bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
        elif self.gender == 'female':
            bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
        else:
            male_bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
            female_bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
            bmr = (male_bmr + female_bmr) / 2
        return round(bmr, 2)

    def calculate_tdee(self):
        bmr = self.calculate_bmr()
        if not bmr:
            return None
        multipliers = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
        return round(bmr * multipliers.get(self.activity_level, 1.55), 2)

    def to_dict(self):
        return {'id': self.id, 'height': self.height, 'weight': self.weight, 'age': self.age, 'gender': self.gender, 'activity_level': self.activity_level, 'daily_calorie_goal': self.daily_calorie_goal, 'goal_type': self.goal_type, 'unit_system': self.unit_system, 'language': self.language, 'notifications_enabled': self.notifications_enabled, 'bmi': self.calculate_bmi(), 'bmr': self.calculate_bmr(), 'tdee': self.calculate_tdee()}

    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'
