# reportes/views.py
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models.functions import ExtractYear
import datetime
import json  # 👈 IMPORTANTE

from .forms import FiltroReporteREMForm, FiltroReporteServicioSaludForm
from . import services
from . import export
from parto.models import Parto


class ReportesMenuView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_menu.html'


class ReporteREMView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_rem.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        anios_con_datos = Parto.objects.annotate(
            anio_parto=ExtractYear('fecha')
        ).values_list('anio_parto', flat=True).distinct().order_by('-anio_parto')
        context['anios_disponibles'] = list(anios_con_datos)

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


class ReporteServicioSaludView(LoginRequiredMixin, TemplateView):
    """
    Vista para el Resumen del Servicio de Salud Ñuble.
    """
    template_name = 'reportes/reportes_servicio_salud.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Años dinámicos según partos
        anios_con_datos = Parto.objects.annotate(
            anio_parto=ExtractYear('fecha')
        ).values_list('anio_parto', flat=True).distinct().order_by('-anio_parto')
        context['anios_disponibles'] = list(anios_con_datos)

        context['trimestres_disponibles'] = [
            ('1', 'T1'), ('2', 'T2'), ('3', 'T3'), ('4', 'T4')
        ]
        
        form = FiltroReporteServicioSaludForm(self.request.GET or None)
        context['form'] = form
        
        if form.is_valid():
            anio = form.cleaned_data['anio']
            trimestre = form.cleaned_data['trimestre']
            datos = services.get_datos_servicio_salud(anio, trimestre)
            context['datos'] = datos
            
            grafico = datos.get('grafico_cumplimiento')
            if grafico:
                # 👇 Enviamos listas como JSON string para JS
                context['grafico_labels_json'] = json.dumps(grafico.get('labels', []))
                context['grafico_data_json'] = json.dumps(grafico.get('data', []))

        return context


class ReporteCalidadView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes_calidad.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['datos'] = services.get_datos_calidad()
        return context
