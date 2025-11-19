# recien_nacido/forms.py
from django import forms
from .models import RecienNacido, ProfiRN, RNObservacion
from parto.models import Parto
from catalogo.models import Catalogo


class RNForm(forms.ModelForm):
    """
    Formulario Unificado para Creación (selecciona Parto) y Edición.
    """
    # CAMPO PARTO: Incluido para la creación autónoma
    parto = forms.ModelChoiceField(
        queryset=Parto.objects.filter(activo=True).order_by('-fecha', '-hora'),
        label="Seleccionar Parto asociado",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = RecienNacido
        fields = [
            'parto',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ocultar el campo 'parto' si estamos en edición
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

    def clean_pc(self):
        """
        Validación para Perímetro Craneano:
        - No permite valores nulos negativos ni cero.
        """
        pc = self.cleaned_data.get("pc")
        if pc is None:
            return pc  # por si el campo es opcional en el modelo
        if pc <= 0:
            raise forms.ValidationError("El perímetro craneano debe ser mayor a 0 cm.")
        return pc


class ProfiRNForm(forms.ModelForm):
    """
    Formulario de Profilaxis.
    """
    tipo = forms.ModelChoiceField(
        queryset=Catalogo.objects.filter(tipo='VAL_PROFILAXIS_RN', activo=True),
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
    Formulario de Observación/Diagnóstico del RN.
    """
    class Meta:
        model = RNObservacion
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Escribir observación o diagnóstico...',
                    'class': 'form-control'
                }
            ),
        }
        labels = {
            'texto': 'Nueva Observación / Diagnóstico'
        }


class RNDeleteForm(forms.Form):
    """
    Formulario para eliminar un Recién Nacido:
    - Pide motivo
    - Pide clave de firma (contraseña del usuario)
    """
    razon = forms.CharField(
        label="Motivo de eliminación",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Explique brevemente por qué se elimina este RN..."
            }
        ),
        required=True,
    )
    clave_firma = forms.CharField(
        label="Clave de firma",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="Ingrese su contraseña de usuario para confirmar la eliminación.",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_clave_firma(self):
        clave = self.cleaned_data.get("clave_firma")

        if not clave:
            raise forms.ValidationError("Debe ingresar la clave para validar la eliminación.")

        if self.user is None or not self.user.is_authenticated:
            raise forms.ValidationError("Debe iniciar sesión para poder eliminar registros.")

        if not self.user.check_password(clave):
            raise forms.ValidationError("La clave no coincide con su contraseña de usuario.")

        return clave
