# recien_nacido/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DetailView, CreateView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.utils import timezone
from django.contrib import messages
from django.utils.decorators import method_decorator  
from usuarios.decorators import role_required 

from .models import RecienNacido, ProfiRN, RNObservacion
from .forms import RNForm, ProfiRNForm, RNObservacionForm, RNDeleteForm
from parto.models import Parto

from auditoria.models import LogAccion
from auditoria.signals import get_client_ip


# ================================================
#  1. LISTA DE TODOS LOS RECIÉN NACIDOS
# ================================================
@method_decorator(role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']), name='dispatch')
class RNListView(LoginRequiredMixin, ListView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista.html'
    context_object_name = 'recien_nacidos'
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().select_related('parto', 'parto__madre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recien_nacidos_pendientes_count'] = RecienNacido.objects.filter(fecha_alta__isnull=True).count()
        return context


# ================================================
#  2. LISTA DE RN PENDIENTES DE ALTA
# ================================================
@method_decorator(role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']), name='dispatch')
class RNAltaPendienteListView(LoginRequiredMixin, ListView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista_pendientes_alta.html'
    context_object_name = 'recien_nacidos_pendientes'

    def get_queryset(self):
        return RecienNacido.objects.filter(fecha_alta__isnull=True).select_related('parto', 'parto__madre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_pending_list'] = True
        return context


# ================================================
#  3. CREAR RECIÉN NACIDO
# ================================================
@method_decorator(role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']), name='dispatch')
class RNCreateView(LoginRequiredMixin, CreateView):
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'

    def get_success_url(self):
        return reverse('recien_nacido:rn_lista')

    def form_valid(self, form):
        if hasattr(form.instance, "creado_por"):
            form.instance.creado_por = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creating'] = True
        return context


# ================================================
#  4. EDITAR RECIÉN NACIDO
# ================================================
@method_decorator(role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']), name='dispatch')
class RNUpdateView(LoginRequiredMixin, UpdateView):
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'

    def get_success_url(self):
        return reverse('recien_nacido:rn_lista')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creating'] = False
        return context


# ================================================
#  5. VALIDACIÓN DE ALTA (CRÍTICO)
# ================================================
# Exclusivo Profesional de Salud (Médico/Matrona). Técnico y TI BLOQUEADOS.
@method_decorator(role_required(['profesional_salud']), name='dispatch')
class RNValidarAltaView(LoginRequiredMixin, DetailView):
    """
    Vista para mostrar la pantalla de validación de alta del Recién Nacido
    y procesar las acciones de 'Validar Alta' y 'Enviar a Corrección'.
    """
    model = RecienNacido
    template_name = 'recien_nacido/rn_validar_alta.html'
    context_object_name = 'rn'

    def evaluar_datos_criticos(self, rn):
        datos_criticos_completos = True
        mensajes_error = []

        # 1. Peso y talla
        if rn.peso is None or rn.peso <= 0:
            datos_criticos_completos = False
            mensajes_error.append("El peso del Recién Nacido es un dato crítico y falta.")
        if rn.talla is None or rn.talla <= 0:
            datos_criticos_completos = False
            mensajes_error.append("La talla del Recién Nacido es un dato crítico y falta.")

        # 2. APGAR 5'
        if rn.apgar_5 is None:
            datos_criticos_completos = False
            mensajes_error.append("El APGAR a los 5 minutos es un dato crítico y falta.")

        # 3. Profilaxis
        profilaxis_completa = rn.profilaxis_set.exists()
        if not profilaxis_completa:
            datos_criticos_completos = False
            mensajes_error.append("No se ha registrado ninguna profilaxis para el Recién Nacido.")

        return datos_criticos_completos, mensajes_error, profilaxis_completa

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rn = self.object

        datos_criticos_completos, mensajes_error, profilaxis_completa = \
            self.evaluar_datos_criticos(rn)

        context['datos_criticos_completos'] = datos_criticos_completos
        context['mensajes_error'] = mensajes_error
        context['profilaxis_completa'] = profilaxis_completa
        context['id_unico_rn'] = f"M{rn.parto.madre.pk:03d}-RN{rn.pk:03d}"

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        rn = self.object

        datos_criticos_completos, mensajes_error, profilaxis_completa = \
            self.evaluar_datos_criticos(rn)

        action = request.POST.get("action")

        if action == "validar_alta":
            if not datos_criticos_completos:
                messages.error(request, "No se puede validar el alta porque faltan datos críticos.")
                context = self.get_context_data()
                context['datos_criticos_completos'] = datos_criticos_completos
                context['mensajes_error'] = mensajes_error
                context['profilaxis_completa'] = profilaxis_completa
                return render(request, self.template_name, context)

            rn.fecha_alta = timezone.now()
            rn.save()
            messages.success(request, "Alta validada correctamente.")
            return redirect('recien_nacido:rn_pendientes_alta')

        elif action == "enviar_correccion":
            messages.warning(request, "El registro se ha marcado para corrección. Revise y edite los datos del RN.")
            return redirect('recien_nacido:rn_editar', pk=rn.pk)

        messages.error(request, "Acción no reconocida.")
        return redirect(request.path_info)


# ================================================
#  6. PROFILAXIS (VACUNAS)
# ================================================
# TENS habilitados para registrar vacunas
@method_decorator(role_required(['profesional_salud', 'tecnico_salud']), name='dispatch')
class RNProfilaxisView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_profilaxis.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profilaxis_form'] = ProfiRNForm()
        context['profilaxis_list'] = self.object.profilaxis_set.all().select_related('tipo', 'registrado_por')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProfiRNForm(request.POST)

        if form.is_valid():
            prof = form.save(commit=False)
            prof.rn = self.object
            prof.registrado_por = request.user
            prof.save()
            return redirect(request.path_info)

        context = self.get_context_data()
        context['profilaxis_form'] = form
        return render(request, self.template_name, context)


# ================================================
#  7. OBSERVACIONES
# ================================================
# TENS y Profesionales pueden dejar notas/observaciones
@method_decorator(role_required(['profesional_salud', 'tecnico_salud']), name='dispatch')
class RNObservacionesView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_observaciones.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['observacion_form'] = RNObservacionForm()
        context['observaciones'] = self.object.observaciones.all().select_related('autor')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = RNObservacionForm(request.POST)

        if form.is_valid():
            obs = form.save(commit=False)
            obs.rn = self.object
            obs.autor = request.user
            obs.save()
            return redirect(request.path_info)

        context = self.get_context_data()
        context['observacion_form'] = form
        return render(request, self.template_name, context)


# ================================================
#  8. ELIMINAR RECIÉN NACIDO
# ================================================
# Restringido: Solo TI (Soporte) y Profesional Salud. TENS NO puede eliminar.
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class RNDeleteView(LoginRequiredMixin, View):
    """
    Vista para eliminar un Recién Nacido.
    """
    template_name = "recien_nacido/rn_confirm_delete.html"

    def get(self, request, pk):
        rn = get_object_or_404(RecienNacido, pk=pk)
        form = RNDeleteForm(user=request.user)

        context = {
            "rn": rn,
            "form": form,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        rn = get_object_or_404(RecienNacido, pk=pk)
        form = RNDeleteForm(request.POST, user=request.user)

        if not form.is_valid():
            context = {
                "rn": rn,
                "form": form,
            }
            return render(request, self.template_name, context)

        razon = form.cleaned_data["razon"]

        detalle = (
            f"Eliminación de RN ID={rn.id}, "
            f"Madre RUT={rn.parto.madre.rut}, Madre={rn.parto.madre.nombre_completo}. "
            f"Motivo: {razon}."
        )

        LogAccion.objects.create(
            usuario=request.user,
            accion=LogAccion.ACCION_DELETE,
            modelo="RecienNacido",
            objeto_id=str(rn.pk),
            detalle=detalle,
            ip_address=get_client_ip(),
        )

        rn.delete()

        messages.success(
            request,
            "Recién nacido eliminado correctamente. La ficha de la madre y otros RN asociados no fueron modificados."
        )
        return redirect("recien_nacido:rn_lista")