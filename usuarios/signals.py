from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea un perfil automáticamente cuando se crea un usuario"""
    if created:
        Perfil.objects.create(user=instance, rol='usuario')  


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    try:
        instance.perfil.save()
    except Perfil.DoesNotExist:
        Perfil.objects.create(user=instance, rol='usuario')  