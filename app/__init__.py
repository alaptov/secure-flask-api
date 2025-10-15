from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from config import config
import os

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
talisman = Talisman()


def create_app(config_name=None):
    """
    Application factory pattern.
    Creates and configures the Flask application.
    """

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'  # Protect against session hijacking

    # Configure rate limiting
    limiter.init_app(app)

    # Configure security headers (Flask-Talisman)
    if app.config.get('TALISMAN_FORCE_HTTPS', False):
        talisman.init_app(
            app,
            force_https=app.config['TALISMAN_FORCE_HTTPS'],
            strict_transport_security=app.config['TALISMAN_STRICT_TRANSPORT_SECURITY'],
            strict_transport_security_max_age=app.config['TALISMAN_STRICT_TRANSPORT_SECURITY_MAX_AGE'],
            content_security_policy=app.config['TALISMAN_CONTENT_SECURITY_POLICY']
        )

    # Register blueprints
    from app.routes import auth, api, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(main.bp)

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create default admin user if it doesn't exist
        from app.models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
                is_admin=True
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'changeme123'))
            db.session.add(admin)
            db.session.commit()
            print('Default admin user created. Please change the password!')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        from flask import render_template, request
        if request.path.startswith('/api/'):
            from flask import jsonify
            return jsonify(error="Rate limit exceeded", message=str(e.description)), 429
        return render_template('errors/429.html'), 429

    # Context processor for templates
    @app.context_processor
    def inject_config():
        return {
            'app_name': app.config.get('API_TITLE', 'Secure Flask API'),
            'app_version': app.config.get('API_VERSION', '1.0.0')
        }

    return app
