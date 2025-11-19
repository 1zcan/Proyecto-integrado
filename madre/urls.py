# madre/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Listado de madres
    path('', views.MadreListView.as_view(), name='madre_lista'),
    
    # Formularios de Madre (Crear/Editar)
    path('nueva/', views.MadreCreateView.as_view(), name='madre_crear'),
    path('<int:pk>/editar/', views.MadreUpdateView.as_view(), name='madre_editar'),
    
    # Formulario de Tamizajes (REM A11)
    path('<int:madre_pk>/tamizajes/', views.TamizajeCreateUpdateView.as_view(), name='madre_tamizajes'),
    
    # Observaciones (firma con contraseña del usuario)
    path(
        '<int:madre_pk>/observaciones/',
        views.MadreObservacionesView.as_view(),
        name='madre_observaciones'
    ),
]
