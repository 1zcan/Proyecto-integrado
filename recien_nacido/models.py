from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

# --- DEPENDENCIAS DE OTRAS APPS ---
from parto.models import Parto
# from usuarios.models import Usuario (vía settings.AUTH_USER_MODEL)
# from catalogos.models import Catalogo

class RecienNacido(models.Model):
    """
    Modelo principal para los datos clínicos del Recién Nacido.
    Vinculado a un Parto. Contiene datos de Atención Inmediata (REM A24).
    """
    SEXO_CHOICES = (
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('I', 'Indeterminado'),
    )

    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE, # Si se borra el parto, se borra el RN
        related_name="recien_nacidos"
    )
    
    # --- Datos RN (rn_lista.html) ---
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    peso = models.PositiveSmallIntegerField("Peso (gramos)")
    talla = models.PositiveSmallIntegerField("Talla (cm)")
    pc = models.DecimalField("Perímetro Craneano (cm)", max_digits=4, decimal_places=1)
    
    apgar_1 = models.PositiveSmallIntegerField(
        "APGAR al 1er minuto",
        validators=[MaxValueValidator(10), MinValueValidator(0)]
    )
    apgar_5 = models.PositiveSmallIntegerField(
        "APGAR a los 5 minutos",
        validators=[MaxValueValidator(10), MinValueValidator(0)]
    )

    # --- Atención Inmediata (rn_form.html - REM A24 D.2) ---
    reanimacion_basica = models.BooleanField("Reanimación Básica", default=False)
    reanimacion_avanzada = models.BooleanField("Reanimación Avanzada", default=False)
    clampeo_tardio = models.BooleanField("Clampeo Tardío de Cordón", default=False)
    lactancia_60min = models.BooleanField("Inicio Lactancia < 60 min", default=False)
    
    # --- 🟢 CAMPO AÑADIDO: NECESARIO PARA VALIDAR ALTA ---
    fecha_alta = models.DateTimeField(
        "Fecha y Hora de Alta (Egreso)", 
        null=True, 
        blank=True
    )
    # --- FIN CAMPO AÑADIDO ---

    # Campos de auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="rn_creados"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Recién Nacido"
        verbose_name_plural = "Recién Nacidos"
        ordering = ['-parto__fecha']

    def __str__(self):
        return f"RN de {self.parto.madre} ({self.get_sexo_display()})"


class ProfiRN(models.Model):
    # ... (Resto del modelo ProfiRN sigue igual) ...
    """
    Modelo para la Profilaxis del RN (Vacunas/POG).
    Basado en rn_profilaxis.html (REM A11/J).
    """
    rn = models.ForeignKey(
        RecienNacido,
        on_delete=models.CASCADE,
        related_name="profilaxis_set"
    )
    
    # Usamos Catálogo según Regla 6
    tipo = models.ForeignKey(
        'catalogo.Catalogo',
        on_delete=models.SET_NULL,
        null=True,
        related_name="profilaxis_aplicadas",
        limit_choices_to={'tipo': 'VAL_PROFILAXIS_RN', 'activo': True}
    )
    
    fecha_hora = models.DateTimeField("Fecha y Hora de Administración")
    profesional = models.CharField("Profesional que administra", max_length=255)
    reaccion_adversa = models.TextField("Reacción Adversa (si aplica)", null=True, blank=True)

    # Campos de auditoría
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="profilaxis_registradas"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profilaxis de RN"
        verbose_name_plural = "Profilaxis de RN"
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.tipo} para {self.rn}"


class RNObservacion(models.Model):
    # ... (Resto del modelo RNObservacion sigue igual) ...
    """
    Bitácora de observaciones del Recién Nacido.
    Basado en rn_observaciones.html.
    """
    rn = models.ForeignKey(
        RecienNacido,
        on_delete=models.CASCADE,
        related_name="observaciones"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="obs_rn_escritas"
    )
    texto = models.TextField("Observación / Diagnóstico")
    fecha = models.DateTimeField(auto_now_add=True)
    firma_simple = models.BooleanField("Firmado", default=False) # Lógica de firma a implementar

    class Meta:
        verbose_name = "Observación de RN"
        verbose_name_plural = "Observaciones de RN"
        ordering = ['-fecha']

    def __str__(self):
        return f"Obs de {self.autor} en {self.rn} ({self.fecha.date()})"