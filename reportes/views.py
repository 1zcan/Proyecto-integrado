# reportes/views.py
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import ExtractYear
from django.utils.decorators import method_decorator
from usuarios.decorators import role_required
import datetime
import json

from recien_nacido.models import RecienNacido, DefuncionRN
from madre.models import DefuncionMadre
from parto.models import Parto

from .forms import FiltroReporteREMForm, FiltroReporteServicioSaludForm
from . import services
from . import export

# -----------------------------
# Menú principal de reportes
# -----------------------------
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class ReportesMenuView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_menu.html'

# -----------------------------
# Reportes REM (A11, A21, etc)
# -----------------------------
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class ReporteREMView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_rem.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Años disponibles según partos
        anios_con_datos = Parto.objects.annotate(
            anio_parto=ExtractYear('fecha')
        ).values_list('anio_parto', flat=True).distinct().order_by('-anio_parto')
        context['anios_disponibles'] = list(anios_con_datos)

        # Meses
        context['meses_disponibles'] = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]

        selected_anio = self.request.GET.get('anio')
        selected_mes = self.request.GET.get('mes')
        context['selected_anio'] = selected_anio
        context['selected_mes'] = selected_mes
        context['vista_elegida'] = self.request.GET.get('vista', 'CONSOLIDADO')

        form = FiltroReporteREMForm(self.request.GET or None)
        context['form'] = form
        
        if form.is_valid():
            anio = form.cleaned_data['anio']
            mes = form.cleaned_data['mes']
            context['datos'] = services.get_datos_rem(anio, mes)
        
        return context

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get('format', None)
        
        if export_format:
            form = FiltroReporteREMForm(request.GET)
            if form.is_valid():
                anio = form.cleaned_data['anio']
                mes = form.cleaned_data['mes']
                datos = services.get_datos_rem(anio, mes)
                
                if export_format == 'excel':
                    return export.export_rem_excel(datos)
                elif export_format == 'pdf':
                    return export.export_rem_pdf(datos)

        return super().get(request, *args, **kwargs)

# -----------------------------
# Reporte Servicio de Salud Ñuble
# -----------------------------
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class ReporteServicioSaludView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_servicio_salud.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        anios_con_datos = Parto.objects.annotate(
            anio_parto=ExtractYear('fecha')
        ).values_list('anio_parto', flat=True).distinct().order_by('-anio_parto')
        context['anios_disponibles'] = list(anios_con_datos)

        context['trimestres_disponibles'] = [('1', 'T1'), ('2', 'T2'), ('3', 'T3'), ('4', 'T4')]
        
        form = FiltroReporteServicioSaludForm(self.request.GET or None)
        context['form'] = form
        
        if form.is_valid():
            anio = form.cleaned_data['anio']
            trimestre = form.cleaned_data['trimestre']
            datos = services.get_datos_servicio_salud(anio, trimestre)
            context['datos'] = datos
            
            grafico = datos.get('grafico_cumplimiento')
            if grafico:
                context['grafico_labels_json'] = json.dumps(grafico.get('labels', []))
                context['grafico_data_json'] = json.dumps(grafico.get('data', []))

        return context

# -----------------------------
# Reporte de Calidad
# -----------------------------
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class ReporteCalidadView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_calidad.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['datos'] = services.get_datos_calidad()
        return context

# -----------------------------
# Historial de Altas de Recién Nacidos
# -----------------------------
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class ReporteHistorialAltasView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_historial_altas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = RecienNacido.objects.filter(fecha_alta__isnull=False).select_related(
            'parto', 'parto__madre'
        ).order_by('-fecha_alta')

        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')

        if fecha_desde:
            qs = qs.filter(fecha_alta__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_alta__date__lte=fecha_hasta)

        context['altas'] = qs
        context['fecha_desde'] = fecha_desde
        context['fecha_hasta'] = fecha_hasta
        return context

# -----------------------------
# Reporte de Defunciones
# -----------------------------
@method_decorator(role_required(['profesional_salud', 'ti_informatica']), name='dispatch')
class ReporteDefuncionesView(LoginRequiredMixin, TemplateView):
    template_name = "reportes/reportes_defunciones.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Madres fallecidas
        context["madres"] = DefuncionMadre.objects.select_related(
            "madre", "usuario_registra"
        ).order_by("-fecha")

        # Recién Nacidos fallecidos
        context["rn"] = DefuncionRN.objects.select_related(
            "rn", "usuario_registra"
        ).order_by("-fecha")

        return context
