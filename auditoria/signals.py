# auditoria/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import LogAccion
from .middleware import get_current_request

User = get_user_model()


def get_client_ip(request=None):
    """
    Uso:
      - Desde vistas: get_client_ip(request)  → retorna IP real.
      - Desde signals (sin request): get_client_ip() → retorna None.
    Así evitamos errores de tipo y no rompemos auditar_post_save.
    """
    if request is None:
        return None  # para las signals que la llaman sin parámetros

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Si viene en X-Forwarded-For (proxies / PythonAnywhere), tomamos la primera IP
        ip = x_forwarded_for.split(",")[0].strip()
        return ip

    return request.META.get("REMOTE_ADDR")




def get_current_user():
    """
    Devuelve el usuario autenticado del request actual (si lo hay).
    """
    request = get_current_request()
    if not request:
        return None
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user
    return None


@receiver(post_save)
def auditar_post_save(sender, instance, created, **kwargs):
    # Evitar recursión si se guarda el propio LogAccion
    if sender is LogAccion:
        return

    LogAccion.objects.create(
        usuario=get_current_user(),
        accion=LogAccion.ACCION_CREATE if created else LogAccion.ACCION_UPDATE,
        modelo=sender.__name__,
        objeto_id=str(getattr(instance, "pk", "")),

        ip_address=get_client_ip(),
        timestamp=timezone.now(),
    )


@receiver(post_delete)
def auditar_post_delete(sender, instance, **kwargs):
    if sender is LogAccion:
        return

    LogAccion.objects.create(
        usuario=get_current_user(),
        accion=LogAccion.ACCION_DELETE,
        modelo=sender.__name__,
        objeto_id=str(getattr(instance, "pk", "")),
      
        ip_address=get_client_ip(),
        timestamp=timezone.now(),
    )