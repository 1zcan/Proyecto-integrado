from django.apps import AppConfig

class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'

    def ready(self):
        import sys
        # El chequeo de sys.argv a veces falla, así que vamos a lo seguro:
        # 🔴 COMENTA ESTA LÍNEA PONIENDO UN # AL INICIO:
        import auditoria.signals
        pass