# parto/models.py
from django.db import models
from madre.models import Madre
from django.contrib.auth.models import User
from catalogo.models import Catalogo


class Parto(models.Model):
    madre = models.ForeignKey(
        Madre,
        on_delete=models.PROTECT,
        related_name="partos"
    )
    fecha = models.DateField()
    hora = models.TimeField()
    tipo_parto = models.ForeignKey(
        Catalogo,
        on_delete=models.PROTECT,
        related_name="partos",
        limit_choices_to={'tipo': 'VAL_TIPO_PARTO'},  # Solo cargará tipos de parto
        verbose_name="Tipo de Parto"
    )
    edad_gestacional_semanas = models.IntegerField()
    establecimiento = models.ForeignKey(
        Catalogo,
        on_delete=models.PROTECT,
        related_name="partos_establecimiento",
        limit_choices_to={'tipo': 'VAL_ESTABLECIMIENTO'},
        verbose_name="Establecimiento"
    )

    acompanamiento_trabajo_parto = models.BooleanField(default=False)
    acompanamiento_solo_expulsivo = models.BooleanField(default=False)
    piel_piel_madre_30min = models.BooleanField(default=False)
    piel_piel_acomp_30min = models.BooleanField(default=False)
    gemelos = models.BooleanField(default=False, verbose_name="Gemelos")

    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']
        verbose_name = "Registro de Parto"
        verbose_name_plural = "Registros de Partos"

    def __str__(self):
        return f"Parto de {self.madre} - {self.fecha}"


class ModeloAtencionParto(models.Model):
    parto = models.OneToOneField(
        Parto,
        on_delete=models.CASCADE,
        related_name="modelo_atencion"
    )

    libertad_movimiento = models.BooleanField(default=False)
    regimen_hidrico_amplio = models.BooleanField(default=False)
    manejo_dolor = models.CharField(max_length=100)
    posicion_expulsivo = models.CharField(max_length=100)

    def __str__(self):
        return f"Modelo de Atención para {self.parto}"

    class Meta:
        verbose_name = "Modelo de Atención del Parto (REM A21)"
        verbose_name_plural = "Modelos de Atención del Parto (REM A21)"


class RobsonParto(models.Model):
    parto = models.OneToOneField(
        Parto,
        on_delete=models.CASCADE,
        related_name="clasificacion_robson"
    )

    grupo = models.CharField(max_length=10)
    cesarea_electiva = models.BooleanField(default=False)
    cesarea_urgencia = models.BooleanField(default=False)

    def __str__(self):
        return f"Clasificación Robson para {self.parto} (Grupo {self.grupo})"

    class Meta:
        verbose_name = "Clasificación Robson"
        verbose_name_plural = "Clasificaciones Robson"


class PartoObservacion(models.Model):
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name="observaciones"
    )
    # Permite borrar el usuario: deja autor en NULL y NO lanza ProtectedError
    autor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="obs_parto"
    )
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    firma_simple = models.BooleanField(default=False)

    def __str__(self):
        if self.autor:
            nombre = self.autor.get_full_name() or self.autor.username
        else:
            nombre = "Autor eliminado"
        return f"Observación de {nombre} en {self.parto.fecha}"

    class Meta:
        verbose_name = "Observación de Parto"
        verbose_name_plural = "Observaciones de Parto"
        ordering = ['-fecha']
