from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from django.http import HttpResponse
import io

from django.db.models.deletion import ProtectedError  # 👈 IMPORTANTE

# Librería ReportLab para generar PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Importaciones del proyecto
from usuarios.decorators import role_required
from .models import Madre, TamizajeMaterno, MadreObservacion
from .forms import MadreForm, TamizajeMaternoForm, MadreObservacionForm, MadreDeleteForm, DefuncionMadreForm
from recien_nacido.models import RecienNacido
from auditoria.models import LogAccion
from auditoria.utils import registrar_log
from auditoria.signals import get_client_ip  # si lo sigues usando en otros lados


# ================================================
#  LISTA DE MADRES ACTIVAS
# ================================================
@method_decorator(
    role_required(['administrativo', 'profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreListView(ListView):
    model = Madre
    template_name = "madre/madre_lista.html"
    context_object_name = "madres"
    paginate_by = 25

    def get_queryset(self):
        # Solo madres activas (que NO tienen registro de defunción)
        qs = (
            Madre.objects
            .select_related("comuna", "cesfam")
            .filter(activo=True, defunciones__isnull=True)
            .distinct()
        )
        
        # Filtros
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


# ================================================
#  CREAR MADRE
# ================================================
@method_decorator(
    role_required(['administrativo', 'profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreCreateView(CreateView):
    model = Madre
    form_class = MadreForm
    template_name = "madre/madre_form.html"
    success_url = reverse_lazy('madre:madre_lista')

    def form_valid(self, form):
        madre = form.save()

        registrar_log(
            self.request,
            LogAccion.ACCION_CREATE,
            "Madre",
            madre.pk,
            f"Madre creada. RUT={madre.rut}",
        )

        messages.success(self.request, "Ficha de madre creada correctamente.")
        return redirect(self.success_url)


# ================================================
#  EDITAR MADRE
# ================================================
@method_decorator(
    role_required(['administrativo', 'profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreUpdateView(UpdateView):
    model = Madre
    form_class = MadreForm
    template_name = "madre/madre_form.html"
    success_url = reverse_lazy('madre:madre_lista')

    def form_valid(self, form):
        madre = form.save()

        registrar_log(
            self.request,
            LogAccion.ACCION_UPDATE,
            "Madre",
            madre.pk,
            f"Ficha de madre actualizada. RUT={madre.rut}",
        )

        messages.success(self.request, "Ficha de madre actualizada correctamente.")
        return redirect(self.success_url)


# ================================================
#  TAMIZAJES MATERNOS
# ================================================
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
        return reverse_lazy('madre:madre_lista')

    def form_valid(self, form):
        tamizaje = form.save()

        registrar_log(
            self.request,
            LogAccion.ACCION_UPDATE,
            "TamizajeMaterno",
            tamizaje.pk,
            f"Tamizaje materno actualizado para Madre ID={tamizaje.madre.pk}",
        )

        messages.success(self.request, "Tamizajes maternos actualizados correctamente.")
        return redirect(self.get_success_url())


# ================================================
#  OBSERVACIONES DE MADRE (FIRMA SIMPLE)
# ================================================
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
        madre = Madre.objects.get(pk=self.kwargs['madre_pk'])

        form.instance.autor = self.request.user
        form.instance.madre = madre
        form.instance.firma_simple = True
        obs = form.save()

        registrar_log(
            self.request,
            LogAccion.ACCION_CREATE,
            "MadreObservacion",
            obs.pk,
            f"Observación firmada para Madre ID={madre.pk}.",
        )

        messages.success(self.request, "Observación registrada y firmada correctamente.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        madre = Madre.objects.get(pk=self.kwargs['madre_pk'])
        context['madre'] = madre
        context['observaciones'] = madre.observaciones.all()
        return context

    def get_success_url(self):
        return reverse_lazy('madre:madre_observaciones', kwargs={'madre_pk': self.kwargs['madre_pk']})


# ================================================
#  ELIMINAR MADRE
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreDeleteView(LoginRequiredMixin, View):
    template_name = "madre/madre_confirm_delete.html"

    def get(self, request, pk):
        madre = get_object_or_404(Madre, pk=pk, activo=True)
        hijos = RecienNacido.objects.filter(parto__madre=madre)
        total_hijos = hijos.count()
        form = MadreDeleteForm(user=request.user)
        return render(
            request,
            self.template_name,
            {"madre": madre, "hijos": hijos, "total_hijos": total_hijos, "form": form},
        )

    def post(self, request, pk):
        madre = get_object_or_404(Madre, pk=pk, activo=True)
        hijos = RecienNacido.objects.filter(parto__madre=madre)
        total_hijos = hijos.count()
        form = MadreDeleteForm(request.POST, user=request.user)

        if not form.is_valid():
            # Formulario inválido, volvemos a mostrar la pantalla
            return render(
                request,
                self.template_name,
                {"madre": madre, "hijos": hijos, "total_hijos": total_hijos, "form": form},
            )

        # ✅ Si el formulario es válido:
        razon = form.cleaned_data["razon"]

        # ⚠️ Primero verificamos si tiene partos asociados (FK PROTECT en Parto.madre)
        if madre.partos.exists():
            messages.error(
                request,
                "No se puede eliminar esta madre porque tiene partos registrados. "
                "Para proteger la historia clínica, primero revise esos registros."
            )
            return redirect("madre:madre_lista")

        # Si no tiene partos, entonces podemos continuar
        hijos_ids = list(hijos.values_list("pk", flat=True))
        total_hijos_eliminados = len(hijos_ids)

        try:
            # Eliminamos RN asociados
            hijos.delete()

            madre_id = madre.pk
            madre_rut = madre.rut

            # Intentamos eliminar la madre
            madre.delete()

        except ProtectedError:
            # Si por alguna otra relación protegida falla, mostramos mensaje y no reventamos
            messages.error(
                request,
                "No se puede eliminar esta madre porque tiene registros asociados protegidos."
            )
            return redirect("madre:madre_lista")

        # Log solo si REALMENTE se eliminó
        registrar_log(
            request,
            LogAccion.ACCION_DELETE,
            "Madre",
            madre_id,
            f"Madre eliminada. RUT={madre_rut}. Motivo: {razon}. "
            f"Se eliminaron {total_hijos_eliminados} RN asociados: IDs={hijos_ids}.",
        )

        messages.success(request, "Madre eliminada correctamente.")
        return redirect("madre:madre_lista")


# ================================================
#  SECCIÓN DE DEFUNCIONES MADRE
# ================================================
@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class RegistrarDefuncionMadreView(LoginRequiredMixin, View):
    def post(self, request, pk):
        madre = get_object_or_404(Madre, pk=pk, activo=True)
        password = request.POST.get("password_confirm")

        # Validar Contraseña para firma simple
        user = authenticate(request, username=request.user.username, password=password)

        if user:
            form = DefuncionMadreForm(request.POST)
            if form.is_valid():
                registro = form.save(commit=False)
                registro.madre = madre
                registro.usuario_registra = request.user
                registro.save()

                # Marcar madre como fallecida (inactiva)
                madre.activo = False
                madre.save()

                # 🟣 Log defunción madre
                registrar_log(
                    request,
                    LogAccion.ACCION_UPDATE,
                    "Madre",
                    madre.pk,
                    f"Defunción registrada. Razón: {registro.razon}",
                )

                messages.success(request, "Defunción registrada correctamente.")
            else:
                messages.error(request, "Error en el formulario.")
        else:
            messages.error(request, "Contraseña incorrecta.")

        return redirect("madre:madre_lista")


@method_decorator(
    role_required(['administrativo', 'profesional_salud', 'tecnico_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreDefuncionesListView(ListView):
    model = Madre
    template_name = "madre/madre_defunciones_lista.html"
    context_object_name = "madres_fallecidas"
    paginate_by = 25

    def get_queryset(self):
        # Filtra madres inactivas que tienen un registro de defunción
        return (
            Madre.objects
            .select_related("comuna", "cesfam")
            .filter(activo=False, defunciones__isnull=False)
            .distinct()
            .order_by('-defunciones__fecha')
        )


@method_decorator(
    role_required(['profesional_salud', 'ti_informatica']),
    name='dispatch'
)
class MadreDefuncionPDFView(View):
    def get(self, request, pk):
        madre = get_object_or_404(Madre, pk=pk)
        defuncion = madre.defunciones.last()

        if not defuncion:
            messages.error(request, "No se encontró registro de defunción.")
            return redirect('madre:madre_defunciones_lista')

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Encabezado
        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, height - inch, "Certificado de Defunción Materna")
        c.setFont("Helvetica", 10)
        c.drawString(inch, height - 1.2 * inch, "Hosp. Clínico Herminda Martín - Registro Interno")
        c.line(inch, height - 1.4 * inch, width - inch, height - 1.4 * inch)

        # Datos Paciente
        y = height - 2 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, y, "1. DATOS DE LA PACIENTE")
        y -= 0.3 * inch
        c.setFont("Helvetica", 11)
        c.drawString(inch, y, f"Nombre: {madre.nombre_completo}")
        y -= 0.25 * inch
        c.drawString(inch, y, f"RUT: {madre.rut}")

        y -= 0.25 * inch
        fecha_nac_fmt = madre.fecha_nacimiento.strftime('%d-%m-%Y')
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
        response['Content-Disposition'] = f'attachment; filename="Defuncion_{madre.rut}.pdf"'
        return response
