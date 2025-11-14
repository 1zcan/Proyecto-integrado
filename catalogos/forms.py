# catalogos/forms.py
from django import forms
from .models import Catalogo

class CatalogoForm(forms.ModelForm):
    
    class Meta:
        model = Catalogo
        fields = ['tipo', 'valor', 'activo', 'orden']
        # Opcional: widgets para que se vea mejor
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opcional: Poner 'Tipo' como un campo de solo lectura
        # si estás editando, para evitar cambiar un valor de grupo.
        if self.instance and self.instance.pk:
            self.fields['tipo'].disabled = True