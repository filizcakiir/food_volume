# -*- coding: utf-8 -*-
from datetime import datetime, date
from . import db

class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    image_path = db.Column(db.String(512), nullable=False)
    mask_path = db.Column(db.String(512), nullable=True)
    food_class = db.Column(db.String(100), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False)
    estimated_grams = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    model_version = db.Column(db.String(50), default='v1.0')
    processing_time = db.Column(db.Float, nullable=True)
    depth_info = db.Column(db.JSON, nullable=True)
    segmentation_info = db.Column(db.JSON, nullable=True)
    user_note = db.Column(db.Text, nullable=True)
    meal_type = db.Column(db.String(20), nullable=True)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_images=True):
        # Include macro nutrients so mobile client can display them
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'food_class': self.food_class,
            'confidence': round(self.confidence, 4),
            'estimated_grams': round(self.estimated_grams, 1),
            'calories': round(self.calories, 1),
            'protein': round(self.protein, 1) if self.protein is not None else None,
            'carbs': round(self.carbs, 1) if self.carbs is not None else None,
            'fat': round(self.fat, 1) if self.fat is not None else None,
            'meal_type': self.meal_type,
            'user_note': self.user_note,
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'model_version': self.model_version,
            'processing_time': self.processing_time
        }
        if include_images:
            data['image_url'] = f'/static/uploads/{self.image_path.split("/")[-1]}' if self.image_path else None
            data['mask_url'] = f'/static/uploads/{self.mask_path.split("/")[-1]}' if self.mask_path else None
        return data

    def to_summary_dict(self):
        return {'id': self.id, 'food_class': self.food_class, 'calories': round(self.calories, 1), 'grams': round(self.estimated_grams, 1), 'created_at': self.created_at.isoformat() if self.created_at else None, 'meal_type': self.meal_type}

    def __repr__(self):
        return f'<PredictionHistory id={self.id} food={self.food_class}>'

class DailyLog(db.Model):
    __tablename__ = 'daily_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    total_calories = db.Column(db.Float, default=0.0, nullable=False)
    total_meals = db.Column(db.Integer, default=0, nullable=False)
    breakfast_calories = db.Column(db.Float, default=0.0)
    lunch_calories = db.Column(db.Float, default=0.0)
    dinner_calories = db.Column(db.Float, default=0.0)
    snack_calories = db.Column(db.Float, default=0.0)
    daily_goal = db.Column(db.Integer, nullable=True)
    goal_achieved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

    @classmethod
    def get_or_create(cls, user_id, target_date=None):
        if target_date is None:
            target_date = date.today()
        log = cls.query.filter_by(user_id=user_id, date=target_date).first()
        if not log:
            log = cls(user_id=user_id, date=target_date)
            db.session.add(log)
            db.session.commit()
        return log

    def add_prediction(self, prediction):
        self.total_calories += prediction.calories
        self.total_meals += 1
        if prediction.meal_type == 'breakfast':
            self.breakfast_calories += prediction.calories
        elif prediction.meal_type == 'lunch':
            self.lunch_calories += prediction.calories
        elif prediction.meal_type == 'dinner':
            self.dinner_calories += prediction.calories
        elif prediction.meal_type == 'snack':
            self.snack_calories += prediction.calories
        if self.daily_goal and self.total_calories >= self.daily_goal * 0.9:
            self.goal_achieved = True
        db.session.commit()

    def get_progress_percentage(self):
        if self.daily_goal and self.daily_goal > 0:
            return min(round((self.total_calories / self.daily_goal) * 100, 1), 100)
        return 0

    def to_dict(self):
        return {'id': self.id, 'user_id': self.user_id, 'date': self.date.isoformat() if self.date else None, 'total_calories': round(self.total_calories, 1), 'total_meals': self.total_meals, 'breakfast_calories': round(self.breakfast_calories, 1), 'lunch_calories': round(self.lunch_calories, 1), 'dinner_calories': round(self.dinner_calories, 1), 'snack_calories': round(self.snack_calories, 1), 'daily_goal': self.daily_goal, 'goal_achieved': self.goal_achieved, 'progress_percentage': self.get_progress_percentage()}

    def __repr__(self):
        return f'<DailyLog user={self.user_id} date={self.date}>'
