"""recreate user table with gender and failed_login_attempts

Revision ID: 22bf52dc3425
Revises: 
Create Date: 2025-07-18 00:00:40.484133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22bf52dc3425'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('insurance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('provider_name', sa.String(length=100), nullable=False),
    sa.Column('plan_name', sa.String(length=100), nullable=False),
    sa.Column('coverage_percentage', sa.Float(), nullable=True),
    sa.Column('annual_limit', sa.Float(), nullable=True),
    sa.Column('deductible', sa.Float(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('contact_info', sa.Text(), nullable=True),
    sa.Column('accepted_services', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('insurance', schema=None) as batch_op:
        batch_op.create_index('idx_insurance_active', ['is_active'], unique=False)
        batch_op.create_index('idx_insurance_provider', ['provider_name'], unique=False)

    op.create_table('service',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('base_cost', sa.Float(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_popular', sa.Boolean(), nullable=True),
    sa.Column('image_url', sa.String(length=255), nullable=True),
    sa.Column('requirements', sa.Text(), nullable=True),
    sa.Column('contraindications', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.create_index('idx_service_active', ['is_active'], unique=False)
        batch_op.create_index('idx_service_category', ['category'], unique=False)

    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('first_name', sa.String(length=50), nullable=False),
    sa.Column('last_name', sa.String(length=50), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('emergency_contact', sa.String(length=100), nullable=True),
    sa.Column('emergency_phone', sa.String(length=20), nullable=True),
    sa.Column('medical_conditions', sa.Text(), nullable=True),
    sa.Column('allergies', sa.Text(), nullable=True),
    sa.Column('medications', sa.Text(), nullable=True),
    sa.Column('insurance_provider', sa.String(length=100), nullable=True),
    sa.Column('insurance_number', sa.String(length=50), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('email_verified', sa.Boolean(), nullable=True),
    sa.Column('verification_token', sa.String(length=100), nullable=True),
    sa.Column('reset_token', sa.String(length=100), nullable=True),
    sa.Column('reset_token_expiry', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
    sa.Column('account_locked_until', sa.DateTime(), nullable=True),
    sa.Column('profile_picture', sa.String(length=255), nullable=True),
    sa.Column('preferred_language', sa.String(length=10), nullable=True),
    sa.Column('timezone', sa.String(length=50), nullable=True),
    sa.Column('gender', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('reset_token'),
    sa.UniqueConstraint('verification_token')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index('idx_user_active', ['is_active', 'is_deleted'], unique=False)
        batch_op.create_index('idx_user_email_username', ['email', 'username'], unique=False)
        batch_op.create_index('idx_user_is_admin', ['is_admin'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('appointment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('time', sa.Time(), nullable=False),
    sa.Column('service_type', sa.String(length=100), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('reminder_sent', sa.Boolean(), nullable=True),
    sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
    sa.Column('follow_up_required', sa.Boolean(), nullable=True),
    sa.Column('follow_up_date', sa.Date(), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.Column('insurance_coverage', sa.Float(), nullable=True),
    sa.Column('payment_status', sa.String(length=20), nullable=True),
    sa.Column('cancellation_reason', sa.Text(), nullable=True),
    sa.Column('cancelled_by', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('appointment', schema=None) as batch_op:
        batch_op.create_index('idx_appointment_date_status', ['date', 'status'], unique=False)
        batch_op.create_index('idx_appointment_status', ['status'], unique=False)
        batch_op.create_index('idx_appointment_user', ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_appointment_date'), ['date'], unique=False)

    op.create_table('article',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('excerpt', sa.Text(), nullable=True),
    sa.Column('image_url', sa.String(length=255), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('is_published', sa.Boolean(), nullable=True),
    sa.Column('is_featured', sa.Boolean(), nullable=True),
    sa.Column('view_count', sa.Integer(), nullable=True),
    sa.Column('tags', sa.Text(), nullable=True),
    sa.Column('seo_title', sa.String(length=100), nullable=True),
    sa.Column('seo_description', sa.Text(), nullable=True),
    sa.Column('slug', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.create_index('idx_article_featured', ['is_featured'], unique=False)
        batch_op.create_index('idx_article_published', ['is_published', 'is_deleted'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_title'), ['title'], unique=False)

    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('table_name', sa.String(length=50), nullable=False),
    sa.Column('record_id', sa.Integer(), nullable=True),
    sa.Column('old_values', sa.Text(), nullable=True),
    sa.Column('new_values', sa.Text(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.create_index('idx_audit_table_record', ['table_name', 'record_id'], unique=False)
        batch_op.create_index('idx_audit_timestamp', ['created_at'], unique=False)
        batch_op.create_index('idx_audit_user_action', ['user_id', 'action'], unique=False)

    op.create_table('medical_record',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('record_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('date_recorded', sa.Date(), nullable=False),
    sa.Column('doctor_name', sa.String(length=100), nullable=True),
    sa.Column('hospital_clinic', sa.String(length=200), nullable=True),
    sa.Column('medications_prescribed', sa.Text(), nullable=True),
    sa.Column('follow_up_required', sa.Boolean(), nullable=True),
    sa.Column('follow_up_date', sa.Date(), nullable=True),
    sa.Column('severity', sa.String(length=20), nullable=True),
    sa.Column('is_confidential', sa.Boolean(), nullable=True),
    sa.Column('attachments', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('medical_record', schema=None) as batch_op:
        batch_op.create_index('idx_medical_record_date', ['date_recorded'], unique=False)
        batch_op.create_index('idx_medical_record_user_type', ['user_id', 'record_type'], unique=False)

    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('notification_type', sa.String(length=50), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('priority', sa.String(length=20), nullable=True),
    sa.Column('action_url', sa.String(length=255), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.create_index('idx_notification_expires', ['expires_at'], unique=False)
        batch_op.create_index('idx_notification_type', ['notification_type'], unique=False)
        batch_op.create_index('idx_notification_user_read', ['user_id', 'is_read'], unique=False)

    op.create_table('dental_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=True),
    sa.Column('procedure_type', sa.String(length=100), nullable=False),
    sa.Column('teeth_affected', sa.String(length=200), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('x_ray_images', sa.Text(), nullable=True),
    sa.Column('treatment_plan', sa.Text(), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.Column('insurance_coverage', sa.Float(), nullable=True),
    sa.Column('payment_status', sa.String(length=20), nullable=True),
    sa.Column('next_appointment', sa.Date(), nullable=True),
    sa.Column('procedure_date', sa.Date(), nullable=False),
    sa.Column('dentist_name', sa.String(length=100), nullable=True),
    sa.Column('complications', sa.Text(), nullable=True),
    sa.Column('post_procedure_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('dental_history', schema=None) as batch_op:
        batch_op.create_index('idx_dental_history_procedure', ['procedure_type'], unique=False)
        batch_op.create_index('idx_dental_history_user', ['user_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dental_history', schema=None) as batch_op:
        batch_op.drop_index('idx_dental_history_user')
        batch_op.drop_index('idx_dental_history_procedure')

    op.drop_table('dental_history')
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.drop_index('idx_notification_user_read')
        batch_op.drop_index('idx_notification_type')
        batch_op.drop_index('idx_notification_expires')

    op.drop_table('notification')
    with op.batch_alter_table('medical_record', schema=None) as batch_op:
        batch_op.drop_index('idx_medical_record_user_type')
        batch_op.drop_index('idx_medical_record_date')

    op.drop_table('medical_record')
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.drop_index('idx_audit_user_action')
        batch_op.drop_index('idx_audit_timestamp')
        batch_op.drop_index('idx_audit_table_record')

    op.drop_table('audit_log')
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_article_title'))
        batch_op.drop_index('idx_article_published')
        batch_op.drop_index('idx_article_featured')

    op.drop_table('article')
    with op.batch_alter_table('appointment', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_appointment_date'))
        batch_op.drop_index('idx_appointment_user')
        batch_op.drop_index('idx_appointment_status')
        batch_op.drop_index('idx_appointment_date_status')

    op.drop_table('appointment')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))
        batch_op.drop_index('idx_user_is_admin')
        batch_op.drop_index('idx_user_email_username')
        batch_op.drop_index('idx_user_active')

    op.drop_table('user')
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.drop_index('idx_service_category')
        batch_op.drop_index('idx_service_active')

    op.drop_table('service')
    with op.batch_alter_table('insurance', schema=None) as batch_op:
        batch_op.drop_index('idx_insurance_provider')
        batch_op.drop_index('idx_insurance_active')

    op.drop_table('insurance')
    # ### end Alembic commands ###
