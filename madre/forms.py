from django import forms
from .models import Madre, TamizajeMaterno, MadreObservacion, DefuncionMadre
from catalogo.models import Catalogo
import re

class MadreForm(forms.ModelForm):
    """
    Formulario para la ficha sociodemográfica y documentos.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cargar comunas y CESFAM dinámicamente
        self.fields['comuna'].queryset = Catalogo.objects.filter(
            tipo='VAL_COMUNA', activo=True
        ).order_by('orden', 'valor')

        self.fields['cesfam'].queryset = Catalogo.objects.filter(
            tipo='VAL_ESTABLECIMIENTO', activo=True
        ).order_by('orden', 'valor')

        self.fields['comuna'].empty_label = "Seleccione una comuna"
        self.fields['cesfam'].empty_label = "Seleccione un establecimiento"

        # Estilos
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Select, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})

        # Checkbox estilo switch
        check_fields = ['migrante', 'pueblo_originario', 'discapacidad']
        for name in check_fields:
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-check-input'})

        # Fecha como date input HTML5
        if 'fecha_nacimiento' in self.fields:
            self.fields['fecha_nacimiento'].widget = forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            )

    class Meta:
        model = Madre
        fields = [
            'rut', 'nombre_completo', 'fecha_nacimiento',
            'comuna', 'cesfam', 'migrante', 'pueblo_originario',
            'discapacidad', 'documentos',
        ]

    def clean_rut(self):
        rut = self.cleaned_data.get("rut", "").strip()
        pattern = r"^[0-9]{1,8}-[0-9Kk]{1}$"

        if not re.match(pattern, rut):
            raise forms.ValidationError(
                "El RUT debe tener el formato 12345678-9 o 12345678-K"
            )
        return rut


class TamizajeMaternoForm(forms.ModelForm):
    """
    Formulario para los Tamizajes (REM A11).
    Convierte los campos de texto en Selects usando el Catálogo.
    """
    class Meta:
        model = TamizajeMaterno
        fields = [
            'vih_resultado', 
            'vdrl_resultado', 'vdrl_tratamiento',
            'hepb_resultado', 
            'chagas_resultado', 
            'profilaxis_vhb_completa'
        ]
        labels = {
            'vih_resultado': 'Resultado VIH',
            'vdrl_resultado': 'Resultado VDRL (Sífilis)',
            'vdrl_tratamiento': '¿Recibió Tratamiento VDRL?',
            'hepb_resultado': 'Resultado Hepatitis B',
            'chagas_resultado': 'Resultado Chagas',
            'profilaxis_vhb_completa': 'Profilaxis VHB Completa (Madre)',
        }
        widgets = {
            'vdrl_tratamiento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profilaxis_vhb_completa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Obtener las opciones desde el Catálogo (VAL_RESULTADO_TAMIZAJE)
        # Buscamos los valores: Negativo, Positivo, Indeterminado, Pendiente
        try:
            opciones_query = Catalogo.objects.filter(
                tipo='VAL_RESULTADO_TAMIZAJE', 
                activo=True
            ).order_by('orden')
            
            # Creamos una lista de tuplas [('Valor', 'Valor'), ...]
            # Usamos upper() en el valor guardado para que coincida con el reporte (POSITIVO)
            choices = [('', '-- Seleccione --')] # Opción vacía inicial
            for op in opciones_query:
                # Guardamos en MAYÚSCULAS (op.valor.upper()) para que el reporte REM lo cuente bien
                choices.append((op.valor.upper(), op.valor))
                
        except Exception:
            # Fallback por si no se ha corrido la migración de catálogos
            choices = [
                ('', '-- Error: Cargue Catálogos --'),
                ('POSITIVO', 'Positivo'),
                ('NEGATIVO', 'Negativo')
            ]

        # 2. Asignar estas opciones a los widgets de los campos de texto
        campos_con_select = ['vih_resultado', 'vdrl_resultado', 'hepb_resultado', 'chagas_resultado']
        
        for campo in campos_con_select:
            if campo in self.fields:
                self.fields[campo].widget = forms.Select(
                    choices=choices,
                    attrs={'class': 'form-select'}
                )


class MadreObservacionForm(forms.ModelForm):
    """
    Formulario para observaciones de la madre que requiere
    la contraseña del usuario para la firma simple.
    """
    clave_firma = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        label="Clave de Firma"
    )

    def __init__(self, *args, **kwargs):
        # RECIBIMOS EL USUARIO DESDE LA VISTA
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = MadreObservacion
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ingrese aquí la observación...'
            }),
        }

    def clean_clave_firma(self):
        clave = self.cleaned_data.get('clave_firma')

        if not clave:
            raise forms.ValidationError("Debe ingresar la clave para validar la observación.")

        # Validar que haya un usuario autenticado
        if self.user is None or not self.user.is_authenticated:
            raise forms.ValidationError("Debe iniciar sesión para poder firmar la observación.")

        # Comparar con la contraseña real del usuario logueado
        if not self.user.check_password(clave):
            raise forms.ValidationError("La clave no coincide con su contraseña de usuario.")

        return clave


class MadreDeleteForm(forms.Form):
    """
    Formulario para eliminar una madre:
    - Pide motivo
    - Pide clave de firma (contraseña del usuario)
    """
    razon = forms.CharField(
        label="Motivo de eliminación",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Explique brevemente por qué se elimina esta madre..."
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

class DefuncionMadreForm(forms.ModelForm):
    class Meta:
        model = DefuncionMadre
        fields = ['razon']
        widgets = {
            'razon': forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
        }