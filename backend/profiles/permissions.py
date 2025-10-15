from rest_framework import permissions

class IsVendor(permissions.BasePermission):
    """
    Custom permission to only allow vendors to access a view.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a vendor
        return request.user.is_authenticated and request.user.is_vendor

class IsCustomer(permissions.BasePermission):
    """
    Custom permission to only allow customers to access a view.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a customer
        return request.user.is_authenticated and request.user.is_customer