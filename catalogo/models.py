# catalogos/models.py
from django.db import models

class Catalogo(models.Model):
    """
    Modelo centralizado para todas las listas desplegables (selects)
    del sistema, según la regla transversal #6.
    """
    
    # Estos TIPO_CHOICES vienen de tu archivo "Catalogos.csv"
    TIPO_CHOICES = [
        ('VAL_TIPO_PARTO', 'Tipo de Parto'),
        ('VAL_SEXO_RN', 'Sexo Recién Nacido'),
        ('VAL_CONSULTORIO', 'Consultorios'),
        ('VAL_REANIMACION', 'Reanimación RN'),
        ('VAL_POSICION_MATERNA', 'Posición Materna'),
        ('VAL_ACOMPANANTE', 'Acompañante'),
        ('VAL_INICIO_TRABAJO_PARTO', 'Inicio Trabajo de Parto'),
        ('VAL_MANEJO_DOLOR', 'Manejo del Dolor'),
        ('VAL_POSICION_EXPULSIVO', 'Posición Expulsivo'),
        ('VAL_DESTINO_RN', 'Destino Recién Nacido'),
        ('VAL_RESULTADO_TAMIZAJE', 'Resultado Tamizaje'),
        ('VAL_VACUNA', 'Vacunas'),
        ('VAL_ROBSON_GRUPO', 'Grupos de Robson'),
        ('VAL_PROFILAXIS_RN', 'Profilaxis Recién Nacido'),
    ]

    tipo = models.CharField(
        max_length=50, 
        choices=TIPO_CHOICES, 
        help_text="Grupo al que pertenece el valor (ej. VAL_SEXO_RN)"
    )
    valor = models.CharField(
        max_length=255, 
        help_text="Valor a mostrar en la lista (ej. FEMENINO)"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Ítem activo y visible en los formularios"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de aparición en la lista"
    )

    class Meta:
        verbose_name = "Valor de Catálogo"
        verbose_name_plural = "Maestro de Catálogos"
        # Asegura que no haya valores duplicados para el mismo tipo
        unique_together = ('tipo', 'valor')
        # Ordena por tipo, luego por el orden manual, y alfabéticamente
        ordering = ['tipo', 'orden', 'valor']

    def __str__(self):
        # Esto se verá en el admin: "[VAL_SEXO_RN] FEMENINO"
        return f"[{self.get_tipo_display()}] {self.valor}"