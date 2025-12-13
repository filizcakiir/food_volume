# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, validates, ValidationError
import re

class RegisterSchema(Schema):
    email = fields.Email(required=True, error_messages={'required': 'Email required', 'invalid': 'Invalid email'})
    password = fields.Str(required=True, error_messages={'required': 'Password required'})
    name = fields.Str(required=False, missing=None)

    @validates('password')
    def validate_password(self, value):
        if len(value) < 6:
            raise ValidationError('Password must be at least 6 characters')
        if not re.search(r'[a-zA-Z]', value):
            raise ValidationError('Password must contain at least one letter')

    @validates('name')
    def validate_name(self, value):
        if value is not None and len(value) > 0:
            if len(value) < 2:
                raise ValidationError('Name must be at least 2 characters')
            if len(value) > 100:
                raise ValidationError('Name must be at most 100 characters')

class LoginSchema(Schema):
    email = fields.Email(required=True, error_messages={'required': 'Email required', 'invalid': 'Invalid email'})
    password = fields.Str(required=True, error_messages={'required': 'Password required'})

class RefreshTokenSchema(Schema):
    refresh_token = fields.Str(required=True, error_messages={'required': 'Refresh token required'})
