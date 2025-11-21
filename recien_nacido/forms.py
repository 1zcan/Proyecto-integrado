# recien_nacido/forms.py
from django import forms
from .models import RecienNacido, ProfiRN, RNObservacion, DefuncionRN
from parto.models import Parto
from catalogo.models import Catalogo


class RNForm(forms.ModelForm):
    """
    Formulario unificado para CREAR y EDITAR RN.

    - En CREAR: se muestra y exige seleccionar un Parto.
    - En EDITAR: no se muestra el Parto, no se vuelve a pedir,
      pero se mantiene el parto original del RN.
    """
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
        # viene desde las views
        self.is_edit = kwargs.pop("is_edit", False)
        super().__init__(*args, **kwargs)

        # Si estamos editando, no queremos que el usuario cambie el parto ni que sea obligatorio
        if self.is_edit:
            if "parto" in self.fields:
                self.fields["parto"].required = False
                self.fields["parto"].widget = forms.HiddenInput()
                # aseguramos que el initial sea el parto actual
                if self.instance and self.instance.pk:
                    self.initial["parto"] = self.instance.parto

    def clean_parto(self):
        """
        - En CREAR: obliga a seleccionar un parto.
        - En EDITAR: si no viene en el POST, reutiliza el parto del instance.
        """
        parto = self.cleaned_data.get("parto")

        # Si es edición y no viene valor, usamos el que ya tenía el RN
        if self.is_edit:
            if not parto and self.instance and self.instance.pk:
                return self.instance.parto
            return parto

        # Caso creación: debe venir sí o sí
        if not parto:
            raise forms.ValidationError(
                "Seleccionar Parto asociado. Este campo es obligatorio."
            )
        return parto

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
        pc = self.cleaned_data.get("pc")
        if pc is None:
            return pc
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
            'fecha_hora': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'profesional': forms.TextInput(attrs={'class': 'form-control'}),
            'reaccion_adversa': forms.Textarea(
                attrs={'rows': 2, 'placeholder': 'Describir si aplica...', 'class': 'form-control'}
            ),
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
        from django.core.exceptions import ValidationError

        clave = self.cleaned_data.get("clave_firma")

        if not clave:
            raise ValidationError("Debe ingresar la clave para validar la eliminación.")

        if self.user is None or not self.user.is_authenticated:
            raise ValidationError("Debe iniciar sesión para poder eliminar registros.")

        if not self.user.check_password(clave):
            raise ValidationError("La clave no coincide con su contraseña de usuario.")

        return clave


class DefuncionRNForm(forms.ModelForm):
    class Meta:
        model = DefuncionRN
        fields = ['razon']
        widgets = {
            'razon': forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
        }
