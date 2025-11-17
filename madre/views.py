# madre/views.py
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Madre, TamizajeMaterno, MadreObservacion
from .forms import MadreForm, TamizajeMaternoForm, MadreObservacionForm


class MadreListView(ListView):
    """
    Vista para listar madres (pacientes)
    """
    model = Madre
    template_name = "madre/madre_lista.html"
    context_object_name = "madres"
    paginate_by = 25

    def get_queryset(self):
        # Usamos select_related para evitar N+1 al acceder a comuna/cesfam en la tabla
        qs = Madre.objects.select_related("comuna", "cesfam").filter(activo=True)

        # --- 🟢 INICIO DE LA CORRECCIÓN (Añadir filtro RUT) ---
        
        # 1. Obtenemos todos los valores de los filtros
        rut = self.request.GET.get("rut")
        comuna = self.request.GET.get("comuna")
        cesfam = self.request.GET.get("cesfam")

        # 2. Aplicamos el filtro RUT (Nuevo)
        if rut:
            # Usamos 'icontains' para que la búsqueda no sea exacta (ej. 12345)
            qs = qs.filter(rut__icontains=rut)

        # 3. Aplicamos los filtros existentes
        if comuna:
            qs = qs.filter(comuna_id=comuna)

        if cesfam:
            qs = qs.filter(cesfam_id=cesfam)
            
        # --- 🟢 FIN DE LA CORRECCIÓN ---

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from catalogo.models import Catalogo

        # (Esto se mantiene igual, es para poblar los dropdowns)
        context["comunas"] = Catalogo.objects.filter(tipo="VAL_COMUNA", activo=True).order_by("valor")
        context["cesfams"] = Catalogo.objects.filter(tipo="VAL_ESTABLECIMIENTO", activo=True).order_by("valor")

        context["selected_comuna"] = self.request.GET.get("comuna", "")
        context["selected_cesfam"] = self.request.GET.get("cesfam", "")
        
        # (El template ya maneja el valor del RUT con {{ request.GET.rut }})

        return context


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


class TamizajeCreateUpdateView(UpdateView):
    """
    Vista para gestionar el tamizaje REM A11 
    """
    model = TamizajeMaterno
    form_class = TamizajeMaternoForm
    template_name = "madre/madre_tamizajes.html"

    def get_object(self, queryset=None):
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
        form.instance.autor = self.request.user
        form.instance.madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        form.instance.firma_simple = True
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        context['madre'] = madre
        context['observaciones'] = madre.observaciones.all()  # Historial de observaciones
        return context

    def get_success_url(self):
        # Redirige a la misma página de observaciones para mostrar la nueva
        return reverse_lazy(
            'madre_observaciones',
            kwargs={'madre_pk': self.kwargs['madre_pk']}
        )