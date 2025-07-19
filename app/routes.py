from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from .models import db, Article, User, Appointment, MedicalRecord, DentalHistory, Service, Insurance, Notification
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
import re
import json
from werkzeug.security import generate_password_hash
import uuid
from .utils import scheduler, analytics, record_manager, reminder_system, data_exporter, health_recommendations
from .data_processor import data_processor

bp = Blueprint('main', __name__)

# Utility functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def create_notification(user_id, title, message, notification_type='general'):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type
    )
    db.session.add(notification)
    db.session.commit()

# Advanced Analytics Routes
@bp.route('/admin/advanced-analytics')
@login_required
def advanced_analytics():
    """Advanced analytics dashboard with data processing"""
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    # Get comprehensive analytics
    appointment_trends = data_processor.get_appointment_trends()
    demographics = data_processor.analyze_user_demographics()
    service_analysis = data_processor.service_analysis()
    demand_prediction = data_processor.predict_appointment_demand()
    health_insights = data_processor.generate_health_insights()
    
    return render_template('advanced_analytics.html',
                         appointment_trends=appointment_trends,
                         demographics=demographics,
                         service_analysis=service_analysis,
                         demand_prediction=demand_prediction,
                         health_insights=health_insights)

@bp.route('/api/analytics/trends')
@login_required
def get_analytics_trends():
    """Get appointment trends data for charts"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    days = request.args.get('days', 30, type=int)
    trends = data_processor.get_appointment_trends(days)
    return jsonify(trends)

@bp.route('/api/analytics/demographics')
@login_required
def get_analytics_demographics():
    """Get demographics data"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    demographics = data_processor.analyze_user_demographics()
    return jsonify(demographics)

@bp.route('/api/analytics/services')
@login_required
def get_analytics_services():
    """Get service analysis data"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    service_analysis = data_processor.service_analysis()
    return jsonify(service_analysis)

@bp.route('/api/analytics/predictions')
@login_required
def get_analytics_predictions():
    """Get demand predictions"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    days_ahead = request.args.get('days', 30, type=int)
    predictions = data_processor.predict_appointment_demand(days_ahead)
    return jsonify(predictions)

@bp.route('/api/analytics/health-insights')
@login_required
def get_health_insights():
    """Get health insights data"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    insights = data_processor.generate_health_insights()
    return jsonify(insights)

@bp.route('/admin/export-report')
@login_required
def export_comprehensive_report():
    """Export comprehensive report as Excel"""
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    try:
        # Generate comprehensive report
        report_data = data_processor.create_performance_report()
        
        # Export to Excel
        excel_file = data_processor.export_to_excel(report_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clinic_report_{timestamp}.xlsx"
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('main.advanced_analytics'))

@bp.route('/api/visualization/<data_type>')
@login_required
def get_visualization(data_type):
    """Get data visualization as base64 image"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        if data_type == 'appointment_trends':
            data = data_processor.get_appointment_trends()
            image_data = data_processor.create_visualization('appointment_trends', data)
        elif data_type == 'service_popularity':
            service_analysis = data_processor.service_analysis()
            popularity_data = {name: stats['total_appointments'] for name, stats in service_analysis['service_statistics'].items()}
            image_data = data_processor.create_visualization('service_popularity', popularity_data)
        elif data_type == 'age_distribution':
            demographics = data_processor.analyze_user_demographics()
            image_data = data_processor.create_visualization('age_distribution', demographics['age_distribution'])
        else:
            return jsonify({'error': 'Invalid visualization type'}), 400
        
        return jsonify({'image': image_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/admin/performance-report')
@login_required
def performance_report():
    """Detailed performance report page"""
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    # Generate comprehensive report
    report_data = data_processor.create_performance_report()
    
    return render_template('performance_report.html', report=report_data)

@bp.route('/api/analytics/recommendations')
@login_required
def get_business_recommendations():
    """Get AI-generated business recommendations"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    recommendations = data_processor.generate_recommendations()
    return jsonify({'recommendations': recommendations})

# New API routes for advanced functionality
@bp.route('/api/available-slots')
@login_required
def get_available_slots():
    """Get available appointment slots for a specific date and service"""
    target_date_str = request.args.get('date')
    service_type = request.args.get('service_type', 'checkup')
    
    if not target_date_str:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        available_slots = scheduler.get_available_slots(target_date, service_type)
        return jsonify({'available_slots': available_slots})
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@bp.route('/api/book-appointment', methods=['POST'])
@login_required
def book_appointment_api():
    """Book an appointment via API"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    service_type = data.get('service_type')
    appointment_date_str = data.get('date')
    appointment_time = data.get('time')
    notes = data.get('notes')
    
    if not all([service_type, appointment_date_str, appointment_time]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        success, message = scheduler.book_appointment(
            current_user.id, service_type, appointment_date, appointment_time, notes
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@bp.route('/api/user-analytics')
@login_required
def get_user_analytics():
    """Get analytics for the current user"""
    user_stats = analytics.get_user_statistics(current_user.id)
    health_summary = record_manager.get_medical_summary(current_user.id)
    recommendations = health_recommendations.get_dental_recommendations(current_user.id)
    health_tips = health_recommendations.get_health_tips()
    
    return jsonify({
        'user_statistics': user_stats,
        'health_summary': health_summary,
        'recommendations': recommendations,
        'health_tips': health_tips
    })

@bp.route('/api/clinic-analytics')
@login_required
def get_clinic_analytics():
    """Get clinic-wide analytics (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    clinic_stats = analytics.get_clinic_statistics()
    service_popularity = analytics.get_service_popularity()
    
    return jsonify({
        'clinic_statistics': clinic_stats,
        'service_popularity': service_popularity
    })

@bp.route('/export-user-data')
@login_required
def export_user_data():
    """Export user's data as JSON"""
    user_data = data_exporter.export_user_data(current_user.id)
    
    # Create a JSON file for download
    filename = f"user_data_{current_user.username}_{date.today().isoformat()}.json"
    
    response = jsonify(user_data)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'application/json'
    
    return response

@bp.route('/api/add-medical-record', methods=['POST'])
@login_required
def add_medical_record_api():
    """Add a medical record via API"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['record_type', 'title', 'description', 'date_recorded']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        date_recorded = datetime.strptime(data['date_recorded'], '%Y-%m-%d').date()
        success = record_manager.add_medical_record(
            user_id=current_user.id,
            record_type=data['record_type'],
            title=data['title'],
            description=data['description'],
            date_recorded=date_recorded,
            doctor_name=data.get('doctor_name'),
            hospital_clinic=data.get('hospital_clinic'),
            medications=data.get('medications', [])
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Medical record added successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to add medical record'}), 500
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@bp.route('/smart-appointment-scheduler')
@login_required
def smart_appointment_scheduler():
    """Smart appointment scheduling page"""
    # Get user's preferences and history
    user_stats = analytics.get_user_statistics(current_user.id)
    recommendations = health_recommendations.get_dental_recommendations(current_user.id)
    
    # Get available dates for next 30 days
    available_dates = []
    for i in range(1, 31):
        check_date = date.today() + timedelta(days=i)
        if scheduler.get_available_slots(check_date):
            available_dates.append(check_date)
    
    return render_template('smart_scheduler.html', 
                         user_stats=user_stats,
                         recommendations=recommendations,
                         available_dates=available_dates[:10])  # Show next 10 available dates

@bp.route('/health-dashboard')
@login_required
def health_dashboard():
    """Personal health dashboard"""
    user_stats = analytics.get_user_statistics(current_user.id)
    health_summary = record_manager.get_medical_summary(current_user.id)
    recommendations = health_recommendations.get_dental_recommendations(current_user.id)
    health_tips = health_recommendations.get_health_tips()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        user_id=current_user.id,
        status='scheduled'
    ).filter(Appointment.date >= date.today()).order_by(Appointment.date, Appointment.time).limit(5).all()
    
    return render_template('health_dashboard.html',
                         user_stats=user_stats,
                         health_summary=health_summary,
                         recommendations=recommendations,
                         health_tips=health_tips,
                         upcoming_appointments=upcoming_appointments)

@bp.route('/admin/analytics-dashboard')
@login_required
def admin_analytics_dashboard():
    """Admin analytics dashboard"""
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    clinic_stats = analytics.get_clinic_statistics()
    service_popularity = analytics.get_service_popularity()
    
    # Get monthly reports for the last 6 months
    monthly_reports = []
    for i in range(6):
        report_date = date.today() - timedelta(days=30*i)
        monthly_report = data_exporter.generate_monthly_report(
            report_date.month, report_date.year
        )
        monthly_reports.append(monthly_report)
    
    return render_template('admin_analytics.html',
                         clinic_stats=clinic_stats,
                         service_popularity=service_popularity,
                         monthly_reports=monthly_reports)

@bp.route('/admin/send-reminders')
@login_required
def admin_send_reminders():
    """Admin function to send reminders"""
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    try:
        reminder_system.send_appointment_reminders()
        reminder_system.send_follow_up_reminders()
        flash('Reminders sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending reminders: {str(e)}', 'error')
    
    return redirect(url_for('main.admin_analytics_dashboard'))

@bp.route('/api/search-services')
def search_services():
    """Search for dental services"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({'services': []})
    
    # Search in services table
    services = Service.query.filter(
        Service.name.ilike(f'%{query}%') | 
        Service.description.ilike(f'%{query}%')
    ).limit(10).all()
    
    service_list = []
    for service in services:
        service_list.append({
            'id': service.id,
            'name': service.name,
            'description': service.description,
            'category': service.category,
            'duration': service.duration,
            'base_cost': service.base_cost
        })
    
    return jsonify({'services': service_list})

@bp.route('/api/health-score')
@login_required
def get_health_score():
    """Get user's health score"""
    health_summary = record_manager.get_medical_summary(current_user.id)
    return jsonify({'health_score': health_summary['health_score']})

@bp.route('/api/appointment-suggestions')
@login_required
def get_appointment_suggestions():
    """Get smart appointment suggestions based on user history"""
    user_stats = analytics.get_user_statistics(current_user.id)
    recommendations = health_recommendations.get_dental_recommendations(current_user.id)
    
    # Suggest next appointment based on last appointment
    suggestions = []
    
    if user_stats['last_appointment']:
        days_since_last = (date.today() - user_stats['last_appointment']).days
        
        if days_since_last > 180:  # More than 6 months
            suggestions.append({
                'type': 'checkup',
                'priority': 'high',
                'reason': 'Regular checkup overdue',
                'recommended_date': date.today() + timedelta(days=7)
            })
        elif days_since_last > 90:  # More than 3 months
            suggestions.append({
                'type': 'cleaning',
                'priority': 'medium',
                'reason': 'Time for dental cleaning',
                'recommended_date': date.today() + timedelta(days=14)
            })
    
    # Add recommendations based on medical history
    for recommendation in recommendations:
        suggestions.append({
            'type': 'consultation',
            'priority': 'medium',
            'reason': recommendation,
            'recommended_date': date.today() + timedelta(days=30)
        })
    
    return jsonify({'suggestions': suggestions})

# Keep existing routes
@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/navigation-guide')
def navigation_guide():
    """Comprehensive navigation guide for all site features"""
    return render_template('navigation_guide.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form_data = {
        'username': '', 'email': '', 'first_name': '', 'last_name': '', 'phone': '',
        'date_of_birth': '', 'address': '', 'emergency_contact': '', 'emergency_phone': ''
    }
    if request.method == 'POST':
        # Get form data
        for field in form_data:
            form_data[field] = request.form.get(field, '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        # Validation
        errors = []
        if not all([form_data['username'], form_data['email'], password, form_data['first_name'], form_data['last_name']]):
            errors.append("All required fields must be filled")
        if form_data['email'] and not validate_email(form_data['email']):
            errors.append("Please enter a valid email address")
        if form_data['phone'] and not validate_phone(form_data['phone']):
            errors.append("Please enter a valid phone number")
        if password:
            is_valid, message = validate_password(password)
            if not is_valid:
                errors.append(message)
        if password != confirm_password:
            errors.append("Passwords do not match")
        if User.query.filter_by(username=form_data['username']).first():
            errors.append("Username already exists")
        if User.query.filter_by(email=form_data['email']).first():
            errors.append("Email already registered")
        dob = None
        if form_data['date_of_birth']:
            try:
                dob = datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid date of birth format")
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html', form_data=form_data)
        try:
            user = User(
                username=form_data['username'],
                email=form_data['email'],
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                phone=form_data['phone'] if form_data['phone'] else None,
                date_of_birth=dob,
                address=form_data['address'] if form_data['address'] else None,
                emergency_contact=form_data['emergency_contact'] if form_data['emergency_contact'] else None,
                emergency_phone=form_data['emergency_phone'] if form_data['emergency_phone'] else None
            )
            user.set_password(password)
            user.generate_verification_token()
            db.session.add(user)
            db.session.commit()
            create_notification(
                user.id,
                "Welcome to BrightSmile!",
                f"Thank you for registering, {form_data['first_name']}! Please verify your email to complete your registration.",
                'general'
            )
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html', form_data=form_data)
    return render_template('register.html', form_data=form_data)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form_data = {'username': ''}
    if request.method == 'POST':
        form_data['username'] = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        if not form_data['username'] or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html', form_data=form_data)
        user = User.query.filter(
            (User.username == form_data['username']) | (User.email == form_data['username'])
        ).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('login.html', form_data=form_data)
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            create_notification(
                user.id,
                "Login Successful",
                f"Welcome back, {user.first_name}! You successfully logged in.",
                'general'
            )
            flash(f'Welcome back, {user.first_name}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username/email or password', 'error')
            return render_template('login.html', form_data=form_data)
    return render_template('login.html', form_data=form_data)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('main.home'))

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        user_id=current_user.id,
        status='scheduled'
    ).filter(Appointment.date >= date.today()).order_by(Appointment.date, Appointment.time).limit(5).all()
    
    # Get recent medical records
    recent_medical_records = MedicalRecord.query.filter_by(
        user_id=current_user.id
    ).order_by(MedicalRecord.date_recorded.desc()).limit(3).all()
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get user statistics
    user_stats = analytics.get_user_statistics(current_user.id)
    health_summary = record_manager.get_medical_summary(current_user.id)
    
    return render_template('dashboard.html', 
                         upcoming_appointments=upcoming_appointments,
                         recent_medical_records=recent_medical_records,
                         unread_notifications=unread_notifications,
                         user_stats=user_stats,
                         health_summary=health_summary)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        date_of_birth = request.form.get('date_of_birth', '')
        address = request.form.get('address', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        emergency_phone = request.form.get('emergency_phone', '').strip()
        insurance_provider = request.form.get('insurance_provider', '').strip()
        insurance_number = request.form.get('insurance_number', '').strip()
        
        # Validation
        errors = []
        
        if not all([first_name, last_name, email]):
            errors.append("First name, last name, and email are required")
        
        if email and not validate_email(email):
            errors.append("Please enter a valid email address")
        
        if phone and not validate_phone(phone):
            errors.append("Please enter a valid phone number")
        
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            errors.append("Email is already registered by another user")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile.html')
        
        # Update user
        try:
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.email = email
            current_user.phone = phone if phone else None
            current_user.address = address if address else None
            current_user.emergency_contact = emergency_contact if emergency_contact else None
            current_user.emergency_phone = emergency_phone if emergency_phone else None
            current_user.insurance_provider = insurance_provider if insurance_provider else None
            current_user.insurance_number = insurance_number if insurance_number else None
            
            if date_of_birth:
                try:
                    current_user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except ValueError:
                    flash("Invalid date of birth format", 'error')
                    return render_template('profile.html')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
    
    return render_template('profile.html')

@bp.route('/medical-history', methods=['GET', 'POST'])
@login_required
def medical_history():
    if request.method == 'POST':
        # Handle medical history updates
        medical_conditions = request.form.getlist('medical_conditions')
        allergies = request.form.getlist('allergies')
        medications = request.form.getlist('medications')
        
        try:
            current_user.set_medical_conditions(medical_conditions)
            current_user.set_allergies(allergies)
            current_user.set_medications(medications)
            db.session.commit()
            flash('Medical history updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating medical history.', 'error')
    
    return render_template('medical_history.html')

@bp.route('/appointments')
@login_required
def user_appointments():
    appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(
        Appointment.date.desc(), Appointment.time.desc()
    ).all()
    return render_template('user_appointments.html', appointments=appointments)

@bp.route('/appointment/<int:appointment_id>')
@login_required
def appointment_detail(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.user_appointments'))
    return render_template('appointment_detail.html', appointment=appointment)

@bp.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).all()
    return render_template('notifications.html', notifications=notifications)

@bp.route('/mark-notification-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403

# Admin routes
@bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    # Get statistics
    total_users = User.query.count()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='scheduled').count()
    today_appointments = Appointment.query.filter_by(date=date.today()).count()
    
    # Get recent appointments
    recent_appointments = Appointment.query.order_by(
        Appointment.created_at.desc()
    ).limit(10).all()
    
    return render_template('admin.html', 
                         total_users=total_users,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments,
                         today_appointments=today_appointments,
                         recent_appointments=recent_appointments)

@bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@bp.route('/admin/appointments')
@login_required
def admin_appointments():
    if not current_user.is_admin:
        flash('Admin access required!', 'error')
        return redirect(url_for('main.home'))
    
    appointments = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return render_template('admin_appointments.html', appointments=appointments)

# API routes for AJAX requests
@bp.route('/api/user-stats')
@login_required
def user_stats():
    """Get user statistics for dashboard"""
    upcoming_appointments = Appointment.query.filter_by(
        user_id=current_user.id,
        status='scheduled'
    ).filter(Appointment.date >= date.today()).count()
    
    total_appointments = Appointment.query.filter_by(user_id=current_user.id).count()
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({
        'upcoming_appointments': upcoming_appointments,
        'total_appointments': total_appointments,
        'unread_notifications': unread_notifications
    })

# Keep existing routes
@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/services')
def services():
    return render_template('services.html')

@bp.route('/appointment')
def appointment():
    return render_template('appointment.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/team')
def team():
    return render_template('team.html')

@bp.route('/news')
def news():
    return render_template('news.html')

@bp.route('/create-admin')
def create_admin():
    if User.query.filter_by(username='admin').first():
        return 'Admin user already exists!'
    
    admin = User(
        username='admin',
        email='admin@brightsmile.com',
        first_name='Admin',
        last_name='User',
        is_admin=True,
        email_verified=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    return 'Admin user created! Username: admin, Password: admin123' 