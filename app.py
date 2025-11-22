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
    
    # ⚠️ Nota: Asegúrese de que 'logo_sanpablo.png' esté en la misma carpeta que su script.
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
    logo_src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUAAABgCAYAAADg1PWnAAAAAXNSR0IArs4c6QAAAXRJREFUeJzt3LFOwzAUBeFvE4kFioK3oV24cAE8A4P0JcQf4AQ8AW8gY2CgICAgICAgICAgICAg+K1c/70lSZIe3D5/l9f/FwAAAACA1V9n39X607Pfb9/Nn5e3b97b1+f7fUe630z9A4H5f+gDAvP/UC+Yn7c/k5e3v0D2H0j9A4H5f6iFm3y7O/t7/R/c4D/vF/v7jVdD/g/1vF/i9p8H4v+hF25x9+Xl7b+w0lP89o3v9/uOdv9z9e4/vF/s73cO/w+7cIu7vy/n1/f3n6Tif/D5eXn/m/9n7d1/tC4tF078Hl8vL+/8XzG4y92Xl7f/gZ/t2r93/jV19uL29vs3n/f7jnb9L4/G/2f9H7duf7w/f79/b9/e77P9G/f2f9+8BBAAAAICrF16Y66yTfG/vAAAAAElFTkSuQmCC" 

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
    # ⚠️ Nota: Reemplace "CONSOLIDADO.xlsx" con la ruta correcta a su archivo.
    try:
        df = pd.read_excel(path, engine="openpyxl")
        df.columns = df.columns.map(lambda c: str(c).strip())
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        return df
    except FileNotFoundError:
        st.warning(f"⚠️ **Advertencia:** Archivo de datos no encontrado. Usando datos de ejemplo (120 filas).")
        # Datos de ejemplo base
        data = {
            "anio": [2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024],
            "mes": [10, 10, 10, 10, 10, 10, 10, 10, 11, 11],
            "nombre_establecimiento": ["IPRESS A", "IPRESS B", "IPRESS A", "IPRESS C", "IPRESS B", "IPRESS A", "IPRESS B", "IPRESS C", "IPRESS A", "IPRESS B"],
            "profesional": ["Cardiología", "Medicina General", "Cardiología", "Ginecología", "Pediatría", "Medicina Interna", "Oftalmología", "Cirugía", "Cardiología", "Medicina General"],
            "nombres_profesional": ["Dr. Perez", "Lic. García", "Dr. Perez", "Dra. Lopez", "Dr. Soto", "Dra. Rojas", "Lic. Vidal", "Dr. Castro", "Dr. Perez", "Lic. García"],
            "Total Atenciones": [150, 220, 180, 90, 300, 110, 250, 140, 160, 230],
            "atendidos_servicios_total": [120, 180, 140, 70, 250, 90, 200, 100, 130, 190],
        }
        
        # Inicializar columnas de días (1 a 31)
        for i in range(1, 32):
             data[str(i)] = [max(1, (10 + j * 2) - abs(i - 15)) for j in range(10)] # Valores base ficticios
             
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
            data["Total Atenciones"].append(100 + idx * 5)
            data["atendidos_servicios_total"].append(90 + idx * 4)
            
            for j in range(1, 32):
                data[str(j)].append(max(0, 5 + (idx % 10) + (j % 5)))

        # Se usa dict comprehension para combinar listas.
        combined_data = {key: data[key] for key in data}
        
        return pd.DataFrame(combined_data)

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
# 🎨 ESTILOS CSS PROFESIONALES (GLOBALes, no de la tabla)
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
    /* Altura por defecto en Desktop */
    padding: 10px 40px; 
    align-items: center;
}

/* 🎯 Ajuste del margen para el primer contenido (Desktop) */
[data-testid="stVerticalBlock"]:nth-child(2) { 
    margin-top: 120px !important; /* Margen positivo para empezar debajo del header */
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
    background-color: #0056d6 !important; /* Azul más claro del encabezado */
    color: white !important;             /* Texto blanco para contraste */
}

/* 4. Aplicar AZUL OSCURO del encabezado al ITEM SELECCIONADO (permanente) */
[data-testid="stOptionSelectable"] {
    background-color: #003c8f !important; /* Azul oscuro principal del encabezado */
    color: white !important;
    font-weight: bold;
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
# ⏰ FECHA DE ACTUALIZACIÓN DEL ARCHIVO Y FUENTE
# ============================================================
fecha_actualizacion = obtener_fecha_modificacion()

# 👉 Contenedor de Fecha y Fuente
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
        # El título del filtro ahora es "Profesión/Especialidad"
        filtro_especialidad = st.selectbox("⚕️ **Profesión/Especialidad**", especialidades) 

    with filtro_col5:
        profesionales = ["Todos"] + sorted(df["nombres_profesional"].dropna().unique().tolist()) if "nombres_profesional" in df.columns else ["Todos"]
        filtro_profesional = st.selectbox("👩‍⚕️ **Profesional**", profesionales)

# ============================================================
# 🔢 PARÁMETROS 
# ============================================================
st.markdown("---") 

# Se apilan en móvil
col_params_izq, col_params_der = st.columns([1, 1])

with col_params_izq:
    # Ajuste de slider si tienes muchos profesionales (máx 100)
    max_prof_count = len(df["nombres_profesional"].dropna().unique()) if "nombres_profesional" in df.columns else 100 
    top_n_default = min(20, max_prof_count)
    top_n = st.slider("🔝 **Ranking de Atenciones por Profesional**", 5, max(50, max_prof_count), top_n_default)
    
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

# 🔥 Ajuste: asegurar suma correcta de Total Atenciones por profesional
if "Total Atenciones" in df_filtrado.columns and group_cols:
    # Calcula la suma real por grupo
    suma_att = df_filtrado.groupby(group_cols, as_index=False)["Total Atenciones"].sum().rename(columns={"Total Atenciones":"Total Atenciones_sum"})
    # Merge para asegurar que el resumen tenga la suma por grupo (evita problemas de filas múltiples)
    resumen = resumen.merge(suma_att, on=group_cols, how="left")
    resumen["Total Atenciones"] = resumen["Total Atenciones_sum"]
    resumen = resumen.drop(columns=["Total Atenciones_sum"])

# 🛑 Aplicación del cambio: "profesional" ahora se etiqueta como "Profesión"
rename_map = {
    "nombre_establecimiento": "Establecimiento",
    "profesional": "Profesión",     
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

# Aquí limitamos el ranking al Top N, aunque el resumen completo tiene >100
resumen_top = resumen.head(top_n).copy() 

# ============================================================
# 📋 TABLA + 📈 GRÁFICO PRINCIPAL
# ============================================================
st.header("Resultados por Profesional y Establecimiento")

show_days_table = st.checkbox("📅 **Mostrar columnas de producción diaria**", value=False)

display_styled_divider()

# Se apilan en móvil
col_izq, col_der = st.columns([3, 2])

# ============================================================
# 🎨 FUNCIÓN DE FORMATO PARA PANDAS
# ============================================================
def format_numbers(val):
    try:
        if isinstance(val, (int, float, pd.Int64Dtype)) and not pd.isna(val):
            return f"{int(val):,}"
    except:
        pass
    return val

# ============================================================
# 📋 TABLA DE PRODUCCIÓN (INYECCIÓN HTML) - CON CABECERA FIJA
# ============================================================
with col_izq:
    
    # 🎯 SUBTÍTULO CON MARGENES REDUCIDOS PARA ALINEACIÓN VERTICAL
    st.markdown('<h3 style="margin-top: 5px; margin-bottom: 5px;">📋 Tabla de Producción</h3>', unsafe_allow_html=True)
    
    display_att_col = "Atenciones" if "Atenciones" in resumen_top.columns else "Suma_Dias"

    # Ahora 'Profesión' es parte de base_cols
    base_cols = ["Profesional", "Profesión", "Establecimiento", "Atendidos", display_att_col]
    display_cols = [c for c in base_cols if c in resumen_top.columns]

    if show_days_table:
        display_cols += [c for c in day_cols if c in resumen_top.columns]

    # Usamos resumen_top (Top N) para la visualización, ya que el slider lo controla
    tabla_final = resumen_top[display_cols].copy()
    
    # 🌟 Forzar MAYÚSCULAS en los nombres de columna 
    tabla_final.columns = [col.upper() for col in tabla_final.columns]
    
    display_cols = [col.upper() for col in display_cols]

    if "SUMA_DIAS" in tabla_final.columns:
        tabla_final = tabla_final.rename(columns={"SUMA_DIAS": "ATENCIONES"})
        display_att_col = "ATENCIONES" 

    tabla_final = tabla_final.dropna(how='all') 
    tabla_final.index = range(1, len(tabla_final) + 1)
    tabla_final.index.name = "ITEM" # Establecer el nombre del índice
    
    # --- 🛑 Solución Final: EXPORTAR A HTML Y INYECTAR ---

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
            /* ✅ CORRECCIÓN FINAL: Bordes grises claros para el encabezado */
            border: 1px solid #BBBBBB; 
            height: 40px; 
            vertical-align: middle;
        }
        
        /* 💡 Aplica el sticky a la primera celda del encabezado (donde Pandas pone ITEM) */
        .dataframe thead th:first-child { 
            position: sticky !important; 
            top: 0 !important;
            z-index: 11 !important; 
            background-color: #003c8f !important; 
            color: white !important;
            font-weight: 700 !important;
            text-align: center !important;
            padding: 10px 4px !important;
            /* ✅ CORRECCIÓN FINAL: Bordes grises claros para el encabezado */
            border: 1px solid #BBBBBB;
            height: 40px;
            vertical-align: middle;
        }
        
        /* 🛑 Oculta la fila vacía que a veces genera Pandas en la cabecera */
        .dataframe thead tr:nth-child(2) {
            display: none; 
            height: 0 !important;
            line-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Cuerpo de la tabla */
        .dataframe tbody tr:nth-child(even) {
            background-color: #eef6ff; /* Rayado */
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
        
        /* 🛑 FIJAR COLUMNAS DE TOTALES EN VERDE */
        .dataframe tbody tr td:nth-child(5), /* ATENDIDOS */
        .dataframe tbody tr td:nth-child(6) { /* ATENCIONES */
            background-color: #d4edda;
            font-weight: bold;
            color: #155724;
        }
        
        /* 🛑 CORRECCIÓN: Asegura la opacidad y el orden de apilamiento para toda la fila. */
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
# 📈 GRÁFICO (CON LÍNEA CONECTANDO BARRAS)
# ============================================================
with col_der:
    
    # 🎯 SUBTÍTULO CON MARGENES REDUCIDOS PARA ALINEACIÓN VERTICAL
    st.markdown('<h3 style="margin-top: 5px; margin-bottom: 5px;">📈 Producción de Atenciones</h3>', unsafe_allow_html=True)

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
        
        # 🎯 ALTURA AJUSTADA PARA ALINEACIÓN VERTICAL
        final_chart = (bars + trend_line + points).properties(height=560) 
        
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


# Se apilan en móvil
m1, m2 = st.columns(2)
m1.metric("👥 Total Atendidos", f"{total_atendidos:,.0f}") 
m2.metric("🏥 Total Atenciones Registradas", f"{total_atenciones:,.0f}")

# ============================================================
# ℹ️ FOOTER / COPYRIGHT
# ============================================================
st.markdown("""
<div style="
    text-align: center; 
    margin-top: 50px; 
    padding: 10px 0;
    font-size: 14px;
    color: #6c757d; /* Gris sutil */
    border-top: 1px solid #e0e0e0;
">
    © 2025 Red San Pablo | Elaborado por: Área de Informática y Estadística.
</div>
""", unsafe_allow_html=True)














