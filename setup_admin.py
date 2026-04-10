#!/usr/bin/env python
"""Setup admin user for the steganography platform"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Database, UserManager

def setup_admin():
    """Create admin user in the database"""
    try:
        # Initialize database and user manager
        db = Database()
        user_manager = UserManager()
        
        # Check if admin already exists
        try:
            existing = db.get_user_by_username("admin")
            if existing:
                print("⚠️  Admin user already exists!")
                print(f"   Username: {existing['username']}")
                print(f"   Email: {existing['email']}")
                return
        except:
            pass  # Admin doesn't exist, that's fine
        
        # Create admin user
        result = user_manager.signup(
            username="admin",
            password="admin123"
        )
        
        # Update email and fullname in the database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET email = ?, fullname = ?
            WHERE username = ?
        ''', ('admin@example.com', 'Administrator', 'admin'))
        conn.commit()
        conn.close()
        
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print("LOGIN CREDENTIALS:")
        print("=" * 50)
        print("Username: admin")
        print("Password: admin123")
        print("=" * 50)
        print("\nYou can now login at: http://localhost:3000/login")
        print("And access admin panel at: http://localhost:3000/admin")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    setup_admin()
