from django import forms
from django.contrib.auth.models import User
from .models import Perfil
from django.forms.widgets import FileInput


class RegistroForm(forms.ModelForm):

    # --- NUEVO: limitar username a 20 caracteres ---
    username = forms.CharField(
        max_length=20,
        label="Nombre de usuario",
        help_text="Máximo 20 caracteres. Solo letras, números y @/./+/-/_"
    )
    # ------------------------------------------------

    # Email obligatorio y con validación de formato
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agregar clase form-control a todos los campos
        for field_name, field in self.fields.items():
            widget = field.widget
            existing_classes = widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                widget.attrs['class'] = (existing_classes + ' form-control').strip()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirmacion']

    # --- Validación de correo ---
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()

        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")

        # Verificar que no exista otro usuario con el mismo mail
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe un usuario registrado con este correo electrónico."
            )

        return email

    # --- Validación de confirmación de contraseña ---
    def clean_password_confirmacion(self):
        password = self.cleaned_data.get('password')
        password_confirmacion = self.cleaned_data.get('password_confirmacion')

        if password and password_confirmacion and password != password_confirmacion:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return password_confirmacion


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

        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")

        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "Ya existe otro usuario usando este correo electrónico."
            )

        return email


class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto']
        widgets = {
            'foto': FileInput(attrs={'class': 'form-control'})
        }
