from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name='activar_cuenta'),

    path('login/', views.login_view, name='login'),
    path('login-2fa/', views.login_2fa, name='login_2fa'),

    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('editar-perfil/', views.editar_perfil_view, name='editar_perfil'),
]
