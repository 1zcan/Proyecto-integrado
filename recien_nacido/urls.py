# recien_nacido/urls.py
from django.urls import path
from . import views

app_name = 'recien_nacido'

urlpatterns = [
    # --- /rn/ ---
    
    # rn_lista.html
    path('', views.RNListView.as_view(), name='rn_lista'),
    
    # 🟢 NUEVA URL: Creación Unificada (Muestra el formulario para seleccionar Parto)
    path('crear/', views.RNCreateView.as_view(), name='rn_crear'),
    
    # rn_form.html (para editar un RN existente)
    path('<int:pk>/editar/', views.RNUpdateView.as_view(), name='rn_editar'),

    # Sub-rutas según especificación (sin cambios)
    path('<int:pk>/profilaxis/', views.RNProfilaxisView.as_view(), name='rn_profilaxis'),
    path('<int:pk>/observaciones/', views.RNObservacionesView.as_view(), name='rn_observaciones'),
]