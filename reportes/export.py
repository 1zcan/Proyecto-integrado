"""
export.py (mencionado como export.py en la guía)

Este módulo maneja la generación de archivos físicos (Excel, PDF)
basado en los datos procesados por services.py.
"""

import io
from django.http import HttpResponse

# --- IMPORTANTE ---
# Necesitarás instalar estas librerías:
# pip install openpyxl
# pip install reportlab

import openpyxl
from openpyxl.styles import Font, Alignment
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def export_rem_excel(datos):
    """
    Genera un archivo Excel (XLSX) con los datos del REM.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"REM {datos['periodo']}"
    
    # Título
    ws['B2'] = f"Reporte REM Consolidado - Periodo {datos['periodo']}"
    ws['B2'].font = Font(bold=True, size=14)
    
    # --- REM A21 ---
    ws['B5'] = "REM A21 - Modelo Atención Parto"
    ws['B5'].font = Font(bold=True)
    ws['B6'] = "Total Partos"
    ws['C6'] = datos['rem_a21']['total_partos']
    ws['B7'] = "Total Cesáreas"
    ws['C7'] = datos['rem_a21']['total_cesareas']
    # ... (agregar más filas de datos)

    # --- REM A24 ---
    ws['B10'] = "REM A24 - Atención Recién Nacido"
    ws['B10'].font = Font(bold=True)
    ws['B11'] = "RN con Lactancia 60 min"
    ws['C11'] = datos['rem_a24']['rn_con_lm_60min']
    # ... (agregar más filas de datos)

    # Configurar respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="rem_{datos["periodo"]}.xlsx"'},
    )
    wb.save(response)
    return response

def export_rem_pdf(datos):
    """
    Genera un archivo PDF con los datos del REM.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    y = height - inch
    
    # Título
    p.setFont("Helvetica-Bold", 14)
    p.drawString(inch, y, f"Reporte REM Consolidado - Periodo {datos['periodo']}")
    y -= 0.5 * inch
    
    p.setFont("Helvetica", 11)
    
    # --- REM A21 ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, y, "REM A21 - Modelo Atención Parto")
    y -= 0.25 * inch
    p.setFont("Helvetica", 11)
    p.drawString(inch * 1.2, y, f"Total Partos: {datos['rem_a21']['total_partos']}")
    y -= 0.25 * inch
    p.drawString(inch * 1.2, y, f"Total Cesáreas: {datos['rem_a21']['total_cesareas']}")
    y -= 0.5 * inch
    
    # --- REM A24 ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, y, "REM A24 - Atención Recién Nacido")
    y -= 0.25 * inch
    p.setFont("Helvetica", 11)
    p.drawString(inch * 1.2, y, f"RN con Lactancia 60 min: {datos['rem_a24']['rn_con_lm_60min']}")
    
    # ... (agregar más datos y saltos de página si es necesario)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="rem_{datos["periodo"]}.pdf"'},
    )
    return response