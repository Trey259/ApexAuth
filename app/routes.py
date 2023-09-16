from flask import Blueprint

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    return 'Welcome to the authentication system!'
