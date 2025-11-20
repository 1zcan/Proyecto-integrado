# reportes/urls.py
from django.urls import path
from . import views

# 1. ESTO ES CRUCIAL:
app_name = 'reportes'

urlpatterns = [
    # 2. ESTE ES EL NOMBRE QUE BUSCA EL TEMPLATE:
    path(
        '',  
        views.ReportesMenuView.as_view(), 
        name='reportes_menu'  # <-- 'reportes_menu'
    ),
    
    path(
        'rem/', 
        views.ReporteREMView.as_view(), 
        name='reportes_rem'
    ),
    path(
        'servicio-salud/', 
        views.ReporteServicioSaludView.as_view(), 
        name='reportes_servicio_salud'
    ),
    path(
        'calidad/', 
        views.ReporteCalidadView.as_view(), 
        name='reportes_calidad'
    ),
        path(
        'historial-altas/',
        views.ReporteHistorialAltasView.as_view(),
        name='reportes_historial_altas'
    ),
    path
    ('defunciones/', views.ReporteDefuncionesView.as_view(), name='reportes_defunciones'),


]