import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'devkey-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///../instance/clinic.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Performance and Caching
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')  # simple, redis, memcached
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = 'dental_clinic_'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_OPTIONS = {
        'connection_pool': 10
    }
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self'"
    }
    
    # Session Configuration
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    SESSION_FILE_DIR = os.path.join(os.path.dirname(__file__), 'sessions')
    SESSION_FILE_THRESHOLD = 500
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Payment Configuration (Stripe)
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    # Cloud Storage (AWS S3)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    AWS_S3_REGION = os.environ.get('AWS_S3_REGION', 'us-east-1')
    
    # Machine Learning Configuration
    ML_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ml_models')
    ML_PREDICTION_THRESHOLD = 0.7
    ML_TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    
    # Analytics Configuration
    ANALYTICS_ENABLED = os.environ.get('ANALYTICS_ENABLED', 'true').lower() in ['true', 'on', '1']
    ANALYTICS_RETENTION_DAYS = 365
    ANALYTICS_BATCH_SIZE = 1000
    
    # Real-time Configuration
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('SOCKETIO_MESSAGE_QUEUE')
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    # Background Tasks (Celery)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    
    # Monitoring and Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    # Health Check Configuration
    HEALTH_CHECK_ENABLED = True
    HEALTH_CHECK_TIMEOUT = 30
    
    # API Configuration
    API_RATE_LIMIT = "1000 per hour"
    API_VERSION = 'v1'
    API_TITLE = 'Dental Clinic API'
    API_DESCRIPTION = 'Advanced dental clinic management API'
    
    # Search Configuration
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
    SEARCH_INDEX_NAME = 'dental_clinic'
    
    # Notification Configuration
    NOTIFICATION_RETENTION_DAYS = 30
    NOTIFICATION_BATCH_SIZE = 100
    PUSH_NOTIFICATIONS_ENABLED = os.environ.get('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() in ['true', 'on', '1']
    
    # Appointment Configuration
    APPOINTMENT_REMINDER_HOURS = 24
    APPOINTMENT_CANCELLATION_HOURS = 24
    APPOINTMENT_DURATION_DEFAULT = 60  # minutes
    APPOINTMENT_SLOT_INTERVAL = 15  # minutes
    
    # Health Score Configuration
    HEALTH_SCORE_WEIGHTS = {
        'appointment_completion': 0.3,
        'recent_activity': 0.2,
        'medical_conditions': 0.3,
        'hygiene_practices': 0.2
    }
    
    # Machine Learning Model Configuration
    ML_MODELS = {
        'appointment_prediction': {
            'algorithm': 'random_forest',
            'features': ['day_of_week', 'month', 'is_weekend', 'lag_1', 'lag_7', 'rolling_mean_7'],
            'training_interval': 30,  # days
            'prediction_horizon': 30  # days
        },
        'churn_prediction': {
            'algorithm': 'logistic_regression',
            'features': ['days_since_last_visit', 'total_appointments', 'cancellation_rate'],
            'threshold': 0.5
        },
        'health_risk_assessment': {
            'algorithm': 'gradient_boosting',
            'features': ['age', 'medical_conditions', 'appointment_history', 'hygiene_practices'],
            'risk_levels': ['low', 'medium', 'high', 'critical']
        }
    }
    
    # Data Export Configuration
    EXPORT_FORMATS = ['xlsx', 'csv', 'pdf', 'json']
    EXPORT_MAX_RECORDS = 10000
    EXPORT_TIMEOUT = 300  # seconds
    
    # Audit Trail Configuration
    AUDIT_LOG_RETENTION_DAYS = 365
    AUDIT_LOG_LEVELS = ['create', 'update', 'delete', 'login', 'logout', 'export']
    
    # Backup Configuration
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() in ['true', 'on', '1']
    BACKUP_SCHEDULE = '0 2 * * *'  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = 30
    BACKUP_STORAGE_PATH = os.path.join(os.path.dirname(__file__), 'backups')
    
    # Feature Flags
    FEATURE_FLAGS = {
        'advanced_analytics': True,
        'machine_learning': True,
        'real_time_notifications': True,
        'health_score': True,
        'appointment_optimization': True,
        'predictive_analytics': True,
        'audit_trail': True,
        'data_export': True,
        'search_functionality': True,
        'mobile_app': False,
        'telemedicine': False,
        'ai_chatbot': False
    }
    
    # API Keys and External Services
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    
    # Development Tools
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', 'on', '1']
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'false').lower() in ['true', 'on', '1']
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
        os.makedirs(app.config['ML_MODEL_PATH'], exist_ok=True)
        os.makedirs(app.config['ML_TRAINING_DATA_PATH'], exist_ok=True)
        os.makedirs(app.config['BACKUP_STORAGE_PATH'], exist_ok=True)
        os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    CACHE_TYPE = 'simple'
    
    # Development-specific settings
    MAIL_SUPPRESS_SEND = True
    TESTING = False
    
    # Enable all features for development
    FEATURE_FLAGS = {
        'advanced_analytics': True,
        'machine_learning': True,
        'real_time_notifications': True,
        'health_score': True,
        'appointment_optimization': True,
        'predictive_analytics': True,
        'audit_trail': True,
        'data_export': True,
        'search_functionality': True,
        'mobile_app': True,
        'telemedicine': True,
        'ai_chatbot': True
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'simple'
    
    # Disable external services for testing
    MAIL_SUPPRESS_SEND = True
    TWILIO_ACCOUNT_SID = None
    STRIPE_SECRET_KEY = None
    AWS_ACCESS_KEY_ID = None

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    CACHE_TYPE = 'redis'
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Disable development features
    FEATURE_FLAGS = {
        'advanced_analytics': True,
        'machine_learning': True,
        'real_time_notifications': True,
        'health_score': True,
        'appointment_optimization': True,
        'predictive_analytics': True,
        'audit_trail': True,
        'data_export': True,
        'search_functionality': True,
        'mobile_app': False,
        'telemedicine': False,
        'ai_chatbot': False
    }

class StagingConfig(Config):
    """Staging configuration"""
    DEBUG = True
    TESTING = False
    
    # Staging-specific settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('STAGING_DATABASE_URL')
    CACHE_TYPE = 'redis'
    
    # Enable most features for testing
    FEATURE_FLAGS = {
        'advanced_analytics': True,
        'machine_learning': True,
        'real_time_notifications': True,
        'health_score': True,
        'appointment_optimization': True,
        'predictive_analytics': True,
        'audit_trail': True,
        'data_export': True,
        'search_functionality': True,
        'mobile_app': True,
        'telemedicine': True,
        'ai_chatbot': True
    }

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config.get(config_name, config['default']) 