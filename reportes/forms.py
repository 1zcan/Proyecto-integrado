import datetime
from django import forms

# Obtenemos el año actual para los selectores
CURRENT_YEAR = datetime.date.today().year
YEAR_CHOICES = [(y, y) for y in range(CURRENT_YEAR - 10, CURRENT_YEAR + 2)]

MONTH_CHOICES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
]

QUARTER_CHOICES = [
    (1, 'Trimestre 1 (Ene-Mar)'),
    (2, 'Trimestre 2 (Abr-Jun)'),
    (3, 'Trimestre 3 (Jul-Sep)'),
    (4, 'Trimestre 4 (Oct-Dic)'),
]

class FiltroReporteREMForm(forms.Form):
    """
    Formulario para filtrar los reportes REM por mes y año.
    """
    anio = forms.ChoiceField(
        choices=YEAR_CHOICES,
        initial=CURRENT_YEAR,
        label="Año",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mes = forms.ChoiceField(
        choices=MONTH_CHOICES,
        initial=datetime.date.today().month,
        label="Mes",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class FiltroReporteServicioSaludForm(forms.Form):
    """
    Formulario para filtrar los reportes del Servicio de Salud por trimestre y año.
    """
    anio = forms.ChoiceField(
        choices=YEAR_CHOICES,
        initial=CURRENT_YEAR,
        label="Año",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    trimestre = forms.ChoiceField(
        choices=QUARTER_CHOICES,
        label="Trimestre",
        widget=forms.Select(attrs={'class': 'form-control'})
    )