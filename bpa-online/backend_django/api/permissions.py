from rest_framework.permissions import BasePermission


class IsAdminPerfil(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "perfil", "") == "admin")
