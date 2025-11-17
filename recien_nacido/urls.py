# recien_nacido/urls.py
from django.urls import path
from . import views

app_name = 'recien_nacido'

urlpatterns = [
    # rn_lista.html
    path('', views.RNListView.as_view(), name='rn_lista'),
    
    # 🟢 NUEVA URL SIMPLE DE CREACIÓN
    path('crear/', views.RNCreateView.as_view(), name='rn_crear'), # <-- La vista RNCreateView maneja este flujo
    
    # Lista de pendientes de alta
    path('pendientes-alta/', views.RNAltaPendienteListView.as_view(), name='rn_pendientes_alta'),

    # Edición
    path('<int:pk>/editar/', views.RNUpdateView.as_view(), name='rn_editar'),

    # Sub-rutas
    path('<int:pk>/validar-alta/', views.RNValidarAltaView.as_view(), name='rn_validar_alta'),
    path('<int:pk>/profilaxis/', views.RNProfilaxisView.as_view(), name='rn_profilaxis'),
    path('<int:pk>/observaciones/', views.RNObservacionesView.as_view(), name='rn_observaciones'),
]