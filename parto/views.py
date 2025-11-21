from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from usuarios.decorators import role_required
from .models import Parto, ModeloAtencionParto, RobsonParto, PartoObservacion
from .forms import PartoForm, ModeloAtencionForm, RobsonForm, PartoObservacionForm
from catalogo.models import Catalogo
from django.shortcuts import get_object_or_404
from madre.models import Madre


# LISTADO: Profesional, TI y TENS
@method_decorator(role_required(['profesional_salud', 'ti_informatica', 'tecnico_salud']), name='dispatch')
class PartoListView(ListView):
    model = Parto
    template_name = "parto/parto_lista.html"
    context_object_name = "partos"
    paginate_by = 25

    def get_queryset(self):
        qs = Parto.objects.filter(activo=True).select_related('madre')

        request = self.request.GET
        fecha_inicio = request.get("filtro_fecha_inicio")
        fecha_fin = request.get("filtro_fecha_fin")
        tipo = request.get("filtro_tipo")
        establecimiento = request.get("filtro_establecimiento")

        if fecha_inicio:
            qs = qs.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            qs = qs.filter(fecha__lte=fecha_fin)
        if tipo:
            qs = qs.filter(tipo_parto_id=tipo)
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

        context["selected_tipo"] = self.request.GET.get("filtro_tipo", "")
        context["selected_establecimiento"] = self.request.GET.get("filtro_establecimiento", "")
        context["selected_fecha_inicio"] = self.request.GET.get("filtro_fecha_inicio", "")
        context["selected_fecha_fin"] = self.request.GET.get("filtro_fecha_fin", "")
        return context


# EDITAR PARTO
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class PartoCreateUpdateView(UpdateView):
    model = Parto
    form_class = PartoForm
    template_name = "parto/parto_form.html"
    success_url = reverse_lazy('parto:parto_lista')


# CREAR PARTO DESDE FICHA DE MADRE (Opcional)
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class PartoCreateView(CreateView):
    model = Parto
    form_class = PartoForm
    template_name = 'parto/parto_form.html'

    def get_initial(self):
        initial = super().get_initial()

        madre_id = self.kwargs.get('madre_id')
        if not madre_id:
            madre_id = self.request.GET.get('madre_id')

        if madre_id:
            try:
                madre = Madre.objects.get(pk=madre_id)
                initial['madre'] = madre
            except Madre.DoesNotExist:
                pass

        return initial

    def form_valid(self, form):
        madre_id = self.kwargs.get('madre_id')

        if not madre_id:
            madre_id = self.request.POST.get('madre')

        if madre_id:
            try:
                madre = Madre.objects.get(pk=madre_id)
                form.instance.madre = madre
            except Madre.DoesNotExist:
                pass

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('parto:parto_lista')


# MODELO DE ATENCIÓN
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
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
        return reverse_lazy('parto:parto_lista')


# ROBSON
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
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
        return reverse_lazy('parto:parto_lista')


# OBSERVACIONES / FIRMA
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class PartoObservacionesView(LoginRequiredMixin, CreateView):
    model = PartoObservacion
    form_class = PartoObservacionForm
    template_name = "parto/parto_observaciones.html"

    def get_form_kwargs(self):
        """Inyectamos el usuario al form para validar la contraseña de firma."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user   # <--- clave correcta
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parto_pk = self.kwargs.get('parto_pk')
        context['parto'] = Parto.objects.get(pk=parto_pk)
        return context

    def form_valid(self, form):
        form.instance.autor = self.request.user
        form.instance.parto = Parto.objects.get(pk=self.kwargs['parto_pk'])
        form.instance.firma_simple = True
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('parto:parto_lista')
