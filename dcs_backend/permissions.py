from rest_framework.permissions import BasePermission

class IsMaker(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "employee"


class IsApprover(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ["manager", "admin", "super_admin"]
    

def check_read_only(document):
    if document.is_read_only:
        raise Exception("Approved document is read-only")
    

class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "employee"


class IsApprover(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ["manager", "admin", "super_admin"]