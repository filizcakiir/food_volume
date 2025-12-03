"""
Flask Uygulama Factory
Backend API için ana giriş noktası
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from config import get_config
from models import db
from utils.logger import setup_logger
from services.notification_service import mail  # Flask-Mail için


# Flask extensions
jwt = JWTManager()
migrate = Migrate()


def create_app(config_name=None):
    """
    Flask app factory function

    Args:
        config_name (str): 'development', 'testing', 'production'

    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)

    # Konfigürasyon yükle
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Logger kurulumu
    setup_logger(app)

    # Database initialize
    db.init_app(app)
    migrate.init_app(app, db)

    # JWT initialize
    jwt.init_app(app)

    # Flask-Mail initialize (email bildirimleri için)
    mail.init_app(app)

    # CORS initialize (mobil uygulama için)
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"]
        }
    })

    # Upload klasörünü oluştur
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Blueprints (API routes) kaydet
    register_blueprints(app)

    # Error handlers
    register_error_handlers(app)

    # JWT callbacks
    register_jwt_callbacks(app)

    # Shell context (flask shell için)
    @app.shell_context_processor
    def make_shell_context():
        from models.user import User, UserProfile
        from models.history import PredictionHistory, DailyLog
        return {
            'db': db,
            'User': User,
            'UserProfile': UserProfile,
            'PredictionHistory': PredictionHistory,
            'DailyLog': DailyLog
        }

    # Health check endpoint
    @app.route('/')
    def index():
        return jsonify({
            'status': 'running',
            'message': 'GastronomGöz Backend API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'auth': '/auth',
                'api': '/api'
            }
        })

    @app.route('/health')
    def health():
        """Sağlık kontrolü endpoint'i"""
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'environment': app.config.get('ENV', 'production')
        })

    return app


def register_blueprints(app):
    """API blueprint'lerini kaydet"""
    # Import burada yapılıyor (circular import engellemek için)
    from api.auth import auth_bp
    from api.user import user_bp
    from api.prediction import prediction_bp
    from api.history import history_bp
    from api.notification import notification_bp

    # Blueprints kaydet
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(prediction_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')
    app.register_blueprint(notification_bp, url_prefix='/api')


def register_error_handlers(app):
    """Global error handler'ları kaydet"""
    from middleware.error_handler import (
        handle_400,
        handle_401,
        handle_403,
        handle_404,
        handle_500,
        handle_validation_error
    )

    app.register_error_handler(400, handle_400)
    app.register_error_handler(401, handle_401)
    app.register_error_handler(403, handle_403)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(500, handle_500)


def register_jwt_callbacks(app):
    """JWT callback fonksiyonlarını kaydet"""

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'error': 'Token süresi dolmuş. Lütfen tekrar giriş yapın.',
            'code': 'TOKEN_EXPIRED'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'error': 'Geçersiz token. Lütfen tekrar giriş yapın.',
            'code': 'INVALID_TOKEN'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'error': 'Token bulunamadı. Lütfen giriş yapın.',
            'code': 'MISSING_TOKEN'
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'error': 'Token iptal edilmiş.',
            'code': 'REVOKED_TOKEN'
        }), 401


if __name__ == '__main__':
    # Development server (Sadece geliştirme için!)
    app = create_app('development')
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
