import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration with secure defaults"""

    # Security: Generate a strong secret key
    # In production: python -c 'import secrets; print(secrets.token_hex(32))'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before using them
        'pool_recycle': 3600,   # Recycle connections after 1 hour
    }

    # Session configuration (security)
    SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)  # Session timeout

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit on CSRF tokens
    WTF_CSRF_SSL_STRICT = True  # Require referrer for HTTPS

    # Bcrypt configuration
    BCRYPT_LOG_ROUNDS = 12  # Cost factor for password hashing

    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"

    # Security headers (Flask-Talisman)
    TALISMAN_FORCE_HTTPS = True
    TALISMAN_STRICT_TRANSPORT_SECURITY = True
    TALISMAN_STRICT_TRANSPORT_SECURITY_MAX_AGE = 31536000  # 1 year
    TALISMAN_CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            'https://cdn.jsdelivr.net',  # Preline CSS
            "'unsafe-inline'"  # Required for Preline
        ],
        'style-src': [
            "'self'",
            'https://cdn.jsdelivr.net',
            "'unsafe-inline'"
        ],
        'img-src': ["'self'", 'data:', 'https:'],
        'font-src': ["'self'", 'https://fonts.gstatic.com'],
    }

    # API configuration
    API_TITLE = "Secure Flask API"
    API_VERSION = "1.0.0"

    # Email configuration (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Password validation
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_PASSWORD_UPPERCASE = True
    REQUIRE_PASSWORD_LOWERCASE = True
    REQUIRE_PASSWORD_DIGIT = True
    REQUIRE_PASSWORD_SPECIAL = True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    TALISMAN_FORCE_HTTPS = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Ensure these are set in production
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    TALISMAN_FORCE_HTTPS = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
