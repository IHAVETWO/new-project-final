import os
from flask import Flask, render_template
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from flask_talisman import Talisman
from .extensions import db, migrate, login_manager
from .models import User

# Initialize extensions
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
compress = Compress()

def create_app():
    # Set templates_path to the correct directory at the project root
    templates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    
    app = Flask(__name__, template_folder=templates_path)
    
    # Enhanced configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/clinic.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devkey-change-in-production')
    
    # Performance optimizations
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Caching configuration
    app.config['CACHE_TYPE'] = 'simple'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    # Security headers
    app.config['SECURITY_HEADERS'] = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize performance extensions
    cache.init_app(app)
    limiter.init_app(app)
    compress.init_app(app)
    
    # Security middleware
    Talisman(app, 
             content_security_policy={
                 'default-src': ["'self'"],
                 'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
                 'style-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com', 'fonts.googleapis.com'],
                 'font-src': ["'self'", 'fonts.gstatic.com'],
                 'img-src': ["'self'", 'data:', 'https:'],
                 'connect-src': ["'self'"]
             },
             force_https=False)  # Set to True in production
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import flash, redirect, url_for
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('main.login'))

    # Register blueprints
    from . import routes
    app.register_blueprint(routes.bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    return app 