from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'

    def ready(self):
        import sys
        if 'migrate' not in sys.argv:
            import auditoria.signals
