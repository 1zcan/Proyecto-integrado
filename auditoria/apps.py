from django.apps import AppConfig

class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'

    def ready(self):
        """
        Importa las señales (signals) cuando la app está lista.
        Esto es crucial para que los receivers se conecten.
        """
        import auditoria.signals