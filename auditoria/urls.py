from django.urls import path
from .views import LogListView

app_name = "auditoria"

urlpatterns = [
    path('', LogListView.as_view(), name='log_list'),
]