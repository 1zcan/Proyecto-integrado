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

class AdminUserCreateForm(forms.ModelForm):
    """
    Formulario para que el administrador cree usuarios
    con asignación de ROL + correo.
    """
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

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ya existe un usuario con ese nombre.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con ese correo.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        rol = self.cleaned_data['rol']

        # Crear usuario
        user = User(
            username=username,
            email=email,
            is_active=True,
        )
        user.set_password(password)

        if commit:
            user.save()

            # ⚠️ IMPORTANTE ⚠️
            # En vez de crear un perfil siempre, usamos get_or_create
            perfil, creado = Perfil.objects.get_or_create(
                user=user,
                defaults={'rol': rol}
            )

            # Si el perfil ya existía (por SIGNAL), solo actualizamos el rol
            if not creado:
                perfil.rol = rol
                perfil.save()

        return user
