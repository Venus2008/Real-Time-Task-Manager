from rest_framework.permissions import BasePermission

class IsAdminFullAccess(BasePermission):

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "ADMIN")

    def has_object_permission(self, request, view, obj):
        # Admin can do everything on any object
        return self.has_permission(request, view)
    
class IsManagerTaskOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and getattr(user, "role", None) == "MANAGER":
            return obj.created_by == user
        return False