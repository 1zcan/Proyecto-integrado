# madre/forms.py
from django import forms
from .models import Madre, TamizajeMaterno, MadreObservacion
from catalogo.models import Catalogo   # <--- NECESARIO PARA OPCIÓN B


class MadreForm(forms.ModelForm):
    """
    Formulario para la ficha sociodemográfica y documentos.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- LISTAS DESPLEGABLEES DESDE CATÁLOGO ---
        self.fields['comuna'].queryset = Catalogo.objects.filter(
            tipo='VAL_COMUNA',
            activo=True
        ).order_by('orden', 'valor')

        self.fields['cesfam'].queryset = Catalogo.objects.filter(
            tipo='VAL_ESTABLECIMIENTO',
            activo=True
        ).order_by('orden', 'valor')

        # Etiquetas vacías más amigables
        self.fields['comuna'].empty_label = "Seleccione una comuna"
        self.fields['cesfam'].empty_label = "Seleccione un establecimiento"

        # Aplicar clases Bootstrap a todos los campos
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Select, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})

        # Campos checkbox
        check_fields = ['migrante', 'pueblo_originario', 'discapacidad']
        for name in check_fields:
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-check-input'})

        # Campo fecha como calendario
        if 'fecha_nacimiento' in self.fields:
            self.fields['fecha_nacimiento'].widget = forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            )

    class Meta:
        model = Madre
        fields = [
            'rut',
            'nombre_completo',
            'fecha_nacimiento',
            'comuna',
            'cesfam',
            'migrante',
            'pueblo_originario',
            'discapacidad',
            'documentos',
        ]


class TamizajeMaternoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        select_fields = ['vdrl_resultado', 'vih_resultado', 'hepb_resultado']
        for field in select_fields:
            if field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-select'})

        check_fields = ['vdrl_tratamiento', 'profilaxis_vhb_completa']
        for field in check_fields:
            if field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})

    class Meta:
        model = TamizajeMaterno
        fields = [
            'vdrl_resultado',
            'vdrl_tratamiento',
            'vih_resultado',
            'hepb_resultado',
            'profilaxis_vhb_completa',
        ]


class MadreObservacionForm(forms.ModelForm):
    clave_firma = forms.CharField(widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['texto'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4
        })

        self.fields['clave_firma'].widget.attrs.update({
            'class': 'form-control'
        })

    class Meta:
        model = MadreObservacion
        fields = ['texto']
