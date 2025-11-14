# madre/forms.py
from django import forms
from .models import Madre, TamizajeMaterno, MadreObservacion

class MadreForm(forms.ModelForm):
    """
    Formulario para la ficha sociodemográfica y documentos.
    """
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
            'documentos'
        ]

class TamizajeMaternoForm(forms.ModelForm):
    """
    Formulario para los tamizajes REM A11.
    """
    class Meta:
        model = TamizajeMaterno
        fields = [
            'vdrl_resultado', 
            'vdrl_tratamiento', 
            'vih_resultado',
            'hepb_resultado', 
            'profilaxis_vhb_completa'
        ]

class MadreObservacionForm(forms.ModelForm):
    """
    Formulario para observaciones firmadas.
    """
    clave_firma = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = MadreObservacion
        fields = ['texto'] # 'autor' y 'madre' se asignan en la vista