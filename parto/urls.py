# parto/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Lista de partos
    path('', views.PartoListView.as_view(), name='parto_lista'),
    
    # Formulario de creación/edición de Parto
    # Asumiendo CreateView y UpdateView separadas
    path('nuevo/', views.PartoCreateUpdateView.as_view(), name='parto_crear'), # Placeholder
    path('<int:pk>/editar/', views.PartoCreateUpdateView.as_view(), name='parto_editar'),
    
    # Formularios de Modelos relacionados (REM A21 y Robson)
    path('<int:pk>/modelo-atencion/', views.ModeloAtencionUpdateView.as_view(), name='parto_modelo_atencion'),
    path('<int:pk>/robson/', views.RobsonUpdateView.as_view(), name='parto_robson'),
    
    # Observaciones
    path('<int:parto_pk>/observaciones/', views.PartoObservacionesView.as_view(), name='parto_observaciones'),
]