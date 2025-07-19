from datetime import datetime, date, timedelta
from .models import db, Appointment, User, MedicalRecord, DentalHistory, Service, Notification
import json
import re
from typing import List, Dict, Optional, Tuple
import random

class AppointmentScheduler:
    """Advanced appointment scheduling system"""
    
    def __init__(self):
        self.working_hours = {
            'monday': {'start': '09:00', 'end': '17:00'},
            'tuesday': {'start': '09:00', 'end': '17:00'},
            'wednesday': {'start': '09:00', 'end': '17:00'},
            'thursday': {'start': '09:00', 'end': '17:00'},
            'friday': {'start': '09:00', 'end': '17:00'},
            'saturday': {'start': '09:00', 'end': '14:00'},
            'sunday': {'start': None, 'end': None}
        }
        self.appointment_durations = {
            'checkup': 30,
            'cleaning': 60,
            'filling': 45,
            'extraction': 60,
            'whitening': 90,
            'consultation': 30,
            'emergency': 60
        }
    
    def get_available_slots(self, target_date: date, service_type: str = 'checkup') -> List[str]:
        """Get available time slots for a specific date and service"""
        duration = self.appointment_durations.get(service_type, 60)
        day_name = target_date.strftime('%A').lower()
        
        if day_name not in self.working_hours or not self.working_hours[day_name]['start']:
            return []
        
        start_time = datetime.strptime(self.working_hours[day_name]['start'], '%H:%M')
        end_time = datetime.strptime(self.working_hours[day_name]['end'], '%H:%M')
        
        # Get existing appointments for this date
        existing_appointments = Appointment.query.filter_by(date=target_date).all()
        booked_times = []
        
        for apt in existing_appointments:
            apt_start = apt.time
            apt_end = (datetime.combine(date.today(), apt.time) + 
                      timedelta(minutes=apt.duration or 60)).time()
            booked_times.append((apt_start, apt_end))
        
        # Generate available slots
        available_slots = []
        current_time = start_time
        
        while current_time + timedelta(minutes=duration) <= end_time:
            slot_start = current_time.time()
            slot_end = (current_time + timedelta(minutes=duration)).time()
            
            # Check if slot conflicts with existing appointments
            is_available = True
            for booked_start, booked_end in booked_times:
                if (slot_start < booked_end and slot_end > booked_start):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(slot_start.strftime('%H:%M'))
            
            current_time += timedelta(minutes=30)  # 30-minute intervals
        
        return available_slots
    
    def book_appointment(self, user_id: int, service_type: str, appointment_date: date, 
                        appointment_time: str, notes: str = None) -> Tuple[bool, str]:
        """Book an appointment with conflict checking"""
        # Check if slot is still available
        available_slots = self.get_available_slots(appointment_date, service_type)
        if appointment_time not in available_slots:
            return False, "Selected time slot is no longer available"
        
        # Create appointment
        try:
            appointment = Appointment(
                user_id=user_id,
                service_type=service_type,
                date=appointment_date,
                time=datetime.strptime(appointment_time, '%H:%M').time(),
                duration=self.appointment_durations.get(service_type, 60),
                notes=notes,
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.commit()
            
            # Create notification
            self.create_appointment_notification(appointment)
            
            return True, "Appointment booked successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error booking appointment: {str(e)}"
    
    def create_appointment_notification(self, appointment: Appointment):
        """Create notification for new appointment"""
        user = User.query.get(appointment.user_id)
        if user:
            notification = Notification(
                user_id=appointment.user_id,
                title="Appointment Confirmed",
                message=f"Your {appointment.service_type} appointment is scheduled for "
                       f"{appointment.date.strftime('%B %d, %Y')} at {appointment.time.strftime('%I:%M %p')}",
                notification_type='appointment'
            )
            db.session.add(notification)
            db.session.commit()

class DentalAnalytics:
    """Analytics and reporting system for dental clinic"""
    
    @staticmethod
    def get_clinic_statistics() -> Dict:
        """Get comprehensive clinic statistics"""
        total_users = User.query.count()
        total_appointments = Appointment.query.count()
        completed_appointments = Appointment.query.filter_by(status='completed').count()
        pending_appointments = Appointment.query.filter_by(status='scheduled').count()
        
        # Monthly statistics
        current_month = date.today().replace(day=1)
        monthly_appointments = Appointment.query.filter(
            Appointment.date >= current_month
        ).count()
        
        # Revenue calculation (simplified)
        total_revenue = DentalHistory.query.with_entities(
            db.func.sum(DentalHistory.cost)
        ).scalar() or 0
        
        return {
            'total_users': total_users,
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'pending_appointments': pending_appointments,
            'monthly_appointments': monthly_appointments,
            'total_revenue': total_revenue,
            'completion_rate': (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
        }
    
    @staticmethod
    def get_user_statistics(user_id: int) -> Dict:
        """Get statistics for a specific user"""
        user_appointments = Appointment.query.filter_by(user_id=user_id).all()
        completed_appointments = [apt for apt in user_appointments if apt.status == 'completed']
        
        # Calculate total spent
        dental_history = DentalHistory.query.filter_by(user_id=user_id).all()
        total_spent = sum(record.cost or 0 for record in dental_history)
        
        # Get most common procedures
        procedures = [record.procedure_type for record in dental_history]
        procedure_counts = {}
        for procedure in procedures:
            procedure_counts[procedure] = procedure_counts.get(procedure, 0) + 1
        
        most_common_procedure = max(procedure_counts.items(), key=lambda x: x[1])[0] if procedure_counts else None
        
        return {
            'total_appointments': len(user_appointments),
            'completed_appointments': len(completed_appointments),
            'total_spent': total_spent,
            'most_common_procedure': most_common_procedure,
            'last_appointment': max(user_appointments, key=lambda x: x.date).date if user_appointments else None
        }
    
    @staticmethod
    def get_service_popularity() -> List[Dict]:
        """Get service popularity statistics"""
        services = Service.query.all()
        service_stats = []
        
        for service in services:
            appointment_count = Appointment.query.filter_by(service_type=service.name).count()
            service_stats.append({
                'service_name': service.name,
                'appointment_count': appointment_count,
                'category': service.category
            })
        
        return sorted(service_stats, key=lambda x: x['appointment_count'], reverse=True)

class MedicalRecordManager:
    """Manage medical records and health tracking"""
    
    @staticmethod
    def add_medical_record(user_id: int, record_type: str, title: str, description: str,
                          date_recorded: date, doctor_name: str = None, 
                          hospital_clinic: str = None, medications: List[str] = None) -> bool:
        """Add a new medical record"""
        try:
            record = MedicalRecord(
                user_id=user_id,
                record_type=record_type,
                title=title,
                description=description,
                date_recorded=date_recorded,
                doctor_name=doctor_name,
                hospital_clinic=hospital_clinic
            )
            
            if medications:
                record.set_medications_prescribed(medications)
            
            db.session.add(record)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_medical_summary(user_id: int) -> Dict:
        """Get a summary of user's medical history"""
        records = MedicalRecord.query.filter_by(user_id=user_id).order_by(
            MedicalRecord.date_recorded.desc()
        ).all()
        
        dental_records = DentalHistory.query.filter_by(user_id=user_id).order_by(
            DentalHistory.created_at.desc()
        ).all()
        
        # Analyze medical conditions
        conditions = []
        for record in records:
            if record.record_type == 'medical':
                conditions.append(record.title)
        
        # Get recent procedures
        recent_procedures = [record.procedure_type for record in dental_records[:5]]
        
        # Calculate health score (simplified)
        health_score = 100
        if len(conditions) > 3:
            health_score -= 20
        if len(dental_records) > 10:
            health_score -= 10
        
        return {
            'total_medical_records': len(records),
            'total_dental_procedures': len(dental_records),
            'medical_conditions': conditions,
            'recent_procedures': recent_procedures,
            'health_score': max(health_score, 0),
            'last_medical_record': records[0].date_recorded if records else None,
            'last_dental_procedure': dental_records[0].created_at if dental_records else None
        }

class ReminderSystem:
    """Automated reminder system for appointments and follow-ups"""
    
    @staticmethod
    def send_appointment_reminders():
        """Send reminders for upcoming appointments"""
        tomorrow = date.today() + timedelta(days=1)
        upcoming_appointments = Appointment.query.filter_by(
            date=tomorrow,
            status='scheduled',
            reminder_sent=False
        ).all()
        
        for appointment in upcoming_appointments:
            user = User.query.get(appointment.user_id)
            if user:
                notification = Notification(
                    user_id=appointment.user_id,
                    title="Appointment Reminder",
                    message=f"Reminder: You have a {appointment.service_type} appointment tomorrow "
                           f"at {appointment.time.strftime('%I:%M %p')}",
                    notification_type='reminder'
                )
                db.session.add(notification)
                appointment.reminder_sent = True
        
        db.session.commit()
    
    @staticmethod
    def send_follow_up_reminders():
        """Send follow-up reminders for completed procedures"""
        # Find appointments completed 6 months ago that need follow-up
        six_months_ago = date.today() - timedelta(days=180)
        completed_appointments = Appointment.query.filter(
            Appointment.date == six_months_ago,
            Appointment.status == 'completed'
        ).all()
        
        for appointment in completed_appointments:
            user = User.query.get(appointment.user_id)
            if user:
                notification = Notification(
                    user_id=appointment.user_id,
                    title="Follow-up Reminder",
                    message=f"It's been 6 months since your {appointment.service_type}. "
                           f"Consider scheduling a follow-up appointment.",
                    notification_type='reminder'
                )
                db.session.add(notification)
        
        db.session.commit()

class DataExporter:
    """Export data for reporting and analysis"""
    
    @staticmethod
    def export_user_data(user_id: int) -> Dict:
        """Export all user data for portability"""
        user = User.query.get(user_id)
        if not user:
            return {}
        
        appointments = Appointment.query.filter_by(user_id=user_id).all()
        medical_records = MedicalRecord.query.filter_by(user_id=user_id).all()
        dental_history = DentalHistory.query.filter_by(user_id=user_id).all()
        
        return {
            'user_info': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'address': user.address,
                'emergency_contact': user.emergency_contact,
                'emergency_phone': user.emergency_phone,
                'medical_conditions': user.get_medical_conditions(),
                'allergies': user.get_allergies(),
                'medications': user.get_medications(),
                'insurance_provider': user.insurance_provider,
                'insurance_number': user.insurance_number,
                'created_at': user.created_at.isoformat()
            },
            'appointments': [
                {
                    'date': apt.date.isoformat(),
                    'time': apt.time.strftime('%H:%M'),
                    'service_type': apt.service_type,
                    'status': apt.status,
                    'notes': apt.notes
                } for apt in appointments
            ],
            'medical_records': [
                {
                    'record_type': record.record_type,
                    'title': record.title,
                    'description': record.description,
                    'date_recorded': record.date_recorded.isoformat(),
                    'doctor_name': record.doctor_name,
                    'hospital_clinic': record.hospital_clinic,
                    'medications_prescribed': record.get_medications_prescribed()
                } for record in medical_records
            ],
            'dental_history': [
                {
                    'procedure_type': record.procedure_type,
                    'teeth_affected': record.teeth_affected,
                    'description': record.description,
                    'cost': record.cost,
                    'payment_status': record.payment_status,
                    'created_at': record.created_at.isoformat()
                } for record in dental_history
            ]
        }
    
    @staticmethod
    def generate_monthly_report(month: int, year: int) -> Dict:
        """Generate monthly clinic report"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        appointments = Appointment.query.filter(
            Appointment.date >= start_date,
            Appointment.date < end_date
        ).all()
        
        new_users = User.query.filter(
            User.created_at >= start_date,
            User.created_at < end_date
        ).count()
        
        revenue = DentalHistory.query.filter(
            DentalHistory.created_at >= start_date,
            DentalHistory.created_at < end_date
        ).with_entities(db.func.sum(DentalHistory.cost)).scalar() or 0
        
        return {
            'month': month,
            'year': year,
            'total_appointments': len(appointments),
            'new_users': new_users,
            'total_revenue': revenue,
            'appointments_by_status': {
                'scheduled': len([apt for apt in appointments if apt.status == 'scheduled']),
                'completed': len([apt for apt in appointments if apt.status == 'completed']),
                'cancelled': len([apt for apt in appointments if apt.status == 'cancelled'])
            }
        }

class HealthRecommendations:
    """AI-powered health recommendations based on user data"""
    
    @staticmethod
    def get_dental_recommendations(user_id: int) -> List[str]:
        """Get personalized dental health recommendations"""
        user = User.query.get(user_id)
        if not user:
            return []
        
        recommendations = []
        
        # Check appointment frequency
        recent_appointments = Appointment.query.filter(
            Appointment.user_id == user_id,
            Appointment.date >= date.today() - timedelta(days=365)
        ).count()
        
        if recent_appointments < 2:
            recommendations.append("Consider scheduling regular dental checkups (recommended every 6 months)")
        
        # Check for specific procedures
        dental_history = DentalHistory.query.filter_by(user_id=user_id).all()
        procedures = [record.procedure_type for record in dental_history]
        
        if 'filling' in procedures:
            recommendations.append("Since you've had fillings, maintain good oral hygiene to prevent further decay")
        
        if 'whitening' in procedures:
            recommendations.append("Avoid staining foods and drinks to maintain your whitening results")
        
        # Age-based recommendations
        if user.date_of_birth:
            age = user.get_age()
            if age and age > 50:
                recommendations.append("Consider more frequent dental visits as oral health needs change with age")
        
        return recommendations
    
    @staticmethod
    def get_health_tips() -> List[str]:
        """Get general dental health tips"""
        tips = [
            "Brush your teeth twice daily with fluoride toothpaste",
            "Floss daily to remove plaque between teeth",
            "Limit sugary foods and drinks",
            "Drink plenty of water throughout the day",
            "Replace your toothbrush every 3-4 months",
            "Use mouthwash for additional protection",
            "Schedule regular dental checkups",
            "Consider using an electric toothbrush for better cleaning",
            "Avoid smoking and excessive alcohol consumption",
            "Eat a balanced diet rich in calcium and vitamins"
        ]
        return random.sample(tips, 5)  # Return 5 random tips

# Initialize global instances
scheduler = AppointmentScheduler()
analytics = DentalAnalytics()
record_manager = MedicalRecordManager()
reminder_system = ReminderSystem()
data_exporter = DataExporter()
health_recommendations = HealthRecommendations() 