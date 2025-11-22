from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

import random
import sendgrid
from sendgrid.helpers.mail import Mail
from socket import error as socket_error

from .models import Perfil, TwoFactorCode
from .forms import RegistroForm, PerfilForm, FotoPerfilForm, AdminUserCreateForm


# -------------------------------------------------------------------
# FUNCIONES AUXILIARES PARA ENVÍO DE CORREO CON SENDGRID
# -------------------------------------------------------------------
def enviar_correo(destinatario, asunto, contenido_texto):
    """
    Envía un correo usando la API de SendGrid.
    No lanza excepción hacia arriba: si falla, devuelve False.
    """
    sg = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)
    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject=asunto,
        plain_text_content=contenido_texto,
    )
    try:
        response = sg.send(message)
        # print(response.status_code)  # opcional para debug
        return True
    except (socket_error, Exception) as e:
        # Muy importante: NO botar la vista si falla el envío
        print(f"[ENVIAR_CORREO] Error enviando correo a {destinatario}: {e}")
        return False


# -------------------------------------------------------------------
# REGISTRO + ACTIVACIÓN POR CORREO
# -------------------------------------------------------------------
def registro(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False
            user.save()
            
            # Asignar rol por defecto si existe perfil
            if hasattr(user, 'perfil'):
                user.perfil.rol = 'usuario'
                user.perfil.save()

            # Generar enlace de activación
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            link_activacion = request.build_absolute_uri(
                reverse('usuarios:activar_cuenta', kwargs={'uidb64': uid, 'token': token})
            )

            asunto = 'Activa tu cuenta'
            cuerpo = (
                f'Hola {user.username},\n\n'
                f'Activa tu cuenta haciendo clic en el siguiente enlace:\n{link_activacion}\n\n'
                'Si no creaste esta cuenta, puedes ignorar este mensaje.'
            )

            enviado = enviar_correo(user.email, asunto, cuerpo)

            if enviado:
                messages.success(
                    request,
                    'Registro exitoso. Te enviamos un enlace de activación a tu correo.'
                )
            else:
                messages.warning(
                    request,
                    'Tu cuenta se registró, pero hubo un problema al enviar el correo de activación. '
                    'Contacta al administrador si el problema persiste.'
                )

            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    
    return render(request, 'usuarios/registro.html', {
        'form': form,
        'hide_navigation': True,
    })


def activar_cuenta(request, uidb64, token):
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
# LOGIN + 2FA (con excepción para SUPERUSER)
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
                return render(request, 'usuarios/login.html', {'form': form, 'hide_navigation': True})

            # SUPERUSER entra directo sin 2FA
            if usuario.is_superuser:
                login(request, usuario)
                messages.success(request, f'Bienvenido administrador {usuario.username}')
                return redirect('dashboard:dashboard')

            # Cuenta debe estar activada
            if not usuario.is_active:
                messages.error(request, 'Tu cuenta aún no está activada. Revisa tu correo.')
                return render(request, 'usuarios/login.html', {'form': form, 'hide_navigation': True})

            # Código 2FA
            code = f"{random.randint(0, 999999):06d}"
            TwoFactorCode.objects.create(user=usuario, code=code)

            # Guardar user_id en sesión para la segunda etapa
            request.session['2fa_user_id'] = usuario.id

            # Enviar código por correo usando SendGrid
            asunto = 'Tu código de verificación'
            cuerpo = f'Tu código de verificación es: {code}'

            enviado = enviar_correo(usuario.email, asunto, cuerpo)

            if enviado:
                messages.info(request, 'Te enviamos un código de verificación a tu correo.')
            else:
                messages.warning(
                    request,
                    'No se pudo enviar el correo con el código de verificación. '
                    'Contacta al administrador si el problema persiste.'
                )

            return redirect('usuarios:login_2fa')

        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')

    else:
        form = AuthenticationForm()
    
    return render(request, 'usuarios/login.html', {
        'form': form,
        'hide_navigation': True,
    })


def login_2fa(request):
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
            messages.error(request, 'No se encontró un código válido. Inicia sesión nuevamente.')
            return render(request, 'usuarios/login_2fa.html', {'hide_navigation': True})

        if code_ingresado != ultimo_codigo.code:
            messages.error(request, 'Código incorrecto.')
            return render(request, 'usuarios/login_2fa.html', {'hide_navigation': True})

        ultimo_codigo.used = True
        ultimo_codigo.save()

        login(request, usuario)
        request.session.pop('2fa_user_id', None)

        messages.success(request, f'¡Bienvenido {usuario.username}!')
        return redirect('dashboard:dashboard')

    return render(request, 'usuarios/login_2fa.html', {'hide_navigation': True})


# -------------------------------------------------------------------
# LOGOUT
# -------------------------------------------------------------------
@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.info(request, f'Hasta pronto, {username}.')
    return redirect('usuarios:login')


# -------------------------------------------------------------------
# PERFIL
# -------------------------------------------------------------------
@login_required
def perfil_view(request):
    if not hasattr(request.user, 'perfil'):
        Perfil.objects.create(user=request.user, rol='usuario')
    
    return render(request, 'usuarios/perfil.html', {
        'perfil': request.user.perfil,
        'hide_navigation': False,
    })


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

    return render(request, 'usuarios/editar_perfil.html', {
        'user_form': user_form,
        'foto_form': foto_form,
        'hide_navigation': False,
    })


# -------------------------------------------------------------------
# ADMIN: Permisos
# -------------------------------------------------------------------
def es_admin_sistema(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return hasattr(user, 'perfil') and user.perfil.rol == 'ti_informatica'


# -------------------------------------------------------------------
# ADMIN: Gestión de usuarios
# -------------------------------------------------------------------
@login_required
@user_passes_test(es_admin_sistema)
def gestion_usuarios(request):
    usuarios = User.objects.select_related('perfil').all().order_by('username')

    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('usuarios:gestion_usuarios')
    else:
        form = AdminUserCreateForm()

    return render(request, 'usuarios/gestion_usuarios.html', {
        'usuarios': usuarios,
        'form': form,
        'hide_navigation': False,
    })


@login_required
@user_passes_test(es_admin_sistema)
def eliminar_usuario(request, user_id):
    """
    Elimina un usuario. Para que esto nunca lance ProtectedError,
    todos los modelos que lo referencian deben usar on_delete=CASCADE o SET_NULL.
    """
    usuario = get_object_or_404(User, pk=user_id)

    # Evitar que un admin se borre a sí mismo
    if request.user.id == usuario.id:
        messages.error(request, "No puedes eliminar tu propio usuario.")
        return redirect('usuarios:gestion_usuarios')

    if request.method == 'POST':
        nombre = usuario.username
        usuario.delete()
        messages.success(request, f"Usuario '{nombre}' eliminado correctamente.")
        return redirect('usuarios:gestion_usuarios')

    # 👇 Usa el template que ya tienes
    return render(request, 'usuarios/confirmar_eliminar_usuario.html', {
        'usuario': usuario,
        'hide_navigation': False,
    })
