# catalogo/urls.py
from django.urls import path
from . import views

app_name = 'catalogo'  

urlpatterns = [
    path('', views.CatalogoListView.as_view(), name='lista'),
    path('crear/', views.CatalogoCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', views.CatalogoUpdateView.as_view(), name='editar'),
    path('borrar/<int:pk>/', views.CatalogoDeleteView.as_view(), name='borrar'),
]