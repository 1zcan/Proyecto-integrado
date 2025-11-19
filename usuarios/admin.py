from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil

# Definimos el perfil como un "inline" (incrustado)
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario (Rol)'
    fk_name = 'user'

# Extendemos el UserAdmin original para incluir el Perfil
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)
    
    # Opcional: Mostrar el rol en la lista de usuarios del admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol', 'is_staff')
    
    def get_rol(self, instance):
        return instance.perfil.get_rol_display()
    get_rol.short_description = 'Rol Asignado'

# Re-registramos el modelo User con nuestra configuración
admin.site.unregister(User)
admin.site.register(User, UserAdmin)