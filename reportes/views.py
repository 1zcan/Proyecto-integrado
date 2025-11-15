from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import FiltroReporteREMForm, FiltroReporteServicioSaludForm
from . import services
from . import export

class ReporteREMView(LoginRequiredMixin, TemplateView):
    """
    Vista para el reporte REM (A11, A21, A24).
    Maneja la visualización HTML y la exportación (Excel/PDF).
    """
    template_name = 'reportes/reportes_rem.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = FiltroReporteREMForm(self.request.GET or None)
        context['form'] = form
        
        if form.is_valid():
            anio = form.cleaned_data['anio']
            mes = form.cleaned_data['mes']
            # Llama al servicio para obtener los datos
            context['datos'] = services.get_datos_rem(anio, mes)
        
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
        
        # Si no hay formato de exportación, renderiza la vista HTML
        return super().get(request, *args, **kwargs)


class ReporteServicioSaludView(LoginRequiredMixin, TemplateView):
    """
    Vista para el Resumen del Servicio de Salud Ñuble.
    """
    template_name = 'reportes/reportes_servicio_salud.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = FiltroReporteServicioSaludForm(self.request.GET or None)
        context['form'] = form
        
        if form.is_valid():
            anio = form.cleaned_data['anio']
            trimestre = form.cleaned_data['trimestre']
            context['datos'] = services.get_datos_servicio_salud(anio, trimestre)
            
            # (Opcional) Si usas gráficos JS, prepara los datos
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
        # Este reporte no suele necesitar filtro, corre sobre todos los datos
        context['datos'] = services.get_datos_calidad()
        return context