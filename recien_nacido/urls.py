from django.urls import path
from . import views

urlpatterns = [
    # --- /rn/ ---
    
    # rn_lista.html
    path('', views.RNListView.as_view(), name='rn-lista'),
    
    # rn_form.html (para crear un RN para un parto específico)
    path('crear/parto/<int:parto_id>/', views.RNCreateUpdateView.as_view(), name='rn-crear'),
    
    # rn_form.html (para editar un RN existente)
    path('<int:pk>/editar/', views.RNCreateUpdateView.as_view(), name='rn-editar'),

    # --- Sub-rutas según especificación ---

    # rn_profilaxis.html
    path('<int:pk>/profilaxis/', views.RNProfilaxisView.as_view(), name='rn-profilaxis'),

    # rn_observaciones.html
    path('<int:pk>/observaciones/', views.RNObservacionesView.as_view(), name='rn-observaciones'),
]