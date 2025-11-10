from django.urls import path
from . import views  

app_name = 'dashboard'

urlpatterns = [
    
    path('', views.dashboard_view, name='dashboard'),
    # path('reportes/', views.reportes_view, name='reportes'),
]