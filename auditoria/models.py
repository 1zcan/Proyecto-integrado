from django.db import models
from django.conf import settings


class LogAccion(models.Model):
    """
    Registro simple de auditoría de acciones.
    """
    ACCION_CREATE = "create"
    ACCION_UPDATE = "update"
    ACCION_DELETE = "delete"
    ACCION_LOGIN = "login"
    ACCION_LOGOUT = "logout"
    ACCION_OTHER = "other"

    ACCION_CHOICES = [
        (ACCION_CREATE, "Crear"),
        (ACCION_UPDATE, "Actualizar"),
        (ACCION_DELETE, "Eliminar / Desactivar"),
        (ACCION_LOGIN, "Login"),
        (ACCION_LOGOUT, "Logout"),
        (ACCION_OTHER, "Otra"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario"
    )
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    modelo = models.CharField(max_length=100, blank=True)
    objeto_id = models.CharField(max_length=100, blank=True)
    detalle = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Log de acción"
        verbose_name_plural = "Logs de acciones"

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.usuario} {self.accion} {self.modelo}({self.objeto_id})"
