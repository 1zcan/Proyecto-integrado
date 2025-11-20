from django.shortcuts import redirect

class SuperuserRedirectMiddleware:
    """
    Si un superusuario inicia sesión y accede a '/' lo enviamos al dashboard automáticamente.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si NO está autenticado → dejar normal
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Si es superusuario y está en la raíz del sitio, lo mandamos al dashboard
        if request.path == "/" and request.user.is_superuser:
            return redirect("dashboard:dashboard")

        return self.get_response(request)
