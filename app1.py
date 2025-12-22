import streamlit as st
import pandas as pd
import altair as alt
import re
import base64
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os 
import streamlit.components.v1 as components 
from io import BytesIO 
from reportlab.lib.pagesizes import A4, landscape 
from reportlab.lib.units import inch 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image 
from reportlab.lib import colors 
from reportlab.lib.styles import getSampleStyleSheet 


# ============================================================
#  CONFIGURACIÓN GENERAL Y CARGA DE LOGO
# ============================================================

def load_logo_base64(file_path):
    """Convierte el archivo de imagen a string Base64."""
    try:
        base_path = Path(__file__).parent
    except NameError:
        base_path = Path.cwd()
    
    logo_path = base_path / file_path
    
    #  Nota: Asegúrese de que 'logo_sanpablo.png' esté en la misma carpeta que su script.
    try:
        with open(logo_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None
    except Exception as e:
        return None

# Intenta cargar el logo. Si falla, usa un string base64 de emergencia.
logo_b64 = load_logo_base64("logo_sanpablo.png") 

if logo_b64:
    logo_src = f"data:image/png;base64,{logo_b64}"
else:
    # Placeholder de emergencia si el archivo de logo no se encuentra
    logo_src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAXRJREFUeJzt3LFOwzAUBeFvE4kFioK3oV24cAE8A4P0JcQf4AQ8AW8gY2CgICAgICAgICAgICAg+K1c/70lSZIe3D5/l9f/FwAAAACA1V9n39X607Pfb9/Nn5e3b97b1+f7fUe630z9A4H5f+gDAvP/UC+Yn7c/k5e3v0D2H0j9A4H5f6iFm3y7O/t7/R/c4D/vF/v7jVdD/g/1vF/i9p8H4v+hF25x9+Xl7b+w0lP89o3v9/uOdv9z9e4/vF/s73cO/w+7cIu7vy/n1/f3n6Tif/D5eXn/m/9n7d1/tC4tF078Hl8vL+/8XzG4y92Xl7f/gZ/t2r93/jV19uL29vs3n/f7jnb9L4/G/2f9H7duf7w/f79/b9/e77P9G/f2f9+8BBAAAAICrF16Y66yTfG/vAAAAAElFTkSuQmCC" 

# Configuración de la página
st.set_page_config(
    page_title="Red San Pablo - Producción HIS", 
    page_icon=logo_src,  
    layout="wide"
)

# Mapeo manual para asegurar los meses en español (usado en la función de fecha)
meses_espanol = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

@st.cache_data
def obtener_fecha_modificacion(path="CONSOLIDADO.xlsx"):
    """Obtiene la fecha y hora de la última modificación del archivo de datos con meses en español."""
    try:
        timestamp = os.path.getmtime(path)
        # Interpretar timestamp como UTC y convertir a hora de Perú (America/Lima)
        dt_object = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC")).astimezone(ZoneInfo("America/Lima"))
        
        dia = dt_object.day
        mes_num = dt_object.month
        anio = dt_object.year
        tiempo = dt_object.strftime("%H:%M") 
        
        mes_nombre = meses_espanol.get(mes_num, "Mes Desconocido")
        
        return f"{dia} de {mes_nombre} de {anio} - {tiempo} Hrs."
    except FileNotFoundError:
        now = datetime.now(ZoneInfo("America/Lima"))
        mes_nombre = meses_espanol.get(now.month, "Mes Desconocido")
        return f"{now.day} de {mes_nombre} de {now.year} - {now.strftime('%H:%M')} Hrs. (Archivo no encontrado)"


@st.cache_data
def cargar_datos(path="CONSOLIDADO.xlsx"):
    """Carga los datos del archivo Excel o usa datos de ejemplo (con más de 100 filas)."""
    #  Nota: Reemplace "CONSOLIDADO.xlsx" con la ruta correcta a su archivo.
    try:
        df = pd.read_excel(path, engine="openpyxl")
        df.columns = df.columns.map(lambda c: str(c).strip())
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        return df
    except FileNotFoundError:
        st.warning(f" **Advertencia:** Archivo de datos no encontrado. Usando datos de ejemplo (120 filas).")
        # Datos de ejemplo base
        data = {
            "anio": [2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024],
            "mes": [10, 10, 10, 10, 10, 10, 10, 10, 11, 11],
            "nombre_establecimiento": ["IPRESS A", "IPRESS B", "IPRESS A", "IPRESS C", "IPRESS B", "IPRESS A", "IPRESS B", "IPRESS C", "IPRESS A", "IPRESS B"],
            "profesional": ["Cardiología", "Medicina General", "Cardiología", "Ginecología", "Pediatría", "Medicina Interna", "Oftalmología", "Cirugía", "Cardiología", "Medicina General"],
            "nombres_profesional": ["Dr. Perez", "Lic. García", "Dr. Perez", "Dra. Lopez", "Dr. Soto", "Dra. Rojas", "Lic. Vidal", "Dr. Castro", "Dr. Perez", "Lic. García"],
            "total.1": [150, 220, 180, 90, 300, 110, 250, 140, 160, 230], # Usando total.1 como columna de atenciones
            "atendidos_servicios_total": [120, 180, 140, 70, 250, 90, 200, 100, 130, 190],
        }
        
        # Inicializar columnas de días (1.1 a 31.1)
        for i in range(1, 32):
            data[f"{i}.1"] = [max(1, (10 + j * 2) - abs(i - 15)) for j in range(10)] # Valores base ficticios
             
        # Crear filas adicionales para simular más de 100 profesionales
        num_initial_rows = len(data["anio"])
        rows_to_add = 110 - num_initial_rows if 110 > num_initial_rows else 0
        
        for i in range(rows_to_add):
            idx = i + num_initial_rows
            
            data["anio"].append(2024)
            data["mes"].append(11)
            data["nombre_establecimiento"].append(f"IPRESS {chr(65 + (idx % 3))}")
            data["profesional"].append(f"Especialidad {idx % 5}")
            data["nombres_profesional"].append(f"Dr(a). Ficticio {idx}")
            data["total.1"].append(100 + idx * 5) # Usando total.1
            data["atendidos_servicios_total"].append(90 + idx * 4)
            
            for j in range(1, 32):
                data[f"{j}.1"].append(max(0, 5 + (idx % 10) + (j % 5)))

        # Se usa dict comprehension para combinar listas.
        combined_data = {key: data[key] for key in data}
        
        return pd.DataFrame(combined_data)

def detectar_dias_columnas(columns):
    """Detecta columnas de días en formato '1.1', '2.1', ..., '31.1'"""
    # Patrón para detectar números del 1 al 31 seguidos de .1
    return sorted([str(c) for c in columns if re.fullmatch(r"(0?[1-9]|[12][0-9]|3[01])\.1", str(c))], 
                  key=lambda x: int(x.split('.')[0]))

def renombrar_columnas_dias(df):
    """Renombra las columnas de días de formato '1.1' a solo '1' para mostrar en la tabla"""
    rename_dict = {}
    for col in df.columns:
        if re.fullmatch(r"(0?[1-9]|[12][0-9]|3[01])\.1", str(col)):
            # Extraer solo el número antes del punto
            nuevo_nombre = col.split('.')[0]
            rename_dict[col] = nuevo_nombre
    return df.rename(columns=rename_dict)

# ============================================================
#  FUNCIÓN DE GENERACIÓN DE PDF (CORREGIDA)
# ============================================================

def crear_pdf_profesional(df_tabla, filtros, logo_data):
    """
    Genera un reporte PDF profesional de la tabla de producción usando ReportLab.
    
    CORRECCIÓN: Se ajustan los anchos de columna dinámicamente, forzando un ancho 
    mínimo para las columnas de días para que la tabla no se descuadre en A4 horizontal.
    """
    buffer = BytesIO()
    # Usar A4 en orientación horizontal para tablas grandes
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=0.5*inch, rightMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    story = []

    # --- TÍTULO PRINCIPAL Y LOGO ---
    
    # 1. Logo (si está disponible)
    img = None
    if logo_data:
        # Reposicionar el puntero del BytesIO si se va a usar
        logo_data.seek(0)
        try:
            # Crear Image desde BytesIO
            img = Image(logo_data, width=0.75*inch, height=0.75*inch)
        except Exception:
            img = None
    
    # 2. Título basado en filtros
    filtro_mes = filtros.get("Mes", "Todos")
    filtro_ipress = filtros.get("Establecimiento", "Todas las IPRESS")
    
    titulo_texto = f"REPORTE GENERAL DE PRODUCCIÓN HIS"
    subtitulo_texto = f"PERÍODO: {filtro_mes} | ESTABLECIMIENTO: {filtro_ipress} | AÑO: {filtros.get('Año', 'Todos')}"
    
    
    # Estilos de títulos
    style_h1 = styles['h1']
    style_h1.alignment = 1 # Centro
    style_h1.textColor = colors.HexColor('#003c8f') # Azul oscuro
    style_h1.fontName = 'Helvetica-Bold'
    style_h1.fontSize = 18
    
    style_sub = styles['h3']
    style_sub.alignment = 1 # Centro
    style_sub.textColor = colors.HexColor('#555555') 
    style_sub.fontName = 'Helvetica'
    style_sub.fontSize = 12

    # Construir el encabezado con logo y texto (usando una tabla de 2 columnas)
    titulo_main = Paragraph(titulo_texto, style_h1)
    titulo_sub = Paragraph(subtitulo_texto, style_sub)
    
    # Crea una tabla para alinear el logo y el texto
    ancho_pagina = landscape(A4)[0]
    ancho_disponible = ancho_pagina - 1.0 * inch # Márgenes de 0.5" a cada lado

    if img:
        # Usamos una estructura de 2x2 para alinear el logo y el texto en el centro
        header_data = [[img, titulo_main], ['', titulo_sub]]
        # Ancho total: ~10.0 pulgadas. Logo: 1 pulgada, Texto: 9.0 pulgadas.
        col_widths_header = [1.0 * inch, ancho_disponible - 1.0 * inch] 
    else:
        header_data = [[titulo_main], [titulo_sub]]
        col_widths_header = [ancho_disponible]

    header_table = Table(header_data, colWidths=col_widths_header)
    
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.25*inch))
    
    # --- TABLA DE DATOS ---
    
    # Preparar datos para ReportLab
    # df_tabla debe tener las columnas que se quieren mostrar
    
    # 1. Renombrar columnas de días en el DataFrame para el PDF
    df_temp = df_tabla.copy()
    
    # Renombrar columnas de días de formato '1.1' a '1' para el PDF
    for col in df_temp.columns:
        if re.fullmatch(r"(0?[1-9]|[12][0-9]|3[01])\.1", str(col)):
            nuevo_nombre = col.split('.')[0]
            df_temp = df_temp.rename(columns={col: nuevo_nombre})
    
    # 2. Añadir columna ITEM (Index + 1)
    df_temp = df_temp.reset_index().rename(columns={'index': 'ITEM'}).copy()
    df_temp['ITEM'] = df_temp.index + 1
    
    # Reordenar para que ITEM sea la primera columna
    cols_order = ['ITEM'] + [col for col in df_temp.columns if col != 'ITEM']
    df_temp = df_temp[cols_order]

    # Convertir a lista de listas para ReportLab
    data = [df_temp.columns.tolist()] + df_temp.values.tolist()
    
    # 3. Convertir números a strings con formato de miles
    for i in range(1, len(data)):
        for j in range(len(data[i])):
            val = data[i][j]
            try:
                # Asumiendo que las columnas numéricas relevantes son enteros (días, atendidos, atenciones)
                if isinstance(val, (int, float)) and not pd.isna(val): 
                    data[i][j] = f"{int(val):,}"
                elif pd.isna(val):
                    data[i][j] = ""
            except:
                pass

    # Crear objeto Table
    # Ancho total disponible (usando el mismo que para el encabezado)
    table_width = ancho_disponible 

    # Número total de columnas
    num_cols = len(data[0]) 
    
    # Crear lista de anchos de columna dinámicamente
    col_widths = []
    
    # Definir el número de columnas fijas de identificación (ITEM, Prof, Profesion, Estab, Atendidos, Atenciones)
    NUM_FIXED_COLS = 6
    
    if num_cols >= NUM_FIXED_COLS:
        # Anchos fijos optimizados para A4 paisaje (suman 5.7 pulgadas)
        col_widths_fixed = [
            0.3 * inch,  # ITEM
            1.7 * inch,  # Profesional (REDUCIDO)
            1.2 * inch,  # Profesión 
            1.2 * inch,  # Establecimiento
            0.7 * inch,  # Atendidos
            0.6 * inch   # Atenciones
        ]
        col_widths.extend(col_widths_fixed)
        
        # Calcular ancho restante
        remaining_width = table_width - sum(col_widths)
        num_day_cols = num_cols - NUM_FIXED_COLS - 1  # Restar 1 para la columna TOTAL
        
        if num_day_cols > 0:
            # Ancho mínimo para columnas de días (0.15 pulgadas = 10.8 puntos)
            day_width_min = 0.15 * inch 
            
            # Usar el ancho mínimo si el espacio lo permite, sino dividir el espacio restante.
            if num_day_cols * day_width_min > remaining_width:
                 # Caso extremo: dividir el espacio restante entre las columnas de días
                 day_width_final = remaining_width / num_day_cols
            else:
                 # Caso normal: usar el ancho mínimo para que las columnas de día sean estrechas
                 day_width_final = day_width_min

            # Asegurar que el ancho de la columna de día no sea negativo (si remaining_width fuera negativo)
            if day_width_final < 0:
                 day_width_final = 0.1 * inch

            col_widths.extend([day_width_final] * num_day_cols)
            
        # Agregar ancho para la columna TOTAL (más ancha que las columnas de días)
        col_widths.append(0.5 * inch)  # Columna TOTAL más ancha

    # Crear la tabla
    if not col_widths: 
        return None
        
    # El ancho de la tabla será la suma de los anchos de columna calculados
    pdf_table = Table(data, colWidths=col_widths)

    # Definir estilos de tabla
    style = TableStyle([
        # Headers
        ('BACKGROUND', (0, 0), (-2, 0), colors.HexColor('#003c8f')), # Azul oscuro para todas excepto TOTAL
        ('TEXTCOLOR', (0, 0), (-2, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-2, 0), 6), # Reducir tamaño de fuente en headers
        ('FONTSIZE', (-1, 0), (-1, 0), 7), # Tamaño de fuente más grande para TOTAL header
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        
        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-2, -1), 5), # AÚN MÁS REDUCIDO: 5 puntos para las filas de datos
        ('FONTSIZE', (-1, 1), (-1, -1), 6), # Tamaño de fuente más grande para datos de TOTAL
        ('ALIGN', (0, 1), (0, -1), 'CENTER'), # ITEM (Index)
        ('ALIGN', (1, 1), (1, -1), 'LEFT'), # PROFESIONAL
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'), # El resto
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        
        # Columna de totales (ATENDIDOS y ATENCIONES) - Índices 4 y 5
        ('BACKGROUND', (4, 1), (5, -1), colors.HexColor('#d4edda')), # Verde claro
        ('TEXTCOLOR', (4, 1), (5, -1), colors.HexColor('#155724')), # Verde oscuro
        ('FONTNAME', (4, 1), (5, -1), 'Helvetica-Bold'),
        
        # Columna TOTAL - aplicar un estilo especial
        ('BACKGROUND', (-1, 0), (-1, 0), colors.HexColor('#ffc107')), # Amarillo para header de TOTAL
        ('TEXTCOLOR', (-1, 0), (-1, 0), colors.HexColor('#856404')), # Marrón oscuro para texto
        ('FONTNAME', (-1, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (-1, 1), (-1, -1), colors.HexColor('#fff3cd')), # Amarillo claro para datos de TOTAL
        ('TEXTCOLOR', (-1, 1), (-1, -1), colors.HexColor('#856404')), # Marrón oscuro para texto
        ('FONTNAME', (-1, 1), (-1, -1), 'Helvetica-Bold'),
    ])
    
    # --- FILAS RAYADAS ---
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.add('BACKGROUND', (0, i), (-2, i), colors.HexColor('#eef6ff')) # Excluir columna TOTAL

    pdf_table.setStyle(style)
    story.append(pdf_table)
    
    # --- FOOTER ---
    story.append(Spacer(1, 0.25*inch))
    fecha_reporte = datetime.now(ZoneInfo("America/Lima")).strftime("%d/%m/%Y %H:%M:%S")
    footer_text = f"Generado el: {fecha_reporte} (Perú). | Fuente de Datos: HISMINSA. | Este reporte incluye {len(df_tabla)} profesionales."
    
    style_footer = styles['Normal']
    style_footer.alignment = 1 # Centro
    style_footer.textColor = colors.HexColor('#6c757d')
    style_footer.fontSize = 8
    
    story.append(Paragraph(footer_text, style_footer))
    
    # --- CONSTRUIR DOCUMENTO ---
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error al generar el PDF: {e}")
        return None


df = cargar_datos()
day_cols = detectar_dias_columnas(df.columns)
fecha_actualizacion = obtener_fecha_modificacion()
orden_meses = list(meses_espanol.values())
if "mes" in df.columns:
    df["mes_nombre"] = df["mes"].map(meses_espanol)
    df["mes_nombre"] = pd.Categorical(df["mes_nombre"], categories=orden_meses, ordered=True)


# ============================================================
#  ESTILOS CSS PROFESIONALES (GLOBALes, no de la tabla)
# ============================================================
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

/* 1. Resetear el padding principal para eliminar el espacio nativo de Streamlit */
[data-testid="stAppViewContainer"] > div:first-child {
    padding-top: 0px !important; 
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Roboto', sans-serif !important;
    background-color: #f6f8fb;
}

/* OCULTAR BARRA BLANCA Y MENÚS NATIVOS  */
[data-testid="stHeader"] {
    display: none !important;
}
[data-testid="stHeader"] > div:last-child { 
    visibility: hidden;
    pointer-events: none;
}
.st-emotion-cache-1pxazr7 > header > div:last-child {
    visibility: hidden;
    pointer-events: none;
}

/* -------------------------------------------------
    ESTILO GLOBAL DEL ENCABEZADO (FIXED)
------------------------------------------------- */
.header-container {
    box-shadow: 0 12px 40px rgba(0,0,0,0.45) !important;
    border-radius: 0 !important; 
    font-family: 'Roboto', sans-serif !important;
    
    position: fixed !important;
    top: 0 !important;
    left: 0;
    right: 0;
    width: 100%;
    z-index: 99999; 
    /* Altura por defecto en Desktop */
    padding: 10px 40px; 
    align-items: center;
}

/* Ajuste del margen para el primer contenido (Desktop) */
[data-testid="stVerticalBlock"]:nth-child(2) { 
    margin-top: 120px !important; 
    /* Margen positivo para empezar debajo del header */
    padding-top: 0px !important;
}

/* -------------------------------------------------
    RESPONSIVO: MEDIA QUERY PARA MÓVILES (< 768px)
------------------------------------------------- */
@media (max-width: 768px) {
    
    /* 1. Ajuste del encabezado para móviles: menos padding, logo más pequeño y centrado */
    .header-container {
        padding: 5px 15px !important;
        /* Forzar apilamiento de logo y texto en móvil */
        flex-direction: column !important;
        align-items: flex-start !important; 
    }
    
    /* 2. Reducir tamaño del logo */
    .header-container img {
        width: 80px !important;
        height: 80px !important; 
        margin-bottom: 5px; /* Espacio entre logo y texto */
    }

    /* 3. Reducir tamaño del texto principal */
    .header-container p:nth-child(1) {
        font-size: 20px !important;
        line-height: 1.2 !important;
    }
    
    /* 4. Reducir tamaño del subtítulo */
    .header-container p:nth-child(2) {
        font-size: 12px !important;
        margin-bottom: 5px;
    }

    /* 5. Ajuste del margen para el primer contenido (Móvil) */
    /* El header fijo es más pequeño en móvil (aprox 100px) */
    [data-testid="stVerticalBlock"]:nth-child(2) { 
        margin-top: 100px !important;
    }
    
    /* 6. Ajustar fuente y fecha */
    div:has(> span:contains("Fuente de Datos")) {
        flex-direction: column !important;
        align-items: flex-start !important;
        font-size: 14px !important;
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }
    div:has(> span:contains("Fuente de Datos")) > span {
        margin-bottom: 5px;
    }

    /* 7. Reducir espacio en métricas */
    .stMetric {
        padding: 8px !important;
        margin-bottom: 10px;
    }
    [data-testid="stMetricValue"] {
        font-size: 20px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
    }
}
/* ------------------------------------------------- */


/* Otros estilos */
.stMetric {
    background: white;
    border-radius: 15px;
    padding: 12px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    border-left: 6px solid #0056d6;
}

[data-testid="stMetricValue"] {
    color: #0b5394;
    font-size: 26px;
    font-weight: 700;
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
    color: #444;
}

/* Ocultar botón de Expander en Filtros */
[data-testid="stExpander"] button {
    display: none !important;
    visibility: hidden !important; 
    pointer-events: none !important;
}

[data-testid="stExpander"] > div:first-child {
    padding-left: 0px !important;
    padding-right: 0px !important;
}

/* Estilos de Hover en Filtros (Contenedores) */
[data-testid="stExpanderDetails"] [data-testid="stVerticalBlock"] {
    margin: 8px 0 !important; 
    background-color: white;
    border-radius: 8px; 
    padding: 8px 10px; 
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease, border 0.2s ease;
}

[data-testid="stExpanderDetails"] [data-testid="stVerticalBlock"]:hover {
    transform: translateY(-2px); 
    box-shadow: 0 6px 15px rgba(0,0,0,0.15); 
    background-color: #e6f0ff; 
    border: 1px solid #0056d6;
}


/* El st.dataframe ya no se usa, pero mantenemos estos estilos genéricos por si acaso */
[data-testid="stStyledDataFrame"] tbody tr:hover {
    background-color: #e6f0ff !important;
    color: #003c8f !important; 
    cursor: pointer;
}

div[data-testid="stSlider"] > div > div:nth-child(1) > div:nth-child(2) > div {
    background-color: #E83E8C !important;
}

div[data-testid="stSlider"] > div > div:nth-child(1) > div:nth-child(2) > div > div {
    background-color: #C03070 !important;
}

/* -------------------------------------------------
    ESTILOS PARA SELECTBOX (MENÚ DESPLEGABLE)
    (Versión 12.1 - Colores ajustados al encabezado)
------------------------------------------------- */

/* 1. Target el contenedor principal para darle un aspecto limpio */
div[data-testid*="stSelectbox"] {
    background-color: white !important;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* 2. Selector que apunta a cualquier elemento que se comporte como opción, forzándolo a ser blanco */
[data-testid*="stOption"], [role="option"] {
    background-color: white !important;
    color: #333333 !important; 
    transition: background-color 0.1s; /* Transición suave */
}

/* 3. Aplicar AZUL similar al encabezado al hacer HOVER */
[data-testid*="stOption"]:hover, [role="option"]:hover,
[data-testid*="stOption"]:focus, [role="option"]:focus { 
    background-color: #0056d6 !important;
    /* Azul más claro del encabezado */
    color: white !important;
    /* Texto blanco para contraste */
}

/* 4. Aplicar AZUL OSCURO del encabezado al ITEM SELECCIONADO (permanente) */
[data-testid="stOptionSelectable"] {
    background-color: #003c8f !important;
    /* Azul oscuro principal del encabezado */
    color: white !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
#  FUNCIÓN DE DIVISOR ESTILIZADO (Reutilizable)
# ============================================================
def display_styled_divider():
    """Muestra un divisor horizontal con gradiente azul personalizado."""
    st.markdown("""
    <div style="
        height: 2px;
        background: linear-gradient(90deg, #0056d6 0%, #003c8f 70%, #f6f8fb 100%);
        margin-top: 10px;
        margin-bottom: 20px;
        border-radius: 1px;
    "></div>
    """, unsafe_allow_html=True)

# ============================================================
#  ENCABEZADO (CON ESTILO FIXED IMPLÍCITO DESDE CSS)
# ============================================================
st.markdown(f"""
<div class="header-container" style="
    width:100%;
    background: linear-gradient(90deg, #003c8f 0%, #0056d6 100%);
    display:flex;
    gap:20px;
    color:white;
    margin-bottom:0px; 
">
    <img src="{logo_src}" style="
        width:100px;
        height:100px; 
        border-radius:50%; 
        object-fit:cover; 
        border:5px solid rgba(255,255,255,1);
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    ">
    <div style="display:flex; flex-direction:column; justify-content:center;">
        <p style="
            margin:2px 0;
            font-size:32px; 
            font-weight:700; 
            line-height:1.1; 
        ">REPORTE DE PRODUCCIÓN HIS - RED SAN PABLO</p>
        <p style="
            margin:2px 0;
            font-size:16px; 
            font-weight:300; 
            line-height:1.1; 
            opacity:0.9;
        ">Análisis dinámico de producción por profesional, establecimiento y días del mes</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
#  FECHA DE ACTUALIZACIÓN DEL ARCHIVO Y FUENTE
# ============================================================
fecha_actualizacion = obtener_fecha_modificacion()

#  Contenedor de Fecha y Fuente
st.markdown(f"""
    <div style="
        display: flex;
        justify-content: space-between; 
        align-items: center;
        margin-top: 0px; 
        margin-bottom: 5px; 
        padding: 5px 0;
        font-size: 16px;
        font-weight: 500;
        color: #0056d6;
    ">
        <span>
            Fuente de Datos: <b>HISMINSA</b>
        </span>
        <span>
            Última Actualización de Datos:  <b>{fecha_actualizacion}</b>
        </span>
    </div>
""", 
unsafe_allow_html=True)

# ============================================================
#  FILTROS (EXPANDER FIJO CON HOVER)
# ============================================================
with st.expander(" **FILTROS DE BÚSQUEDA**", expanded=True):
    # Streamlit se encarga de apilar estas columnas en móvil
    filtro_col1, filtro_col2, filtro_col3, filtro_col4, filtro_col5 = st.columns(5)

    with filtro_col1:
        anios_data = sorted(df["anio"].dropna().unique().tolist()) if "anio" in df.columns else []
        anios = ["Todos"] + anios_data
        
        default_year = "Todos"
        # Lógica para establecer un año por defecto
        if 2025 not in anios_data:
            if 2025 not in anios:
                 anios.append(2025)
                 anios = sorted(anios, key=lambda x: x if x != "Todos" else 0)
        
        if 2025 in anios:
            default_year = 2025
        elif len(anios_data) == 1:
            default_year = anios_data[0]

        default_index = anios.index(default_year) if default_year in anios else 0
        
        filtro_anio = st.selectbox(
            " **Año**", 
            anios, 
            index=default_index
        )

    with filtro_col2:
        filtro_mes = st.selectbox(" **Mes**", ["Todos"] + orden_meses)

    with filtro_col3:
        ipress = ["Todos"] + sorted(df["nombre_establecimiento"].dropna().unique().tolist()) if "nombre_establecimiento" in df.columns else ["Todos"]
        filtro_ipress = st.selectbox(" **Establecimiento**", ipress)

    with filtro_col4:
        especialidades = ["Todos"] + sorted(df["profesional"].dropna().unique().tolist()) if "profesional" in df.columns else ["Todos"]
        # El título del filtro ahora es "Profesión/Especialidad"
        filtro_especialidad = st.selectbox(" **Profesión/Especialidad**", especialidades) 

    with filtro_col5:
        profesionales = ["Todos"] + sorted(df["nombres_profesional"].dropna().unique().tolist()) if "nombres_profesional" in df.columns else ["Todos"]
        filtro_profesional = st.selectbox(" **Profesional**", profesionales)

# ============================================================
#  PARÁMETROS 
# ============================================================
st.markdown("---") 

# Se apilan en móvil
col_params_izq, col_params_der = st.columns([1, 1])

with col_params_izq:
    # Ajuste de slider si tienes muchos profesionales (máx 100)
    max_prof_count = len(df["nombres_profesional"].dropna().unique()) if "nombres_profesional" in df.columns else 100 
    top_n_default = min(20, max_prof_count)
    top_n = st.slider(" **Ranking de Atenciones por Profesional**", 5, max(50, max_prof_count), top_n_default)
    
# ============================================================
#  APLICAR FILTROS
# ============================================================
df_filtrado = df.copy()
if filtro_anio != "Todos":
    try:
        df_filtrado = df_filtrado[df_filtrado["anio"] == int(filtro_anio)]
    except ValueError:
        pass 

if filtro_mes != "Todos":
    df_filtrado = df_filtrado[df_filtrado["mes_nombre"] == filtro_mes]
if filtro_ipress != "Todos":
    df_filtrado = df_filtrado[df_filtrado["nombre_establecimiento"] == filtro_ipress]
if filtro_especialidad != "Todos":
    df_filtrado = df_filtrado[df_filtrado["profesional"] == filtro_especialidad]
if filtro_profesional != "Todos":
    df_filtrado = df_filtrado[df_filtrado["nombres_profesional"] == filtro_profesional]

if df_filtrado.empty:
    st.warning(" No hay datos para los filtros seleccionados.")
    st.stop()

# ============================================================
#  AGRUPACIÓN Y RESÚMENES
# ============================================================
# <-- CAMBIO IMPORTANTE: AHORA USAMOS 'total.1' COMO FUENTE DE ATENCIONES -->
att_col = "total.1" if "total.1" in df_filtrado.columns else None 
att_serv_total_col = "atendidos_servicios_total" if "atendidos_servicios_total" in df_filtrado.columns else None

group_cols = [c for c in ["nombre_establecimiento", "profesional", "nombres_profesional"] if c in df_filtrado.columns]
agg_dict = {d: "sum" for d in day_cols if d in df_filtrado.columns}
if att_serv_total_col:
    agg_dict[att_serv_total_col] = "sum"
if att_col:
    agg_dict[att_col] = "sum"

if not group_cols:
    resumen = df_filtrado.agg(agg_dict).to_frame().T
else:
    resumen = df_filtrado.groupby(group_cols, as_index=False).agg(agg_dict)

# Ajuste: asegurar suma correcta de "total.1" por profesional si existe
if "total.1" in df_filtrado.columns and group_cols:
    # Calcula la suma real por grupo
    suma_att = (
        df_filtrado.groupby(group_cols, as_index=False)["total.1"]
        .sum()
        .rename(columns={"total.1":"Total_Atenciones_sum"}) 
    )
    # Merge para asegurar que el resumen tenga la suma por grupo (evita problemas de filas múltiples)
    resumen = resumen.merge(suma_att, on=group_cols, how="left")
    resumen["total.1"] = resumen["Total_Atenciones_sum"] 
    resumen = resumen.drop(columns=["Total_Atenciones_sum"])

# Aplicación del cambio: "profesional" ahora se etiqueta como "Profesión"
rename_map = {
    "nombre_establecimiento": "Establecimiento",
    "profesional": "Profesión",     
    "nombres_profesional": "Profesional",
    "atendidos_servicios_total": "Atendidos",
    # <-- CAMBIO: ahora mapeamos la columna 'total.1' a "Atenciones" -->
    "total.1": "Atenciones" 
}
resumen = resumen.rename(columns=rename_map)

sort_col = "Atenciones"
if "Atenciones" not in resumen.columns:
    resumen["Suma_Dias"] = resumen[[c for c in day_cols if c in resumen.columns]].sum(axis=1)
    sort_col = "Suma_Dias"

# AGREGAR COLUMNA TOTAL DESPUÉS DE LOS DÍAS
# Primero, asegurarnos de que las columnas de días estén al final
column_order = []
for col in resumen.columns:
    if col not in day_cols:
        column_order.append(col)
        
# Agregar las columnas de días
for col in day_cols:
    if col in resumen.columns:
        column_order.append(col)

# Reordenar el DataFrame
resumen = resumen[column_order]

# AGREGAR LA COLUMNA TOTAL QUE SUMA TODAS LAS COLUMNAS DE DÍAS
# Obtener solo las columnas numéricas de días
dias_numericos = [col for col in day_cols if col in resumen.columns]
if dias_numericos:
    resumen['TOTAL'] = resumen[dias_numericos].sum(axis=1)

resumen = resumen.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

# Aquí limitamos el ranking al Top N, aunque el resumen completo tiene >100
resumen_top = resumen.head(top_n).copy() 

# ============================================================
#  INICIO DE LÓGICA DE PDF Y TABLA PRINCIPAL
# ============================================================

st.header("Resultados por Profesional y Establecimiento")

# ------------------------------------------------------------
# 1. LÓGICA DE GENERACIÓN DE PDF (Movida al inicio de la tabla)
# ------------------------------------------------------------

# Obtener el logo binario para el PDF (si está disponible)
logo_file_path = "logo_sanpablo.png"
logo_data = None
try:
    base_path = Path(__file__).parent
    logo_path = base_path / logo_file_path
    with open(logo_path, "rb") as f:
        logo_data = BytesIO(f.read())
except Exception:
    pass

# Prepara el DataFrame final para el PDF (usa el resumen completo)
df_for_pdf = resumen.copy() # 'resumen' tiene todos los datos filtrados, ordenados

# Renombrar columnas de días en el DataFrame para el PDF (de 1.1 a 1, etc.)
df_for_pdf_pdf = df_for_pdf.copy()
for col in df_for_pdf_pdf.columns:
    if re.fullmatch(r"(0?[1-9]|[12][0-9]|3[01])\.1", str(col)):
        nuevo_nombre = col.split('.')[0]
        df_for_pdf_pdf = df_for_pdf_pdf.rename(columns={col: nuevo_nombre})

# Columnas a incluir en el PDF: principales, días
pdf_cols_base = ["Profesional", "Profesión", "Establecimiento", "Atendidos", "Atenciones"]
# Usar el nombre interno correcto para "Atenciones" si fue re-etiquetada
if "Suma_Dias" in df_for_pdf_pdf.columns and "Atenciones" not in df_for_pdf_pdf.columns:
     pdf_cols_base[-1] = "Suma_Dias"

# Obtener columnas de días renombradas (sin .1)
dias_renombrados_pdf = []
for col in day_cols:
    if col in df_for_pdf_pdf.columns:
        dias_renombrados_pdf.append(col.split('.')[0])
    elif col.split('.')[0] in df_for_pdf_pdf.columns:
        dias_renombrados_pdf.append(col.split('.')[0])

pdf_cols = [c for c in pdf_cols_base if c in df_for_pdf_pdf.columns] + [c for c in dias_renombrados_pdf if c in df_for_pdf_pdf.columns]
# Agregar la columna TOTAL al final
if 'TOTAL' in df_for_pdf_pdf.columns:
    pdf_cols.append('TOTAL')

df_pdf_final = df_for_pdf_pdf[pdf_cols]

# Renombrar 'Suma_Dias' de vuelta a 'Atenciones' si fue usado
if 'Suma_Dias' in df_pdf_final.columns:
    df_pdf_final = df_pdf_final.rename(columns={'Suma_Dias': 'Atenciones'})

# Filtros aplicados para el nombre del archivo
filtros_aplicados = {
    "Mes": filtro_mes,
    "Establecimiento": filtro_ipress,
    "Año": filtro_anio
}

# Llamar a la función que genera el PDF (con el DataFrame completo y la data del logo)
pdf_buffer = crear_pdf_profesional(df_pdf_final, filtros_aplicados, logo_data)


# ------------------------------------------------------------
# 2. CHECKBOX Y BOTÓN DE DESCARGA (Lado a lado)
# ------------------------------------------------------------

# Crear columnas para alinear el checkbox y el botón
col_check, col_button, col_spacer = st.columns([0.45, 0.35, 0.2])

with col_check:
    # Checkbox para mostrar/ocultar las columnas de días
    show_days_table = st.checkbox(" **Mostrar columnas de producción diaria**", value=False)
    
with col_button:
    # Botón de descarga de PDF
    if pdf_buffer:
        # Nombre del archivo basado en los filtros aplicados (incluyendo la corrección del año)
        mes_pdf = filtros_aplicados["Mes"].replace(" ", "_")
        ipress_pdf = filtros_aplicados["Establecimiento"].replace(" ", "_")
        anio_pdf = str(filtros_aplicados["Año"])
        filename = f"Reporte_Produccion_{ipress_pdf}_{mes_pdf}_{anio_pdf}.pdf"
        
        # El st.download_button ahora se renderiza aquí
        st.download_button(
            label=" ⬇️ Descargar PDF Completo",
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf",
            type="primary"
        )
    else:
        st.error("No se pudo generar el PDF.")

display_styled_divider()

# Se apilan en móvil
col_izq, col_der = st.columns([3, 2])

# ============================================================
#  FUNCIÓN DE FORMATO PARA PANDAS
# ============================================================
def format_numbers(val):
    try:
        if isinstance(val, (int, float, pd.Int64Dtype)) and not pd.isna(val):
            return f"{int(val):,}"
    except:
        pass
    return val

# ============================================================
#  TABLA DE PRODUCCIÓN (INYECCIÓN HTML) - CON CABECERA FIJA
# ============================================================
with col_izq:
    
    #  SUBTÍTULO CON MARGENES REDUCIDOS PARA ALINEACIÓN VERTICAL
    st.markdown('<h3 style="margin-top: 5px; margin-bottom: 5px;"> Tabla de Producción</h3>', unsafe_allow_html=True)
    
    display_att_col = "Atenciones" if "Atenciones" in resumen_top.columns else "Suma_Dias"

    # Ahora 'Profesión' es parte de base_cols
    base_cols = ["Profesional", "Profesión", "Establecimiento", "Atendidos", display_att_col]
    display_cols = [c for c in base_cols if c in resumen_top.columns]

    if show_days_table:
        # Usar la función renombrar_columnas_dias para mostrar solo números
        resumen_top_renombrado = renombrar_columnas_dias(resumen_top)
        # Obtener las columnas de días ya renombradas (solo números)
        dias_renombrados = [col.split('.')[0] for col in day_cols]
        # Filtrar solo las columnas que existen en el DataFrame renombrado
        dias_existentes = [c for c in dias_renombrados if c in resumen_top_renombrado.columns]
        display_cols += dias_existentes
        
        # Agregar la columna TOTAL al final (si existe)
        if 'TOTAL' in resumen_top_renombrado.columns:
            display_cols.append('TOTAL')
    else:
        # Si no se muestran los días, usar el resumen original sin días
        resumen_top_renombrado = resumen_top.copy()

    # Usamos resumen_top_renombrado para la visualización
    tabla_final = resumen_top_renombrado[display_cols].copy()
    
    #  Forzar MAYÚSCULAS en los nombres de columna 
    tabla_final.columns = [col.upper() for col in tabla_final.columns]
    
    display_cols = [col.upper() for col in display_cols]

    if "SUMA_DIAS" in tabla_final.columns:
        tabla_final = tabla_final.rename(columns={"SUMA_DIAS": "ATENCIONES"})
        display_att_col = "ATENCIONES" 

    tabla_final = tabla_final.dropna(how='all') 
    tabla_final.index = range(1, len(tabla_final) + 1)
    tabla_final.index.name = "ITEM" # Establecer el nombre del índice
    
    # ---  Solución Final: EXPORTAR A HTML Y INYECTAR ---

    # 1. Definir estilos CSS para la tabla HTML
    css_styles_table = """
    <style>
        /* Estilos globales para la tabla */
        .dataframe {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Roboto', sans-serif;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-top: 0px;
        }
        
        /* Contenedor del encabezado */
        .dataframe thead {
            border-bottom: 2px solid #003c8f;
        }
        
        /* Estilo para los encabezados de columna de datos (PROFESIONAL, ATENDIDOS, 1, 2, etc.) */
        .dataframe thead th {
            /* === PROPIEDADES CLAVE PARA EL ENCABEZADO FIJO === */
            position: sticky !important;
            top: 0 !important; /* Mantiene la cabecera arriba del contenedor con scroll */
            z-index: 11 !important;
            /* ================================================= */
            background-color: #003c8f !important;
            color: white !important;
            font-weight: 700 !important;
            text-align: center !important;
            padding: 10px 4px !important;
            text-transform: none !important;
            /* CORRECCIÓN FINAL: Bordes grises claros para el encabezado */
            border: 1px solid #BBBBBB;
            height: 40px; 
            vertical-align: middle;
        }
        
        /* Aplica el sticky a la primera celda del encabezado (donde Pandas pone ITEM) */
        .dataframe thead th:first-child { 
            position: sticky !important;
            top: 0 !important;
            z-index: 11 !important; 
            background-color: #003c8f !important; 
            color: white !important;
            font-weight: 700 !important;
            text-align: center !important;
            padding: 10px 4px !important;
            /* CORRECCIÓN FINAL: Bordes grises claros para el encabezado */
            border: 1px solid #BBBBBB;
            height: 40px;
            vertical-align: middle;
        }
        
        /* Estilo especial para la columna TOTAL en el encabezado */
        .dataframe thead th:last-child {
            background-color: #ffc107 !important; /* Amarillo más fuerte para el header */
            color: #856404 !important;
            font-weight: bold !important;
        }
        
        /* Oculta la fila vacía que a veces genera Pandas en la cabecera */
        .dataframe thead tr:nth-child(2) {
            display: none;
            height: 0 !important;
            line-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Cuerpo de la tabla */
        .dataframe tbody tr:nth-child(even) {
            background-color: #eef6ff;
            /* Rayado */
        }
        .dataframe tbody tr:hover {
            background-color: #e6f0ff !important;
            color: #003c8f;
            cursor: pointer;
        }
        
        .dataframe td {
            padding: 8px;
            text-align: center;
            font-size: 14px;
            /* Añadir bordes internos (gris suave del cuerpo) */
            border: 1px solid #e0e0e0;
            vertical-align: middle;
        }
        
        /* Alineación de los valores de ITEM (Index data, que tienen la clase row_heading) */
        .dataframe th.row_heading { 
             text-align: center;
             background-color: #f0f0f0; 
             color: #333;
             font-weight: 600;
             border: 1px solid #e0e0e0;
             vertical-align: middle;
        }
        
        /* Estilo para la columna PROFESIONAL (2da celda de la fila) */
        .dataframe td:nth-child(2) { 
            color: #003c8f;
            font-weight: bold; 
            text-align: left;
        }
        
        /* FIJAR COLUMNAS DE TOTALES EN VERDE */
        .dataframe tbody tr td:nth-child(5), /* ATENDIDOS */
        .dataframe tbody tr td:nth-child(6) { /* ATENCIONES */
            background-color: #d4edda;
            font-weight: bold;
            color: #155724;
        }
        
        /* Estilo especial para la columna TOTAL */
        .dataframe tbody tr td:last-child {
            background-color: #fff3cd !important; /* Amarillo claro */
            font-weight: bold !important;
            color: #856404 !important; /* Marrón oscuro */
            font-size: 14px !important;
        }
        
        /* CORRECCIÓN: Asegura la opacidad y el orden de apilamiento para toda la fila.
        */
        .dataframe thead tr {
            background-color: #003c8f !important;
            z-index: 10 !important;
        }
    </style>
    """
    
    # 2. Aplicar formato y generar el HTML
    html_table = (
        tabla_final.style
        .format(format_numbers)
        .set_table_attributes('class="dataframe"')
        .to_html(escape=False, index=True, header=True, index_names=False) 
    )

    # 3. Combinar el CSS con la tabla HTML
    full_html = css_styles_table + html_table

    # 4. USAR max-height para forzar el scroll en el div contenedor
    scrollable_html = f"""
    <div style="max-height: 550px; overflow-y: scroll; border: 1px solid #e0e0e0; border-radius: 8px; padding-top: 0px;">
        {full_html}
    </div>
    """
    
    components.html(
        scrollable_html,
        height=570, # El height del iframe debe ser ligeramente mayor al max-height del div
        scrolling=False 
    )
    
    st.caption("")

# ============================================================
#  GRÁFICO (CON LÍNEA CONECTANDO BARRAS)
# ============================================================
with col_der:
    
    #  SUBTÍTULO CON MARGENES REDUCIDOS PARA ALINEACIÓN VERTICAL
    st.markdown('<h3 style="margin-top: 5px; margin-bottom: 5px;"> Producción de Atenciones</h3>', unsafe_allow_html=True)

    # Usamos la columna en minúsculas/título para el gráfico, ya que Altair lo maneja mejor
    att_column_name_chart = "Atenciones" if "Atenciones" in resumen_top.columns else "Suma_Dias"

    if att_column_name_chart in resumen_top.columns:
        
        bars = (
            alt.Chart(resumen_top)
            .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
            .encode(
                x=alt.X(f"{att_column_name_chart}:Q", title="Total de Atenciones"),
                y=alt.Y("Profesional:N", sort="-x", title=""), # Reducir título en móvil
                color=alt.Color("Establecimiento:N", legend=alt.Legend(title="Establecimiento")),
                tooltip=["Establecimiento", "Profesión", "Profesional", "Atendidos", alt.Tooltip(att_column_name_chart, title="Atenciones", format=',.0f')]
            )
        )
        
        trend_line = (
            alt.Chart(resumen_top)
            .mark_line(color='#E83E8C', strokeWidth=4)
            .encode(
                x=alt.X(f"{att_column_name_chart}:Q"),
                y=alt.Y("Profesional:N", sort="-x"),
                order=alt.Order(f"{att_column_name_chart}", sort="descending"), 
                tooltip=["Establecimiento", "Profesión", "Profesional", alt.Tooltip(att_column_name_chart, title="Atenciones", format=',.0f')]
            )
        )

        points = (
            alt.Chart(resumen_top)
            .mark_point(filled=True, size=150, color='#C03070', stroke='white', strokeWidth=2)
            .encode(
                x=alt.X(f"{att_column_name_chart}:Q"),
                y=alt.Y("Profesional:N", sort="-x"),
                order=alt.Order(f"{att_column_name_chart}", sort="descending"),
                tooltip=["Establecimiento", "Profesión", "Profesional", alt.Tooltip(att_column_name_chart, title="Atenciones", format=',.0f')]
            )
        )
        
        #  ALTURA AJUSTADA PARA ALINEACIÓN VERTICAL
        final_chart = (bars + trend_line + points).properties(height=560) 
        
        st.altair_chart(final_chart, use_container_width=True)
    else:
        st.info("No se encontró la columna 'Atenciones' para generar el gráfico principal.")

# ============================================================
#  GRÁFICO DE TENDENCIA DIARIA
# ============================================================

st.markdown("---") 
st.header("Tendencia Diaria de Producción General")

@st.cache_data
def get_daily_trend_data(df, day_cols):
    """
    Transforma el DataFrame filtrado para obtener una suma de atenciones por día.
    """
    if not day_cols:
        return pd.DataFrame()

    id_vars = [c for c in ["anio", "mes_nombre", "nombre_establecimiento", "profesional", "nombres_profesional"] if c in df.columns]
    
    df_melted = df.melt(
        id_vars=id_vars,
        value_vars=day_cols,
        var_name="Día",
        value_name="Atenciones_Diarias"
    )
    
    # Extraer solo el número del día (antes del punto)
    df_melted["Día"] = pd.to_numeric(df_melted["Día"].str.split('.').str[0], errors='coerce').dropna().astype(int)
    
    df_daily_trend = df_melted.groupby("Día", as_index=False)["Atenciones_Diarias"].sum()
    
    df_daily_trend = df_daily_trend.dropna(subset=["Atenciones_Diarias"])
    df_daily_trend = df_daily_trend.sort_values(by="Día")
    
    return df_daily_trend

df_tendencia = get_daily_trend_data(df_filtrado, day_cols)

if not df_tendencia.empty:
    
    COLOR_AMARILLO_FUERTE = '#FFD700'
    COLOR_TEXTO_OSCURO = '#555555' 

    chart_tendencia = (
        alt.Chart(df_tendencia)
        .mark_line(point=True, color=COLOR_AMARILLO_FUERTE, strokeWidth=4)
        .encode(
            x=alt.X("Día:O", title="Días del Mes", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Atenciones_Diarias:Q", title="Total de Atenciones"),
            tooltip=[
                alt.Tooltip("Día", title="Días del Mes"),
                alt.Tooltip("Atenciones_Diarias", title="Atenciones", format=',.0f')
            ]
        ).properties(
            title=""
        ).interactive()
    )
    
    text = chart_tendencia.mark_text(
        align='center',
        baseline='bottom',
        dy=-8 
    ).encode(
        text=alt.Text("Atenciones_Diarias:Q", format=',.0f'),
        color=alt.value(COLOR_TEXTO_OSCURO) 
    )

    st.altair_chart(chart_tendencia + text, use_container_width=True)
    
    st.caption("Gráfico de barras de Atenciones Diarias")
    chart_barras = (
        alt.Chart(df_tendencia)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color=COLOR_AMARILLO_FUERTE)
        .encode(
            x=alt.X("Día:O", title="Días del Mes", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Atenciones_Diarias:Q", title="Total de Atenciones"),
            tooltip=[
                alt.Tooltip("Día", title="Días del Mes"),
                alt.Tooltip("Atenciones_Diarias", title="Atenciones", format=',.0f')
            ]
        ).properties(height=200)
    )
    st.altair_chart(chart_barras, use_container_width=True)

else:
    st.info("No hay suficientes datos de producción diaria (columnas '1.1' a '31.1') para generar el gráfico de tendencia.")
    
# ============================================================
#  MÉTRICAS FINALES
# ============================================================
st.markdown("---")

total_atendidos = resumen["Atendidos"].sum() if "Atendidos" in resumen.columns else 0
sort_col_name = "Atenciones" if "Atenciones" in resumen.columns else "Suma_Dias"
total_atenciones = resumen[sort_col_name].sum() if sort_col_name in resumen.columns else 0

# Calcular total de la columna TOTAL si existe
if 'TOTAL' in resumen.columns:
    total_diario = resumen['TOTAL'].sum()
else:
    total_diario = 0


# Se apilan en móvil
m1, m2, m3 = st.columns(3)
m1.metric(" Total Atendidos", f"{total_atendidos:,.0f}") 
m2.metric(" Total Atenciones Registradas", f"{total_atenciones:,.0f}")
if show_days_table:
    m3.metric(" Total Producción Diaria", f"{total_diario:,.0f}")

# ============================================================
#  FOOTER / COPYRIGHT
# ============================================================
st.markdown("""
<div style="
    text-align: center; 
    margin-top: 50px; 
    padding: 10px 0;
    font-size: 14px;
    color: #6c757d;
    /* Gris sutil */
    border-top: 1px solid #e0e0e0;
    ">
    © 2025 Red San Pablo | Elaborado por: Área de Informática y Estadística.
</div>
""", unsafe_allow_html=True)

