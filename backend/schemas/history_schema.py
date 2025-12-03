# -*- coding: utf-8 -*-
"""
GastronomGöz - Tahmin Geçmişi Veri Doğrulama Şemaları

Bu modül, tahmin geçmişi API'leri için veri doğrulama şemalarını içerir.
Marshmallow kütüphanesi kullanılarak gelen verilerin geçerliliği kontrol edilir.
"""

from marshmallow import Schema, fields, validate, ValidationError

# Geçerli öğün tipleri
MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']

# Geçerli sıralama alanları
SORT_FIELDS = ['created_at', 'calories', 'confidence', 'food_class']

# Geçerli sıralama yönleri
SORT_ORDERS = ['asc', 'desc']


class UpdatePredictionSchema(Schema):
    """
    Tahmin güncelleme şeması

    Kullanıcı tarafından değiştirilebilecek alanları doğrular:
    - user_note: Kullanıcı notu (opsiyonel, max 500 karakter)
    - meal_type: Öğün tipi (opsiyonel, breakfast/lunch/dinner/snack)
    - is_favorite: Favori işareti (opsiyonel, true/false)
    """
    user_note = fields.Str(
        required=False,
        validate=validate.Length(max=500),
        allow_none=True,
        error_messages={
            'length': 'Not en fazla 500 karakter olabilir.'
        }
    )

    meal_type = fields.Str(
        required=False,
        validate=validate.OneOf(MEAL_TYPES),
        allow_none=True,
        error_messages={
            'validator_failed': f'Öğün tipi şunlardan biri olmalı: {", ".join(MEAL_TYPES)}'
        }
    )

    is_favorite = fields.Bool(
        required=False,
        allow_none=True
    )


class HistoryFilterSchema(Schema):
    """
    Tahmin geçmişi filtreleme şeması

    Listeleme API'si için filtreleme ve sayfalama parametrelerini doğrular:
    - page: Sayfa numarası (varsayılan: 1, min: 1)
    - per_page: Sayfa başına kayıt (varsayılan: 20, min: 1, max: 100)
    - meal_type: Öğün tipine göre filtrele
    - food_class: Yemek adına göre filtrele
    - is_favorite: Favori kayıtları filtrele
    - start_date: Başlangıç tarihi (YYYY-MM-DD formatında)
    - end_date: Bitiş tarihi (YYYY-MM-DD formatında)
    - min_calories: Minimum kalori
    - max_calories: Maksimum kalori
    - sort_by: Sıralama alanı (created_at, calories, confidence, food_class)
    - sort_order: Sıralama yönü (asc, desc)
    """
    page = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        missing=1,
        error_messages={
            'validator_failed': 'Sayfa numarası en az 1 olmalı.'
        }
    )

    per_page = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100),
        missing=20,
        error_messages={
            'validator_failed': 'Sayfa başına kayıt sayısı 1 ile 100 arasında olmalı.'
        }
    )

    meal_type = fields.Str(
        required=False,
        validate=validate.OneOf(MEAL_TYPES),
        allow_none=True,
        error_messages={
            'validator_failed': f'Öğün tipi şunlardan biri olmalı: {", ".join(MEAL_TYPES)}'
        }
    )

    food_class = fields.Str(
        required=False,
        validate=validate.Length(min=1, max=100),
        allow_none=True
    )

    is_favorite = fields.Bool(
        required=False,
        allow_none=True
    )

    start_date = fields.Date(
        required=False,
        allow_none=True,
        error_messages={
            'invalid': 'Başlangıç tarihi YYYY-MM-DD formatında olmalı.'
        }
    )

    end_date = fields.Date(
        required=False,
        allow_none=True,
        error_messages={
            'invalid': 'Bitiş tarihi YYYY-MM-DD formatında olmalı.'
        }
    )

    min_calories = fields.Float(
        required=False,
        validate=validate.Range(min=0),
        allow_none=True,
        error_messages={
            'validator_failed': 'Minimum kalori 0 veya daha büyük olmalı.'
        }
    )

    max_calories = fields.Float(
        required=False,
        validate=validate.Range(min=0),
        allow_none=True,
        error_messages={
            'validator_failed': 'Maksimum kalori 0 veya daha büyük olmalı.'
        }
    )

    sort_by = fields.Str(
        required=False,
        validate=validate.OneOf(SORT_FIELDS),
        missing='created_at',
        error_messages={
            'validator_failed': f'Sıralama alanı şunlardan biri olmalı: {", ".join(SORT_FIELDS)}'
        }
    )

    sort_order = fields.Str(
        required=False,
        validate=validate.OneOf(SORT_ORDERS),
        missing='desc',
        error_messages={
            'validator_failed': 'Sıralama yönü "asc" veya "desc" olmalı.'
        }
    )


class DateRangeSchema(Schema):
    """
    Tarih aralığı şeması

    Günlük günlük API'leri için tarih parametrelerini doğrular:
    - date: Belirli bir tarih (YYYY-MM-DD formatında)
    - start_date: Başlangıç tarihi
    - end_date: Bitiş tarihi
    """
    date = fields.Date(
        required=False,
        allow_none=True,
        error_messages={
            'invalid': 'Tarih YYYY-MM-DD formatında olmalı.'
        }
    )

    start_date = fields.Date(
        required=False,
        allow_none=True,
        error_messages={
            'invalid': 'Başlangıç tarihi YYYY-MM-DD formatında olmalı.'
        }
    )

    end_date = fields.Date(
        required=False,
        allow_none=True,
        error_messages={
            'invalid': 'Bitiş tarihi YYYY-MM-DD formatında olmalı.'
        }
    )
