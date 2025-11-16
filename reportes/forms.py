# reportes/forms.py
from django import forms

# Usamos rangos de años y meses para los filtros
YEAR_CHOICES = [(y, str(y)) for y in range(2023, 2030)]
MONTH_CHOICES = [(m, str(m)) for m in range(1, 13)]
QUARTER_CHOICES = [('1', 'T1'), ('2', 'T2'), ('3', 'T3'), ('4', 'T4')]

# --- Formulario REM (Modificado) ---
class FiltroReporteREMForm(forms.Form):
    # Opciones para el nuevo filtro de vista
    CHOICES_VISTA = [
        ('CONSOLIDADO', 'Reporte Consolidado'),
        ('A11', 'Solo REM A11 (Madre)'),
        ('A21', 'Solo REM A21 (Parto)'),
        ('A24', 'Solo REM A24 (Recién Nacido)'),
    ]

    anio = forms.ChoiceField(label="Año", choices=YEAR_CHOICES, required=True, initial=2025)
    mes = forms.ChoiceField(label="Mes", choices=MONTH_CHOICES, required=True, initial=11)
    
    # --- 🟢 NUEVO CAMPO AÑADIDO ---
    vista = forms.ChoiceField(
        choices=CHOICES_VISTA,
        required=False, # No es obligatorio
        initial='CONSOLIDADO', # Por defecto muestra todo
        label="Tipo de Vista"
    )

# --- Formulario Servicio Salud (Lo creamos basado en tu views.py) ---
class FiltroReporteServicioSaludForm(forms.Form):
    anio = forms.ChoiceField(label="Año", choices=YEAR_CHOICES, required=True, initial=2025)
    trimestre = forms.ChoiceField(label="Trimestre", choices=QUARTER_CHOICES, required=True)