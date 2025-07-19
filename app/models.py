from .extensions import db
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import uuid
import json
from sqlalchemy import event, Index
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
import re

from flask import current_app as app

class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None

class User(db.Model, UserMixin, TimestampMixin, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    emergency_phone = db.Column(db.String(20), nullable=True)
    medical_conditions = db.Column(db.Text, nullable=True)  # JSON string
    allergies = db.Column(db.Text, nullable=True)  # JSON string
    medications = db.Column(db.Text, nullable=True)  # JSON string
    insurance_provider = db.Column(db.String(100), nullable=True)
    insurance_number = db.Column(db.String(50), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    preferred_language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    gender = db.Column(db.String(10))
    
    # Relationships
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    medical_records = db.relationship('MedicalRecord', backref='user', lazy=True)
    dental_history = db.relationship('DentalHistory', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    # Indexes for better performance
    __table_args__ = (
        Index('idx_user_email_username', 'email', 'username'),
        Index('idx_user_active', 'is_active', 'is_deleted'),
        Index('idx_user_is_admin', 'is_admin'),
    )

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError('Email is required')
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()

    @validates('phone')
    def validate_phone(self, key, phone):
        if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValueError('Invalid phone number format')
        return phone

    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError('Username is required')
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            raise ValueError('Username must be 3-20 characters, alphanumeric and underscore only')
        return username.lower()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)
    
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def set_medical_conditions(self, conditions_list):
        self.medical_conditions = json.dumps(conditions_list)
    
    def get_medical_conditions(self):
        if self.medical_conditions:
            return json.loads(self.medical_conditions)
        return []
    
    def set_allergies(self, allergies_list):
        self.allergies = json.dumps(allergies_list)
    
    def get_allergies(self):
        if self.allergies:
            return json.loads(self.allergies)
        return []
    
    def set_medications(self, medications_list):
        self.medications = json.dumps(medications_list)
    
    def get_medications(self):
        if self.medications:
            return json.loads(self.medications)
        return []
    
    def generate_verification_token(self):
        self.verification_token = str(uuid.uuid4())
        return self.verification_token
    
    def generate_reset_token(self):
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.reset_token
    
    def verify_reset_token(self, token):
        return self.reset_token == token and self.reset_token_expiry > datetime.utcnow()

    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def is_account_locked(self):
        if self.account_locked_until and self.account_locked_until > datetime.utcnow():
            return True
        return False

    def __repr__(self):
        return f'<User {self.username}>'

class Article(db.Model, TimestampMixin, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    tags = db.Column(db.Text, nullable=True)  # JSON string
    seo_title = db.Column(db.String(100), nullable=True)
    seo_description = db.Column(db.Text, nullable=True)
    slug = db.Column(db.String(100), unique=True, nullable=True)

    __table_args__ = (
        Index('idx_article_published', 'is_published', 'is_deleted'),
        Index('idx_article_featured', 'is_featured'),
    )

    def set_tags(self, tags_list):
        self.tags = json.dumps(tags_list)
    
    def get_tags(self):
        if self.tags:
            return json.loads(self.tags)
        return []

    def increment_view_count(self):
        self.view_count += 1

    def __repr__(self):
        return f'<Article {self.title}>'

class Appointment(db.Model, TimestampMixin, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    service_type = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.Integer, default=60)  # minutes
    status = db.Column(db.String(20), default='scheduled')  # scheduled, confirmed, completed, cancelled, no_show
    message = db.Column(db.Text)
    notes = db.Column(db.Text)  # Staff notes
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    insurance_coverage = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, partial
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancelled_by = db.Column(db.String(50), nullable=True)  # patient, staff, system

    __table_args__ = (
        Index('idx_appointment_date_status', 'date', 'status'),
        Index('idx_appointment_user', 'user_id'),
        Index('idx_appointment_status', 'status'),
    )

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()

    @validates('phone')
    def validate_phone(self, key, phone):
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValueError('Invalid phone number format')
        return phone

    def is_overdue(self):
        return self.date < date.today() and self.status == 'scheduled'

    def can_be_cancelled(self):
        # Can cancel if appointment is more than 24 hours away
        appointment_datetime = datetime.combine(self.date, self.time)
        return appointment_datetime > datetime.now() + timedelta(hours=24)

    def __repr__(self):
        return f'<Appointment {self.name} {self.date}>'

class MedicalRecord(db.Model, TimestampMixin, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)  # medical, dental, emergency
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_recorded = db.Column(db.Date, nullable=False)
    doctor_name = db.Column(db.String(100), nullable=True)
    hospital_clinic = db.Column(db.String(200), nullable=True)
    medications_prescribed = db.Column(db.Text, nullable=True)  # JSON string
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date, nullable=True)
    severity = db.Column(db.String(20), default='low')  # low, medium, high, critical
    is_confidential = db.Column(db.Boolean, default=False)
    attachments = db.Column(db.Text, nullable=True)  # JSON string of file URLs
    
    __table_args__ = (
        Index('idx_medical_record_user_type', 'user_id', 'record_type'),
        Index('idx_medical_record_date', 'date_recorded'),
    )
    
    def set_medications_prescribed(self, medications_list):
        self.medications_prescribed = json.dumps(medications_list)
    
    def get_medications_prescribed(self):
        if self.medications_prescribed:
            return json.loads(self.medications_prescribed)
        return []

    def set_attachments(self, attachment_urls):
        self.attachments = json.dumps(attachment_urls)
    
    def get_attachments(self):
        if self.attachments:
            return json.loads(self.attachments)
        return []

class DentalHistory(db.Model, TimestampMixin, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    procedure_type = db.Column(db.String(100), nullable=False)
    teeth_affected = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    x_ray_images = db.Column(db.Text, nullable=True)  # JSON string of image URLs
    treatment_plan = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    insurance_coverage = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, partial
    next_appointment = db.Column(db.Date, nullable=True)
    procedure_date = db.Column(db.Date, nullable=False)
    dentist_name = db.Column(db.String(100), nullable=True)
    complications = db.Column(db.Text, nullable=True)
    post_procedure_notes = db.Column(db.Text, nullable=True)
    
    __table_args__ = (
        Index('idx_dental_history_user', 'user_id'),
        Index('idx_dental_history_procedure', 'procedure_type'),
    )
    
    def set_x_ray_images(self, image_urls):
        self.x_ray_images = json.dumps(image_urls)
    
    def get_x_ray_images(self):
        if self.x_ray_images:
            return json.loads(self.x_ray_images)
        return []

class Service(db.Model, TimestampMixin, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # general, cosmetic, orthodontic, emergency
    duration = db.Column(db.Integer, default=60)  # minutes
    base_cost = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_popular = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(255), nullable=True)
    requirements = db.Column(db.Text, nullable=True)  # JSON string
    contraindications = db.Column(db.Text, nullable=True)  # JSON string
    
    __table_args__ = (
        Index('idx_service_category', 'category'),
        Index('idx_service_active', 'is_active'),
    )

    def set_requirements(self, requirements_list):
        self.requirements = json.dumps(requirements_list)
    
    def get_requirements(self):
        if self.requirements:
            return json.loads(self.requirements)
        return []

    def set_contraindications(self, contraindications_list):
        self.contraindications = json.dumps(contraindications_list)
    
    def get_contraindications(self):
        if self.contraindications:
            return json.loads(self.contraindications)
        return []

class Insurance(db.Model, TimestampMixin, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    provider_name = db.Column(db.String(100), nullable=False)
    plan_name = db.Column(db.String(100), nullable=False)
    coverage_percentage = db.Column(db.Float, nullable=True)
    annual_limit = db.Column(db.Float, nullable=True)
    deductible = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    contact_info = db.Column(db.Text, nullable=True)  # JSON string
    accepted_services = db.Column(db.Text, nullable=True)  # JSON string
    
    __table_args__ = (
        Index('idx_insurance_provider', 'provider_name'),
        Index('idx_insurance_active', 'is_active'),
    )

    def set_contact_info(self, contact_dict):
        self.contact_info = json.dumps(contact_dict)
    
    def get_contact_info(self):
        if self.contact_info:
            return json.loads(self.contact_info)
        return {}

    def set_accepted_services(self, services_list):
        self.accepted_services = json.dumps(services_list)
    
    def get_accepted_services(self):
        if self.accepted_services:
            return json.loads(self.accepted_services)
        return []

class Notification(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # appointment, reminder, general, system
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    action_url = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_expires', 'expires_at'),
    )

    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()

    def is_expired(self):
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

class AuditLog(db.Model, TimestampMixin):
    """Audit trail for important actions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(db.Text, nullable=True)  # JSON string
    new_values = db.Column(db.Text, nullable=True)  # JSON string
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_table_record', 'table_name', 'record_id'),
        Index('idx_audit_timestamp', 'created_at'),
    )

    def set_old_values(self, values_dict):
        self.old_values = json.dumps(values_dict)
    
    def get_old_values(self):
        if self.old_values:
            return json.loads(self.old_values)
        return {}

    def set_new_values(self, values_dict):
        self.new_values = json.dumps(values_dict)
    
    def get_new_values(self):
        if self.new_values:
            return json.loads(self.new_values)
        return {}

# Import timedelta for token expiry
from datetime import timedelta

# Event listeners for audit logging
@event.listens_for(User, 'after_update')
def log_user_changes(mapper, connection, target):
    """Log user changes to audit trail"""
    if hasattr(target, '_changed_fields'):
        audit_log = AuditLog(
            user_id=target.id,
            action='update',
            table_name='user',
            record_id=target.id,
            old_values=target._changed_fields.get('old'),
            new_values=target._changed_fields.get('new')
        )
        db.session.add(audit_log)

@event.listens_for(Appointment, 'after_insert')
def log_appointment_creation(mapper, connection, target):
    """Log appointment creation"""
    audit_log = AuditLog(
        user_id=target.user_id,
        action='create',
        table_name='appointment',
        record_id=target.id,
        new_values={'appointment_id': target.id, 'date': str(target.date)}
    )
    db.session.add(audit_log) 