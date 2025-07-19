#!/usr/bin/env python3
"""
Setup script to create admin account for BrightSmile Dental Clinic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
from datetime import datetime, date

def setup_admin():
    """Create admin account with username 'admin' and password 'admin123'"""
    app = create_app()
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print("Admin account already exists!")
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            print(f"Is Admin: {admin.is_admin}")
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@brightsmile.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            phone='+995555123456',
            date_of_birth=date(1990, 1, 1),
            address='123 Admin Street, Admin City, AS 12345',
            emergency_contact='Emergency Contact',
            emergency_phone='(555) 987-6543',
            medical_conditions='[]',  # Empty JSON array
            allergies='[]',  # Empty JSON array
            medications='[]',  # Empty JSON array
            insurance_provider='Admin Insurance',
            insurance_number='ADMIN123456',
            is_admin=True,
            is_active=True,
            email_verified=True
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin account created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@brightsmile.com")
            print("\nYou can now log in to the admin panel.")
        except Exception as e:
            print(f"❌ Error creating admin account: {e}")
            db.session.rollback()

if __name__ == '__main__':
    setup_admin() 