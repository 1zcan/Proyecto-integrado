# recien_nacido/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DetailView, CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
# Usamos timezone y messages para la vista de validación de alta
from django.utils import timezone 
from django.contrib import messages 

from .models import RecienNacido, ProfiRN, RNObservacion
# Importamos el formulario unificado (RNForm) y auxiliares
from .forms import RNForm, ProfiRNForm, RNObservacionForm
from parto.models import Parto


# ================================================
#  1. LISTA DE TODOS LOS RECIÉN NACIDOS
# ================================================
class RNListView(LoginRequiredMixin, ListView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista.html'
    context_object_name = 'recien_nacidos'
    paginate_by = 25

    def get_queryset(self):
        # Muestra todos los RNs
        return super().get_queryset().select_related('parto', 'parto__madre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Contar pendientes de alta para mostrar en el botón de navegación
        context['recien_nacidos_pendientes_count'] = RecienNacido.objects.filter(fecha_alta__isnull=True).count()
        return context


# ================================================
#  🟢 2. LISTA DE RN PENDIENTES DE ALTA (Clase Faltante)
# ================================================
class RNAltaPendienteListView(LoginRequiredMixin, ListView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista_pendientes_alta.html'
    context_object_name = 'recien_nacidos_pendientes' 
    
    def get_queryset(self):
        # Filtra solo los Recién Nacidos que no tienen fecha de alta (están pendientes)
        return RecienNacido.objects.filter(fecha_alta__isnull=True).select_related('parto', 'parto__madre')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_pending_list'] = True
        return context


# ================================================
#  3. CREAR RECIÉN NACIDO (Flujo Único)
# ================================================
class RNCreateView(LoginRequiredMixin, CreateView):
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'
    
    def get_success_url(self):
        return reverse('recien_nacido:rn_lista')

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creating'] = True
        return context


# ================================================
#  4. EDITAR RECIÉN NACIDO
# ================================================
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
#  5. VALIDACIÓN DE ALTA
# ================================================
class RNValidarAltaView(LoginRequiredMixin, DetailView):
    """
    Vista para mostrar la pantalla de validación de alta del Recién Nacido
    y procesar las acciones de 'Validar Alta' y 'Enviar a Corrección'.
    """
    model = RecienNacido
    template_name = 'recien_nacido/rn_validar_alta.html'
    context_object_name = 'rn'

    # --------- MÉTODO AUXILIAR: evalúa datos críticos ----------
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

    # --------- GET: solo mostrar la pantalla ----------
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

    # --------- POST: manejar los botones del formulario ----------
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        rn = self.object

        # Re-evaluar datos críticos
        datos_criticos_completos, mensajes_error, profilaxis_completa = \
            self.evaluar_datos_criticos(rn)

        action = request.POST.get("action")

        # 1) VALIDAR ALTA
        if action == "validar_alta":
            if not datos_criticos_completos:
                messages.error(
                    request,
                    "No se puede validar el alta porque faltan datos críticos."
                )
                # Volver a mostrar la misma página con los errores
                context = self.get_context_data()
                # por si acaso, sobre-escribimos por consistencia
                context['datos_criticos_completos'] = datos_criticos_completos
                context['mensajes_error'] = mensajes_error
                context['profilaxis_completa'] = profilaxis_completa
                return render(request, self.template_name, context)

            # Si está todo OK, marcar alta
            rn.fecha_alta = timezone.now()
            rn.save()
            messages.success(request, "Alta validada correctamente.")
            return redirect('recien_nacido:rn_pendientes_alta')

        # 2) ENVIAR A CORRECCIÓN
        elif action == "enviar_correccion":
            messages.warning(
                request,
                "El registro se ha marcado para corrección. Revise y edite los datos del RN."
            )
            return redirect('recien_nacido:rn_editar', pk=rn.pk)

        # Acción desconocida: simplemente recargar
        messages.error(request, "Acción no reconocida.")
        return redirect(request.path_info)



# ================================================
#  6. PROFILAXIS Y OBSERVACIONES (Vistas ya existentes)
# ================================================
class RNProfilaxisView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_profilaxis.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profilaxis_form'] = ProfiRNForm()
        
        # --- 🟢 CORRECCIÓN APLICADA AQUÍ ---
        # Usamos el related_name correcto: 'profilaxis_set'
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


class RNObservacionesView(LoginRequiredMixin, DetailView):
    # ... (código sin cambios)
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