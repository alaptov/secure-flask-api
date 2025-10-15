from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError, Regexp
)
from app.models import User
import re


class PasswordValidator:
    """Custom password validator for strong password requirements"""

    def __init__(self, min_length=8):
        self.min_length = min_length

    def __call__(self, form, field):
        password = field.data
        errors = []

        if len(password) < self.min_length:
            errors.append(f'at least {self.min_length} characters')

        if not re.search(r'[A-Z]', password):
            errors.append('at least one uppercase letter')

        if not re.search(r'[a-z]', password):
            errors.append('at least one lowercase letter')

        if not re.search(r'\d', password):
            errors.append('at least one digit')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('at least one special character')

        if errors:
            raise ValidationError(
                f'Password must contain {", ".join(errors)}.'
            )


class RegistrationForm(FlaskForm):
    """
    User registration form with strong validation.
    Includes CSRF protection automatically via FlaskForm.
    """

    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=80, message='Username must be between 3 and 80 characters'),
            Regexp(
                r'^[a-zA-Z0-9_-]+$',
                message='Username can only contain letters, numbers, underscores, and hyphens'
            )
        ],
        render_kw={"placeholder": "Choose a username"}
    )

    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must be less than 120 characters')
        ],
        render_kw={"placeholder": "your.email@example.com"}
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            PasswordValidator(min_length=8)
        ],
        render_kw={"placeholder": "Create a strong password"}
    )

    password2 = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={"placeholder": "Re-enter your password"}
    )

    submit = SubmitField('Register')

    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'Username already taken. Please choose a different one.'
            )

    def validate_email(self, email):
        """Check if email already exists"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError(
                'Email already registered. Please use a different email or login.'
            )


class LoginForm(FlaskForm):
    """
    User login form with CSRF protection.
    """

    username = StringField(
        'Username or Email',
        validators=[
            DataRequired(message='Username or email is required')
        ],
        render_kw={"placeholder": "Enter your username or email"}
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required')
        ],
        render_kw={"placeholder": "Enter your password"}
    )

    remember_me = BooleanField('Remember Me')

    submit = SubmitField('Login')


class ChangePasswordForm(FlaskForm):
    """Form for changing user password"""

    current_password = PasswordField(
        'Current Password',
        validators=[
            DataRequired(message='Current password is required')
        ],
        render_kw={"placeholder": "Enter your current password"}
    )

    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='New password is required'),
            PasswordValidator(min_length=8)
        ],
        render_kw={"placeholder": "Enter your new password"}
    )

    new_password2 = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm your new password'),
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={"placeholder": "Re-enter your new password"}
    )

    submit = SubmitField('Change Password')


class ApiKeyForm(FlaskForm):
    """Form for creating API keys"""

    name = StringField(
        'API Key Name',
        validators=[
            DataRequired(message='API key name is required'),
            Length(min=3, max=100, message='Name must be between 3 and 100 characters')
        ],
        render_kw={"placeholder": "e.g., Production API Key"}
    )

    submit = SubmitField('Generate API Key')


class ProfileUpdateForm(FlaskForm):
    """Form for updating user profile"""

    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must be less than 120 characters')
        ],
        render_kw={"placeholder": "your.email@example.com"}
    )

    submit = SubmitField('Update Profile')

    def __init__(self, original_email, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        """Check if email is already taken by another user"""
        if email.data.lower() != self.original_email.lower():
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError(
                    'Email already registered. Please use a different email.'
                )
