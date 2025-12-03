# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, validates, ValidationError

class UserProfileSchema(Schema):
    """User profile update schema"""
    height = fields.Float(required=False, allow_none=True)
    weight = fields.Float(required=False, allow_none=True)
    age = fields.Integer(required=False, allow_none=True)
    gender = fields.Str(required=False, allow_none=True)
    activity_level = fields.Str(required=False, allow_none=True)
    daily_calorie_goal = fields.Integer(required=False, allow_none=True)
    goal_type = fields.Str(required=False, allow_none=True)
    unit_system = fields.Str(required=False, allow_none=True)
    language = fields.Str(required=False, allow_none=True)
    notifications_enabled = fields.Boolean(required=False, allow_none=True)

    @validates('height')
    def validate_height(self, value):
        if value is not None and (value < 50 or value > 300):
            raise ValidationError('Height must be between 50 and 300 cm')

    @validates('weight')
    def validate_weight(self, value):
        if value is not None and (value < 20 or value > 500):
            raise ValidationError('Weight must be between 20 and 500 kg')

    @validates('age')
    def validate_age(self, value):
        if value is not None and (value < 10 or value > 120):
            raise ValidationError('Age must be between 10 and 120')

    @validates('gender')
    def validate_gender(self, value):
        if value is not None:
            valid_genders = ['male', 'female', 'other']
            if value not in valid_genders:
                raise ValidationError(f'Gender must be one of: {", ".join(valid_genders)}')

    @validates('activity_level')
    def validate_activity_level(self, value):
        if value is not None:
            valid_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
            if value not in valid_levels:
                raise ValidationError(f'Activity level must be one of: {", ".join(valid_levels)}')

    @validates('goal_type')
    def validate_goal_type(self, value):
        if value is not None:
            valid_types = ['lose', 'gain', 'maintain']
            if value not in valid_types:
                raise ValidationError(f'Goal type must be one of: {", ".join(valid_types)}')

    @validates('unit_system')
    def validate_unit_system(self, value):
        if value is not None:
            valid_systems = ['metric', 'imperial']
            if value not in valid_systems:
                raise ValidationError(f'Unit system must be one of: {", ".join(valid_systems)}')

    @validates('language')
    def validate_language(self, value):
        if value is not None:
            valid_languages = ['tr', 'en']
            if value not in valid_languages:
                raise ValidationError(f'Language must be one of: {", ".join(valid_languages)}')

    @validates('daily_calorie_goal')
    def validate_daily_calorie_goal(self, value):
        if value is not None and (value < 500 or value > 10000):
            raise ValidationError('Daily calorie goal must be between 500 and 10000')


class UpdateGoalSchema(Schema):
    """Update daily calorie goal schema"""
    daily_calorie_goal = fields.Integer(required=True)
    goal_type = fields.Str(required=False, allow_none=True)

    @validates('daily_calorie_goal')
    def validate_daily_calorie_goal(self, value):
        if value < 500 or value > 10000:
            raise ValidationError('Daily calorie goal must be between 500 and 10000')

    @validates('goal_type')
    def validate_goal_type(self, value):
        if value is not None:
            valid_types = ['lose', 'gain', 'maintain']
            if value not in valid_types:
                raise ValidationError(f'Goal type must be one of: {", ".join(valid_types)}')
