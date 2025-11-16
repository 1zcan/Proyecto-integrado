# recien_nacido/views.py
from django.shortcuts import render, get_object_or_404, redirect
# 🟢 Añadir CreateView
from django.views.generic import ListView, UpdateView, DetailView, CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from .models import RecienNacido, ProfiRN, RNObservacion
# 🟢 Ya no necesitamos RNStandaloneForm
from .forms import RNForm, ProfiRNForm, RNObservacionForm 
from parto.models import Parto


# ================================================
#  LISTA DE RECIÉN NACIDOS
# ================================================
class RNListView(LoginRequiredMixin, ListView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista.html'
    context_object_name = 'recien_nacidos'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('parto', 'parto__madre')
        # Filtros opcionales (código sin cambios)
        parto_id = self.request.GET.get('parto_id')
        if parto_id:
            queryset = queryset.filter(parto_id=parto_id)

        madre_id = self.request.GET.get('madre_id')
        if madre_id:
            queryset = queryset.filter(parto__madre_id=madre_id)

        return queryset


# ================================================
#  CREAR RECIÉN NACIDO (Flujo Único y Simple)
# ================================================
class RNCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un RN, seleccionando el Parto desde el formulario.
    """
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'
    
    def get_success_url(self):
        # 🟢 CORRECCIÓN: Usamos el app_name para la redirección
        return reverse('recien_nacido:rn_lista')

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        # El campo 'parto' ya está en el form, por lo que se guarda automáticamente.
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # Aseguramos que el formulario se muestre limpio al crear
        context = super().get_context_data(**kwargs)
        context['is_creating'] = True
        return context


# ================================================
#  EDITAR RECIÉN NACIDO
# ================================================
class RNUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar un RN existente.
    """
    model = RecienNacido
    form_class = RNForm # Usamos el mismo formulario, pero el constructor lo oculta
    template_name = 'recien_nacido/rn_form.html'

    def get_success_url(self):
        # 🟢 CORRECCIÓN: Usamos el app_name para la redirección
        return reverse('recien_nacido:rn_lista')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_creating'] = False
        return context


# ... (RNProfilaxisView y RNObservacionesView siguen igual) ...
# ... (Te los dejo en el archivo para que sea completo) ...
class RNProfilaxisView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_profilaxis.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profilaxis_form'] = ProfiRNForm()
        context['profilaxis_list'] = self.object.profilaxis.all().select_related('tipo', 'registrado_por')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProfiRNForm(request.POST)

        if form.is_valid():
            prof = form.save(commit=False)
            prof.rn = self.object
            prof.registrado_por = request.user
            prof.save()
            return redirect(request.path_info)

        context = self.get_context_data()
        context['profilaxis_form'] = form
        return render(request, self.template_name, context)


class RNObservacionesView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_observaciones.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['observacion_form'] = RNObservacionForm()
        context['observaciones'] = self.object.observaciones.all().select_related('autor')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = RNObservacionForm(request.POST)

        if form.is_valid():
            obs = form.save(commit=False)
            obs.rn = self.object
            obs.autor = request.user
            obs.save()
            return redirect(request.path_info)

        context = self.get_context_data()
        context['observacion_form'] = form
        return render(request, self.template_name, context)