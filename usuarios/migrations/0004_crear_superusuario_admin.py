from django.db import migrations
from django.contrib.auth.hashers import make_password

def crear_superusuario_inicial(apps, schema_editor):
    # Obtenemos los modelos históricos
    User = apps.get_model('auth', 'User')
    Perfil = apps.get_model('usuarios', 'Perfil')

    username = 'admin'
    password = 'admin1234'
    email = 'admin@hchm.cl'

    # Verificamos si ya existe para no dar error
    if not User.objects.filter(username=username).exists():
        # Creamos el usuario manualmente (create_superuser no está disponible en migraciones históricas)
        user = User(
            username=username,
            email=email,
            is_staff=True,     # Permiso para entrar al admin de Django
            is_superuser=True, # Permiso total
            is_active=True,
            password=make_password(password) # Encriptamos la contraseña
        )
        user.save()

        # Le creamos su perfil de TI automáticamente
        # (A veces las señales post_save no corren en migraciones, así que lo hacemos manual)
        if not Perfil.objects.filter(user=user).exists():
            Perfil.objects.create(
                user=user,
                rol='ti_informatica' # Rol con acceso total según tu sistema
            )
            
def eliminar_superusuario(apps, schema_editor):
    # Lógica para revertir la migración si fuera necesario
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='admin').delete()

class Migration(migrations.Migration):

    dependencies = [
        # Asegúrate que esta dependencia apunte a la última migración que tengas en 'usuarios'
        # Generalmente es '0001_initial' o similar. Revisa tu carpeta usuarios/migrations/
        ('usuarios', '0003_alter_perfil_rol'),
    ]

    operations = [
        migrations.RunPython(crear_superusuario_inicial, eliminar_superusuario),
    ]