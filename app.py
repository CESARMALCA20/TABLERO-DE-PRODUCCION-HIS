import streamlit as st
import pandas as pd
import altair as alt
import re
import base64
from pathlib import Path
from datetime import datetime
import os 

# ============================================================
# 🔧 CONFIGURACIÓN GENERAL Y CARGA DE LOGO
# ============================================================

def load_logo_base64(file_path):
    """Convierte el archivo de imagen a string Base64."""
    try:
        base_path = Path(__file__).parent
    except NameError:
        base_path = Path.cwd()
    
    logo_path = base_path / file_path
    
    try:
        with open(logo_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None
    except Exception as e:
        return None

# Asegúrate de tener el archivo "logo_sanpablo.png" en la misma carpeta que tu script
logo_b64 = load_logo_base64("logo_sanpablo.png") 

if logo_b64:
    logo_src = f"data:image/png;base64,{logo_b64}"
else:
    logo_src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADg1PWnAAAAAXNSR0IArs4c6QAAAXRJREFUeJzt3LFOwzAUBeFvE4kFioK3oV24cAE8A4P0JcQf4AQ8AW8gY2CgICAgICAgICAgICAg+K1c/70lSZIe3D5/l98/FwAAAACA1V9n39X607Pfb9/Nn5e3b97b1+f7fUe630z9A4H5f+gDAvP/UC+Yn7c/k5e3v0D2H0j9A4H5f6iFm3y7O/t7/R/c4D/vF/v7jVdD/g/1vF/i9p8H4v+hF25x9+Xl7b+w0lP89o3v9/uOdv8z9e4/vF/s73cO/w+7cIu7vy/n1/f3n6Tif/D5eXn/m/9n7d1/tC4tF078Hl8vL+/8XzG4y92Xl7f/gZ/t2r93/jV19uL29vs3n/f7jnb9L4/G/2f9H7duf7w/f79/b9/e77P9G/f2f9+8BBAAAAICrF16Y66yTfG/vAAAAAElFTkSuQmCC" 

# Configuración de la página
st.set_page_config(
    page_title="Tablero HIS - Red San Pablo", 
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
        dt_object = datetime.fromtimestamp(timestamp)
        
        dia = dt_object.day
        mes_num = dt_object.month
        anio = dt_object.year
        tiempo = dt_object.strftime("%H:%M") 
        
        mes_nombre = meses_espanol.get(mes_num, "Mes Desconocido")
        
        return f"{dia} de {mes_nombre} de {anio} - {tiempo} Hrs."
        
    except FileNotFoundError:
        now = datetime.now()
        mes_nombre = meses_espanol.get(now.month, "Mes Desconocido")
        return f"{now.day} de {mes_nombre} de {now.year} - {now.strftime('%H:%M')} Hrs. (Archivo no encontrado)"


@st.cache_data
def cargar_datos(path="CONSOLIDADO.xlsx"):
    """Carga los datos del archivo Excel o usa datos de ejemplo."""
    try:
        df = pd.read_excel(path, engine="openpyxl")
        df.columns = df.columns.map(lambda c: str(c).strip())
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        return df
    except FileNotFoundError:
        st.warning(f"⚠️ **Advertencia:** Archivo de datos no encontrado. Usando datos de ejemplo.")
        # Datos de ejemplo para que la aplicación corra
        data = {
            "anio": [2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024],
            "mes": [10, 10, 10, 10, 10, 10, 10, 10, 11, 11],
            "nombre_establecimiento": ["IPRESS A", "IPRESS B", "IPRESS A", "IPRESS C", "IPRESS B", "IPRESS A", "IPRESS B", "IPRESS C", "IPRESS A", "IPRESS B"],
            "profesional": ["Cardiología", "Medicina General", "Cardiología", "Ginecología", "Pediatría", "Medicina Interna", "Oftalmología", "Cirugía", "Cardiología", "Medicina General"],
            "nombres_profesional": ["Dr. Perez", "Lic. García", "Dr. Perez", "Dra. Lopez", "Dr. Soto", "Dra. Rojas", "Lic. Vidal", "Dr. Castro", "Dr. Perez", "Lic. García"],
            "Total Atenciones": [150, 220, 180, 90, 300, 110, 250, 140, 160, 230],
            "1": [10, 20, 15, 5, 25, 8, 18, 12, 11, 21], "2": [12, 25, 18, 7, 30, 9, 20, 14, 13, 26], "3": [14, 28, 20, 8, 35, 10, 22, 16, 15, 29],
            "4": [10, 20, 15, 5, 25, 8, 18, 12, 11, 21], "5": [12, 25, 18, 7, 30, 9, 20, 14, 13, 26], "6": [14, 28, 20, 8, 35, 10, 22, 16, 15, 29]
        }
        for i in range(7, 32):
            data[str(i)] = [max(0, x - 2) for x in data.get(str(i-3), [0] * 10)] if i > 3 and str(i-3) in data else [0] * 10
        return pd.DataFrame(data)

def detectar_dias_columnas(columns):
    return sorted([str(c) for c in columns if re.fullmatch(r"0?[1-9]|[12][0-9]|3[01]", str(c))], key=lambda x: int(x))

df = cargar_datos()
day_cols = detectar_dias_columnas(df.columns)
fecha_actualizacion = obtener_fecha_modificacion()
orden_meses = list(meses_espanol.values())
if "mes" in df.columns:
    df["mes_nombre"] = df["mes"].map(meses_espanol)
    df["mes_nombre"] = pd.Categorical(df["mes_nombre"], categories=orden_meses, ordered=True)


# ============================================================
# 🎨 ESTILOS CSS PROFESIONALES (SOLUCIÓN DEFINITIVA DE FIXED)
# ============================================================
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

/* 🎯 SOLUCIÓN FINAL: Eliminamos el padding superior que Streamlit pone por defecto para la barra nativa (que está oculta) */
[data-testid="stAppViewContainer"] > div:first-child {
    padding-top: 0px !important; 
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Roboto', sans-serif !important;
    background-color: #f6f8fb;
}

/* 🛑 OCULTAR BARRA BLANCA Y MENÚS NATIVOS 🛑 */
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
}

.header-container p {
    color: white !important;
    text-shadow: 1px 1px 5px rgba(0,0,0,0.4);
}

/* 🎯 AJUSTE CRÍTICO (Para que el primer contenido visible se mueva hacia arriba) */
/* El bloque de la fuente de datos (primer contenido que escribiste) */
[data-testid="stVerticalBlock"]:nth-child(2) { 
    margin-top: 120px !important; /* Ahora el margen es POSITIVO para que baje bajo el header fijo */
    padding-top: 0px !important; 
}

/* ------------------------------------------------- */

/* Métricas */
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

/* -------------------------------------------------
    OCULTAR BOTÓN DE EXPANDER/CHECKBOX EN FILTROS
------------------------------------------------- */
[data-testid="stExpander"] button {
    display: none !important;
    visibility: hidden !important; 
    pointer-events: none !important;
}

[data-testid="stExpander"] > div:first-child {
    padding-left: 0px !important;
    padding-right: 0px !important;
}

/* -------------------------------------------------
    ESTILOS PARA TABLA st.dataframe
------------------------------------------------- */
[data-testid="stStyledDataFrame"] * {
    background-color: unset !important;
    color: unset !important;
}

[data-testid="stStyledDataFrame"] thead th {
    background-color: #003c8f !important;
    color: white !important;
    font-weight: 700 !important; 
    text-align: center !important;
}

div.stDataFrame > div > div > div:nth-child(1) > div > div > div:nth-child(2) {
    text-align: left !important;
}

/* -------------------------------------------------
    HOVER INDIVIDUAL DEL FILTRO (BLOQUE EXTERNO)
------------------------------------------------- */
[data-testid="stExpanderDetails"] > div > div > div {
    padding: 0 10px 0 10px;
    background-color: transparent !important;
    box-shadow: none !important;
    transform: none !important;
    border: none !important;
}

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

/* -------------------------------------------------
    HOVER AZUL SUAVE EN FILAS DE LA TABLA
------------------------------------------------- */
[data-testid="stStyledDataFrame"] tbody tr:hover {
    background-color: #e6f0ff !important; 
    color: #003c8f !important; 
    cursor: pointer;
}

[data-testid="stStyledDataFrame"] tbody tr:hover td {
    background-color: transparent !important; 
    color: #003c8f !important;
}

[data-testid="stStyledDataFrame"] tbody tr:hover th {
    background-color: #c0d8f7 !important; 
    color: #003c8f !important;
}

/* -------------------------------------------------
    HOVER AZUL CLARO EN LAS OPCIONES DEL DROPDOWN
------------------------------------------------- */
div[data-baseweb="popover"] ul li[role="option"]:hover {
    background-color: #e6f0ff !important; 
    color: #003c8f !important; 
}
div[data-baseweb="popover"] ul li[role="option"][aria-selected="true"] {
    background-color: #0056d6 !important; 
    color: white !important;
}
div[data-baseweb="popover"] ul {
    background-color: white !important; 
}

/* -------------------------------------------------
    ESTILO ESPECÍFICO DEL SLIDER (Fucsia Agresivo)
------------------------------------------------- */

/* Título */
div[data-testid="stSlider"] label p {
    font-size: 18px !important; 
    font-weight: 700 !important; 
    color: #333 !important;
}

/* Valor (ej: 20) */
div[data-testid="stSlider"] > div > div:nth-child(1) > div:nth-child(1) {
    color: #E83E8C !important; 
    font-size: 24px !important;
    font-weight: 700 !important;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

/* Pista (Track) - Color Fucsia */
div[data-testid="stSlider"] > div > div:nth-child(1) > div:nth-child(2) > div {
    background-color: #E83E8C !important; 
    height: 8px; 
    border-radius: 4px; 
}

/* Pulgar (Thumb) - Círculo */
div[data-testid="stSlider"] > div > div:nth-child(1) > div:nth-child(2) > div > div {
    background-color: #C03070 !important; 
    border: 3px solid white !important;
    box-shadow: 0 0 5px rgba(0,0,0,0.3);
    width: 18px; 
    height: 18px; 
}

/* Hover */
div[data-testid="stSlider"] > div > div:nth-child(1) > div:nth-child(2) > div > div:hover {
    box-shadow: 0 0 10px rgba(232, 62, 140, 0.8); 
}
/* ------------------------------------------------- */

</style>
""", unsafe_allow_html=True)


# ============================================================
# ⚙️ FUNCIÓN DE DIVISOR ESTILIZADO (Reutilizable)
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
# 🧩 ENCABEZADO (CON ESTILO FIXED IMPLÍCITO DESDE CSS)
# ============================================================
st.markdown(f"""
<div class="header-container" style="
    width:100%;
    background: linear-gradient(90deg, #003c8f 0%, #0056d6 100%);
    padding:10px 40px; 
    display:flex;
    align-items:center;
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
# ⏰ FECHA DE ACTUALIZACIÓN DEL ARCHIVO Y FUENTE
# ============================================================
fecha_actualizacion = obtener_fecha_modificacion()

# 👉 Contenedor de Fecha y Fuente
# Este bloque es el [data-testid="stVerticalBlock"]:nth-child(2)
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
            Última Actualización de Datos: 🗓️ <b>{fecha_actualizacion}</b>
        </span>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# 🔍 FILTROS (EXPANDER FIJO CON HOVER)
# ============================================================
with st.expander("⚙️ **FILTROS DE BÚSQUEDA**", expanded=True):
    filtro_col1, filtro_col2, filtro_col3, filtro_col4, filtro_col5 = st.columns(5)

    with filtro_col1:
        anios_data = sorted(df["anio"].dropna().unique().tolist()) if "anio" in df.columns else []
        anios = ["Todos"] + anios_data
        
        default_year = "Todos"
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
            "📅 **Año**", 
            anios, 
            index=default_index
        )

    with filtro_col2:
        filtro_mes = st.selectbox("🗓️ **Mes**", ["Todos"] + orden_meses)

    with filtro_col3:
        ipress = ["Todos"] + sorted(df["nombre_establecimiento"].dropna().unique().tolist()) if "nombre_establecimiento" in df.columns else ["Todos"]
        filtro_ipress = st.selectbox("🏥 **Establecimiento**", ipress)

    with filtro_col4:
        especialidades = ["Todos"] + sorted(df["profesional"].dropna().unique().tolist()) if "profesional" in df.columns else ["Todos"]
        filtro_especialidad = st.selectbox("⚕️ **Especialidad**", especialidades)

    with filtro_col5:
        profesionales = ["Todos"] + sorted(df["nombres_profesional"].dropna().unique().tolist()) if "nombres_profesional" in df.columns else ["Todos"]
        filtro_profesional = st.selectbox("👩‍⚕️ **Profesional**", profesionales)

# ============================================================
# 🔢 PARÁMETROS 
# ============================================================
st.markdown("---") 

col_params_izq, col_params_der = st.columns([1, 1])

with col_params_izq:
    top_n = st.slider("🔝 **Ranking de Atenciones por Profesional**", 5, 100, 20)
    
# ============================================================
# 🚦 APLICAR FILTROS
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
    df_filtrado = df_filtrado[df_filtrado[
        "nombres_profesional"] == filtro_profesional]

if df_filtrado.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados.")
    st.stop()

# ============================================================
# 📊 AGRUPACIÓN Y RESÚMENES
# ============================================================
att_col = "Total Atenciones" if "Total Atenciones" in df_filtrado.columns else None
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

rename_map = {
    "nombre_establecimiento": "Establecimiento",
    "profesional": "Especialidad",
    "nombres_profesional": "Profesional",
    "atendidos_servicios_total": "Atendidos",
    "Total Atenciones": "Atenciones"
}
resumen = resumen.rename(columns=rename_map)

sort_col = "Atenciones"
if "Atenciones" not in resumen.columns:
    resumen["Suma_Dias"] = resumen[[c for c in day_cols if c in resumen.columns]].sum(axis=1)
    sort_col = "Suma_Dias"

resumen = resumen.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
resumen_top = resumen.head(top_n).copy()

# ============================================================
# 📋 TABLA + 📈 GRÁFICO PRINCIPAL
# ============================================================
st.header("Resultados por Profesional y Establecimiento")

show_days_table = st.checkbox("📅 **Mostrar columnas de producción diaria**", value=False)

display_styled_divider()

col_izq, col_der = st.columns([3, 2])

# ============================================================
# 🎨 FUNCIONES DE ESTILO AVANZADAS PARA LA TABLA
# ============================================================

def highlight_totals(s):
    if s.name in ['Atendidos', 'Atenciones']:
        return ['background-color: #d4edda; font-weight: bold; color: #155724'] * len(s) 
    return [''] * len(s)

def style_profesional(s):
    return ['color: #003c8f; font-weight: bold; text-align: left'] * len(s)

def highlight_alternate_rows(row):
    is_even = (row.name % 2) == 0
    color = '#eef6ff' if is_even else 'white' 
    return [f'background-color: {color}'] * len(row)

def format_numbers(val):
    try:
        if isinstance(val, (int, float, pd.Int64Dtype)) and not pd.isna(val):
            return f"{int(val):,}"
    except:
        pass
    return val

# ============================================================
# 📋 TABLA DE PRODUCCIÓN
# ============================================================
with col_izq:
    
    st.subheader("📋 Tabla de Producción")
    
    display_att_col = "Atenciones" if "Atenciones" in resumen_top.columns else "Suma_Dias"

    base_cols = ["Profesional", "Especialidad", "Establecimiento", "Atendidos", display_att_col]
    display_cols = [c for c in base_cols if c in resumen_top.columns]

    if show_days_table:
        display_cols += [c for c in day_cols if c in resumen_top.columns]

    tabla_final = resumen_top[display_cols].copy()
    
    if "Suma_Dias" in tabla_final.columns:
        tabla_final = tabla_final.rename(columns={"Suma_Dias": "Atenciones"})
        display_cols = [c.replace("Suma_Dias", "Atenciones") for c in display_cols] 

    tabla_final = tabla_final.dropna(how='all') 

    tabla_final.index = range(1, len(tabla_final) + 1)
    tabla_final.index.name = "Item"

    styled = (
        tabla_final.style
        .apply(highlight_alternate_rows, axis=1)
        .apply(style_profesional, subset=['Profesional'], axis=0) 
        .apply(highlight_totals, axis=0) 
        .format(format_numbers)
        .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#003c8f'),
                                         ('color', 'white'),
                                         ('font-weight', 'bold'),
                                         ('text-align', 'center'),
                                         ('padding', '8px 4px')]}, 
            
            {'selector': '.row_heading', 'props': [('background-color', '#dddddd'), 
                                                   ('color', '#333'),
                                                   ('font-weight', 'bold')]} 
        ])
        .set_properties(**{
            'text-align': 'center',
            'font-size': '14px',
            'vertical-align': 'middle',
        })
    )

    st.dataframe(styled, use_container_width=True, height=520) 

# ============================================================
# 📈 GRÁFICO (CON LÍNEA CONECTANDO BARRAS)
# ============================================================
with col_der:
    st.subheader("📈 Producción de Atenciones (Top N)")

    att_column_name = "Atenciones" if "Atenciones" in resumen_top.columns else "Suma_Dias"

    if att_column_name in resumen_top.columns:
        
        bars = (
            alt.Chart(resumen_top)
            .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
            .encode(
                x=alt.X(f"{att_column_name}:Q", title="Total de Atenciones"),
                y=alt.Y("Profesional:N", sort="-x"),
                color=alt.Color("Establecimiento:N", legend=alt.Legend(title="Establecimiento")),
                tooltip=["Establecimiento", "Especialidad", "Profesional", "Atendidos", alt.Tooltip(att_column_name, title="Atenciones", format=',.0f')]
            )
        )
        
        trend_line = (
            alt.Chart(resumen_top)
            .mark_line(color='#E83E8C', strokeWidth=4)
            .encode(
                x=alt.X(f"{att_column_name}:Q"),
                y=alt.Y("Profesional:N", sort="-x"),
                order=alt.Order(f"{att_column_name}", sort="descending"), 
                tooltip=["Establecimiento", "Especialidad", "Profesional", alt.Tooltip(att_column_name, title="Atenciones", format=',.0f')]
            )
        )

        points = (
            alt.Chart(resumen_top)
            .mark_point(filled=True, size=150, color='#C03070', stroke='white', strokeWidth=2)
            .encode(
                x=alt.X(f"{att_column_name}:Q"),
                y=alt.Y("Profesional:N", sort="-x"),
                order=alt.Order(f"{att_column_name}", sort="descending"),
                tooltip=["Establecimiento", "Especialidad", "Profesional", alt.Tooltip(att_column_name, title="Atenciones", format=',.0f')]
            )
        )
        
        final_chart = (bars + trend_line + points).properties(height=520)
        
        st.altair_chart(final_chart, use_container_width=True)
    else:
        st.info("No se encontró la columna 'Atenciones' para generar el gráfico principal.")

# ============================================================
# 📈 GRÁFICO DE TENDENCIA DIARIA
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
    
    df_melted["Día"] = pd.to_numeric(df_melted["Día"], errors='coerce').dropna().astype(int)
    
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
    st.info("No hay suficientes datos de producción diaria (columnas '1' a '31') para generar el gráfico de tendencia.")
    
# ============================================================
# 🔢 MÉTRICAS FINALES
# ============================================================
st.markdown("---")

total_atendidos = resumen["Atendidos"].sum() if "Atendidos" in resumen.columns else 0
sort_col_name = "Atenciones" if "Atenciones" in resumen.columns else "Suma_Dias"
total_atenciones = resumen[sort_col_name].sum() if sort_col_name in resumen.columns else 0


m1, m2 = st.columns(2)
m1.metric("👥 Total Atendidos", f"{total_atendidos:,.0f}") 
m2.metric("🩺 Total Atenciones", f"{total_atenciones:,.0f}")

# ============================================================
# 📝 SECCIÓN DE AUTORÍA FINAL
# ============================================================
st.markdown("""
    <div style="text-align: right; margin-top: 40px; color: #555; font-size: 14px;">
        Elaborado por **César Malca Cabanillas** - Red San Pablo 2025.
    </div>
""", unsafe_allow_html=True)







