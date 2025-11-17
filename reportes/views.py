# reportes/views.py
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models.functions import ExtractYear # 🟢 Para extraer el año
import datetime

# --- Importamos los forms y modelos necesarios ---
from .forms import FiltroReporteREMForm, FiltroReporteServicioSaludForm
from . import services
from . import export
from parto.models import Parto # 🟢 Importamos el modelo Parto para consultar los años

class ReportesMenuView(LoginRequiredMixin, TemplateView):
    """
    Vista que muestra el menú de sub-secciones de reportes.
    """
    template_name = 'reportes/reportes_menu.html'

class ReporteREMView(LoginRequiredMixin, TemplateView):
    """
    Vista para el reporte REM (A11, A21, A24).
    """
    template_name = 'reportes/reportes_rem.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 🟢 INICIO DE LA CORRECCIÓN DINÁMICA ---
        
        # 1. Obtener AÑOS dinámicamente desde la base de datos (Modelo Parto)
        #    Esto busca todos los años distintos donde existe al menos un parto.
        anios_con_datos = Parto.objects.annotate(
            anio_parto=ExtractYear('fecha')
        ).values_list('anio_parto', flat=True).distinct().order_by('-anio_parto')
        
        context['anios_disponibles'] = list(anios_con_datos)
        
        # 2. Los MESES son estáticos (Enero-Diciembre)
        context['meses_disponibles'] = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]

        # 3. Obtener los valores seleccionados (si existen)
        selected_anio = self.request.GET.get('anio')
        selected_mes = self.request.GET.get('mes')
        context['selected_anio'] = selected_anio
        context['selected_mes'] = selected_mes
        context['vista_elegida'] = self.request.GET.get('vista', 'CONSOLIDADO') # (Mantenemos la lógica del filtro de vista)

        # 4. Procesar el formulario
        form = FiltroReporteREMForm(self.request.GET or None)
        context['form'] = form
        
        if form.is_valid():
            anio = form.cleaned_data['anio']
            mes = form.cleaned_data['mes']
            
            context['datos'] = services.get_datos_rem(anio, mes)
        
        # --- 🟢 FIN DE LA CORRECCIÓN ---
        
        return context

    def get(self, request, *args, **kwargs):
        # Revisa si se solicitó un formato de exportación
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


class ReporteServicioSaludView(LoginRequiredMixin, TemplateView):
    """
    Vista para el Resumen del Servicio de Salud Ñuble.
    """
    template_name = 'reportes/reportes_servicio_salud.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 🟢 Lógica dinámica de AÑOS también para este reporte ---
        anios_con_datos = Parto.objects.annotate(
            anio_parto=ExtractYear('fecha')
        ).values_list('anio_parto', flat=True).distinct().order_by('-anio_parto')
        context['anios_disponibles'] = list(anios_con_datos)
        context['trimestres_disponibles'] = [('1', 'T1'), ('2', 'T2'), ('3', 'T3'), ('4', 'T4')]
        # --- Fin Lógica dinámica ---
        
        form = FiltroReporteServicioSaludForm(self.request.GET or None)
        context['form'] = form
        
        if form.is_valid():
            anio = form.cleaned_data['anio']
            trimestre = form.cleaned_data['trimestre']
            context['datos'] = services.get_datos_servicio_salud(anio, trimestre)
            
            if 'datos' in context and 'grafico_cumplimiento' in context['datos']:
                context['grafico_labels_json'] = context['datos']['grafico_cumplimiento']['labels']
                context['grafico_data_json'] = context['datos']['grafico_cumplimiento']['data']

        return context

class ReporteCalidadView(LoginRequiredMixin, TemplateView):
    """
    Vista para el reporte de Control de Calidad y consistencia de datos.
    """
    template_name = 'reportes/reportes_calidad.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['datos'] = services.get_datos_calidad()
        return context