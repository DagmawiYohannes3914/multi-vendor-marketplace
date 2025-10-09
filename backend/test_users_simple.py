# test_users_simple.py - Simple script to test first_name and last_name fields
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# Print database info
print(f"Database engine: {connection.vendor}")

# Clean up any existing test users
User.objects.filter(username__in=['simpleuser1', 'simpleuser2']).delete()

# Create users with first and last names
try:
    # Create first user
    user1 = User.objects.create(
        username='simpleuser1',
        email='user1@example.com',
        first_name='First',
        last_name='User'
    )
    user1.set_password('password123')
    user1.save()
    
    # Create second user
    user2 = User.objects.create(
        username='simpleuser2',
        email='user2@example.com',
        first_name='Second',
        last_name='User'
    )
    user2.set_password('password123')
    user2.save()
    
    # Retrieve and print users
    users = User.objects.filter(username__in=['simpleuser1', 'simpleuser2'])
    for user in users:
        print(f"\nUser: {user.username}")
        print(f"ID: {user.id}")
        print(f"First name: {user.first_name}")
        print(f"Last name: {user.last_name}")
        print(f"Email: {user.email}")
        print(f"Is vendor: {user.is_vendor}")
        print(f"Is customer: {user.is_customer}")
    
    print("\nUsers created successfully!")
    
except Exception as e:
    print(f"Error creating users: {e}")