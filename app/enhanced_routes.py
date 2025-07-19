from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file, current_app
from .models import db, Article, User, Appointment, MedicalRecord, DentalHistory, Service, Insurance, Notification, AuditLog
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
import re
import json
from werkzeug.security import generate_password_hash
import uuid
from .utils import scheduler, analytics, record_manager, reminder_system, data_exporter, health_recommendations
from .data_processor import data_processor
from .advanced_analytics import advanced_analytics
from .realtime_service import get_realtime_service
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('enhanced', __name__)

# Rate limiting decorator
def rate_limit(limit=100, window=3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = f"rate_limit:{request.remote_addr}:{f.__name__}"
            current = current_app.cache.get(key) or 0
            
            if current >= limit:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            current_app.cache.set(key, current + 1, timeout=window)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Cache decorator
def cache_response(timeout=300):
    """Cache response decorator"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            cache_key = f"cache:{f.__name__}:{request.args.get('cache_key', 'default')}"
            cached = current_app.cache.get(cache_key)
            
            if cached:
                return cached
            
            result = f(*args, **kwargs)
            current_app.cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapped
    return decorator

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required!', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

# Enhanced validation functions
def validate_email(email):
    """Enhanced email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Enhanced phone validation"""
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """Enhanced password validation"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"

def create_notification(user_id, title, message, notification_type='general', priority='normal', action_url=None):
    """Create notification with enhanced features"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url
        )
        db.session.add(notification)
        db.session.commit()
        
        # Send real-time notification
        realtime_service = get_realtime_service()
        if realtime_service:
            realtime_service.send_notification(user_id, title, message, notification_type, priority, action_url)
        
        logger.info(f"Notification created for user {user_id}: {title}")
        return True
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        return False

# Enhanced Dashboard Route
@bp.route('/enhanced-dashboard')
@login_required
@cache_response(timeout=60)
def enhanced_dashboard():
    """Enhanced dashboard with real-time data and ML insights"""
    try:
        # Get user statistics
        user_appointments = Appointment.query.filter_by(
            user_id=current_user.id,
            is_deleted=False
        ).all()
        
        total_appointments = len(user_appointments)
        upcoming_appointments = len([apt for apt in user_appointments 
                                   if apt.date >= date.today() and apt.status == 'scheduled'])
        completed_appointments = len([apt for apt in user_appointments 
                                    if apt.status == 'completed'])
        
        # Calculate health score using ML
        health_score = calculate_health_score(current_user.id)
        
        # Get recent activities
        recent_activities = get_recent_activities(current_user.id)
        
        # Get unread notifications
        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        # Get upcoming appointments
        upcoming = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            Appointment.date >= date.today(),
            Appointment.status == 'scheduled',
            Appointment.is_deleted == False
        ).order_by(Appointment.date, Appointment.time).limit(5).all()
        
        stats = {
            'total_appointments': total_appointments,
            'upcoming_appointments': upcoming_appointments,
            'completed_appointments': completed_appointments,
            'health_score': health_score
        }
        
        return render_template('dashboard.html',
                             stats=stats,
                             upcoming_appointments=upcoming,
                             recent_activities=recent_activities,
                             unread_notifications=unread_notifications)
    
    except Exception as e:
        logger.error(f"Error in enhanced dashboard: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return redirect(url_for('main.home'))

def calculate_health_score(user_id):
    """Calculate health score using ML algorithms"""
    try:
        # Get user's medical records and appointments
        medical_records = MedicalRecord.query.filter_by(user_id=user_id).all()
        appointments = Appointment.query.filter_by(user_id=user_id).all()
        
        # Base score
        score = 80
        
        # Factors affecting score
        completed_appointments = len([apt for apt in appointments if apt.status == 'completed'])
        cancelled_appointments = len([apt for apt in appointments if apt.status == 'cancelled'])
        
        # Appointment completion rate
        if completed_appointments > 0:
            completion_rate = completed_appointments / (completed_appointments + cancelled_appointments)
            score += completion_rate * 10
        
        # Recent activity bonus
        recent_appointments = [apt for apt in appointments 
                             if apt.date >= date.today() - timedelta(days=90)]
        if recent_appointments:
            score += 5
        
        # Medical conditions penalty
        for record in medical_records:
            if record.severity == 'high':
                score -= 5
            elif record.severity == 'medium':
                score -= 3
            elif record.severity == 'low':
                score -= 1
        
        return max(0, min(100, round(score)))
    
    except Exception as e:
        logger.error(f"Error calculating health score: {str(e)}")
        return 75  # Default score

def get_recent_activities(user_id, limit=10):
    """Get recent user activities"""
    try:
        activities = []
        
        # Get recent appointments
        recent_appointments = Appointment.query.filter_by(
            user_id=user_id
        ).order_by(Appointment.created_at.desc()).limit(5).all()
        
        for apt in recent_appointments:
            activities.append({
                'type': 'appointment',
                'icon': 'calendar',
                'title': f'Appointment {apt.status}',
                'timestamp': apt.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        # Get recent medical records
        recent_records = MedicalRecord.query.filter_by(
            user_id=user_id
        ).order_by(MedicalRecord.created_at.desc()).limit(5).all()
        
        for record in recent_records:
            activities.append({
                'type': 'medical',
                'icon': 'notes-medical',
                'title': f'Medical record: {record.title}',
                'timestamp': record.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        # Sort by timestamp and return top activities
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]
    
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        return []

# Enhanced Analytics Routes
@bp.route('/enhanced-analytics')
@login_required
@admin_required
@cache_response(timeout=300)
def enhanced_analytics():
    """Enhanced analytics with ML insights"""
    try:
        # Get comprehensive analytics
        appointment_trends = advanced_analytics.get_appointment_trends()
        demographics = advanced_analytics.analyze_user_demographics()
        service_analysis = advanced_analytics.service_analysis()
        demand_prediction = advanced_analytics.predict_appointment_demand_ml()
        health_insights = advanced_analytics.generate_health_insights()
        business_insights = advanced_analytics.generate_business_insights()
        
        return render_template('advanced_analytics.html',
                             appointment_trends=appointment_trends,
                             demographics=demographics,
                             service_analysis=service_analysis,
                             demand_prediction=demand_prediction,
                             health_insights=health_insights,
                             recommendations=business_insights.get('strategic_recommendations', []))
    
    except Exception as e:
        logger.error(f"Error in enhanced analytics: {str(e)}")
        flash('Error loading analytics data', 'error')
        return redirect(url_for('main.admin'))

# Enhanced API Routes
@bp.route('/api/enhanced/user-stats')
@login_required
@rate_limit(limit=100, window=3600)
def enhanced_user_stats():
    """Enhanced user statistics API"""
    try:
        user_appointments = Appointment.query.filter_by(
            user_id=current_user.id,
            is_deleted=False
        ).all()
        
        total_appointments = len(user_appointments)
        upcoming_appointments = len([apt for apt in user_appointments 
                                   if apt.date >= date.today() and apt.status == 'scheduled'])
        completed_appointments = len([apt for apt in user_appointments 
                                    if apt.status == 'completed'])
        health_score = calculate_health_score(current_user.id)
        
        # Get recent activity
        recent_activities = get_recent_activities(current_user.id, limit=5)
        
        return jsonify({
            'total_appointments': total_appointments,
            'upcoming_appointments': upcoming_appointments,
            'completed_appointments': completed_appointments,
            'health_score': health_score,
            'recent_activities': recent_activities,
            'last_updated': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in enhanced user stats: {str(e)}")
        return jsonify({'error': 'Failed to load user statistics'}), 500

@bp.route('/api/enhanced/appointment-suggestions')
@login_required
@rate_limit(limit=50, window=3600)
def enhanced_appointment_suggestions():
    """Enhanced appointment suggestions using ML"""
    try:
        # Get user's appointment history
        user_appointments = Appointment.query.filter_by(
            user_id=current_user.id,
            is_deleted=False
        ).all()
        
        # Analyze patterns
        service_frequency = {}
        for apt in user_appointments:
            service = apt.service_type or 'general'
            service_frequency[service] = service_frequency.get(service, 0) + 1
        
        # Get most frequent service
        most_frequent = max(service_frequency.items(), key=lambda x: x[1])[0] if service_frequency else 'general'
        
        # Calculate next suggested date based on patterns
        if user_appointments:
            last_appointment = max(user_appointments, key=lambda x: x.date)
            avg_days_between = 90  # Default 3 months
            
            if len(user_appointments) > 1:
                dates = sorted([apt.date for apt in user_appointments])
                intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_days_between = sum(intervals) / len(intervals)
            
            suggested_date = last_appointment.date + timedelta(days=avg_days_between)
        else:
            suggested_date = date.today() + timedelta(days=30)
        
        # Get available services
        services = Service.query.filter_by(is_active=True).all()
        
        suggestions = []
        for service in services:
            suggestions.append({
                'service_name': service.name,
                'description': service.description,
                'duration': service.duration,
                'base_cost': service.base_cost,
                'recommended': service.name.lower() == most_frequent.lower(),
                'suggested_date': suggested_date.isoformat()
            })
        
        return jsonify({
            'suggestions': suggestions,
            'most_frequent_service': most_frequent,
            'suggested_date': suggested_date.isoformat(),
            'reasoning': f'Based on your appointment history and {avg_days_between:.0f} day average interval'
        })
    
    except Exception as e:
        logger.error(f"Error in appointment suggestions: {str(e)}")
        return jsonify({'error': 'Failed to generate suggestions'}), 500

# Enhanced Appointment Management
@bp.route('/api/enhanced/book-appointment', methods=['POST'])
@login_required
@rate_limit(limit=10, window=3600)
def enhanced_book_appointment():
    """Enhanced appointment booking with ML optimization"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        service_type = data.get('service_type')
        appointment_date_str = data.get('date')
        appointment_time = data.get('time')
        notes = data.get('notes')
        
        if not all([service_type, appointment_date_str, appointment_time]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        
        # Check for conflicts
        existing_appointment = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            Appointment.date == appointment_date,
            Appointment.status.in_(['scheduled', 'confirmed']),
            Appointment.is_deleted == False
        ).first()
        
        if existing_appointment:
            return jsonify({'error': 'You already have an appointment on this date'}), 400
        
        # Create appointment
        appointment = Appointment(
            user_id=current_user.id,
            name=current_user.full_name,
            email=current_user.email,
            phone=current_user.phone,
            date=appointment_date,
            time=datetime.strptime(appointment_time, '%H:%M').time(),
            service_type=service_type,
            message=notes,
            status='scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Create notification
        create_notification(
            user_id=current_user.id,
            title='Appointment Booked',
            message=f'Your {service_type} appointment has been scheduled for {appointment_date_str} at {appointment_time}',
            notification_type='appointment',
            priority='high',
            action_url=f'/appointment/{appointment.id}'
        )
        
        # Send real-time update
        realtime_service = get_realtime_service()
        if realtime_service:
            realtime_service.send_appointment_update(appointment.id, 'created', {
                'service_type': service_type,
                'date': appointment_date_str,
                'time': appointment_time
            })
        
        return jsonify({
            'success': True,
            'message': 'Appointment booked successfully',
            'appointment_id': appointment.id
        })
    
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return jsonify({'error': 'Failed to book appointment'}), 500

# Enhanced Health Monitoring
@bp.route('/api/enhanced/health-monitor')
@login_required
@rate_limit(limit=50, window=3600)
def enhanced_health_monitor():
    """Enhanced health monitoring with ML insights"""
    try:
        # Get user's health data
        medical_records = MedicalRecord.query.filter_by(
            user_id=current_user.id,
            is_deleted == False
        ).all()
        
        dental_history = DentalHistory.query.filter_by(
            user_id=current_user.id,
            is_deleted == False
        ).all()
        
        appointments = Appointment.query.filter_by(
            user_id=current_user.id,
            is_deleted == False
        ).all()
        
        # Calculate health metrics
        health_score = calculate_health_score(current_user.id)
        
        # Analyze trends
        recent_records = [r for r in medical_records 
                         if r.date_recorded >= date.today() - timedelta(days=365)]
        
        # Get recommendations
        recommendations = generate_health_recommendations(current_user.id)
        
        # Risk assessment
        risk_factors = assess_health_risks(current_user.id)
        
        return jsonify({
            'health_score': health_score,
            'total_medical_records': len(medical_records),
            'total_dental_procedures': len(dental_history),
            'total_appointments': len(appointments),
            'recent_activity': len(recent_records),
            'recommendations': recommendations,
            'risk_factors': risk_factors,
            'last_updated': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in health monitor: {str(e)}")
        return jsonify({'error': 'Failed to load health data'}), 500

def generate_health_recommendations(user_id):
    """Generate personalized health recommendations"""
    try:
        recommendations = []
        
        # Get user's medical conditions
        user = User.query.get(user_id)
        medical_conditions = user.get_medical_conditions() if user else []
        
        # Get recent appointments
        recent_appointments = Appointment.query.filter(
            Appointment.user_id == user_id,
            Appointment.date >= date.today() - timedelta(days=365)
        ).all()
        
        # Generate recommendations based on data
        if not recent_appointments:
            recommendations.append({
                'type': 'appointment',
                'priority': 'high',
                'message': 'Schedule your annual dental checkup',
                'action': 'book_appointment'
            })
        
        if medical_conditions:
            recommendations.append({
                'type': 'health',
                'priority': 'medium',
                'message': 'Update your medical conditions in your profile',
                'action': 'update_profile'
            })
        
        # Add general recommendations
        recommendations.append({
            'type': 'hygiene',
            'priority': 'low',
            'message': 'Maintain good oral hygiene with regular brushing and flossing',
            'action': 'none'
        })
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return []

def assess_health_risks(user_id):
    """Assess health risks based on user data"""
    try:
        risks = []
        
        # Check for overdue appointments
        overdue_appointments = Appointment.query.filter(
            Appointment.user_id == user_id,
            Appointment.date < date.today(),
            Appointment.status == 'scheduled',
            Appointment.is_deleted == False
        ).all()
        
        if overdue_appointments:
            risks.append({
                'type': 'overdue_appointments',
                'severity': 'high',
                'message': f'You have {len(overdue_appointments)} overdue appointment(s)',
                'count': len(overdue_appointments)
            })
        
        # Check for frequent cancellations
        cancelled_appointments = Appointment.query.filter(
            Appointment.user_id == user_id,
            Appointment.status == 'cancelled',
            Appointment.is_deleted == False
        ).all()
        
        if len(cancelled_appointments) > 3:
            risks.append({
                'type': 'frequent_cancellations',
                'severity': 'medium',
                'message': 'You have cancelled multiple appointments recently',
                'count': len(cancelled_appointments)
            })
        
        return risks
    
    except Exception as e:
        logger.error(f"Error assessing health risks: {str(e)}")
        return []

# Enhanced Admin Routes
@bp.route('/api/enhanced/admin/real-time-stats')
@login_required
@admin_required
@rate_limit(limit=200, window=3600)
def enhanced_admin_real_time_stats():
    """Enhanced real-time admin statistics"""
    try:
        # Get real-time data
        total_users = User.query.filter(User.is_deleted == False).count()
        active_appointments = Appointment.query.filter(
            Appointment.status == 'scheduled',
            Appointment.is_deleted == False
        ).count()
        
        # Get today's appointments
        today_appointments = Appointment.query.filter(
            Appointment.date == date.today(),
            Appointment.is_deleted == False
        ).count()
        
        # Get system health
        realtime_service = get_realtime_service()
        connected_users = realtime_service.get_connected_users_count() if realtime_service else 0
        
        # Get recent activities
        recent_activities = AuditLog.query.order_by(
            AuditLog.created_at.desc()
        ).limit(10).all()
        
        activities = []
        for activity in recent_activities:
            activities.append({
                'action': activity.action,
                'table': activity.table_name,
                'user_id': activity.user_id,
                'timestamp': activity.created_at.isoformat()
            })
        
        return jsonify({
            'total_users': total_users,
            'active_appointments': active_appointments,
            'today_appointments': today_appointments,
            'connected_users': connected_users,
            'recent_activities': activities,
            'last_updated': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in admin real-time stats: {str(e)}")
        return jsonify({'error': 'Failed to load admin statistics'}), 500

# Enhanced Export Routes
@bp.route('/api/enhanced/export/health-report')
@login_required
@rate_limit(limit=5, window=3600)
def enhanced_export_health_report():
    """Export comprehensive health report"""
    try:
        # Generate comprehensive health report
        report_data = generate_health_report(current_user.id)
        
        # Export to Excel
        excel_file = data_exporter.export_health_report(report_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"health_report_{current_user.username}_{timestamp}.xlsx"
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logger.error(f"Error exporting health report: {str(e)}")
        flash('Error generating health report', 'error')
        return redirect(url_for('main.dashboard'))

def generate_health_report(user_id):
    """Generate comprehensive health report"""
    try:
        user = User.query.get(user_id)
        medical_records = MedicalRecord.query.filter_by(user_id=user_id).all()
        dental_history = DentalHistory.query.filter_by(user_id=user_id).all()
        appointments = Appointment.query.filter_by(user_id=user_id).all()
        
        report = {
            'user_info': {
                'name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'age': user.get_age()
            },
            'medical_records': [
                {
                    'title': record.title,
                    'type': record.record_type,
                    'date': record.date_recorded.isoformat(),
                    'description': record.description,
                    'severity': record.severity
                } for record in medical_records
            ],
            'dental_history': [
                {
                    'procedure': record.procedure_type,
                    'date': record.procedure_date.isoformat(),
                    'description': record.description,
                    'cost': record.cost
                } for record in dental_history
            ],
            'appointments': [
                {
                    'date': apt.date.isoformat(),
                    'time': apt.time.isoformat(),
                    'service': apt.service_type,
                    'status': apt.status
                } for apt in appointments
            ],
            'health_score': calculate_health_score(user_id),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating health report: {str(e)}")
        return {}

# Enhanced Search Routes
@bp.route('/api/enhanced/search')
@login_required
@rate_limit(limit=100, window=3600)
def enhanced_search():
    """Enhanced search functionality"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')
        
        if not query:
            return jsonify({'results': [], 'total': 0})
        
        results = []
        
        if search_type in ['all', 'appointments']:
            # Search appointments
            appointments = Appointment.query.filter(
                Appointment.user_id == current_user.id,
                Appointment.service_type.ilike(f'%{query}%'),
                Appointment.is_deleted == False
            ).limit(10).all()
            
            for apt in appointments:
                results.append({
                    'type': 'appointment',
                    'id': apt.id,
                    'title': f'Appointment: {apt.service_type}',
                    'description': f'{apt.date.strftime("%B %d, %Y")} at {apt.time.strftime("%I:%M %p")}',
                    'status': apt.status,
                    'url': url_for('main.appointment_detail', appointment_id=apt.id)
                })
        
        if search_type in ['all', 'medical']:
            # Search medical records
            records = MedicalRecord.query.filter(
                MedicalRecord.user_id == current_user.id,
                MedicalRecord.title.ilike(f'%{query}%'),
                MedicalRecord.is_deleted == False
            ).limit(10).all()
            
            for record in records:
                results.append({
                    'type': 'medical',
                    'id': record.id,
                    'title': f'Medical Record: {record.title}',
                    'description': record.description or 'No description available',
                    'date': record.date_recorded.isoformat(),
                    'url': url_for('main.medical_history')
                })
        
        return jsonify({
            'results': results,
            'total': len(results),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Error in enhanced search: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

# Enhanced Notification Routes
@bp.route('/api/enhanced/notifications/mark-read', methods=['POST'])
@login_required
@rate_limit(limit=50, window=3600)
def enhanced_mark_notification_read():
    """Mark notification as read with real-time update"""
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return jsonify({'error': 'Notification ID required'}), 400
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.mark_as_read()
        db.session.commit()
        
        # Send real-time update
        realtime_service = get_realtime_service()
        if realtime_service:
            realtime_service.socketio.emit('notification_updated', {
                'notification_id': notification_id,
                'is_read': True
            }, room=f"user_{current_user.id}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error marking notification read: {str(e)}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

# Enhanced Profile Routes
@bp.route('/api/enhanced/profile/update', methods=['POST'])
@login_required
@rate_limit(limit=10, window=3600)
def enhanced_update_profile():
    """Enhanced profile update with validation and audit trail"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate phone
        if not validate_phone(data['phone']):
            return jsonify({'error': 'Invalid phone format'}), 400
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(
            User.email == data['email'],
            User.id != current_user.id
        ).first()
        
        if existing_user:
            return jsonify({'error': 'Email is already registered'}), 400
        
        # Store old values for audit trail
        old_values = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'email': current_user.email,
            'phone': current_user.phone
        }
        
        # Update user
        current_user.first_name = data['first_name']
        current_user.last_name = data['last_name']
        current_user.email = data['email']
        current_user.phone = data['phone']
        
        # Update optional fields
        if data.get('address'):
            current_user.address = data['address']
        if data.get('emergency_contact'):
            current_user.emergency_contact = data['emergency_contact']
        if data.get('emergency_phone'):
            current_user.emergency_phone = data['emergency_phone']
        
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='profile_update',
            table_name='user',
            record_id=current_user.id,
            old_values=json.dumps(old_values),
            new_values=json.dumps(data),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        # Create notification
        create_notification(
            user_id=current_user.id,
            title='Profile Updated',
            message='Your profile has been successfully updated',
            notification_type='system',
            priority='normal'
        )
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'email': current_user.email,
                'phone': current_user.phone
            }
        })
    
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500 