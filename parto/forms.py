# parto/forms.py
from django import forms
from .models import Parto, ModeloAtencionParto, RobsonParto, PartoObservacion

class PartoForm(forms.ModelForm):
    """
    Formulario para crear/editar el registro del parto [cite: 42, 198]
    """
    class Meta:
        model = Parto
        fields = [
            'madre', 
            'fecha', 
            'hora', 
            'tipo_parto', 
            'edad_gestacional_semanas', 
            'establecimiento',
            'acompanamiento_trabajo_parto', 
            'acompanamiento_solo_expulsivo',
            'piel_piel_madre_30min', 
            'piel_piel_acomp_30min'
        ]

        widgets = {
            'fecha': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'hora': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),
            'madre': forms.Select(attrs={'class': 'form-select'}),
            'tipo_parto': forms.Select(attrs={'class': 'form-select'}),
            'edad_gestacional_semanas': forms.NumberInput(attrs={'class': 'form-control'}),
            'establecimiento': forms.Select(attrs={'class': 'form-select'}),
        }


class ModeloAtencionForm(forms.ModelForm):
    """
    Formulario para el Modelo de Atención (REM A21) [cite: 42, 204]
    """
    class Meta:
        model = ModeloAtencionParto
        fields = [
            'libertad_movimiento', 
            'regimen_hidrico_amplio', 
            'manejo_dolor', 
            'posicion_expulsivo'
        ]


class RobsonForm(forms.ModelForm):
    """
    Formulario para la Clasificación Robson [cite: 42, 210]
    """
    class Meta:
        model = RobsonParto
        fields = ['grupo', 'cesarea_electiva', 'cesarea_urgencia']


class PartoObservacionForm(forms.ModelForm):
    """
    Formulario para añadir observaciones firmadas [cite: 42, 216]
    """
    clave_firma = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = PartoObservacion
        fields = ['texto']  # 'autor' y 'parto' se asignan en la vista
