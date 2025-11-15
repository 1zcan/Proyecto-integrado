"""
services.py (mencionado como services/queries.py en la guía)

Este módulo contiene la lógica de negocio para obtener y procesar
los datos de los reportes. Importa modelos de las otras apps.
"""
import datetime
from django.db.models import Count, Q, Case, When, IntegerField, F
from django.db.models.functions import ExtractYear

# --- IMPORTANTE ---
# Ahora importamos los modelos reales de tus otras apps
# (Asegúrate que estas apps estén en tu INSTALLED_APPS en settings.py)
try:
    from madre.models import Madre, TamizajeMaterno
    from parto.models import Parto, ModeloAtencionParto, RobsonParto
    from recien_nacido.models import RecienNacido, ProfiRN
    from auditoria.models import LogAccion
except ImportError:
    # Si hay un error de importación, usamos un truco para que Django pueda arrancar
    print("ADVERTENCIA: No se pudieron importar modelos de otras apps en reportes/services.py")
    # Usamos un placeholder que fallará si se usa, pero permite que el servidor inicie
    Madre, TamizajeMaterno, Parto, ModeloAtencionParto, RobsonParto, RecienNacido, ProfiRN, LogAccion = (None,) * 8


def get_datos_rem(anio, mes):
    """
    Calcula los agregados para los reportes REM (A11, A21, A24)
    para un año y mes específicos.
    """
    print(f"Calculando REM para {anio}-{mes}")
    
    # --- Lógica con datos reales ---
    
    # 1. Datos de Parto (REM A21, H2/H3)
    base_partos_mes = Parto.objects.filter(fecha__year=anio, fecha__month=mes)
    total_partos = base_partos_mes.count()
    # (Ajusta 'CESAREA' si el valor guardado en tu modelo es diferente, ej: 'C')
    total_cesareas = base_partos_mes.filter(tipo_parto='CESAREA').count()

    # 2. Datos de Modelo de Atención (REM A21)
    # (Basado en la guía, estos campos están en el modelo Parto)
    partos_con_acompanamiento = base_partos_mes.filter(
        Q(acompanamiento_trabajo_parto=True) | Q(acompanamiento_solo_expulsivo=True)
    ).count()
    
    # 3. Datos de Recién Nacido (REM A24)
    base_rn_mes = RecienNacido.objects.filter(parto__fecha__year=anio, parto__fecha__month=mes)
    total_rn = base_rn_mes.count()
    rn_con_lm_60min = base_rn_mes.filter(lactancia_60min=True).count()
    
    # 4. Datos de Tamizajes (REM A11)
    # (Ajusta 'POSITIVO' si el valor guardado es diferente)
    
    # --- CORRECCIÓN ---
    # Evitamos el 'join' inverso (madre__parto) que está fallando.
    
    # 1. Obtenemos los IDs de las madres que tuvieron partos en el período.
    madres_con_parto_ids = base_partos_mes.values_list('madre_id', flat=True)
    
    # 2. Filtramos los tamizajes por esos IDs de madres.
    tamizajes_vih_positivos = TamizajeMaterno.objects.filter(
        madre_id__in=madres_con_parto_ids, 
        vih_resultado='POSITIVO'
    ).count()

    # Estructura de datos consolidada para la vista/template
    datos_consolidados = {
        'periodo': f"{mes}-{anio}",
        'rem_a21': {
            'total_partos': total_partos,
            'total_cesareas': total_cesareas,
            'total_vaginales': total_partos - total_cesareas,
            'partos_con_acompanamiento': partos_con_acompanamiento,
            # ... más indicadores A21 (puedes agregarlos aquí)
        },
        'rem_a24': {
            'total_rn': total_rn,
            'rn_con_lm_60min': rn_con_lm_60min,
            # ... más indicadores A24 (puedes agregarlos aquí)
        },
        'rem_a11': {
            'tamizajes_vih_positivos': tamizajes_vih_positivos,
            # ... más indicadores A11 (puedes agregarlos aquí)
        },
        'indicadores_h2_h3': {
            # El cálculo de Robson es complejo, requiere agrupar
            # Dejamos en 0 como placeholder
            'h2_parto_vertical': 0, # (cálculo pendiente)
            'h3_cesarea_g1_g10': 0, # (cálculo pendiente)
        }
    }
    
    return datos_consolidados

def get_datos_servicio_salud(anio, trimestre):
    """
    Calcula los agregados para el reporte del Servicio de Salud Ñuble.
    """
    print(f"Calculando SS Ñuble para {anio}-T{trimestre}")
    
    # --- Lógica con datos reales (sin simulación) ---
    
    # Mapeo de meses por trimestre
    if trimestre == '1':
        meses = [1, 2, 3]
        labels = ['Ene', 'Feb', 'Mar']
    elif trimestre == '2':
        meses = [4, 5, 6]
        labels = ['Abr', 'May', 'Jun']
    elif trimestre == '3':
        meses = [7, 8, 9]
        labels = ['Jul', 'Ago', 'Sep']
    else: # trimestre == '4'
        meses = [10, 11, 12]
        labels = ['Oct', 'Nov', 'Dic']

    # Consultas base
    partos_trimestre = Parto.objects.filter(fecha__year=anio, fecha__month__in=meses)
    rn_trimestre = RecienNacido.objects.filter(parto__fecha__year=anio, parto__fecha__month__in=meses)
    
    # --- CORRECCIÓN ---
    # Usamos la misma lógica de IDs para evitar el join problemático
    madres_con_parto_ids = partos_trimestre.values_list('madre_id', flat=True)
    madres_parto_trimestre = Madre.objects.filter(id__in=madres_con_parto_ids)

    # 1. Total Partos
    total_partos_trimestre = partos_trimestre.count()
    
    # 2. Cumplimiento Profilaxis VHB
    total_rn_trimestre = rn_trimestre.count()
    vhb_completas = ProfiRN.objects.filter(rn__in=rn_trimestre, tipo='VHB').count() # Asumiendo tipo='VHB'
    cumplimiento_vhb = (vhb_completas / total_rn_trimestre * 100) if total_rn_trimestre > 0 else 0

    # 3. Gráfico (ej: partos por mes)
    data_grafico = []
    for mes in meses:
        partos_del_mes = partos_trimestre.filter(fecha__month=mes).count()
        data_grafico.append(partos_del_mes)
    
    # 4. Totales por Edad Materna
    # (Requiere que Madre tenga 'fecha_nacimiento')
    # --- CORRECCIÓN ---
    # Calculamos la edad en la consulta de 'Parto', que es más directa
    partos_con_edad_madre = partos_trimestre.annotate(
        edad_madre=ExtractYear('fecha') - ExtractYear('madre__fecha_nacimiento')
    )
    
    menor_15 = partos_con_edad_madre.filter(edad_madre__lt=15).count()
    _15_19 = partos_con_edad_madre.filter(edad_madre__gte=15, edad_madre__lte=19).count()
    _20_34 = partos_con_edad_madre.filter(edad_madre__gte=20, edad_madre__lte=34).count()
    mayor_35 = partos_con_edad_madre.filter(edad_madre__gte=35).count()

    datos_consolidados = {
        'periodo': f"Trimestre {trimestre} - {anio}",
        'total_partos': total_partos_trimestre,
        'cumplimiento_profilaxis_vhb': round(cumplimiento_vhb, 1),
        'grafico_cumplimiento': {
            'labels': labels,
            'data': data_grafico
        },
        'totales_por_edad': {
            'menor_15': menor_15,
            '15_19': _15_19,
            '20_34': _20_34,
            'mayor_35': mayor_35
        }
    }
    return datos_consolidados

def get_datos_calidad():
    """
    Ejecuta chequeos de consistencia de datos (Control de Calidad).
    """
    print("Ejecutando chequeos de calidad...")
    
    # --- Consultas de calidad reales (sin simulación) ---
    inconsistencias = []
    
    # 1. Madres sin parto asociado
    # --- CORRECCIÓN ---
    # Usamos 'exclude' con los IDs de las madres que sí tienen parto
    madres_con_parto_ids = Parto.objects.values_list('madre_id', flat=True)
    madres_sin_parto = Madre.objects.exclude(id__in=madres_con_parto_ids) # Ajusta este filtro si es necesario
    if madres_sin_parto.exists():
        inconsistencias.append({
            'id': 'M-001', 
            'descripcion': f'Encontradas {madres_sin_parto.count()} madres activas sin parto asociado.', 
            'tipo': 'Advertencia'
        })

    # 2. Partos sin RN asociado
    # --- CORRECCIÓN ---
    # Asumiendo 'OneToOneField' en Parto, el reverso en Madre es 'parto'
    # Si 'OneToOneField' está en Madre, el reverso en Parto es 'madre'
    # 'reciennacido' es el nombre más probable de la relación inversa OneToOne
    partos_sin_rn = Parto.objects.filter(reciennacido__isnull=True)
    if partos_sin_rn.exists():
        inconsistencias.append({
            'id': 'P-005', 
            'descripcion': f'Encontrados {partos_sin_rn.count()} partos sin Recién Nacido asociado.', 
            'tipo': 'Error'
        })
        
    # 3. Tamizajes VDRL+ sin tratamiento
    vdrl_sin_tratamiento = TamizajeMaterno.objects.filter(
        vdrl_resultado='POSITIVO', 
        vdrl_tratamiento=False
    )
    if vdrl_sin_tratamiento.exists():
        inconsistencias.append({
            'id': 'T-003', 
            'descripcion': f'Encontrados {vdrl_sin_tratamiento.count()} tamizajes VDRL Positivo sin tratamiento.', 
            'tipo': 'Crítico'
        })
        
    # 4. Apgar fuera de rango (0-10)
    rn_apgar_error = RecienNacido.objects.filter(Q(apgar_1__gt=10) | Q(apgar_5__gt=10) | Q(apgar_1__lt=0) | Q(apgar_5__lt=0))
    if rn_apgar_error.exists():
        inconsistencias.append({
            'id': 'RN-002', 
            'descripcion': f'Encontrados {rn_apgar_error.count()} RN con Apgar fuera de rango (0-10).', 
            'tipo': 'Error'
        })
    
    # Conteo de totales
    total_errores = partos_sin_rn.count() + rn_apgar_error.count()
    total_advertencias = madres_sin_parto.count()
    total_criticos = vdrl_sin_tratamiento.count()
    
    return {
        'total_errores': total_errores + total_criticos, # Sumamos críticos a errores para el banner
        'total_advertencias': total_advertencias,
        'chequeos': inconsistencias
    }