from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # 👉 Página raíz: redirige al login de usuarios
    path('', RedirectView.as_view(pattern_name='usuarios:login', permanent=False)),

    # 👉 App de usuarios (con namespace)
    path('usuarios/', include(('usuarios.urls', 'usuarios'), namespace='usuarios')),

    # 👉 Dashboard (con namespace)
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),

    # OTRAS APPS (solo si existen en tu proyecto, si no, bórralas)
    path('auditoria/', include(('auditoria.urls', 'auditoria'), namespace='auditoria')),
    path('madres/', include(('madre.urls', 'madre'), namespace='madre')),
    path('partos/', include(('parto.urls', 'parto'), namespace='parto')),
    path('catalogo/', include(('catalogo.urls', 'catalogo'), namespace='catalogo')),
    path('rn/', include(('recien_nacido.urls', 'recien_nacido'), namespace='recien_nacido')),
    path('reportes/', include(('reportes.urls', 'reportes'), namespace='reportes')),
]
