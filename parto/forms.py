# parto/forms.py
from django import forms
from .models import Parto, ModeloAtencionParto, RobsonParto, PartoObservacion


class PartoForm(forms.ModelForm):
    """
    Formulario para crear/editar el registro del parto
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
            'piel_piel_acomp_30min',
        ]

        widgets = {
            'fecha': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'hora': forms.TimeInput(
                attrs={'type': 'time', 'class': 'form-control'}
            ),
            'madre': forms.Select(attrs={'class': 'form-select'}),
            'tipo_parto': forms.Select(attrs={'class': 'form-select'}),

            'edad_gestacional_semanas': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),

            'establecimiento': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_edad_gestacional_semanas(self):
        eg = self.cleaned_data.get('edad_gestacional_semanas')
        if eg is None:
            return eg

        if eg < 0:
            raise forms.ValidationError("La EG (semanas) no puede ser negativa.")
        if eg > 45:
            raise forms.ValidationError("La EG (semanas) no puede ser mayor a 45.")
        return eg


class ModeloAtencionForm(forms.ModelForm):
    """Formulario para Modelo de Atención"""
    class Meta:
        model = ModeloAtencionParto
        fields = [
            'libertad_movimiento',
            'regimen_hidrico_amplio',
            'manejo_dolor',
            'posicion_expulsivo',
        ]


class RobsonForm(forms.ModelForm):
    """Formulario para Clasificación Robson"""
    class Meta:
        model = RobsonParto
        fields = ['grupo', 'cesarea_electiva', 'cesarea_urgencia']


class PartoObservacionForm(forms.ModelForm):
    """
    Formulario para añadir observaciones con firma simple
    """
    clave_firma = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Clave de Firma"
    )

    class Meta:
        model = PartoObservacion
        fields = ['texto', 'clave_firma']

    def __init__(self, *args, **kwargs):
        # Recibe el usuario desde la vista
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
