from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html', title='Home')


@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - requires authentication"""
    return render_template('dashboard.html', title='Dashboard')


@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html', title='About')
