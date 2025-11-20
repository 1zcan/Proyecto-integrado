from django.db import migrations

def cargar_datos_iniciales(apps, schema_editor):
    # Obtenemos el modelo histórico para evitar errores si el modelo cambia a futuro
    Catalogo = apps.get_model('catalogo', 'Catalogo')

    # Diccionario con los datos maestros oficiales
    datos_maestros = [
        # --- UBICACIÓN (Ñuble) ---
        ('VAL_COMUNA', [
            'Chillán', 'Chillán Viejo', 'San Carlos', 'Coihueco', 'Pinto', 
            'Bulnes', 'Quillón', 'San Nicolás', 'Ñiquén', 'San Fabián', 
            'Yungay', 'Pemuco', 'El Carmen', 'San Ignacio', 'Quirihue', 
            'Ninhue', 'Portezuelo', 'Trehuaco', 'Cobquecura', 'Coelemu', 'Ránquil'
        ]),
        ('VAL_ESTABLECIMIENTO', [
            'Hosp. Clínico Herminda Martín', 
            'Hosp. de San Carlos',
            'CESFAM Violeta Parra', 
            'CESFAM Sol de Oriente', 
            'CESFAM Los Volcanes',
            'CESFAM Isabel Riquelme',
            'CESFAM San Ramón Nonato',
            'PSR Quinchamalí'
        ]),

        # --- DATOS MATERNOS ---
        ('VAL_PUEBLO_ORIGINARIO', ['Mapuche', 'Aymara', 'Rapa Nui', 'Diaguita', 'Ninguno']),
        ('VAL_PREVISION', ['FONASA A', 'FONASA B', 'FONASA C', 'FONASA D', 'ISAPRE', 'Particular']),

        # --- DATOS DEL PARTO (REM A21) ---
        ('VAL_TIPO_PARTO', [
            'Parto Vaginal Cefálico', 
            'Parto Vaginal Podálica', 
            'Fórceps', 
            'Cesárea Electiva', 
            'Cesárea Urgencia'
        ]),
        ('VAL_ROBSON_GRUPO', [
            'G1: Nulípara, feto único, cefálica, >=37 sem, espontáneo',
            'G2: Nulípara, feto único, cefálica, >=37 sem, inducido/cesárea',
            'G3: Multípara, feto único, cefálica, >=37 sem, espontáneo',
            'G4: Multípara, feto único, cefálica, >=37 sem, inducido/cesárea',
            'G5: Cesárea anterior, feto único, cefálica, >=37 sem',
            'G6: Nulípara, podálica',
            'G7: Multípara, podálica',
            'G8: Embarazo múltiple',
            'G9: Situación transversa u oblicua',
            'G10: Pretérmino (<37 sem), cefálica'
        ]),
        ('VAL_MANEJO_DOLOR', ['Sin analgesia', 'Peridural', 'Raquídea', 'General', 'Analgesia no farmacológica']),
        ('VAL_POSICION_EXPULSIVO', ['Litotomía (Acostada)', 'Vertical', 'Cuclillas', 'Lateral']),
        ('VAL_ACOMPANANTE', ['Pareja', 'Familiar', 'Doula', 'Sin acompañante']),

        # --- DATOS DEL RECIÉN NACIDO (REM A24) ---
        ('VAL_SEXO_RN', ['Masculino', 'Femenino', 'Indeterminado']),
        ('VAL_DESTINO_RN', ['Alojamiento Conjunto (Puerperio)', 'Neonatología (UTI/UCI)', 'Traslado extra-sistema', 'Fallecido']),
        ('VAL_PROFILAXIS_RN', [
            'VHB (Hepatitis B)', 
            'VITK (Vitamina K)', 
            'POF (Profilaxis Ocular)', 
            'BCG'
        ]),
        ('VAL_REANIMACION', [
            'No requiere', 
            'Estimulación táctil / Aspiración', 
            'Ventilación a presión positiva (VPP)', 
            'Masaje cardíaco', 
            'Adrenalina / Medicamentos'
        ]),

        # --- TAMIZAJES (REM A11) ---
        ('VAL_RESULTADO_TAMIZAJE', ['Negativo', 'Positivo', 'Indeterminado', 'Pendiente']),
    ]

    # Insertamos los datos
    objetos_a_crear = []
    for tipo, lista_valores in datos_maestros:
        for indice, valor in enumerate(lista_valores, start=1):
            # Usamos get_or_create para no duplicar si se corre dos veces
            if not Catalogo.objects.filter(tipo=tipo, valor=valor).exists():
                objetos_a_crear.append(
                    Catalogo(tipo=tipo, valor=valor, orden=indice, activo=True)
                )
    
    Catalogo.objects.bulk_create(objetos_a_crear)

class Migration(migrations.Migration):

    dependencies = [
        # Aquí Django pondrá automáticamente la dependencia correcta.
        # No toques esto a menos que esté vacío.
        ('catalogo', '0003_alter_catalogo_tipo'),
    ]

    operations = [
        migrations.RunPython(cargar_datos_iniciales),
    ]