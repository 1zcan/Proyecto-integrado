# usuarios/mixins.py
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class RoleRequiredMixin(AccessMixin):
    """
    Mixin para restringir acceso a Vistas según el Rol del Perfil.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # TI / Informática (o Superusuario) tiene acceso total
        if request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.rol == 'ti_informatica'):
            return super().dispatch(request, *args, **kwargs)

        # Verificar otros roles
        if hasattr(request.user, 'perfil'):
            user_rol = request.user.perfil.rol
            if user_rol in self.allowed_roles:
                return super().dispatch(request, *args, **kwargs)
        
        messages.error(request, "⛔ No tienes permisos para acceder a esta sección.")
        return redirect('dashboard:dashboard')