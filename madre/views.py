from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from usuarios.decorators import role_required

from .models import Madre, TamizajeMaterno, MadreObservacion
from .forms import MadreForm, TamizajeMaternoForm, MadreObservacionForm, MadreDeleteForm
from recien_nacido.models import RecienNacido
from auditoria.models import LogAccion
from auditoria.signals import get_client_ip


# LISTADO: Acceso para todos los roles del sistema (necesitan buscar pacientes)
@method_decorator(
    role_required(
        ['administrativo', 'profesional_salud', 'tecnico_salud', 'ti_informatica']
    ),
    name='dispatch'
)
class MadreListView(ListView):
    model = Madre
    template_name = "madre/madre_lista.html"
    context_object_name = "madres"
    paginate_by = 25

    def get_queryset(self):
        qs = Madre.objects.select_related("comuna", "cesfam").filter(activo=True)
        rut = self.request.GET.get("rut")
        comuna = self.request.GET.get("comuna")
        cesfam = self.request.GET.get("cesfam")

        if rut:
            qs = qs.filter(rut__icontains=rut)
        if comuna:
            qs = qs.filter(comuna_id=comuna)
        if cesfam:
            qs = qs.filter(cesfam_id=cesfam)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from catalogo.models import Catalogo
        context["comunas"] = Catalogo.objects.filter(
            tipo="VAL_COMUNA", activo=True
        ).order_by("valor")
        context["cesfams"] = Catalogo.objects.filter(
            tipo="VAL_ESTABLECIMIENTO", activo=True
        ).order_by("valor")
        context["selected_comuna"] = self.request.GET.get("comuna", "")
        context["selected_cesfam"] = self.request.GET.get("cesfam", "")
        return context


# CREAR (Datos Demográficos): Admisión, Profesionales y TI.
@method_decorator(
    role_required(['administrativo', 'profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreCreateView(CreateView):
    model = Madre
    form_class = MadreForm
    template_name = "madre/madre_form.html"
    # ANTES: success_url = reverse_lazy('madre_lista')
    success_url = reverse_lazy('madre:madre_lista')


# EDITAR (Datos Demográficos): Admisión, Profesionales y TI.
@method_decorator(
    role_required(['administrativo', 'profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreUpdateView(UpdateView):
    model = Madre
    form_class = MadreForm
    template_name = "madre/madre_form.html"
    # ANTES: success_url = reverse_lazy('madre_lista')
    success_url = reverse_lazy('madre:madre_lista')


# DATOS CLÍNICOS (Tamizajes): EXCLUSIVO Salud (Profesional y Técnico).
# Administrativo NO entra aquí.
@method_decorator(
    role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class TamizajeCreateUpdateView(UpdateView):
    model = TamizajeMaterno
    form_class = TamizajeMaternoForm
    template_name = "madre/madre_tamizajes.html"

    def get_object(self, queryset=None):
        madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        obj, created = TamizajeMaterno.objects.get_or_create(madre=madre)
        return obj

    def get_success_url(self):
        # ANTES: reverse_lazy('madre_lista')
        return reverse_lazy('madre:madre_lista')


# FIRMA (Observaciones): EXCLUSIVO Profesional de Salud (Médico/Matrona).
# Técnico NO firma.
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreObservacionesView(LoginRequiredMixin, CreateView):
    model = MadreObservacion
    form_class = MadreObservacionForm
    template_name = "madre/madre_observaciones.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.autor = self.request.user
        form.instance.madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        form.instance.firma_simple = True
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        context['madre'] = madre
        context['observaciones'] = madre.observaciones.all()
        return context

    def get_success_url(self):
        # ANTES: reverse_lazy('madre_observaciones', kwargs={...})
        return reverse_lazy('madre:madre_observaciones',
                            kwargs={'madre_pk': self.kwargs['madre_pk']})


# ELIMINAR: Solo Profesionales (Responsables) y TI (Soporte técnico).
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreDeleteView(LoginRequiredMixin, View):
    template_name = "madre/madre_confirm_delete.html"

    def get(self, request, pk):
        madre = get_object_or_404(Madre, pk=pk, activo=True)
        hijos = RecienNacido.objects.filter(parto__madre=madre)
        form = MadreDeleteForm(user=request.user)
        context = {
            "madre": madre,
            "hijos": hijos,
            "total_hijos": hijos.count(),
            "form": form,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        madre = get_object_or_404(Madre, pk=pk, activo=True)
        hijos = RecienNacido.objects.filter(parto__madre=madre)
        form = MadreDeleteForm(request.POST, user=request.user)

        if not form.is_valid():
            context = {
                "madre": madre,
                "hijos": hijos,
                "total_hijos": hijos.count(),
                "form": form,
            }
            return render(request, self.template_name, context)

        razon = form.cleaned_data["razon"]
        detalle = (
            f"Eliminación de Madre ID={madre.id}, RUT={madre.rut}. "
            f"Motivo: {razon}. Total RN eliminados: {hijos.count()}."
        )

        LogAccion.objects.create(
            usuario=request.user,
            accion=LogAccion.ACCION_DELETE,
            modelo="Madre",
            objeto_id=str(madre.pk),
            detalle=detalle,
            ip_address=get_client_ip(),
        )

        madre.partos.all().delete()
        madre.delete()

        messages.success(request, "Madre y registros asociados eliminados correctamente.")
        # ANTES: redirect("madre_lista")
        return redirect("madre:madre_lista")
