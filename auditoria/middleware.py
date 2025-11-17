# auditoria/middleware.py
import threading

_thread_locals = threading.local()


def get_current_request():
    """
    Devuelve el request actual almacenado en el hilo.
    """
    return getattr(_thread_locals, "request", None)


class ThreadLocalMiddleware:
    """
    Guarda el request en una variable de hilo para poder
    acceder a él desde los signals (donde no llega el request).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response