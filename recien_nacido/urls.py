# recien_nacido/urls.py
from django.urls import path
from . import views

app_name = 'recien_nacido'

urlpatterns = [
    # Lista general
    path('', views.RNListView.as_view(), name='rn_lista'),
    
    # Crear
    path('crear/', views.RNCreateView.as_view(), name='rn_crear'),
    
    # Lista de pendientes de alta
    path('pendientes-alta/', views.RNAltaPendienteListView.as_view(), name='rn_pendientes_alta'),

    # Edición
    path('<int:pk>/editar/', views.RNUpdateView.as_view(), name='rn_editar'),
    # Eliminar
    path('<int:pk>/eliminar/', views.RNDeleteView.as_view(), name='rn_eliminar'),

    # Sub-rutas
    path('<int:pk>/validar-alta/', views.RNValidarAltaView.as_view(), name='rn_validar_alta'),
    path('<int:pk>/profilaxis/', views.RNProfilaxisView.as_view(), name='rn_profilaxis'),
    path('<int:pk>/observaciones/', views.RNObservacionesView.as_view(), name='rn_observaciones'),
]
