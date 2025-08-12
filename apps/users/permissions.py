from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it. Assumes the model instance has `is_owner` attribute True.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_owner


class IsSuperOrIsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it. Assumes the model instance has `is_owner` attribute True.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_owner or request.user.is_superuser
