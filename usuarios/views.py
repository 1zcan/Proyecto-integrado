from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Perfil
from .forms import RegistroForm, PerfilForm, FotoPerfilForm


def registro(request):

    if request.user.is_authenticated:
        return redirect('articulos:lista_articulos')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            if hasattr(user, 'perfil'):
                user.perfil.rol = 'usuario'
                user.perfil.save()
            messages.success(request, 'Registro exitoso.')
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
    
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            usuario = authenticate(request, username=username, password=password)
            if usuario is not None:
                login(request, usuario)
                messages.success(request, f'¡Bienvenido {username}!')
                
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})


@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.info(request, f'Hasta pronto, {username}. Has cerrado sesión exitosamente.')
    return redirect('usuarios:login')


@login_required
def perfil_view(request):

    if not hasattr(request.user, 'perfil'):
        Perfil.objects.create(user=request.user, rol='usuario')
    
    perfil = request.user.perfil
    return render(request, 'usuarios/perfil.html', {'perfil': perfil})


@login_required
def editar_perfil_view(request):

    if not hasattr(request.user, 'perfil'):
        Perfil.objects.create(user=request.user, rol='usuario')
    
    if request.method == 'POST':
        user_form = PerfilForm(request.POST, instance=request.user)
        foto_form = FotoPerfilForm(request.POST, request.FILES, instance=request.user.perfil)

        if user_form.is_valid() and foto_form.is_valid():
            user_form.save()
            foto_form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado exitosamente!')
            return redirect('usuarios:perfil')
    else:
        user_form = PerfilForm(instance=request.user)
        foto_form = FotoPerfilForm(instance=request.user.perfil)

    context = {
        'user_form': user_form,
        'foto_form': foto_form
    }
    return render(request, 'usuarios/editar_perfil.html', context)