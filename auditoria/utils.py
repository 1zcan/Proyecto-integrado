from auditoria.models import LogAccion

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip or "-"
    

def registrar_log(request, accion, modelo, objeto_id, detalle=""):
    usuario = request.user if request.user.is_authenticated else None
    ip = get_client_ip(request)

    LogAccion.objects.create(
        usuario=usuario,
        accion=accion,
        modelo=modelo,
        objeto_id=str(objeto_id),
        detalle=detalle,
        ip_address=ip
    )
