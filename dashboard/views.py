from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """
    Vista para el panel principal.
    El filtrado visual se hace en el template usando user.perfil.rol
    """
    return render(request, 'dashboard/dashboard.html')