# catalogo/views.py
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError

# 🟢 CORRECCIÓN: Importamos desde 'usuarios.mixins', NO de 'seguridad'
from usuarios.mixins import RoleRequiredMixin 

from .models import Catalogo
from .forms import CatalogoForm

# --- LISTAR CATÁLOGOS ---
class CatalogoListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Catalogo
    template_name = 'catalogo/catalogo_lista.html'
    context_object_name = 'elementos'
    paginate_by = 25
    allowed_roles = ['ti_informatica'] 

    def get_queryset(self):
        queryset = super().get_queryset().order_by('tipo', 'orden', 'valor')
        tipo_filtro = self.request.GET.get('tipo')
        if tipo_filtro:
            queryset = queryset.filter(tipo=tipo_filtro)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_disponibles'] = Catalogo.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
        context['selected_tipo'] = self.request.GET.get('tipo', '')
        return context

# --- CREAR ---
class CatalogoCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Catalogo
    form_class = CatalogoForm
    template_name = 'catalogo/catalogo_form.html'
    success_url = reverse_lazy('catalogo:lista') 
    allowed_roles = ['ti_informatica']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Valor de Catálogo'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Elemento creado exitosamente.")
        return super().form_valid(form)

# --- EDITAR ---
class CatalogoUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Catalogo
    form_class = CatalogoForm
    template_name = 'catalogo/catalogo_form.html'
    success_url = reverse_lazy('catalogo:lista')
    allowed_roles = ['ti_informatica']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Valor: {self.object.valor}'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Elemento actualizado exitosamente.")
        return super().form_valid(form)

# --- ELIMINAR ---
class CatalogoDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Catalogo
    template_name = 'catalogo/catalogo_confirm_delete.html'
    success_url = reverse_lazy('catalogo:lista')
    context_object_name = 'item'
    allowed_roles = ['ti_informatica']

    def post(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, "⛔ No se puede eliminar este elemento porque está siendo utilizado en otros registros.")
            return redirect('catalogo:lista')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Elemento de catálogo eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)