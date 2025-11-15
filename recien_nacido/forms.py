from django import forms
from .models import RecienNacido, ProfiRN, RNObservacion
from catalogo.models import Catalogo
from django.core.validators import MaxValueValidator, MinValueValidator

class RNForm(forms.ModelForm):
    """
    Formulario para la Atención Inmediata (rn_form.html).
    """
    class Meta:
        model = RecienNacido
        fields = [
            # Datos RN
            'sexo', 
            'peso', 
            'talla', 
            'pc', 
            'apgar_1', 
            'apgar_5',
            # REM A24
            'reanimacion_basica',
            'reanimacion_avanzada',
            'clampeo_tardio',
            'lactancia_60min',
        ]
        labels = {
            'pc': 'Perímetro Craneano (cm)',
            'apgar_1': 'APGAR 1er min (0-10)',
            'apgar_5': 'APGAR 5to min (0-10)',
        }
        widgets = {
            'peso': forms.NumberInput(attrs={'placeholder': 'en gramos'}),
            'talla': forms.NumberInput(attrs={'placeholder': 'en cm'}),
            'pc': forms.NumberInput(attrs={'placeholder': 'en cm'}),
        }
    
    # Se puede añadir validación extra si es necesario
    def clean_apgar_1(self):
        data = self.cleaned_data['apgar_1']
        if not (0 <= data <= 10):
            raise forms.ValidationError("El APGAR debe estar entre 0 y 10.")
        return data

    def clean_apgar_5(self):
        data = self.cleaned_data['apgar_5']
        if not (0 <= data <= 10):
            raise forms.ValidationError("El APGAR debe estar entre 0 y 10.")
        return data

class ProfiRNForm(forms.ModelForm):
    """
    Formulario para añadir Profilaxis (rn_profilaxis.html).
    """
    tipo = forms.ModelChoiceField(
        queryset=Catalogo.objects.filter(tipo='PROFILAXIS_RN', activo=True),
        required=True,
        label="Tipo de Profilaxis"
    )

    class Meta:
        model = ProfiRN
        fields = [
            'tipo',
            'fecha_hora',
            'profesional',
            'reaccion_adversa'
        ]
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reaccion_adversa': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Describir si aplica...'}),
        }
        labels = {
            'fecha_hora': 'Fecha y Hora de Administración',
            'reaccion_adversa': 'Reacción Adversa (Opcional)',
        }

class RNObservacionForm(forms.ModelForm):
    """
    Formulario simple para añadir una nueva observación (rn_observaciones.html).
    """
    class Meta:
        model = RNObservacion
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribir observación o diagnóstico...'}),
        }
        labels = {
            'texto': 'Nueva Observación / Diagnóstico'
        }