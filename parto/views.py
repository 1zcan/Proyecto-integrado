# parto/views.py
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from .models import Parto, ModeloAtencionParto, RobsonParto, PartoObservacion
from .forms import PartoForm, ModeloAtencionForm, RobsonForm, PartoObservacionForm
from catalogo.models import Catalogo


class PartoListView(ListView):
    model = Parto
    template_name = "parto/parto_lista.html"
    context_object_name = "partos"
    paginate_by = 25

    def get_queryset(self):
        qs = Parto.objects.filter(activo=True).select_related('madre')

        # --- FILTROS ---
        request = self.request.GET

        # Filtro por fechas
        fecha_inicio = request.get("filtro_fecha_inicio")
        fecha_fin = request.get("filtro_fecha_fin")
        if fecha_inicio:
            qs = qs.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            qs = qs.filter(fecha__lte=fecha_fin)

        # Filtro por tipo de parto
        tipo = request.get("filtro_tipo")
        if tipo:
            qs = qs.filter(tipo_parto_id=tipo)

        # Filtro por establecimiento
        establecimiento = request.get("filtro_establecimiento")
        if establecimiento:
            qs = qs.filter(establecimiento_id=establecimiento)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipos_parto"] = Catalogo.objects.filter(
            tipo="VAL_TIPO_PARTO", activo=True
        ).order_by("valor")
        context["establecimientos"] = Catalogo.objects.filter(
            tipo="VAL_ESTABLECIMIENTO", activo=True
        ).order_by("valor")

        # Mantener selección del usuario
        context["selected_tipo"] = self.request.GET.get("filtro_tipo", "")
        context["selected_establecimiento"] = self.request.GET.get("filtro_establecimiento", "")
        context["selected_fecha_inicio"] = self.request.GET.get("filtro_fecha_inicio", "")
        context["selected_fecha_fin"] = self.request.GET.get("filtro_fecha_fin", "")
        return context


class PartoCreateUpdateView(UpdateView):
    model = Parto
    form_class = PartoForm
    template_name = "parto/parto_form.html"
    success_url = reverse_lazy('parto_lista')


class ModeloAtencionUpdateView(UpdateView):
    model = ModeloAtencionParto
    form_class = ModeloAtencionForm
    template_name = "parto/parto_modelo_atencion.html"

    def get_object(self, queryset=None):
        parto_pk = self.kwargs.get('pk')
        parto = Parto.objects.get(pk=parto_pk)
        obj, created = ModeloAtencionParto.objects.get_or_create(parto=parto)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parto_pk = self.kwargs.get('pk')
        context['parto'] = Parto.objects.get(pk=parto_pk)
        return context

    def get_success_url(self):
        return reverse_lazy('parto_lista')

class RobsonUpdateView(UpdateView):
    model = RobsonParto
    form_class = RobsonForm
    template_name = "parto/parto_robson.html"

    def get_object(self, queryset=None):
        parto_pk = self.kwargs.get('pk')
        parto = Parto.objects.get(pk=parto_pk)
        obj, created = RobsonParto.objects.get_or_create(parto=parto)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parto_pk = self.kwargs.get('pk')
        context['parto'] = Parto.objects.get(pk=parto_pk)
        return context

    def get_success_url(self):
        return reverse_lazy('parto_lista')


class PartoObservacionesView(CreateView):
    model = PartoObservacion
    form_class = PartoObservacionForm
    template_name = "parto/parto_observaciones.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Trae el objeto Parto para la plantilla
        parto_pk = self.kwargs.get('parto_pk')
        context['parto'] = Parto.objects.get(pk=parto_pk)
        return context

    def form_valid(self, form):
        # Asigna automáticamente autor, parto y firma
        form.instance.autor = self.request.user
        form.instance.parto = Parto.objects.get(pk=self.kwargs['parto_pk'])
        form.instance.firma_simple = True
        return super().form_valid(form)

    def get_success_url(self):
        # Redirige a la misma página de observaciones del parto
        return reverse('parto_observaciones', kwargs={'parto_pk': self.kwargs['parto_pk']})


class PartoCreateView(CreateView):
    model = Parto
    form_class = PartoForm
    template_name = 'parto/parto_form.html'

    def get_initial(self):
        return {'madre': self.kwargs['madre_id']}

    def form_valid(self, form):
        form.instance.madre_id = self.kwargs['madre_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('parto_lista')
