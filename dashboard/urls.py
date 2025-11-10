from django.urls import path
from . import views  


urlpatterns = [
    
    path('', views.dashboard_view, name='dashboard'),
    # path('reportes/', views.reportes_view, name='reportes'),
]