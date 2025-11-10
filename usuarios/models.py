from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):

    ROLES = (
        ('administrador', 'Administrador'),
        ('editor', 'Editor'),
        ('usuario', 'Usuario'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario')
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.rol}"