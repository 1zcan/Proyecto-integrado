# usuarios/forms.py
from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import FileInput
from .models import Perfil
import re


# ---------------------------------------------------------
# VALIDACIÓN DE CONTRASEÑA SEGURA
# ---------------------------------------------------------
def validar_password_segura(password):
    """
    Reglas:
    - mínimo 8 caracteres
    - al menos 1 mayúscula
    - al menos 1 número
    """
    if len(password) < 8:
        raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")

    if not re.search(r"[A-Z]", password):
        raise forms.ValidationError("La contraseña debe incluir al menos una letra mayúscula.")

    if not re.search(r"\d", password):
        raise forms.ValidationError("La contraseña debe incluir al menos un número.")

    return password


# ---------------------------------------------------------
# FORMULARIO DE REGISTRO
# ---------------------------------------------------------
class RegistroForm(forms.ModelForm):

    username = forms.CharField(
        max_length=20,
        label="Nombre de usuario",
        help_text="Máximo 20 caracteres. Solo letras, números y @/./+/-/_"
    )
    
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.cl'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Contraseña'
    )

    password_confirmacion = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirmar Contraseña'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirmacion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            clases = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (clases + ' form-control').strip()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        return validar_password_segura(password)

    def clean_password_confirmacion(self):
        p1 = self.cleaned_data.get('password')
        p2 = self.cleaned_data.get('password_confirmacion')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2


# ---------------------------------------------------------
# FORMULARIOS DE PERFIL
# ---------------------------------------------------------
class PerfilForm(forms.ModelForm):

    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.cl'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe otro usuario usando este correo electrónico.")
        return email


class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto']
        widgets = {
            'foto': FileInput(attrs={'class': 'form-control'})
        }


# ---------------------------------------------------------
# FORMULARIO ADMIN → CREAR USUARIOS
# ---------------------------------------------------------
class AdminUserCreateForm(forms.ModelForm):

    rol = forms.ChoiceField(
        choices=Perfil.ROLES,
        label="Rol"
    )
    
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'Usuario',
            'email': 'Correo',
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")
            return cleaned_data

        if p1:
            try:
                validar_password_segura(p1)
            except forms.ValidationError as e:
                self.add_error('password1', e)

        return cleaned_data

    def save(self, commit=True):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        rol = self.cleaned_data['rol']

        user = User(username=username, email=email, is_active=True)
        user.set_password(password)

        if commit:
            user.save()
            perfil, creado = Perfil.objects.get_or_create(user=user, defaults={'rol': rol})
            if not creado:
                perfil.rol = rol
                perfil.save()

        return user
