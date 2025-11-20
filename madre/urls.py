# madre/urls.py
from django.urls import path
from . import views

app_name = "madre"   #  <<<<<< ***ESTO ES OBLIGATORIO*** !!!

urlpatterns = [
    # Listado de madres
    path('', views.MadreListView.as_view(), name='madre_lista'),
    
    # Formularios de Madre (Crear/Editar)
    path('nueva/', views.MadreCreateView.as_view(), name='madre_crear'),
    path('<int:pk>/editar/', views.MadreUpdateView.as_view(), name='madre_editar'),
    path('<int:pk>/eliminar/', views.MadreDeleteView.as_view(), name='madre_eliminar'),
    
    # Formulario de Tamizajes (REM A11)
    path('<int:madre_pk>/tamizajes/', views.TamizajeCreateUpdateView.as_view(), name='madre_tamizajes'),
    
    # Observaciones (firma con contraseña del usuario)
    path(
        '<int:madre_pk>/observaciones/',
        views.MadreObservacionesView.as_view(),
        name='madre_observaciones'
    ),
    path(
        'madre/<int:pk>/defuncion/', views.RegistrarDefuncionMadreView.as_view(), name='madre_defuncion'
        ),

]
