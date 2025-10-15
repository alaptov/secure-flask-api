from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, bcrypt, login_manager


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """User model with secure password hashing"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Security fields
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    account_locked_until = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    api_keys = db.relationship('ApiKey', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """
        Hash and set the user's password using bcrypt.
        This is more secure than storing plain text passwords.
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """
        Verify a password against the stored hash.
        Returns True if password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_account_locked(self):
        """Check if account is currently locked due to failed login attempts"""
        if self.account_locked_until:
            if datetime.utcnow() < self.account_locked_until:
                return True
            else:
                # Unlock account if lock period has expired
                self.account_locked_until = None
                self.failed_login_attempts = 0
                db.session.commit()
        return False

    def record_failed_login(self):
        """Record a failed login attempt and lock account if necessary"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()

        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)

        db.session.commit()

    def reset_failed_logins(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        self.last_login = datetime.utcnow()
        db.session.commit()

    def to_dict(self, include_email=False):
        """
        Convert user to dictionary for API responses.
        Excludes sensitive information like password hash.
        """
        data = {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        if include_email:
            data['email'] = self.email
        return data


class ApiKey(db.Model):
    """API Key model for token-based authentication"""

    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Security
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<ApiKey {self.name}>'

    def set_key(self, key):
        """Hash and store the API key"""
        self.key_hash = generate_password_hash(key)

    def verify_key(self, key):
        """Verify an API key against the stored hash"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return check_password_hash(self.key_hash, key)

    def record_usage(self):
        """Record API key usage"""
        self.last_used = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """Convert API key to dictionary (excluding sensitive hash)"""
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
