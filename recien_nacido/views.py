from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DetailView, CreateView, View
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from django.http import HttpResponse
import io

# Librería PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Importaciones del proyecto
from usuarios.decorators import role_required
from .models import RecienNacido, ProfiRN, RNObservacion, DefuncionRN
from .forms import RNForm, ProfiRNForm, RNObservacionForm, RNDeleteForm, DefuncionRNForm
from parto.models import Parto
from auditoria.models import LogAccion
from auditoria.utils import registrar_log   # 🟢 helper central
from auditoria.signals import get_client_ip


# ================================================
#  1. LISTA GENERAL DE RECIÉN NACIDOS
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class RNListView(LoginRequiredMixin, ListView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista.html'
    context_object_name = 'recien_nacidos'
    paginate_by = 25

    def get_queryset(self):
        # Solo RN activos (sin defunciones)
        return (
            super()
            .get_queryset()
            .select_related('parto', 'parto__madre')
            .filter(defunciones__isnull=True)
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Contador para el botón de "Validar Altas"
        context['recien_nacidos_pendientes_count'] = (
            RecienNacido.objects
            .filter(fecha_alta__isnull=True, defunciones__isnull=True)
            .distinct()
            .count()
        )
        return context


# ================================================
#  2. LISTA DE PENDIENTES DE ALTA
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class RNAltaPendienteListView(LoginRequiredMixin, ListView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista_pendientes_alta.html'
    context_object_name = 'recien_nacidos_pendientes'

    def get_queryset(self):
        return (
            RecienNacido.objects
            .filter(fecha_alta__isnull=True, defunciones__isnull=True)
            .select_related('parto', 'parto__madre')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_pending_list'] = True
        return context


# ================================================
#  3. CREAR RECIÉN NACIDO
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class RNCreateView(LoginRequiredMixin, CreateView):
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["is_edit"] = False
        return kwargs

    def get_success_url(self):
        return reverse('recien_nacido:rn_lista')

    def form_valid(self, form):
        """
        Guardado explícito + log de creación.
        """
        rn = form.save(commit=False)

        if hasattr(rn, "creado_por"):
            rn.creado_por = self.request.user

        rn.save()
        form.save_m2m()

        # 🟢 REGISTRO DE AUDITORÍA - CREACIÓN RN
        registrar_log(
            self.request,
            LogAccion.ACCION_CREATE,
            "RecienNacido",
            rn.pk,
            "RN creado desde el formulario de creación.",
        )

        messages.success(self.request, "Recién nacido creado correctamente.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creating'] = True
        return context


# ================================================
#  4. EDITAR RECIÉN NACIDO
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class RNUpdateView(LoginRequiredMixin, UpdateView):
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["is_edit"] = True
        return kwargs

    def get_success_url(self):
        return reverse('recien_nacido:rn_lista')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Para que el template sepa que es edición
        context['is_creating'] = False
        return context

    def form_valid(self, form):
        """
        Guarda siempre los cambios del RN y registra el log.
        """
        rn = form.save(commit=False)

        # Si tienes campo 'modificado_por', se llena aquí
        if hasattr(rn, "modificado_por"):
            rn.modificado_por = self.request.user

        rn.save()
        form.save_m2m()

        # 🟡 REGISTRO DE AUDITORÍA - UPDATE RN
        registrar_log(
            self.request,
            LogAccion.ACCION_UPDATE,
            "RecienNacido",
            rn.pk,
            "Datos del RN actualizados desde el formulario de edición.",
        )

        messages.success(self.request, "Datos del recién nacido actualizados correctamente.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """
        Si el formulario es inválido, mostramos un mensaje y
        dejamos que el template pinte los errores.
        """
        print("ERRORES RNUpdateView:", form.errors)  # logs en consola

        messages.error(
            self.request,
            "Hay errores en el formulario. Revisa los campos marcados en rojo."
        )
        return super().form_invalid(form)


# ================================================
#  5. VALIDAR ALTA (Detalle)
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class RNValidarAltaView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_validar_alta.html'
    context_object_name = 'rn'

    def evaluar_datos_criticos(self, rn):
        datos_criticos_completos = True
        mensajes_error = []

        if rn.peso is None or rn.peso <= 0:
            datos_criticos_completos = False
            mensajes_error.append("El peso del Recién Nacido es un dato crítico y falta.")
        if rn.talla is None or rn.talla <= 0:
            datos_criticos_completos = False
            mensajes_error.append("La talla del Recién Nacido es un dato crítico y falta.")
        if rn.apgar_5 is None:
            datos_criticos_completos = False
            mensajes_error.append("El APGAR a los 5 minutos es un dato crítico y falta.")

        # Verifica si existe al menos una profilaxis registrada
        profilaxis_completa = rn.profilaxis_set.exists()
        if not profilaxis_completa:
            datos_criticos_completos = False
            mensajes_error.append("No se ha registrado ninguna profilaxis para el Recién Nacido.")

        return datos_criticos_completos, mensajes_error, profilaxis_completa

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rn = self.object
        datos_criticos_completos, mensajes_error, profilaxis_completa = self.evaluar_datos_criticos(rn)

        context['datos_criticos_completos'] = datos_criticos_completos
        context['mensajes_error'] = mensajes_error
        context['profilaxis_completa'] = profilaxis_completa
        context['id_unico_rn'] = f"M{rn.parto.madre.pk:03d}-RN{rn.pk:03d}"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        rn = self.object
        datos_criticos_completos, mensajes_error, profilaxis_completa = self.evaluar_datos_criticos(rn)
        action = request.POST.get("action")

        if action == "validar_alta":
            if not datos_criticos_completos:
                messages.error(request, "No se puede validar el alta porque faltan datos críticos.")
                context = self.get_context_data()
                return render(request, self.template_name, context)

            rn.fecha_alta = timezone.now()
            rn.save()

            # 🔵 Log de validación de alta
            registrar_log(
                request,
                LogAccion.ACCION_UPDATE,
                "RecienNacido",
                rn.pk,
                "Alta de RN validada.",
            )

            messages.success(request, "Alta validada correctamente.")
            return redirect('recien_nacido:rn_pendientes_alta')

        elif action == "enviar_correccion":
            messages.warning(request, "El registro se ha marcado para corrección.")
            return redirect('recien_nacido:rn_editar', pk=rn.pk)

        return redirect(request.path_info)


# ================================================
#  6. PROFILAXIS
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class RNProfilaxisView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_profilaxis.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profilaxis_form'] = ProfiRNForm()
        context['profilaxis_list'] = (
            self.object.profilaxis_set.all().select_related('tipo', 'registrado_por')
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProfiRNForm(request.POST)
        if form.is_valid():
            prof = form.save(commit=False)
            prof.rn = self.object
            prof.registrado_por = request.user
            prof.save()

            # 🔵 Log de profilaxis
            registrar_log(
                request,
                LogAccion.ACCION_CREATE,
                "ProfiRN",
                prof.pk,
                f"Profilaxis registrada para RN ID {self.object.pk}.",
            )

            return redirect(request.path_info)

        context = self.get_context_data()
        context['profilaxis_form'] = form
        return render(request, self.template_name, context)


# ================================================
#  7. OBSERVACIONES
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class RNObservacionesView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_observaciones.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['observacion_form'] = RNObservacionForm()
        context['observaciones'] = (
            self.object.observaciones.all().select_related('autor')
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = RNObservacionForm(request.POST)
        if form.is_valid():
            obs = form.save(commit=False)
            obs.rn = self.object
            obs.autor = request.user
            obs.save()

            registrar_log(
                request,
                LogAccion.ACCION_CREATE,
                "RNObservacion",
                obs.pk,
                f"Observación registrada para RN ID {self.object.pk}.",
            )

            return redirect(request.path_info)

        context = self.get_context_data()
        context['observacion_form'] = form
        return render(request, self.template_name, context)


# ================================================
#  8. ELIMINAR RN (Borrado normal)
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class RNDeleteView(LoginRequiredMixin, View):
    template_name = "recien_nacido/rn_confirm_delete.html"

    def get(self, request, pk):
        rn = get_object_or_404(RecienNacido, pk=pk)
        form = RNDeleteForm(user=request.user)
        hijos = None  # si luego quieres mostrar algo más
        return render(request, self.template_name, {"rn": rn, "form": form})

    def post(self, request, pk):
        rn = get_object_or_404(RecienNacido, pk=pk)
        form = RNDeleteForm(request.POST, user=request.user)

        if not form.is_valid():
            return render(request, self.template_name, {"rn": rn, "form": form})

        razon = form.cleaned_data["razon"]

        # 🔴 Log eliminación
        registrar_log(
            request,
            LogAccion.ACCION_DELETE,
            "RecienNacido",
            rn.pk,
            f"Eliminación de RN. Motivo: {razon}",
        )

        rn.delete()
        messages.success(request, "Recién nacido eliminado correctamente.")
        return redirect("recien_nacido:rn_lista")


# ================================================
#  9. REGISTRAR DEFUNCIÓN
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class RegistrarDefuncionRNView(LoginRequiredMixin, View):
    def post(self, request, pk):
        rn = get_object_or_404(RecienNacido, pk=pk)
        password = request.POST.get("password_confirm")
        user = authenticate(request, username=request.user.username, password=password)

        if user:
            form = DefuncionRNForm(request.POST)
            if form.is_valid():
                registro = form.save(commit=False)
                registro.rn = rn
                registro.usuario_registra = request.user
                registro.save()

                # Auditoría
                registrar_log(
                    request,
                    LogAccion.ACCION_UPDATE,
                    "RecienNacido",
                    rn.pk,
                    f"Defunción RN registrada. Razón: {registro.razon}",
                )

                messages.success(
                    request,
                    "Defunción del recién nacido registrada correctamente."
                )
            else:
                messages.error(request, "Error en el formulario.")
        else:
            messages.error(request, "Contraseña incorrecta.")

        return redirect('recien_nacido:rn_lista')


# ================================================
#  10. LISTAR DEFUNCIONES RN
# ================================================
@method_decorator(
    role_required(['administrativo', 'profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class RNDefuncionesListView(ListView):
    model = RecienNacido
    template_name = "recien_nacido/rn_defunciones_lista.html"
    context_object_name = "rn_fallecidos"
    paginate_by = 25

    def get_queryset(self):
        # Filtra RNs que tienen registro de defunción
        return (
            RecienNacido.objects
            .select_related("parto__madre")
            .filter(defunciones__isnull=False)
            .distinct()
            .order_by('-defunciones__fecha')
        )


# ================================================
#  11. GENERAR PDF DEFUNCIÓN RN
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class RNDefuncionPDFView(View):
    def get(self, request, pk):
        rn = get_object_or_404(RecienNacido, pk=pk)
        defuncion = rn.defunciones.last()

        if not defuncion:
            messages.error(request, "No se encontró registro de defunción.")
            return redirect('recien_nacido:rn_lista')

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Encabezado
        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, height - inch, "Certificado de Defunción Neonatal")
        c.setFont("Helvetica", 10)
        c.drawString(inch, height - 1.2 * inch, "Hosp. Clínico Herminda Martín - Registro Interno")
        c.line(inch, height - 1.4 * inch, width - inch, height - 1.4 * inch)

        # Datos RN
        y = height - 2 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, y, "1. DATOS DEL RECIÉN NACIDO")
        y -= 0.3 * inch
        c.setFont("Helvetica", 11)
        c.drawString(inch, y, f"Madre: {rn.parto.madre.nombre_completo}")
        y -= 0.25 * inch
        c.drawString(inch, y, f"RUT Madre: {rn.parto.madre.rut}")
        y -= 0.25 * inch
        c.drawString(inch, y, f"Sexo: {rn.get_sexo_display()}")
        y -= 0.25 * inch
        fecha_nac_fmt = rn.parto.fecha.strftime('%d-%m-%Y')
        c.drawString(inch, y, f"Fecha Nacimiento: {fecha_nac_fmt}")

        # Datos Defunción
        y -= 0.6 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, y, "2. DETALLES DEL FALLECIMIENTO")
        y -= 0.3 * inch
        c.setFont("Helvetica", 11)

        fecha_def_fmt = defuncion.fecha.strftime('%d/%m/%Y %H:%M')
        c.drawString(inch, y, f"Fecha y Hora: {fecha_def_fmt}")

        y -= 0.25 * inch
        # Lógica segura para nombre de usuario
        registrador = "Sistema"
        if defuncion.usuario_registra:
            registrador = (
                defuncion.usuario_registra.get_full_name()
                or defuncion.usuario_registra.username
            )
        c.drawString(inch, y, f"Registrado por: {registrador}")

        y -= 0.4 * inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(inch, y, "Causa / Razón Clínica:")
        y -= 0.25 * inch
        c.setFont("Helvetica", 11)

        # Texto largo
        import textwrap
        text_object = c.beginText(inch, y)
        text_object.setFont("Helvetica", 11)
        lineas = textwrap.wrap(defuncion.razon, width=80)
        for linea in lineas:
            text_object.textLine(linea)
        c.drawText(text_object)

        c.showPage()
        c.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Defuncion_RN_{rn.pk}.pdf"'
        return response
