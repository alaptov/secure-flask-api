from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User
from app.forms import RegistrationForm, LoginForm, ChangePasswordForm, ProfileUpdateForm

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # Prevent registration spam
def register():
    """User registration with strong password requirements"""

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data.lower()
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f'Registration error: {e}')

    return render_template('auth/register.html', form=form, title='Register')


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Prevent brute force attacks
def login():
    """User login with account lockout protection"""

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        # Support login with username or email
        user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.username.data.lower())
        ).first()

        # Check if user exists and account is not locked
        if user and user.is_account_locked():
            flash(
                'Your account is temporarily locked due to multiple failed login attempts. '
                'Please try again later.',
                'warning'
            )
            return render_template('auth/login.html', form=form, title='Login')

        # Verify password
        if user and user.check_password(form.password.data):
            # Check if account is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form, title='Login')

            # Reset failed login attempts and log in
            user.reset_failed_logins()
            login_user(user, remember=form.remember_me.data)

            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))

        else:
            # Record failed login attempt if user exists
            if user:
                user.record_failed_login()

            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html', form=form, title='Login')


@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""

    form = ProfileUpdateForm(current_user.email)

    if form.validate_on_submit():
        current_user.email = form.email.data.lower()
        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    elif request.method == 'GET':
        form.email.data = current_user.email

    return render_template('auth/profile.html', form=form, title='Profile')


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    """Change user password"""

    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html', form=form, title='Change Password')

        # Check that new password is different
        if current_user.check_password(form.new_password.data):
            flash('New password must be different from current password.', 'warning')
            return render_template('auth/change_password.html', form=form, title='Change Password')

        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash('Your password has been changed successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form, title='Change Password')
