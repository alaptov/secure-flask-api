from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from app import db, limiter
from app.models import User, ApiKey
from app.forms import ApiKeyForm
import secrets

bp = Blueprint('api', __name__, url_prefix='/api')


def api_key_required(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide an API key in the X-API-Key header'
            }), 401

        # Verify API key
        api_key_obj = ApiKey.query.filter_by(is_active=True).all()
        authenticated = False
        user = None

        for key_obj in api_key_obj:
            if key_obj.verify_key(api_key):
                key_obj.record_usage()
                user = key_obj.user
                authenticated = True
                break

        if not authenticated:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid or has expired'
            }), 401

        # Check if user is active
        if not user.is_active:
            return jsonify({
                'error': 'Account deactivated',
                'message': 'Your account has been deactivated'
            }), 403

        # Attach user to request context
        request.api_user = user
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'You must be logged in to access this resource'
            }), 401

        if not current_user.is_admin:
            return jsonify({
                'error': 'Admin access required',
                'message': 'You do not have permission to access this resource'
            }), 403

        return f(*args, **kwargs)

    return decorated_function


# API Information
@bp.route('/', methods=['GET'])
@limiter.limit("100 per hour")
def api_info():
    """API information and available endpoints"""
    return jsonify({
        'name': 'Secure Flask API',
        'version': '1.0.0',
        'description': 'A secure REST API with authentication and rate limiting',
        'endpoints': {
            'auth': {
                'POST /api/auth/login': 'Login and get API key',
                'GET /api/auth/me': 'Get current user info (requires API key)'
            },
            'users': {
                'GET /api/users': 'List all users (admin only)',
                'GET /api/users/<id>': 'Get user by ID (admin only)',
                'PUT /api/users/<id>': 'Update user (admin only)',
                'DELETE /api/users/<id>': 'Delete user (admin only)'
            },
            'keys': {
                'GET /api/keys': 'List your API keys (requires login)',
                'POST /api/keys': 'Create new API key (requires login)',
                'DELETE /api/keys/<id>': 'Revoke API key (requires login)'
            }
        },
        'rate_limits': {
            'default': '200 per day, 50 per hour',
            'authentication': '10 per minute'
        }
    }), 200


# Authentication endpoints
@bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def api_login():
    """
    API login endpoint.
    Request body: {"username": "user", "password": "pass"}
    Returns: API key for authentication
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'error': 'Invalid request',
            'message': 'Username and password are required'
        }), 400

    # Find user
    user = User.query.filter(
        (User.username == data['username']) |
        (User.email == data['username'].lower())
    ).first()

    # Verify credentials
    if not user or not user.check_password(data['password']):
        return jsonify({
            'error': 'Authentication failed',
            'message': 'Invalid username or password'
        }), 401

    # Check account status
    if user.is_account_locked():
        return jsonify({
            'error': 'Account locked',
            'message': 'Your account is temporarily locked'
        }), 403

    if not user.is_active:
        return jsonify({
            'error': 'Account deactivated',
            'message': 'Your account has been deactivated'
        }), 403

    # Generate API key
    api_key = secrets.token_urlsafe(32)
    api_key_obj = ApiKey(
        name=f"API Key - {data.get('device', 'Unknown')}",
        user_id=user.id
    )
    api_key_obj.set_key(api_key)

    db.session.add(api_key_obj)
    user.reset_failed_logins()
    db.session.commit()

    return jsonify({
        'message': 'Authentication successful',
        'api_key': api_key,
        'user': user.to_dict(),
        'expires_at': None  # No expiration by default
    }), 200


@bp.route('/auth/me', methods=['GET'])
@api_key_required
@limiter.limit("100 per hour")
def get_current_user():
    """Get current authenticated user information"""
    user = request.api_user
    return jsonify({
        'user': user.to_dict(include_email=True)
    }), 200


# API Key management
@bp.route('/keys', methods=['GET'])
@login_required
@limiter.limit("50 per hour")
def list_api_keys():
    """List all API keys for current user"""
    keys = ApiKey.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'keys': [key.to_dict() for key in keys]
    }), 200


@bp.route('/keys', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def create_api_key():
    """Create new API key"""
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({
            'error': 'Invalid request',
            'message': 'API key name is required'
        }), 400

    # Generate new API key
    api_key = secrets.token_urlsafe(32)
    api_key_obj = ApiKey(
        name=data['name'],
        user_id=current_user.id
    )
    api_key_obj.set_key(api_key)

    db.session.add(api_key_obj)
    db.session.commit()

    return jsonify({
        'message': 'API key created successfully',
        'api_key': api_key,
        'key_info': api_key_obj.to_dict(),
        'warning': 'Save this key now. You will not be able to see it again.'
    }), 201


@bp.route('/keys/<int:key_id>', methods=['DELETE'])
@login_required
@limiter.limit("10 per hour")
def revoke_api_key(key_id):
    """Revoke (delete) an API key"""
    api_key = ApiKey.query.filter_by(
        id=key_id,
        user_id=current_user.id
    ).first()

    if not api_key:
        return jsonify({
            'error': 'Not found',
            'message': 'API key not found'
        }), 404

    db.session.delete(api_key)
    db.session.commit()

    return jsonify({
        'message': 'API key revoked successfully'
    }), 200


# User management (admin only)
@bp.route('/users', methods=['GET'])
@login_required
@admin_required
@limiter.limit("100 per hour")
def list_users():
    """List all users (admin only)"""
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': len(users)
    }), 200


@bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
@limiter.limit("100 per hour")
def get_user(user_id):
    """Get user by ID (admin only)"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            'error': 'Not found',
            'message': 'User not found'
        }), 404

    return jsonify({
        'user': user.to_dict(include_email=True)
    }), 200


@bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
@limiter.limit("50 per hour")
def update_user(user_id):
    """Update user (admin only)"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            'error': 'Not found',
            'message': 'User not found'
        }), 404

    data = request.get_json()

    # Update allowed fields
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    if 'email' in data:
        user.email = data['email'].lower()

    db.session.commit()

    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict(include_email=True)
    }), 200


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def delete_user(user_id):
    """Delete user (admin only)"""
    # Prevent self-deletion
    if user_id == current_user.id:
        return jsonify({
            'error': 'Invalid operation',
            'message': 'You cannot delete your own account'
        }), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            'error': 'Not found',
            'message': 'User not found'
        }), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'message': 'User deleted successfully'
    }), 200


# Error handlers for API
@bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad request',
        'message': str(error)
    }), 400


@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404


@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500
