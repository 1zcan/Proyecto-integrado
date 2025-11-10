from django import forms
from django.contrib.auth.models import User
from .models import Perfil

class RegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password_confirmacion = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña')

    # Para agregar estilos bootstrap a todos los campos y no uno a uno
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplica la clase Bootstrap a todos los campos automáticamente
        for field_name, field in self.fields.items():
            widget = field.widget
            existing_classes = widget.attrs.get('class', '')
            # Evita duplicar clases
            if 'form-control' not in existing_classes:
                widget.attrs['class'] = (existing_classes + ' form-control').strip()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirmacion']

    def clean_password_confirmacion(self):
        password = self.cleaned_data.get('password')
        password_confirmacion = self.cleaned_data.get('password_confirmacion')
        
        if password and password_confirmacion and password != password_confirmacion:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
        return password_confirmacion



class PerfilForm(forms.ModelForm):
    """
    Formulario para que los usuarios editen su información básica.
    """
    class Meta:
        model = User
        fields = ['username', 'email']

class FotoPerfilForm(forms.ModelForm):
    """
    Un formulario separado solo para la foto, para mantener la lógica limpia.
    """
    class Meta:
        model = Perfil
        fields = ['foto']