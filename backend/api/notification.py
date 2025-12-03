# -*- coding: utf-8 -*-
"""
GastronomGoz - Bildirim Yönetimi API

Bu modül bildirimler, başarılar ve streak takibi için RESTful API endpoint'leri sağlar:
- Kullanıcı bildirimlerini listeleme
- Bildirimleri okundu olarak işaretleme
- Bildirim tercihlerini yönetme
- Başarıları ve rozetleri görüntüleme
- Günlük streak'i kontrol etme

API Endpoint'leri:
- GET    /api/notifications           - Kullanıcının bildirimlerini listele
- GET    /api/notifications/unread    - Okunmamış bildirim sayısını getir
- POST   /api/notifications/<id>/read - Bildirimi okundu olarak işaretle
- POST   /api/notifications/read-all  - Tümünü okundu olarak işaretle
- GET    /api/achievements            - Tüm mevcut başarıları listele
- GET    /api/achievements/user       - Kullanıcının kazandığı başarıları getir
- GET    /api/streak                  - Kullanıcının mevcut streak'ini getir
- GET    /api/preferences/notifications - Bildirim tercihlerini getir
- PUT    /api/preferences/notifications - Bildirim tercihlerini güncelle
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
import logging

from models import db
from models.user import User
from models.notification import NotificationPreference
from services.notification_service import (
    NotificationService,
    AchievementService,
    StreakService
)

# Blueprint oluştur
notification_bp = Blueprint('notification', __name__)

# Logger ayarla
logger = logging.getLogger(__name__)


# ============================================================================
# Veri Doğrulama Şemaları
# ============================================================================

class NotificationPreferenceSchema(Schema):
    """Bildirim tercihleri için doğrulama şeması"""
    # Kanal tercihleri
    enable_email = fields.Bool()  # Email bildirimleri aktif mi?
    enable_push = fields.Bool()   # Push bildirimleri aktif mi?
    enable_in_app = fields.Bool() # Uygulama içi bildirimler aktif mi?

    # Bildirim tipi tercihleri
    notify_achievements = fields.Bool()      # Başarı bildirimleri
    notify_daily_reminder = fields.Bool()    # Günlük hatırlatma
    notify_weekly_summary = fields.Bool()    # Haftalık özet
    notify_goal_reached = fields.Bool()      # Hedefe ulaşıldı
    notify_streak_milestone = fields.Bool()  # Streak kilometre taşları

    # Zamanlama tercihleri
    daily_reminder_time = fields.Time(allow_none=True)  # Günlük hatırlatma saati (örn: 20:00)
    weekly_summary_day = fields.Int(validate=validate.Range(min=0, max=6), allow_none=True)  # 0=Pazartesi, 6=Pazar


notification_preference_schema = NotificationPreferenceSchema()


# ============================================================================
# Yardımcı Fonksiyonlar
# ============================================================================

def success_response(data, message="Success", status=200):
    """Başarılı yanıt döndür"""
    return jsonify({
        'success': True,
        'message': message,
        'data': data
    }), status


def error_response(message, status=400):
    """Hata yanıtı döndür"""
    return jsonify({
        'success': False,
        'error': message
    }), status


# ============================================================================
# Bildirim Endpoint'leri
# ============================================================================

@notification_bp.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    """
    GET /api/notifications - Kullanıcının bildirimlerini listele

    Query Parametreleri:
    - unread_only: Sadece okunmamışları döndür (true/false)
    - limit: Maksimum bildirim sayısı (varsayılan: 50, max: 100)
    - offset: Sayfalama için offset (varsayılan: 0)

    Yanıt:
    {
        "success": true,
        "message": "Bildirimler başarıyla getirildi",
        "data": {
            "notifications": [...],    # Bildirim listesi
            "total_count": 25,         # Toplam bildirim sayısı
            "unread_count": 5          # Okunmamış bildirim sayısı
        }
    }
    """
    # Giriş yapmış kullanıcının ID'sini al
    user_id = get_jwt_identity()

    # Query parametrelerini parse et
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
    offset = int(request.args.get('offset', 0))

    # Bildirimleri getir
    notifications = NotificationService.get_user_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    # Toplam ve okunmamış sayıları hesapla
    from models.notification import Notification
    total_count = Notification.query.filter_by(user_id=user_id).count()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return success_response({
        'notifications': [n.to_dict() for n in notifications],
        'total_count': total_count,
        'unread_count': unread_count
    }, "Bildirimler başarıyla getirildi")


@notification_bp.route('/notifications/unread', methods=['GET'])
@jwt_required()
def get_unread_count():
    """
    GET /api/notifications/unread - Okunmamış bildirim sayısını getir

    Yanıt:
    {
        "success": true,
        "message": "Okunmamış sayısı getirildi",
        "data": {
            "unread_count": 5
        }
    }
    """
    user_id = get_jwt_identity()

    # Okunmamış bildirim sayısını hesapla
    from models.notification import Notification
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return success_response({
        'unread_count': unread_count
    }, "Okunmamış sayısı getirildi")


@notification_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """
    POST /api/notifications/<id>/read - Bildirimi okundu olarak işaretle

    Parametreler:
    - notification_id: Bildirim ID'si

    Yanıt:
    {
        "success": true,
        "message": "Bildirim okundu olarak işaretlendi"
    }
    """
    user_id = get_jwt_identity()

    # Bildirimi okundu olarak işaretle (güvenlik için user_id kontrolü yapılır)
    success = NotificationService.mark_as_read(notification_id, user_id)

    if success:
        return success_response({}, "Bildirim okundu olarak işaretlendi")
    else:
        return error_response("Bildirim bulunamadı", 404)


@notification_bp.route('/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_read():
    """
    POST /api/notifications/read-all - Tüm bildirimleri okundu olarak işaretle

    Yanıt:
    {
        "success": true,
        "message": "Tüm bildirimler okundu olarak işaretlendi",
        "data": {
            "count": 5  # İşaretlenen bildirim sayısı
        }
    }
    """
    user_id = get_jwt_identity()

    # Tüm bildirimleri okundu olarak işaretle
    count = NotificationService.mark_all_as_read(user_id)

    return success_response({
        'count': count
    }, f"{count} bildirim okundu olarak işaretlendi")


# ============================================================================
# Başarı (Achievement) Endpoint'leri
# ============================================================================

@notification_bp.route('/achievements', methods=['GET'])
@jwt_required()
def list_achievements():
    """
    GET /api/achievements - Tüm mevcut başarıları listele

    Sisteme tanımlı tüm başarıları (rozetleri) döndürür.
    Kullanıcı bunlardan hangilerini kazanmış görmek için /achievements/user kullanın.

    Yanıt:
    {
        "success": true,
        "message": "Başarılar başarıyla getirildi",
        "data": {
            "achievements": [
                {
                    "id": 1,
                    "code": "first_prediction",
                    "name": "İlk Adım",
                    "description": "İlk yemek tahmini yaptın",
                    "icon": "star",
                    "category": "prediction",
                    "points": 10
                },
                ...
            ]
        }
    }
    """
    # Tüm mevcut başarıları getir
    achievements = AchievementService.get_available_achievements()

    return success_response({
        'achievements': [a.to_dict() for a in achievements]
    }, "Başarılar başarıyla getirildi")


@notification_bp.route('/achievements/user', methods=['GET'])
@jwt_required()
def get_user_achievements():
    """
    GET /api/achievements/user - Kullanıcının kazandığı başarıları getir

    Giriş yapmış kullanıcının şimdiye kadar kazandığı tüm başarıları listeler.

    Yanıt:
    {
        "success": true,
        "message": "Kullanıcı başarıları getirildi",
        "data": {
            "achievements": [
                {
                    "id": 1,
                    "achievement_id": 1,
                    "earned_at": "2025-11-30T12:00:00",
                    "achievement": {
                        "code": "first_prediction",
                        "name": "İlk Adım",
                        ...
                    }
                },
                ...
            ],
            "total_earned": 5,      # Toplam kazanılan başarı sayısı
            "total_points": 150     # Toplam puan
        }
    }
    """
    user_id = get_jwt_identity()

    # Kullanıcının kazandığı başarıları getir
    user_achievements = AchievementService.get_user_achievements(user_id)

    # Toplam puanı hesapla
    total_points = sum(ua.achievement.points for ua in user_achievements)

    return success_response({
        'achievements': [ua.to_dict() for ua in user_achievements],
        'total_earned': len(user_achievements),
        'total_points': total_points
    }, "Kullanıcı başarıları getirildi")


# ============================================================================
# Streak (Günlük Seri) Endpoint'leri
# ============================================================================

@notification_bp.route('/streak', methods=['GET'])
@jwt_required()
def get_streak():
    """
    GET /api/streak - Kullanıcının mevcut streak'ini getir

    Kullanıcının üst üste kaç gün yemek kaydı yaptığını ve istatistiklerini döndürür.

    Yanıt:
    {
        "success": true,
        "message": "Streak başarıyla getirildi",
        "data": {
            "current_streak": 7,              # Şu anki üst üste gün sayısı
            "longest_streak": 14,             # En uzun streak
            "last_activity_date": "2025-11-30",  # Son aktivite tarihi
            "total_active_days": 45           # Toplam aktif gün sayısı
        }
    }
    """
    user_id = get_jwt_identity()

    # Kullanıcının streak bilgilerini getir
    streak = StreakService.get_user_streak(user_id)

    return success_response(
        streak.to_dict(),
        "Streak başarıyla getirildi"
    )


# ============================================================================
# Bildirim Tercih Endpoint'leri
# ============================================================================

@notification_bp.route('/preferences/notifications', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    """
    GET /api/preferences/notifications - Bildirim tercihlerini getir

    Kullanıcının bildirim ayarlarını döndürür.
    Hangi bildirimleri almak istediği, hangi kanalları kullandığı vb.

    Yanıt:
    {
        "success": true,
        "message": "Tercihler getirildi",
        "data": {
            "user_id": 1,
            "enable_email": true,           # Email bildirimleri aktif
            "enable_push": true,            # Push bildirimleri aktif
            "enable_in_app": true,          # Uygulama içi bildirimler aktif
            "notify_achievements": true,    # Başarı bildirimleri
            "notify_daily_reminder": true,  # Günlük hatırlatma
            "notify_weekly_summary": true,  # Haftalık özet
            "notify_goal_reached": true,    # Hedef başarısı
            "notify_streak_milestone": true,  # Streak kilometre taşları
            "daily_reminder_time": "20:00:00",  # Hatırlatma saati
            "weekly_summary_day": 0         # Haftalık özet günü (0=Pazartesi)
        }
    }
    """
    user_id = get_jwt_identity()

    # Kullanıcının bildirim tercihlerini getir (yoksa varsayılanlarla oluştur)
    prefs = NotificationPreference.get_or_create(user_id)

    return success_response(
        prefs.to_dict(),
        "Tercihler getirildi"
    )


@notification_bp.route('/preferences/notifications', methods=['PUT'])
@jwt_required()
def update_notification_preferences():
    """
    PUT /api/preferences/notifications - Bildirim tercihlerini güncelle

    Kullanıcının bildirim ayarlarını günceller.

    İstek Gövdesi:
    {
        "enable_email": true,
        "enable_push": false,
        "notify_achievements": true,
        "notify_daily_reminder": false,
        "daily_reminder_time": "20:00:00",
        ...
    }

    Yanıt:
    {
        "success": true,
        "message": "Tercihler başarıyla güncellendi",
        "data": {
            ...  # Güncellenmiş tercihler
        }
    }
    """
    try:
        # Gelen veriyi doğrula
        data = notification_preference_schema.load(request.json or {})
    except ValidationError as err:
        return error_response(err.messages, 400)

    user_id = get_jwt_identity()

    # Kullanıcının tercihlerini getir
    prefs = NotificationPreference.get_or_create(user_id)

    # Gelen verileri güncelle
    for key, value in data.items():
        if hasattr(prefs, key):
            setattr(prefs, key, value)

    try:
        # Değişiklikleri kaydet
        db.session.commit()
        logger.info(f"Notification preferences updated for user {user_id}")

        return success_response(
            prefs.to_dict(),
            "Tercihler başarıyla güncellendi"
        )

    except Exception as e:
        # Hata durumunda geri al
        db.session.rollback()
        logger.error(f"Error updating preferences: {str(e)}")
        return error_response("Tercihler güncellenirken hata oluştu", 500)


# ============================================================================
# Admin Endpoint'leri (Başarıları başlatma)
# ============================================================================

@notification_bp.route('/admin/init-achievements', methods=['POST'])
@jwt_required()
def initialize_achievements():
    """
    POST /api/admin/init-achievements - Varsayılan başarıları başlat

    Veritabanına ön tanımlı başarıları ekler.

    Not: Üretim ortamında bu endpoint sadece admin'ler için açık olmalı
    veya CLI komutu olarak çalıştırılmalı.

    Yanıt:
    {
        "success": true,
        "message": "Başarılar başarıyla başlatıldı"
    }
    """
    try:
        # Varsayılan başarıları veritabanına ekle
        AchievementService.initialize_achievements()
        return success_response({}, "Başarılar başarıyla başlatıldı")
    except Exception as e:
        logger.error(f"Error initializing achievements: {str(e)}")
        return error_response("Başarılar başlatılırken hata oluştu", 500)
