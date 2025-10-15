# Secure Flask API

A production-ready Flask application with comprehensive security features, built using bcrypt authentication, Flask-WTF forms, SQLAlchemy ORM, and Preline CSS for modern UI design.

## Features

### Security Features
- **Password Hashing**: Bcrypt password hashing with configurable cost factor (12 rounds)
- **CSRF Protection**: Automatic CSRF token generation and validation on all forms
- **Rate Limiting**: Built-in rate limiting to prevent brute-force attacks
- **Account Lockout**: Automatic account lockout after 5 failed login attempts (30 minutes)
- **Session Security**: Secure session management with httpOnly and SameSite cookies
- **Security Headers**: Flask-Talisman for HTTPS enforcement, CSP, HSTS, and X-Frame-Options
- **API Key Authentication**: Secure API key generation and management
- **Password Requirements**: Strong password validation (8+ chars, uppercase, lowercase, digit, special char)
- **Environment-based Config**: Separate configurations for development, testing, and production

### Application Features
- User registration and authentication
- User profile management
- Password change functionality
- RESTful API with authentication
- Admin user management
- Responsive UI with Preline CSS (Tailwind)
- Dark mode support
- API documentation

## Technology Stack

- **Flask 3.1+**: Modern Python web framework
- **SQLAlchemy 2.0+**: Python SQL toolkit and ORM
- **Flask-Bcrypt**: Password hashing with bcrypt
- **Flask-WTF**: Form validation and CSRF protection
- **Flask-Login**: User session management
- **Flask-Limiter**: Rate limiting for API endpoints
- **Flask-Talisman**: Security headers and HTTPS enforcement
- **Preline CSS**: Modern Tailwind CSS component library

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup

1. **Clone or download the repository**
   ```bash
   cd flask-app
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and update the following:
   - `SECRET_KEY`: Generate a secure secret key
     ```bash
     python -c 'import secrets; print(secrets.token_hex(32))'
     ```
   - `DATABASE_URL`: Database connection string (default: SQLite)
   - `ADMIN_EMAIL`: Initial admin user email
   - `ADMIN_PASSWORD`: Initial admin user password (change after first login!)

5. **Initialize the database**
   The database will be created automatically on first run with a default admin user.

6. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://127.0.0.1:5000`

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/app.db
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme123
```

### Configuration Profiles

- **Development**: Debug enabled, HTTP allowed, relaxed security
- **Production**: Debug disabled, HTTPS enforced, strict security
- **Testing**: In-memory database, CSRF disabled for testing

## Usage

### Default Admin Account

On first run, a default admin account is created:
- **Username**: `admin`
- **Email**: From `ADMIN_EMAIL` in `.env` (default: admin@example.com)
- **Password**: From `ADMIN_PASSWORD` in `.env` (default: changeme123)

**Important**: Change the admin password immediately after first login!

### Web Interface

1. **Homepage**: `http://127.0.0.1:5000/`
2. **Register**: `http://127.0.0.1:5000/auth/register`
3. **Login**: `http://127.0.0.1:5000/auth/login`
4. **Dashboard**: `http://127.0.0.1:5000/dashboard` (requires login)
5. **Profile**: `http://127.0.0.1:5000/auth/profile` (requires login)

### API Endpoints

#### Authentication
- `POST /api/auth/login` - Login and get API key
  ```json
  {
    "username": "your_username",
    "password": "your_password"
  }
  ```

- `GET /api/auth/me` - Get current user info (requires API key)

#### API Key Management
- `GET /api/keys` - List your API keys (requires login)
- `POST /api/keys` - Create new API key (requires login)
- `DELETE /api/keys/<id>` - Revoke API key (requires login)

#### User Management (Admin Only)
- `GET /api/users` - List all users
- `GET /api/users/<id>` - Get user by ID
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user

### API Authentication

Include your API key in the request headers:

```bash
curl -H "X-API-Key: your-api-key-here" http://127.0.0.1:5000/api/auth/me
```

### Rate Limits

- **Default**: 200 requests per day, 50 per hour
- **Registration**: 5 per hour
- **Login**: 10 per minute
- **Password Change**: 5 per hour

## Security Best Practices

### For Development
1. Never commit `.env` file or `instance/` directory
2. Use strong, unique secret keys
3. Change default admin credentials immediately
4. Keep dependencies updated

### For Production
1. Set `FLASK_ENV=production`
2. Use environment variables for all sensitive data
3. Use HTTPS (Talisman enforces this)
4. Use a production database (PostgreSQL, MySQL)
5. Set up proper logging and monitoring
6. Use a production WSGI server (Gunicorn, uWSGI)
7. Implement backup strategies
8. Review and customize security headers

### Production Deployment Example (Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 'app:create_app("production")'
```

## Project Structure

```
flask-app/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── forms.py             # WTForms forms
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── api.py           # API routes
│   │   └── main.py          # Main routes
│   ├── static/
│   │   └── css/
│   └── templates/           # Jinja2 templates
│       ├── base.html
│       ├── auth/
│       ├── errors/
│       └── ...
├── instance/                # Instance folder (not in git)
│   └── app.db              # SQLite database
├── config.py               # Configuration classes
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example           # Example environment file
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Testing

To run the application in testing mode:

```python
from app import create_app

app = create_app('testing')
```

## Contributing

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation
4. Ensure all security features remain intact

## Security Reporting

If you discover a security vulnerability, please email the maintainer directly rather than using the issue tracker.

## License

MIT License - feel free to use this for your projects!

## Support

For issues and questions:
1. Check the documentation
2. Review the code comments
3. Open an issue on the repository

## Acknowledgments

- Flask team for the amazing framework
- Preline for the beautiful UI components
- All the Flask extension authors

---

**Built with security in mind**
Version 1.0.0
