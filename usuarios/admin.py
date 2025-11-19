from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil

class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario (Rol)'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol', 'is_staff')
    
    def get_rol(self, instance):
        if hasattr(instance, 'perfil'):
            return instance.perfil.get_rol_display()
        return None
    get_rol.short_description = 'Rol Asignado'

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        return [PerfilInline]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)