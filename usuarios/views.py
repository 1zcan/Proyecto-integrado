from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import random

from .models import Perfil, TwoFactorCode
from .forms import RegistroForm, PerfilForm, FotoPerfilForm, AdminUserCreateForm


# -------------------------------------------------------------------
# REGISTRO + ACTIVACIÓN POR CORREO
# -------------------------------------------------------------------
def registro(request):
    # 🔁 Si ya está logueado, lo mando al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Aseguramos set_password
            user.set_password(form.cleaned_data['password'])
            # Cuenta inactiva hasta activar por correo
            user.is_active = False
            user.save()
            
            # Si ya existe perfil, fijamos rol por defecto
            if hasattr(user, 'perfil'):
                user.perfil.rol = 'usuario'
                user.perfil.save()

            # Generar link de activación
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            link_activacion = request.build_absolute_uri(
                reverse('usuarios:activar_cuenta', kwargs={'uidb64': uid, 'token': token})
            )

            send_mail(
                subject='Activa tu cuenta',
                message=(
                    f'Hola {user.username},\n\n'
                    f'Activa tu cuenta haciendo clic en el siguiente enlace:\n{link_activacion}\n\n'
                    'Si no creaste esta cuenta, puedes ignorar este mensaje.'
                ),
                from_email=None,  # usa DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
            )

            messages.success(
                request,
                'Registro exitoso. Te enviamos un enlace de activación a tu correo.'
            )
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    
    context = {
        'form': form,
        'hide_navigation': True,
    }
    return render(request, 'usuarios/registro.html', context)


def activar_cuenta(request, uidb64, token):
    """
    Activa la cuenta del usuario si el token es válido.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Tu cuenta ha sido activada. Ya puedes iniciar sesión.')
        return redirect('usuarios:login')
    else:
        messages.error(request, 'El enlace de activación es inválido o ha expirado.')
        return render(request, 'usuarios/activacion_invalida.html', {'hide_navigation': True})


# -------------------------------------------------------------------
# LOGIN + 2FA POR CORREO
# -------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            usuario = authenticate(request, username=username, password=password)

            if usuario is None:
                messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
                context = {'form': form, 'hide_navigation': True}
                return render(request, 'usuarios/login.html', context)

            # Verificar que la cuenta esté activada
            if not usuario.is_active:
                messages.error(request, 'Tu cuenta aún no está activada. Revisa tu correo.')
                context = {'form': form, 'hide_navigation': True}
                return render(request, 'usuarios/login.html', context)

            # Generar código 2FA y enviarlo al correo
            code = f"{random.randint(0, 999999):06d}"  # 6 dígitos
            TwoFactorCode.objects.create(user=usuario, code=code)

            # Guardar el id en sesión para el segundo paso
            request.session['2fa_user_id'] = usuario.id

            # Enviar correo con el código
            send_mail(
                subject='Tu código de verificación',
                message=f'Tu código de verificación es: {code}',
                from_email=None,
                recipient_list=[usuario.email],
            )

            messages.info(request, 'Te enviamos un código de verificación a tu correo.')
            return redirect('usuarios:login_2fa')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
        'hide_navigation': True,
    }
    return render(request, 'usuarios/login.html', context)


def login_2fa(request):
    """
    Segundo paso del login: el usuario ingresa el código enviado al correo.
    """
    user_id = request.session.get('2fa_user_id')

    if not user_id:
        messages.error(request, 'Tu sesión de verificación ha expirado. Inicia sesión de nuevo.')
        return redirect('usuarios:login')

    try:
        usuario = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Error al encontrar el usuario. Intenta nuevamente.')
        return redirect('usuarios:login')

    if request.method == 'POST':
        code_ingresado = request.POST.get('code', '').strip()

        try:
            ultimo_codigo = TwoFactorCode.objects.filter(
                user=usuario,
                used=False
            ).latest('created_at')
        except TwoFactorCode.DoesNotExist:
            messages.error(request, 'No se encontró un código válido. Solicita iniciar sesión nuevamente.')
            return render(request, 'usuarios/login_2fa.html', {'hide_navigation': True})

        if code_ingresado != ultimo_codigo.code:
            messages.error(request, 'Código incorrecto.')
            return render(request, 'usuarios/login_2fa.html', {'hide_navigation': True})

        # Marcar código como usado
        ultimo_codigo.used = True
        ultimo_codigo.save()

        # Ahora sí iniciamos sesión
        login(request, usuario)
        # Limpiamos el dato de sesión
        request.session.pop('2fa_user_id', None)

        messages.success(request, f'¡Bienvenido {usuario.username}!')
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard:dashboard')

    return render(request, 'usuarios/login_2fa.html', {'hide_navigation': True})


# -------------------------------------------------------------------
# LOGOUT
# -------------------------------------------------------------------
@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.info(request, f'Hasta pronto, {username}. Has cerrado sesión exitosamente.')
    return redirect('usuarios:login')


# -------------------------------------------------------------------
# PERFIL Y EDICIÓN DE PERFIL
# -------------------------------------------------------------------
@login_required
def perfil_view(request):
    if not hasattr(request.user, 'perfil'):
        Perfil.objects.create(user=request.user, rol='usuario')
    
    perfil = request.user.perfil
    
    context = {
        'perfil': perfil,
        'hide_navigation': False,
    }
    return render(request, 'usuarios/perfil.html', context)


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
        'foto_form': foto_form,
        'hide_navigation': False,
    }
    return render(request, 'usuarios/editar_perfil.html', context)


# -------------------------------------------------------------------
# HELPER: COMPROBAR SI ES ADMIN (para gestión de usuarios)
# -------------------------------------------------------------------
def es_admin_sistema(user):
    """
    Solo permite acceso a:
    - superuser
    - staff
    - o usuarios con rol 'ti_informatica'
    Ajusta el nombre del rol si usas otro para el admin.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return hasattr(user, 'perfil') and user.perfil.rol == 'ti_informatica'


# -------------------------------------------------------------------
# GESTIÓN DE USUARIOS (ADMIN)
# -------------------------------------------------------------------
@login_required
@user_passes_test(es_admin_sistema)
def gestion_usuarios(request):
    """
    Lista usuarios y permite crear nuevos con USUARIO, CORREO y ROL.
    """
    usuarios = User.objects.select_related('perfil').all().order_by('username')

    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('usuarios:gestion_usuarios')
    else:
        form = AdminUserCreateForm()

    context = {
        'usuarios': usuarios,
        'form': form,
        'hide_navigation': False,
    }
    return render(request, 'usuarios/gestion_usuarios.html', context)


@login_required
@user_passes_test(es_admin_sistema)
def eliminar_usuario(request, user_id):
    """
    Elimina un usuario seleccionado.
    (Aquí bloqueamos que el usuario se borre a sí mismo).
    """
    usuario = get_object_or_404(User, pk=user_id)

    if request.user.id == usuario.id:
        messages.error(request, "No puedes eliminar tu propio usuario.")
        return redirect('usuarios:gestion_usuarios')

    if request.method == 'POST':
        nombre = usuario.username
        usuario.delete()
        messages.success(request, f"Usuario '{nombre}' eliminado correctamente.")
        return redirect('usuarios:gestion_usuarios')

    context = {
        'usuario': usuario,
        'hide_navigation': False,
    }
    return render(request, 'usuarios/confirmar_eliminar_usuario.html', context)
