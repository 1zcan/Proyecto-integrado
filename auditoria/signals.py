# auditoria/signals.py
import sys

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.utils import ProgrammingError, OperationalError

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


def can_write_log():
    """
    Devuelve False cuando:
      - Estamos corriendo migraciones / makemigrations.
      - La tabla de LogAccion aún no existe.
    Así evitamos que los signals rompan 'migrate'.
    """
    # 1) No auditar durante migraciones
    if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return False

    # 2) Verificar que la tabla exista en la BD
    try:
        connection = connections['default']
        tables = connection.introspection.table_names()
        return LogAccion._meta.db_table in tables
    except Exception:
        # Cualquier problema de conexión / introspección → no escribir log
        return False


@receiver(post_save)
def auditar_post_save(sender, instance, created, **kwargs):
    # Evitar recursión si se guarda el propio LogAccion
    if sender is LogAccion:
        return

    # Evitar problemas si tabla no existe o estamos en migraciones
    if not can_write_log():
        return

    try:
        LogAccion.objects.create(
            usuario=get_current_user(),
            accion=LogAccion.ACCION_CREATE if created else LogAccion.ACCION_UPDATE,
            modelo=sender.__name__,
            objeto_id=str(getattr(instance, "pk", "")),
            ip_address=get_client_ip(),
            timestamp=timezone.now(),
        )
    except (ProgrammingError, OperationalError):
        # Tabla aún no creada o BD no lista → no romper nada
        pass


@receiver(post_delete)
def auditar_post_delete(sender, instance, **kwargs):
    if sender is LogAccion:
        return

    if not can_write_log():
        return

    try:
        LogAccion.objects.create(
            usuario=get_current_user(),
            accion=LogAccion.ACCION_DELETE,
            modelo=sender.__name__,
            objeto_id=str(getattr(instance, "pk", "")),
            ip_address=get_client_ip(),
            timestamp=timezone.now(),
        )
    except (ProgrammingError, OperationalError):
        pass
