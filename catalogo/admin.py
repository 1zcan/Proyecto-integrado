from django.contrib import admin
from .models import Catalogo

@admin.register(Catalogo)
class CatalogoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'valor', 'activo', 'orden')
    list_filter = ('tipo', 'activo')
    search_fields = ('valor',)
    ordering = ('tipo', 'orden', 'valor')
