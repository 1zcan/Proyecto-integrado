from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil

@receiver(post_save, sender=User)
def gestionar_perfil_usuario(sender, instance, created, **kwargs):

    # Crear el perfil si no existe
    perfil, created_perfil = Perfil.objects.get_or_create(user=instance)

    # Si el usuario es superusuario → rol TI / Informática
    if instance.is_superuser or instance.is_staff:
        perfil.rol = 'ti_informatica'
        perfil.save()
        return

    # Si es un usuario normal y el perfil fue recién creado
    # le asignamos el rol de usuario común
    if created or created_perfil:
        perfil.rol = 'usuario'
        perfil.save()
