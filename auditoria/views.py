from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import LogAccion


class LogListView(LoginRequiredMixin, ListView):
    """
    Vista simple para revisar la bitácora de acciones.
    """
    model = LogAccion
    template_name = "auditoria/log_list.html"
    context_object_name = "logs"
    paginate_by = 50
