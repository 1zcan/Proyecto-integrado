from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from .models import RecienNacido, ProfiRN, RNObservacion
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

        # Filtros opcionales
        parto_id = self.request.GET.get('parto_id')
        if parto_id:
            queryset = queryset.filter(parto_id=parto_id)

        madre_id = self.request.GET.get('madre_id')
        if madre_id:
            queryset = queryset.filter(parto__madre_id=madre_id)

        return queryset


# ================================================
#  CREAR / EDITAR RECIÉN NACIDO
# ================================================
class RNCreateUpdateView(LoginRequiredMixin, UpdateView):
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'

    def get_success_url(self):
        return reverse('rn_lista')

    def get_object(self, queryset=None):
        parto_id = self.kwargs.get('parto_id')
        pk = self.kwargs.get('pk')

        if pk:
            return get_object_or_404(RecienNacido, pk=pk)

        if parto_id:
            parto = get_object_or_404(Parto, pk=parto_id)
            return RecienNacido(parto=parto)

        raise Http404("Se requiere un Parto o un PK para gestionar el RN.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parto'] = self.object.parto
        context['madre'] = self.object.parto.madre
        return context

    def form_valid(self, form):
        # Si es nuevo, asignar parto y usuario
        if not form.instance.pk:
            form.instance.parto = self.object.parto
            form.instance.creado_por = self.request.user

        return super().form_valid(form)


# ================================================
#  PROFILAXIS DEL RN
# ================================================
class RNProfilaxisView(LoginRequiredMixin, DetailView):
    model = RecienNacido
    template_name = 'recien_nacido/rn_profilaxis.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profilaxis_form'] = ProfiRNForm()
        context['profilaxis_list'] = self.object.profilaxis_set.all().select_related('tipo', 'registrado_por')
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


# ================================================
#  OBSERVACIONES DEL RN
# ================================================
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
