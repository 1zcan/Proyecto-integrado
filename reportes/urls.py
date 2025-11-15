from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
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
]