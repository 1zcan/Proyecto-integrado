# madre/models.py
from django.db import models
from django.contrib.auth.models import User
from catalogo.models import Catalogo   # <--- NECESARIO PARA OPCIÓN B


class Madre(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre_completo = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()

    # 🔥 OPCIÓN B: Relaciones al catálogo
    comuna = models.ForeignKey(
        Catalogo,
        on_delete=models.PROTECT,
        limit_choices_to={'tipo': 'VAL_COMUNA'},
        related_name='madres_comuna'
    )

    cesfam = models.ForeignKey(
        Catalogo,
        on_delete=models.PROTECT,
        limit_choices_to={'tipo': 'VAL_ESTABLECIMIENTO'},
        related_name='madres_cesfam'
    )

    migrante = models.BooleanField(default=False)
    pueblo_originario = models.BooleanField(default=False)
    discapacidad = models.BooleanField(default=False)

    documentos = models.FileField(upload_to="documentos_madre/", blank=True, null=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"

    class Meta:
        verbose_name = "Ficha Madre"
        verbose_name_plural = "Fichas Madres"


class TamizajeMaterno(models.Model):
    madre = models.OneToOneField(Madre, on_delete=models.CASCADE, related_name="tamizaje")

    vdrl_resultado = models.CharField(max_length=50)
    vdrl_tratamiento = models.BooleanField(default=False)

    vih_resultado = models.CharField(max_length=50)

    hepb_resultado = models.CharField(max_length=50)
    profilaxis_vhb_completa = models.BooleanField(default=False)

    def __str__(self):
        return f"Tamizaje de {self.madre.nombre_completo}"

    class Meta:
        verbose_name = "Tamizaje Materno (REM A11)"
        verbose_name_plural = "Tamizajes Maternos (REM A11)"


class MadreObservacion(models.Model):
    madre = models.ForeignKey(Madre, on_delete=models.CASCADE, related_name="observaciones")
    autor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="obs_madre")
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    firma_simple = models.BooleanField(default=False)

    def __str__(self):
        return f"Observación de {self.autor} (Madre: {self.madre.id})"

    class Meta:
        verbose_name = "Observación de Madre"
        verbose_name_plural = "Observaciones de Madre"
        ordering = ['-fecha']
