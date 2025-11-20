# auditoria/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from usuarios.decorators import role_required

from .models import LogAccion


# ACCESO EXCLUSIVO: Solo TI / Informática puede ver la bitácora
@method_decorator(role_required(['ti_informatica']), name='dispatch')
class LogListView(LoginRequiredMixin, ListView):
    """
    Vista para revisar la bitácora de acciones con filtros:
    - modelo (Madre, RecienNacido, Parto, etc.)
    - acción (create, update, delete)
    - búsqueda por texto (detalle, incluye el 'Motivo')
    """
    model = LogAccion
    template_name = "auditoria/log_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = LogAccion.objects.all().order_by("-timestamp")

        # Filtros por GET
        modelo = self.request.GET.get("modelo", "").strip()
        accion = self.request.GET.get("accion", "").strip()
        query = self.request.GET.get("q", "").strip()

        if modelo:
            qs = qs.filter(modelo__icontains=modelo)

        if accion:
            qs = qs.filter(accion=accion)

        # Búsqueda en detalle (donde guardamos el motivo)
        if query:
            qs = qs.filter(detalle__icontains=query)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Mantener los valores en el formulario de filtro
        context["filtro_modelo"] = self.request.GET.get("modelo", "").strip()
        context["filtro_accion"] = self.request.GET.get("accion", "").strip()
        context["filtro_q"] = self.request.GET.get("q", "").strip()

        # Opcional: lista de acciones para el <select>
        context["acciones_disponibles"] = [
            ("", "Todas"),
            ("create", "Creación"),
            ("update", "Actualización"),
            ("delete", "Eliminación"),
        ]

        return context
