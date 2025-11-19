# madre/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Madre, TamizajeMaterno, MadreObservacion
from .forms import MadreForm, TamizajeMaternoForm, MadreObservacionForm, MadreDeleteForm

from recien_nacido.models import RecienNacido
from auditoria.models import LogAccion
from auditoria.signals import get_client_ip


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

        # --- filtros ---
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


class MadreObservacionesView(LoginRequiredMixin, CreateView):
    """
    Vista para añadir observaciones firmadas.
    Requiere que el usuario ingrese su contraseña (firma simple).
    """
    model = MadreObservacion
    form_class = MadreObservacionForm
    template_name = "madre/madre_observaciones.html"

    def get_form_kwargs(self):
        """
        Aquí pasamos el usuario logueado al formulario para que
        pueda validar la clave de firma contra su contraseña real.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # CLAVE PARA LA VALIDACIÓN
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
        context['observaciones'] = madre.observaciones.all()  # Historial de observaciones
        return context

    def get_success_url(self):
        # Redirige a la misma página de observaciones para mostrar la nueva
        return reverse_lazy(
            'madre_observaciones',
            kwargs={'madre_pk': self.kwargs['madre_pk']}
        )


class MadreDeleteView(LoginRequiredMixin, View):
    """
    Vista para eliminar una Madre.

    Lógica:
    - Pide motivo + clave de firma (contraseña del usuario).
    - Muestra advertencia si tiene RN asociados.
    - Al confirmar:
        * Se eliminan los Partos de esa madre.
        * Por cascada, se eliminan los RN de esos partos.
        * Luego se elimina la propia Madre.
    - Todo queda registrado en LogAccion (auditoría).
    """
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

        # Construir detalle para la auditoría
        detalle = (
            f"Eliminación de Madre ID={madre.id}, RUT={madre.rut}, "
            f"Nombre={madre.nombre_completo}. Motivo: {razon}. "
            f"Total RN asociados eliminados: {hijos.count()}."
        )

        if hijos.exists():
            lista_hijos = ", ".join(
                [
                    f"RN ID={rn.id} (Parto ID={rn.parto_id}, Sexo={rn.get_sexo_display()}, Peso={rn.peso}g)"
                    for rn in hijos
                ]
            )
            detalle += f" Detalle RN: {lista_hijos}"

        LogAccion.objects.create(
            usuario=request.user,
            accion=LogAccion.ACCION_DELETE,
            modelo="Madre",
            objeto_id=str(madre.pk),
            detalle=detalle,
            ip_address=get_client_ip(),
        )

        # 1) Eliminar partos (esto cascadeará a RecienNacido por on_delete=CASCADE)
        madre.partos.all().delete()

        # 2) Eliminar la madre
        madre.delete()

        messages.success(
            request,
            "Madre eliminada correctamente. Todos los recién nacidos asociados también fueron eliminados."
        )
        return redirect("madre_lista")
