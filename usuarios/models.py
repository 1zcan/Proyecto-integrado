from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Perfil(models.Model):
   
    ROLES = (
        ('ti_informatica', 'TI / Informática'),     
        ('profesional_salud', 'Profesional Salud'),  
        ('tecnico_salud', 'Técnico Salud'),          
        ('administrativo', 'Administrativo'),       
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='administrativo')
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"


class TwoFactorCode(models.Model):
    """
    Guarda los códigos de verificación (2FA) que se envían al correo.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Código 2FA de {self.user.username}: {self.code}"
