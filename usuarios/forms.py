from django import forms
from django.contrib.auth.models import User
from .models import Perfil
from django.forms.widgets import FileInput

class RegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password_confirmacion = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña')

  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        for field_name, field in self.fields.items():
            widget = field.widget
            existing_classes = widget.attrs.get('class', '')
           
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
    class Meta:
        model = Perfil
        fields = ['foto']
        widgets = {
            'foto': FileInput(attrs={'class': 'form-control'})
        }
        