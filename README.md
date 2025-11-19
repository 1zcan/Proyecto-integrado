# Proyecto-integrado
Código para la aplicación de la asignatura proyecto integrado.

## Instalación

python -m venv .venv

en caso de error: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

.venv\Scripts\activate.ps1

pip install -r requirements.txt

Crear el archivo .env con valores para:

-DB_NAME=

-DB_USER=

-DB_PASSWORD=

-SECRET_KEY=

-SENDGRID_API_KEY =

python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver

EN CASO DE ERROR 400, usar pestaña de incognito o forzar conexión http.
