from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from .models import RecienNacido, ProfiRN, RNObservacion
from .forms import RNForm, ProfiRNForm, RNObservacionForm
from parto.models import Parto # Dependencia

# --- Vistas basadas en la especificación ---

class RNListView(LoginRequiredMixin, ListView):
    """
    rn_lista.html
    Lista todos los Recién Nacidos registrados.
    """
    model = RecienNacido
    template_name = 'recien_nacido/rn_lista.html'
    context_object_name = 'recien_nacidos'
    paginate_by = 25

    def get_queryset(self):
        # Optimiza la consulta para incluir datos del parto y la madre
        queryset = super().get_queryset().select_related('parto', 'parto__madre')
        
        # Permite filtrar por parto o madre si se pasa en la URL
        parto_id = self.request.GET.get('parto_id')
        if parto_id:
            queryset = queryset.filter(parto_id=parto_id)
        
        madre_id = self.request.GET.get('madre_id')
        if madre_id:
            queryset = queryset.filter(parto__madre_id=madre_id)
            
        return queryset

class RNCreateUpdateView(LoginRequiredMixin, UpdateView):
    """
    rn_form.html
    Maneja la CREACIÓN (ligada a un Parto) y EDICIÓN de un RecienNacido.
    """
    model = RecienNacido
    form_class = RNForm
    template_name = 'recien_nacido/rn_form.html'
    
    def get_success_url(self):
        # Vuelve a la lista de RNs
        return reverse('rn-lista')

    def get_object(self, queryset=None):
        """
        Intenta obtener el RN. Si la URL es para 'crear',
        crea un nuevo objeto RN ligado a un Parto.
        """
        parto_id = self.kwargs.get('parto_id')
        pk = self.kwargs.get('pk')

        if pk:
            # Es una edición de un RN existente
            return get_object_or_404(RecienNacido, pk=pk)
        
        if parto_id:
            # Es una creación de un nuevo RN para un parto
            parto = get_object_or_404(Parto, pk=parto_id)
            # Creamos un objeto RN en memoria
            return RecienNacido(parto=parto)

        raise Http404("Se requiere un Parto para crear un RN o un PK para editarlo.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadimos el 'parto' y la 'madre' al contexto para mostrarlos
        context['parto'] = self.object.parto
        context['madre'] = self.object.parto.madre
        return context

    def form_valid(self, form):
        """
        Asigna el usuario 'creado_por' si es un objeto nuevo.
        """
        if not form.instance.pk: # Si es nuevo
            form.instance.creado_por = self.request.user
        return super().form_valid(form)

class RNProfilaxisView(LoginRequiredMixin, DetailView):
    """
    rn_profilaxis.html
    Muestra la lista de profilaxis de un RN y permite añadir nuevas.
    """
    model = RecienNacido
    template_name = 'recien_nacido/rn_profilaxis.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añade el formulario de nueva profilaxis
        context['profilaxis_form'] = ProfiRNForm()
        # Añade la lista de profilaxis existentes
        context['profilaxis_list'] = self.object.profilaxis_set.all().select_related('tipo', 'registrado_por')
        return context

    def post(self, request, *args, **kwargs):
        """
Setting the POST request.
        """
        self.object = self.get_object() # Obtener el RecienNacido
        form = ProfiRNForm(request.POST)
        
        if form.is_valid():
            prof = form.save(commit=False)
            prof.rn = self.object
            prof.registrado_por = request.user
            prof.save()
            # Redirigir a la misma página
            return redirect(request.path_info)
        
        # Si el formulario no es válido, volver a renderizar con el error
        context = self.get_context_data()
        context['profilaxis_form'] = form
        return render(request, self.template_name, context)

class RNObservacionesView(LoginRequiredMixin, DetailView):
    """
    rn_observaciones.html
    Muestra las observaciones de un RN y permite añadir nuevas.
    """
    model = RecienNacido
    template_name = 'recien_nacido/rn_observaciones.html'
    context_object_name = 'rn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['observacion_form'] = RNObservacionForm()
        context['observaciones'] = self.object.observaciones.all().select_related('autor')
        return context

    def post(self, request, *args, **kwargs):
        """
Setting the POST request.
        """
        self.object = self.get_object() # Obtener el RecienNacido
        form = RNObservacionForm(request.POST)
        
        if form.is_valid():
            obs = form.save(commit=False)
            obs.rn = self.object
            obs.autor = request.user
            # obs.firma_simple = ... (lógica de firma iría aquí)
            obs.save()
            return redirect(request.path_info)
        
        context = self.get_context_data()
        context['observacion_form'] = form
        return render(request, self.template_name, context)