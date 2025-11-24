# parto/forms.py
from django import forms
from .models import Parto, ModeloAtencionParto, RobsonParto, PartoObservacion



class PartoForm(forms.ModelForm):
    """
    Formulario para crear/editar el registro del parto.
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
            'gemelos',
        ]

        widgets = {
            'fecha': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                },
                format='%Y-%m-%d'
            ),
            'hora': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                },
                format='%H:%M'
            ),
            'madre': forms.Select(attrs={'class': 'form-select'}),
            'tipo_parto': forms.Select(attrs={'class': 'form-select'}),
            # EG (Semanas) → bloqueamos negativos en HTML
            'edad_gestacional_semanas': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                }
            ),
            'establecimiento': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatos que el form aceptará al parsear los valores
        self.fields['fecha'].input_formats = ['%Y-%m-%d']
        self.fields['hora'].input_formats = ['%H:%M']

    # Validación en el servidor para EG (Semanas)
    def clean_edad_gestacional_semanas(self):
        eg = self.cleaned_data.get('edad_gestacional_semanas')

        if eg is None:
            return eg  # por si en algún momento lo vuelves opcional

        if eg < 0:
            raise forms.ValidationError("La EG (semanas) no puede ser negativa.")

        # opcional: límite superior razonable
        if eg > 45:
            raise forms.ValidationError("La EG (semanas) no puede ser mayor a 45.")

        return eg


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
            'posicion_expulsivo',
        ]


class RobsonForm(forms.ModelForm):
    """
    Formulario para la Clasificación Robson [cite: 42, 210]
    """
    class Meta:
        model = RobsonParto
        fields = ['grupo', 'cesarea_electiva', 'cesarea_urgencia']


class PartoObservacionForm(forms.ModelForm):
    class Meta:
        model = PartoObservacion
        fields = ['observacion', 'password_firma']  # o los campos que tengas
    def __init__(self, *args, **kwargs):
        # Sacamos el user del kwargs para que no llegue al ModelForm padre
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    """
    Formulario para añadir observaciones firmadas [cite: 42, 216]
    """
    clave_firma = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = PartoObservacion
        fields = ['texto']  # 'autor' y 'parto' se asignan en la vista
    def __init__(self, *args, **kwargs):
        # Saco el usuario de los kwargs, si viene
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
