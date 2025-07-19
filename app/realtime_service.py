import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from .models import db, User, Appointment, Notification
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeService:
    """Real-time service for WebSocket connections and live updates"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connected_users: Dict[int, Set[str]] = {}  # user_id -> set of session_ids
        self.user_sessions: Dict[str, int] = {}  # session_id -> user_id
        self.appointment_reminders: Dict[int, datetime] = {}  # appointment_id -> reminder_time
        self.setup_event_handlers()
        self.start_background_tasks()
    
    def setup_event_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            emit('connected', {'status': 'connected', 'sid': request.sid})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            session_id = request.sid
            user_id = self.user_sessions.get(session_id)
            
            if user_id:
                # Remove from connected users
                if user_id in self.connected_users:
                    self.connected_users[user_id].discard(session_id)
                    if not self.connected_users[user_id]:
                        del self.connected_users[user_id]
                
                # Remove session mapping
                del self.user_sessions[session_id]
                logger.info(f"User {user_id} disconnected from session {session_id}")
            
            logger.info(f"Client disconnected: {session_id}")
        
        @self.socketio.on('authenticate')
        def handle_authentication(data):
            """Authenticate user and join their personal room"""
            try:
                user_id = data.get('user_id')
                if user_id:
                    session_id = request.sid
                    
                    # Verify user exists
                    user = User.query.get(user_id)
                    if user and user.is_active:
                        # Add to connected users
                        if user_id not in self.connected_users:
                            self.connected_users[user_id] = set()
                        self.connected_users[user_id].add(session_id)
                        
                        # Map session to user
                        self.user_sessions[session_id] = user_id
                        
                        # Join user's personal room
                        join_room(f"user_{user_id}")
                        
                        # Join admin room if user is admin
                        if user.is_admin:
                            join_room("admin_room")
                        
                        emit('authenticated', {
                            'status': 'success',
                            'user_id': user_id,
                            'is_admin': user.is_admin
                        })
                        
                        # Send unread notifications
                        self.send_unread_notifications(user_id)
                        
                        logger.info(f"User {user_id} authenticated for session {session_id}")
                    else:
                        emit('authenticated', {'status': 'error', 'message': 'Invalid user'})
                else:
                    emit('authenticated', {'status': 'error', 'message': 'Missing user_id'})
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                emit('authenticated', {'status': 'error', 'message': 'Authentication failed'})
        
        @self.socketio.on('join_appointment_room')
        def handle_join_appointment_room(data):
            """Join appointment-specific room for real-time updates"""
            appointment_id = data.get('appointment_id')
            user_id = self.user_sessions.get(request.sid)
            
            if appointment_id and user_id:
                room_name = f"appointment_{appointment_id}"
                join_room(room_name)
                emit('joined_room', {'room': room_name, 'appointment_id': appointment_id})
        
        @self.socketio.on('leave_appointment_room')
        def handle_leave_appointment_room(data):
            """Leave appointment-specific room"""
            appointment_id = data.get('appointment_id')
            if appointment_id:
                room_name = f"appointment_{appointment_id}"
                leave_room(room_name)
                emit('left_room', {'room': room_name, 'appointment_id': appointment_id})
        
        @self.socketio.on('mark_notification_read')
        def handle_mark_notification_read(data):
            """Mark notification as read"""
            notification_id = data.get('notification_id')
            user_id = self.user_sessions.get(request.sid)
            
            if notification_id and user_id:
                notification = Notification.query.filter_by(
                    id=notification_id, 
                    user_id=user_id
                ).first()
                
                if notification:
                    notification.mark_as_read()
                    db.session.commit()
                    emit('notification_updated', {
                        'notification_id': notification_id,
                        'is_read': True
                    })
        
        @self.socketio.on('request_appointment_update')
        def handle_appointment_update_request(data):
            """Handle request for appointment updates"""
            appointment_id = data.get('appointment_id')
            user_id = self.user_sessions.get(request.sid)
            
            if appointment_id and user_id:
                appointment = Appointment.query.get(appointment_id)
                if appointment and (appointment.user_id == user_id or 
                                  User.query.get(user_id).is_admin):
                    emit('appointment_update', {
                        'appointment_id': appointment_id,
                        'status': appointment.status,
                        'notes': appointment.notes,
                        'updated_at': appointment.updated_at.isoformat()
                    })
    
    def start_background_tasks(self):
        """Start background tasks for real-time features"""
        def run_background_tasks():
            while True:
                try:
                    self.check_appointment_reminders()
                    self.cleanup_expired_notifications()
                    self.send_system_updates()
                    time.sleep(60)  # Run every minute
                except Exception as e:
                    logger.error(f"Background task error: {str(e)}")
                    time.sleep(60)
        
        # Start background thread
        background_thread = threading.Thread(target=run_background_tasks, daemon=True)
        background_thread.start()
    
    def send_notification(self, user_id: int, title: str, message: str, 
                         notification_type: str = 'general', priority: str = 'normal',
                         action_url: str = None, expires_at: datetime = None):
        """Send real-time notification to user"""
        try:
            # Create notification in database
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                action_url=action_url,
                expires_at=expires_at
            )
            db.session.add(notification)
            db.session.commit()
            
            # Send to connected users
            if user_id in self.connected_users:
                notification_data = {
                    'id': notification.id,
                    'title': title,
                    'message': message,
                    'type': notification_type,
                    'priority': priority,
                    'action_url': action_url,
                    'created_at': notification.created_at.isoformat(),
                    'is_read': False
                }
                
                for session_id in self.connected_users[user_id]:
                    self.socketio.emit('new_notification', notification_data, room=session_id)
            
            logger.info(f"Notification sent to user {user_id}: {title}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
    
    def send_appointment_update(self, appointment_id: int, update_type: str, 
                               data: Dict[str, Any] = None):
        """Send appointment update to all users in appointment room"""
        try:
            room_name = f"appointment_{appointment_id}"
            update_data = {
                'appointment_id': appointment_id,
                'update_type': update_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data or {}
            }
            
            self.socketio.emit('appointment_update', update_data, room=room_name)
            logger.info(f"Appointment update sent for appointment {appointment_id}")
            
        except Exception as e:
            logger.error(f"Error sending appointment update: {str(e)}")
    
    def send_admin_alert(self, alert_type: str, message: str, data: Dict[str, Any] = None):
        """Send alert to all connected admin users"""
        try:
            alert_data = {
                'type': alert_type,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data or {}
            }
            
            self.socketio.emit('admin_alert', alert_data, room="admin_room")
            logger.info(f"Admin alert sent: {alert_type} - {message}")
            
        except Exception as e:
            logger.error(f"Error sending admin alert: {str(e)}")
    
    def send_unread_notifications(self, user_id: int):
        """Send unread notifications to user upon connection"""
        try:
            notifications = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).filter(
                (Notification.expires_at.is_(None)) | 
                (Notification.expires_at > datetime.utcnow())
            ).order_by(Notification.created_at.desc()).limit(10).all()
            
            for notification in notifications:
                notification_data = {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'type': notification.notification_type,
                    'priority': notification.priority,
                    'action_url': notification.action_url,
                    'created_at': notification.created_at.isoformat(),
                    'is_read': False
                }
                
                if user_id in self.connected_users:
                    for session_id in self.connected_users[user_id]:
                        self.socketio.emit('existing_notification', notification_data, room=session_id)
            
        except Exception as e:
            logger.error(f"Error sending unread notifications: {str(e)}")
    
    def check_appointment_reminders(self):
        """Check and send appointment reminders"""
        try:
            now = datetime.utcnow()
            tomorrow = now.date() + timedelta(days=1)
            
            # Get appointments for tomorrow that haven't had reminders sent
            appointments = Appointment.query.filter(
                Appointment.date == tomorrow,
                Appointment.reminder_sent == False,
                Appointment.status == 'scheduled',
                Appointment.is_deleted == False
            ).all()
            
            for appointment in appointments:
                # Send reminder notification
                self.send_notification(
                    user_id=appointment.user_id,
                    title="Appointment Reminder",
                    message=f"Your appointment is scheduled for tomorrow at {appointment.time.strftime('%I:%M %p')}",
                    notification_type='reminder',
                    priority='high',
                    action_url=f"/appointment/{appointment.id}"
                )
                
                # Mark reminder as sent
                appointment.reminder_sent = True
                appointment.reminder_sent_at = now
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error checking appointment reminders: {str(e)}")
    
    def cleanup_expired_notifications(self):
        """Clean up expired notifications"""
        try:
            expired_notifications = Notification.query.filter(
                Notification.expires_at < datetime.utcnow()
            ).all()
            
            for notification in expired_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            
            if expired_notifications:
                logger.info(f"Cleaned up {len(expired_notifications)} expired notifications")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired notifications: {str(e)}")
    
    def send_system_updates(self):
        """Send system updates and health checks"""
        try:
            # Check for overdue appointments
            overdue_appointments = Appointment.query.filter(
                Appointment.date < datetime.utcnow().date(),
                Appointment.status == 'scheduled',
                Appointment.is_deleted == False
            ).all()
            
            if overdue_appointments:
                self.send_admin_alert(
                    alert_type='overdue_appointments',
                    message=f"Found {len(overdue_appointments)} overdue appointments",
                    data={'count': len(overdue_appointments)}
                )
            
            # Check system health
            total_users = User.query.filter(User.is_deleted == False).count()
            active_appointments = Appointment.query.filter(
                Appointment.status == 'scheduled',
                Appointment.is_deleted == False
            ).count()
            
            # Send health metrics to admin room
            health_data = {
                'total_users': total_users,
                'active_appointments': active_appointments,
                'connected_users': len(self.connected_users),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.socketio.emit('system_health', health_data, room="admin_room")
            
        except Exception as e:
            logger.error(f"Error sending system updates: {str(e)}")
    
    def get_connected_users_count(self) -> int:
        """Get count of currently connected users"""
        return len(self.connected_users)
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if user is currently connected"""
        return user_id in self.connected_users and bool(self.connected_users[user_id])
    
    def broadcast_to_all(self, event: str, data: Dict[str, Any]):
        """Broadcast event to all connected users"""
        try:
            self.socketio.emit(event, data)
            logger.info(f"Broadcast sent: {event}")
        except Exception as e:
            logger.error(f"Error broadcasting: {str(e)}")

# Global instance
realtime_service = None

def init_realtime_service(socketio: SocketIO):
    """Initialize the real-time service"""
    global realtime_service
    realtime_service = RealtimeService(socketio)
    return realtime_service

def get_realtime_service() -> RealtimeService:
    """Get the global real-time service instance"""
    return realtime_service 