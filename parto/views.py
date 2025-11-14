# parto/views.py
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import Parto, ModeloAtencionParto, RobsonParto, PartoObservacion
from .forms import PartoForm, ModeloAtencionForm, RobsonForm, PartoObservacionForm
# Se necesitarían Mixins para permisos, ej: from seguridad.mixins import RolRequiredMixin

class PartoListView(ListView):
    """
    Vista para listar partos 
    """
    model = Parto
    template_name = "parto/parto_lista.html"
    context_object_name = "partos"
    paginate_by = 25
    
    def get_queryset(self):
        # Aquí se implementan los filtros [cite: 193]
        return Parto.objects.filter(activo=True).select_related('madre')

class PartoCreateUpdateView(UpdateView): # O CreateView/UpdateView separadas
    """
    Vista para crear y actualizar el registro del parto 
    """
    model = Parto
    form_class = PartoForm
    template_name = "parto/parto_form.html"
    success_url = reverse_lazy('parto_lista')
    # Nota: El doc  la llama CreateUpdateView. 
    # Usualmente se usan CreateView y UpdateView separadas.
    # Esta implementación es de UpdateView; se necesitaría una CreateView.

class ModeloAtencionUpdateView(UpdateView):
    """
    Vista para actualizar el Modelo de Atención (REM A21) 
    """
    model = ModeloAtencionParto
    form_class = ModeloAtencionForm
    template_name = "parto/parto_modelo_atencion.html"
    # El success_url debería redirigir de vuelta al detalle del parto

class RobsonUpdateView(UpdateView):
    """
    Vista para actualizar la Clasificación Robson 
    """
    model = RobsonParto
    form_class = RobsonForm
    template_name = "parto/parto_robson.html"
    # El success_url debería redirigir de vuelta al detalle del parto

class PartoObservacionesView(CreateView): # Usualmente un CreateView + ListView
    """
    Vista para gestionar observaciones del parto 
    """
    model = PartoObservacion
    form_class = PartoObservacionForm
    template_name = "parto/parto_observaciones.html"
    
    def form_valid(self, form):
        # 1. Validar la clave_firma del form contra el Usuario [cite: 88, 308]
        # ... (Lógica de validación de firma_clave hash)
        
        # 2. Asignar autor y parto
        form.instance.autor = self.request.user
        form.instance.parto = Parto.objects.get(pk=self.kwargs['parto_pk'])
        form.instance.firma_simple = True # Si la validación de clave fue exitosa
        
        # 3. Guardar y registrar en auditoría [cite: 81, 220]
        return super().form_valid(form)