# catalogos/urls.py
from django.urls import path
from . import views

app_name = 'catalogos'  # Importante para el namespacing

urlpatterns = [
    # ej: /catalogos/
    path(
        '', 
        views.CatalogoListView.as_view(), 
        name='lista'
    ),
    # ej: /catalogos/crear/
    path(
        'crear/', 
        views.CatalogoCreateView.as_view(), 
        name='crear'
    ),
    # ej: /catalogos/editar/15/
    path(
        'editar/<int:pk>/', 
        views.CatalogoUpdateView.as_view(), 
        name='editar'
    ),
    # ej: /catalogos/borrar/15/
    path(
        'borrar/<int:pk>/', 
        views.CatalogoDeleteView.as_view(), 
        name='borrar'
    ),
]