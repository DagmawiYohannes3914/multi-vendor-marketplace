from rest_framework import permissions

class IsVendorAndOwner(permissions.BasePermission):
    """
    Custom permission to only allow vendors to manage their own products.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated and is a vendor
        return request.user.is_authenticated and hasattr(request.user, 'vendorprofile')
    
    def has_object_permission(self, request, view, obj):
        # Check if the product belongs to the vendor
        return obj.vendor == request.user.vendorprofile