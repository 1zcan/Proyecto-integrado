# catalogos/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Catalogo
from .forms import CatalogoForm

class CatalogoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar todos los valores del catálogo (catalogos_maestros.html).
    """
    model = Catalogo
    template_name = 'catalogos/catalogos_maestros.html'
    context_object_name = 'catalogos'  # Nombre de la variable en el template
    paginate_by = 25  # Opcional: paginación
    permission_required = 'catalogos.view_catalogo' # Permiso requerido

    def get_queryset(self):
        # Permite filtrar por tipo si se pasa un query param ?tipo=...
        queryset = super().get_queryset().order_by('tipo', 'orden', 'valor')
        tipo_filtro = self.request.GET.get('tipo')
        if tipo_filtro:
            queryset = queryset.filter(tipo=tipo_filtro)
        return queryset

class CatalogoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear un nuevo valor de catálogo.
    """
    model = Catalogo
    form_class = CatalogoForm
    template_name = 'catalogos/catalogo_form.html' # Usaremos un template genérico
    success_url = reverse_lazy('catalogos:lista') # Redirige a la lista
    permission_required = 'catalogos.add_catalogo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Valor de Catálogo'
        return context

class CatalogoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar un valor de catálogo existente.
    """
    model = Catalogo
    form_class = CatalogoForm
    template_name = 'catalogos/catalogo_form.html'
    success_url = reverse_lazy('catalogos:lista')
    permission_required = 'catalogos.change_catalogo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Valor: {self.object.valor}'
        return context

class CatalogoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar (o desactivar) un valor de catálogo.
    RECOMENDACIÓN: Es mejor desactivar ('activo'=False) que borrar.
    Esta vista borra, pero se puede sobreescribir el método delete()
    para que solo desactive.
    """
    model = Catalogo
    template_name = 'catalogos/catalogo_confirm_delete.html'
    success_url = reverse_lazy('catalogos:lista')
    permission_required = 'catalogos.delete_catalogo'