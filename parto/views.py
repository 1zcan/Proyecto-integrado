# parto/views.py
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import Parto, ModeloAtencionParto, RobsonParto, PartoObservacion
from .forms import PartoForm, ModeloAtencionForm, RobsonForm, PartoObservacionForm
from django.urls import reverse, reverse_lazy
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
        # [cite_start]Aquí se implementan los filtros [cite: 193]
        return Parto.objects.filter(activo=True).select_related('madre')

class PartoCreateUpdateView(UpdateView): # O CreateView/UpdateView separadas
    """
    Vista para crear y actualizar el registro del parto 
    """
    model = Parto
    form_class = PartoForm
    template_name = "parto/parto_form.html"
    success_url = reverse_lazy('parto_lista')
    # Nota: El doc  la llama CreateUpdateView. 
    # Usualmente se usan CreateView y UpdateView separadas.
    # Esta implementación es de UpdateView; se necesitaría una CreateView.

class ModeloAtencionUpdateView(UpdateView):
    """
    Vista para actualizar el Modelo de Atención (REM A21) 
    """
    model = ModeloAtencionParto
    form_class = ModeloAtencionForm
    template_name = "parto/parto_modelo_atencion.html"
    
    # --- 🟢 INICIO DE LA CORRECCIÓN ---
    def get_object(self, queryset=None):
        """
        Implementa la lógica "Get or Create" (Obtener o Crear).
        Busca el ModeloAtencionParto; si no existe, lo crea.
        """
        # Obtenemos el Parto (padre) usando la 'pk' de la URL
        parto_pk = self.kwargs.get('pk')
        parto = Parto.objects.get(pk=parto_pk)
        
        try:
            # Intentamos obtener el ModeloAtencionParto relacionado
            # (Asumimos relación OneToOne 'parto')
            modelo_atencion = ModeloAtencionParto.objects.get(parto=parto)
        except ModeloAtencionParto.DoesNotExist:
            # ¡No existe! Lo creamos vacío.
            print(f"Creando ModeloAtencionParto para Parto ID: {parto_pk}")
            modelo_atencion = ModeloAtencionParto.objects.create(parto=parto)
        
        # Devolvemos el objeto (ya sea el encontrado o el recién creado)
        return modelo_atencion

    def get_success_url(self):
        # Redirige de vuelta a la lista de partos
        return reverse_lazy('parto_lista')
    # --- 🟢 FIN DE LA CORRECCIÓN ---

class RobsonUpdateView(UpdateView):
    """
    Vista para actualizar la Clasificación Robson 
    """
    model = RobsonParto
    form_class = RobsonForm
    template_name = "parto/parto_robson.html"
    
    # --- 🟢 INICIO DE LA CORRECCIÓN (MISMA LÓGICA) ---
    def get_object(self, queryset=None):
        """
        Implementa la lógica "Get or Create" (Obtener o Crear).
        Busca el RobsonParto; si no existe, lo crea.
        """
        parto_pk = self.kwargs.get('pk')
        parto = Parto.objects.get(pk=parto_pk)
        
        try:
            # Intentamos obtener el RobsonParto relacionado
            robson = RobsonParto.objects.get(parto=parto)
        except RobsonParto.DoesNotExist:
            # ¡No existe! Lo creamos vacío.
            print(f"Creando RobsonParto para Parto ID: {parto_pk}")
            robson = RobsonParto.objects.create(parto=parto)
        
        return robson

    def get_success_url(self):
        # Redirige de vuelta a la lista de partos
        return reverse_lazy('parto_lista')
    # --- 🟢 FIN DE LA CORRECCIÓN ---

class PartoObservacionesView(CreateView): # Usualmente un CreateView + ListView
    """
    Vista para gestionar observaciones del parto 
    """
    model = PartoObservacion
    form_class = PartoObservacionForm
    template_name = "parto/parto_observaciones.html"
    
    def form_valid(self, form):
        # [cite_start]1. Validar la clave_firma del form contra el Usuario [cite: 88, 308]
        # ... (Lógica de validación de firma_clave hash)
        
        # 2. Asignar autor y parto
        form.instance.autor = self.request.user
        form.instance.parto = Parto.objects.get(pk=self.kwargs['parto_pk'])
        form.instance.firma_simple = True # Si la validación de clave fue exitosa
        
        # [cite_start]3. Guardar y registrar en auditoría [cite: 81, 220]
        return super().form_valid(form)
    
    
class PartoCreateView(CreateView):
    model = Parto
    form_class = PartoForm
    template_name = 'parto/parto_form.html'

    def get_initial(self):
        return {
            'madre': self.kwargs['madre_id']
        }

    def form_valid(self, form):
        form.instance.madre_id = self.kwargs['madre_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('parto_lista')