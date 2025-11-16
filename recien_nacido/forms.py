# recien_nacido/forms.py
from django import forms
from .models import RecienNacido, ProfiRN, RNObservacion
from parto.models import Parto 
from catalogo.models import Catalogo

class RNForm(forms.ModelForm):
    """
    Formulario Unificado para Creación (selecciona Parto) y Edición.
    """
    # 🟢 AÑADIDO: Campo Parto para la creación autónoma
    parto = forms.ModelChoiceField(
        queryset=Parto.objects.filter(activo=True).order_by('-fecha', '-hora'), 
        label="Seleccionar Parto asociado",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = RecienNacido
        fields = [
            'parto', # <-- Incluido para la creación
            'sexo', 
            'peso', 
            'talla', 
            'pc', 
            'apgar_1', 
            'apgar_5',
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
            'sexo': forms.Select(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'placeholder': 'en gramos', 'class': 'form-control'}),
            'talla': forms.NumberInput(attrs={'placeholder': 'en cm', 'class': 'form-control'}),
            'pc': forms.NumberInput(attrs={'placeholder': 'en cm', 'class': 'form-control'}),
            'apgar_1': forms.NumberInput(attrs={'class': 'form-control'}),
            'apgar_5': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    # Resto de validaciones (clean methods)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el objeto ya existe (edición), ocultamos el campo 'parto' 
        # para que no se pueda cambiar el Parto asociado
        if self.instance.pk:
            self.fields['parto'].widget = forms.HiddenInput()


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

# --- El resto de formularios sigue igual ---

class ProfiRNForm(forms.ModelForm):
    """
    Formulario para añadir Profilaxis (rn_profilaxis.html).
    """
    tipo = forms.ModelChoiceField(
        queryset=Catalogo.objects.filter(tipo='PROFILAXIS_RN', activo=True),
        required=True,
        label="Tipo de Profilaxis",
        widget=forms.Select(attrs={'class': 'form-control'})
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
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'profesional': forms.TextInput(attrs={'class': 'form-control'}),
            'reaccion_adversa': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Describir si aplica...', 'class': 'form-control'}),
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
            'texto': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribir observación o diagnóstico...', 'class': 'form-control'}),
        }
        labels = {
            'texto': 'Nueva Observación / Diagnóstico'
        }