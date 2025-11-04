"""
Quick script to create an admin user
Usage: python create_admin_user.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'n_backend.settings')
django.setup()

from n_backend.app.users.models import Users
from n_backend.app.users.views import generate_simple_token

def create_admin_user():
    """Create or update an admin user"""
    email = input("Enter admin email (default: admin@test.com): ").strip() or "admin@test.com"
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    password = input("Enter admin password (default: admin123): ").strip() or "admin123"
    
    try:
        user = Users.objects.get(email=email)
        print(f"User with email {email} already exists.")
        response = input("Update role to admin? (y/n): ").strip().lower()
        if response == 'y':
            user.role = 'admin'
            user.password = password  # Will be hashed in save()
            user.username = username
            user.save()
            print(f"✅ User updated to admin: {user.email}")
        else:
            print("User not updated.")
            return user
    except Users.DoesNotExist:
        user = Users.objects.create(
            username=username,
            email=email,
            password=password,  # Will be hashed in save()
            role='admin'
        )
        print(f"✅ Admin user created: {user.email}")
    
    # Generate token
    token = generate_simple_token(user)
    print(f"\n✅ Admin Token (save this for testing):")
    print(f"{token}\n")
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Role: {user.role}")
    
    return user, token

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  CREATE ADMIN USER")
    print("="*60 + "\n")
    create_admin_user()

