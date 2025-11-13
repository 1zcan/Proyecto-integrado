from django.urls import path
from . import views

app_name = "auditoria"

urlpatterns = [
    path("log/", views.LogListView.as_view(), name="log_list"),
]
