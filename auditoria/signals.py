from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import LogAccion

User = get_user_model()


def get_fake_ip():
    # Si más adelante quieres usar la IP real del request,
    # tendrás que pasarla vía middleware. Por ahora dejamos algo fijo.
    return "127.0.0.1"


@receiver(post_save)
def auditar_post_save(sender, instance, created, **kwargs):
    # Evita registrar acciones sobre el propio modelo LogAccion
    if sender is LogAccion:
        return

    accion = LogAccion.ACCION_CREATE if created else LogAccion.ACCION_UPDATE

    LogAccion.objects.create(
        usuario=None,  # si quieres, luego inyectas el usuario vía middleware
        accion=accion,
        modelo=sender.__name__,
        objeto_id=str(getattr(instance, "pk", "")),
        detalle="",
        ip_address=get_fake_ip(),
        timestamp=timezone.now(),
    )


@receiver(post_delete)
def auditar_post_delete(sender, instance, **kwargs):
    if sender is LogAccion:
        return

    LogAccion.objects.create(
        usuario=None,
        accion=LogAccion.ACCION_DELETE,
        modelo=sender.__name__,
        objeto_id=str(getattr(instance, "pk", "")),
        detalle="Borrado físico",
        ip_address=get_fake_ip(),
        timestamp=timezone.now(),
    )
