# usuarios/email_utils.py
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings
from socket import error as socket_error

def enviar_correo(destinatario, asunto, contenido_texto):
    """
    Envía un correo usando la API de SendGrid.
    """
    sg = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)
    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject=asunto,
        plain_text_content=contenido_texto,
    )
    try:
        response = sg.send(message)
        # Podrías hacer un print para debug:
        # print(response.status_code)
        return True
    except (socket_error, Exception) as e:
        # Importante: NO botar el login si falla el envío
        print(f"Error enviando correo: {e}")
        return False
