# backend/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Marketplace", {"fields": ("is_vendor", "is_customer")}),
    )
    list_display = ("username", "email", "is_staff", "is_vendor", "is_customer")
    list_filter = DjangoUserAdmin.list_filter + ("is_vendor",)
