from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles=[]):
    """
    Decorador para restringir el acceso a vistas según una lista de roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
           
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            
    
            if hasattr(request.user, 'perfil') and request.user.perfil.rol in allowed_roles:
                return view_func(request, *args, **kwargs)
          
            messages.error(request, "No tienes permisos para acceder a esta sección.")
 
            return redirect('dashboard:dashboard') 
            
        return _wrapped_view
    return decorator