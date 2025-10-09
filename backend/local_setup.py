#!/usr/bin/env python

import os
import sys
import django
from django.db import connection
from django.core.management import call_command

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

# Import models after Django setup
from accounts.models import User
from profiles.models import VendorProfile, CustomerProfile
from django.contrib.auth.models import Group, Permission

def setup_local_db():
    """Set up a local SQLite database with test data"""
    # Check if we're using SQLite
    if connection.vendor != 'sqlite':
        print("This script is intended for SQLite development only.")
        return
    
    # Create a test user with UUID
    test_user = User.objects.create_user(
        username='testuuid',
        email='test@example.com',
        password='password123',
        is_vendor=True,
        is_customer=True
    )
    
    print(f"Created test user with UUID: {test_user.id}")
    
    # Create profiles
    vendor_profile = VendorProfile.objects.create(
        user=test_user,
        store_name='Test Store',
        description='A test store',
        address='123 Test St',
        phone='555-1234'
    )
    
    customer_profile = CustomerProfile.objects.create(
        user=test_user,
        address='123 Test St',
        phone='555-1234',
        preferences='{}'
    )
    
    print(f"Created vendor profile with ID: {vendor_profile.id}")
    print(f"Created customer profile with ID: {customer_profile.id}")
    
    # Create a test group
    test_group = Group.objects.create(name='TestGroup')
    test_user.groups.add(test_group)
    
    # Add a permission to the user
    if Permission.objects.exists():
        perm = Permission.objects.first()
        test_user.user_permissions.add(perm)
        print(f"Added permission {perm.codename} to user")
    
    print("Local database setup complete!")

if __name__ == '__main__':
    setup_local_db()