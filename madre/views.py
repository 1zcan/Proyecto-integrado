# madre/views.py
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Madre, TamizajeMaterno, MadreObservacion
from .forms import MadreForm, TamizajeMaternoForm, MadreObservacionForm
# Se necesitarían Mixins para permisos

class MadreListView(ListView):
    """
    Vista para listar madres (pacientes) 
    """
    model = Madre
    template_name = "madre/madre_lista.html"
    context_object_name = "madres"
    paginate_by = 25
    
    def get_queryset(self):
        # Aquí se implementarían los filtros (comuna, cesfam) [cite: 168]
        return Madre.objects.filter(activo=True)

class MadreCreateView(CreateView):
    """
    Vista para registrar una nueva madre 
    """
    model = Madre
    form_class = MadreForm
    template_name = "madre/madre_form.html"
    success_url = reverse_lazy('madre_lista')

class MadreUpdateView(UpdateView):
    """
    Vista para editar la ficha de la madre 
    """
    model = Madre
    form_class = MadreForm
    template_name = "madre/madre_form.html"
    success_url = reverse_lazy('madre_lista')

class TamizajeCreateUpdateView(UpdateView): # O CreateView/UpdateView
    """
    Vista para gestionar el tamizaje REM A11 
    """
    model = TamizajeMaterno
    form_class = TamizajeMaternoForm
    template_name = "madre/madre_tamizajes.html"
    
    # Se debe ajustar la lógica para que cree el Tamizaje si no existe,
    # o lo actualice si ya existe (OneToOneField).

    def get_object(self, queryset=None):
        # Obtener o crear el objeto Tamizaje para la madre
        madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        obj, created = TamizajeMaterno.objects.get_or_create(madre=madre)
        return obj

    def get_success_url(self):
        return reverse_lazy('madre_lista')

class MadreObservacionesView(CreateView):
    """
    Vista para añadir observaciones firmadas 
    """
    model = MadreObservacion
    form_class = MadreObservacionForm
    template_name = "madre/madre_observaciones.html"
    
    def form_valid(self, form):
        # 1. Validar la clave_firma
        # ... (Lógica de validación de firma_clave hash contra request.user)
        
        # 2. Asignar autor y madre
        form.instance.autor = self.request.user
        form.instance.madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        form.instance.firma_simple = True # Si la firma es válida
        
        return super().form_valid(form)

    def get_success_url(self):
        # Volver a la misma página de observaciones
        return reverse_lazy('madre_observaciones', kwargs={'madre_pk': self.kwargs['madre_pk']})