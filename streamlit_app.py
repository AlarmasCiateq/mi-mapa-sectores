import os
import streamlit as st
import folium
import json
import requests
from datetime import date, timedelta
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from shapely.geometry import shape
import pandas as pd
import sqlite3
import altair as alt
from datetime import datetime


MAX_PRESION = 3.0
GOOGLE_DRIVE_JSON_URL = "https://drive.google.com/uc?export=download&id=1lhOfMwDaJYsOHGZhoS3kNTNQ8WCZcfPW"

# --- CONFIGURACIÓN ÚNICA (DEBE SER LA PRIMERA) ---
st.set_page_config(
    page_title="Sectores Hidráulicos CIATEQ",
    page_icon="💧",
    layout="centered"
)

# --- MARCA DE AGUA ---
st.markdown(
    """
    <div style="
        position: fixed;
        top: 10px;
        right: 18px;
        z-index: 999999999;
        color: white;
        font-size: 1.3em;
        background-color: #111;
        padding: 5px 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    ">
        💧 CIATEQ® 💦 2025 © 
    </div>
    """,
    unsafe_allow_html=True
)

# --- BOTÓN DE NAVEGACIÓN CONTEXTUAL (3 VISTAS) ---
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "interactivo"  # Tiempo real por defecto

# Mostrar SOLO el botón correspondiente a la vista actual
# Mostrar SOLO los botones correspondientes a la vista actual (en un solo renglón)
if st.session_state.vista_actual == "interactivo":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬 Ir a evolución histórica", key="btn_historico"):
            st.session_state.vista_actual = "historico"
            st.rerun()
    with col2:
        if st.button("📊 Ir a análisis de datos", key="btn_analisis"):
            st.session_state.vista_actual = "analisis"
            st.rerun()
        
elif st.session_state.vista_actual == "historico":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱ Ir al mapa en tiempo real", key="btn_interactivo"):
            st.session_state.vista_actual = "interactivo"
            st.rerun()
    with col2:
        if st.button("📊 Ir a análisis de datos", key="btn_analisis_h"):
            st.session_state.vista_actual = "analisis"
            st.rerun()
        
else:  # vista_actual == "analisis"
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱ Ir al mapa en tiempo real", key="btn_interactivo_a"):
            st.session_state.vista_actual = "interactivo"
            st.rerun()
    with col2:
        if st.button("🎬 Ir a evolución histórica", key="btn_historico_a"):
            st.session_state.vista_actual = "historico"
            st.rerun()

st.divider()

# ==============================
# VISTA 1: MAPA EN TIEMPO REAL
# ==============================
if st.session_state.vista_actual == "interactivo":
    st.subheader("💧 Presión en Sectores Hidráulicos en Tiempo Real")
    
    # Autorefresh cada 60 segundos
    st_autorefresh(interval=60000, key="data_reloader")

    def interpolar_color(valor):
        pct = max(0.0, min(valor / MAX_PRESION, 1.0))
        r = int(255 * pct)
        g = int(255 * (1 - pct))
        return f"#{r:02x}{g:02x}00"

    def cargar_estado_desde_drive():
        try:
            response = requests.get(GOOGLE_DRIVE_JSON_URL, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.warning(f"No se pudo cargar datos: {e}")
            return {}

    # Cargar GeoJSON
    geojson_path = "data/geojson/sector_hidraulico.geojson"
    if not os.path.exists(geojson_path):
        st.error(f"❌ GeoJSON no encontrado: {geojson_path}")
        st.stop()

    if "geojson_data" not in st.session_state:
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                st.session_state.geojson_data = json.load(f)
        except Exception as e:
            st.error(f"❌ Error al leer GeoJSON: {e}")
            st.stop()

    # Cargar estado
    estado_presion_raw = cargar_estado_desde_drive()

    # Crear mapa
    centro = [24.117124, -110.358397]
    m = folium.Map(location=centro, zoom_start=12)
    m.add_child(Fullscreen(position='topleft'))

    for feature in st.session_state.geojson_data["features"]:
        nombre = feature["properties"].get("name", "Sin nombre")
        sector_data = estado_presion_raw.get(nombre, {})
        valor_entrada = sector_data.get("valor", 0.0)
        fill_color = interpolar_color(valor_entrada)
        fill_opacity = 0.2 + 0.5 * (valor_entrada / MAX_PRESION)
        timestamp = sector_data.get("timestamp", "N/A")
        rssi = sector_data.get("rssi", "N/A")

        # Centroide
        geom = shape(feature["geometry"])
        centro_poligono = geom.centroid

        # Etiqueta de presión
        folium.Marker(
            location=[centro_poligono.y, centro_poligono.x],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:black;text-align:center">{valor_entrada:.2f}kg/cm²</div>'
            )
        ).add_to(m)

        # Tooltip
        tooltip_html = f"""
        <b>{nombre}</b>
        <table style="font-size: 11px; font-family: Arial, sans-serif;">
        <tr><td>Presión: </td><td>{valor_entrada:.2f}kg/cm²</td></tr>
        <tr><td>Hora: </td><td>{timestamp}</td></tr>
        <tr><td>RSSI: </td><td>{rssi}</td></tr>
        </table>
        """
        folium.GeoJson(
            feature,
            style_function=lambda x, fc=fill_color, fo=fill_opacity: {
                "fillColor": fc,
                "color": "#000",
                "weight": 1.5,
                "fillOpacity": fo
            },
            tooltip=folium.Tooltip(tooltip_html, sticky=True)
        ).add_to(m)

    # Mostrar mapa con altura fija
    st_folium(m, width="100%", height=550)

    # Leyenda
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Color:** 0 ➡ 🟢 -- {MAX_PRESION} ➡ 🔴")
    with col2:
        st.markdown("**Opacidad:** 20% (baja) - 70% (alta)")

# ==============================
# VISTA 2: EVOLUCIÓN HISTÓRICA
# ==============================
elif st.session_state.vista_actual == "historico":
    st.subheader("💧 Evolución de Presión en Sectores Hidráulicos")

    GITHUB_USER = "alarmasciateq"
    REPO_NAME = "mi-mapa-sectores"

    @st.cache_data(ttl=3600)
    def obtener_fechas_disponibles():
        fechas = []
        hoy = date.today()
        for i in range(60):
            fecha = hoy - timedelta(days=i)
            url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{fecha}.mp4"
            try:
                respuesta = requests.head(url, timeout=3)
                if respuesta.status_code == 200:
                    fechas.append(fecha)
            except:
                continue
        return sorted(fechas, reverse=True)

    fechas_disponibles = obtener_fechas_disponibles()
    if not fechas_disponibles:
        st.warning("⚠️ No hay videos disponibles.")
        st.stop()

    def fecha_a_texto(fecha):
        dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        return f"{dias[fecha.weekday()]} {fecha.day} {meses[fecha.month-1]} {fecha.year}"

    opciones = {fecha_a_texto(f): f for f in fechas_disponibles}
    seleccion = st.selectbox(
        "Selecciona un día:",
        options=list(opciones.keys()),
        index=0,
        label_visibility="collapsed"
    )
    fecha_sel = opciones[seleccion]
    video_url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{fecha_sel}.mp4"

    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; width: 100%; margin-top: 20px;">
            <video src="{video_url}" controls 
                   style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;">
            </video>
        </div>
        <p style="text-align: center; color: #666; font-size: 0.9em; margin-top: 10px;">
            📥 Si no ves el video, <a href="{video_url}" target="_blank">haz clic aquí para bajarlo🔗</a>.
        </p>
        """,
        unsafe_allow_html=True
    )

# ==============================
# VISTA 3: ANÁLISIS DE DATOS
# ==============================
else:  # vista_actual == "analisis"
    st.set_page_config(
        page_title="Análisis Histórico de Presión",
        page_icon="📊",
        layout="centered"
    )
    
    # Descargar base de datos desde Google Drive
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def descargar_db():
        DB_URL = "https://drive.google.com/uc?export=download&id=13B8eDzBJo2yfDw2MpulcTS7F-zb6NwQy"
        response = requests.get(DB_URL)
        with open("temp_db.db", "wb") as f:
            f.write(response.content)
        return "temp_db.db"
    
    def obtener_fechas_disponibles():
        """Obtiene todas las fechas únicas que existen en la base de datos"""
        db_path = descargar_db()
        with sqlite3.connect(db_path) as conn:
            query = """
            SELECT DISTINCT 
                SUBSTR(timestamp, 7, 4) || '-' || SUBSTR(timestamp, 4, 2) || '-' || SUBSTR(timestamp, 1, 2) as fecha_ansi
            FROM lecturas
            ORDER BY fecha_ansi DESC
            """
            df_fechas = pd.read_sql_query(query, conn)
            fechas = pd.to_datetime(df_fechas['fecha_ansi']).dt.date.tolist()
            return fechas
    
    def cargar_datos(fecha_inicio, fecha_fin, dispositivos):
        """Carga datos de la base de datos filtrados por fecha y dispositivos"""
        db_path = descargar_db()
        with sqlite3.connect(db_path) as conn:
            query = """
            SELECT dispositivo, valor, timestamp
            FROM lecturas 
            WHERE SUBSTR(timestamp, 7, 4) || '-' || SUBSTR(timestamp, 4, 2) || '-' || SUBSTR(timestamp, 1, 2) 
                  BETWEEN ? AND ?
            """
            params = [fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')]
            
            if dispositivos:
                placeholders = ','.join(['?' for _ in dispositivos])
                query += f" AND dispositivo IN ({placeholders})"
                params.extend(dispositivos)
                
            query += " ORDER BY timestamp"
            df = pd.read_sql_query(query, conn, params=params)
            return df
    # Obtener fechas disponibles y dispositivos
    try:
        fechas_disponibles = obtener_fechas_disponibles()
        db_path = descargar_db()
        with sqlite3.connect(db_path) as conn:
            dispositivos = pd.read_sql_query("SELECT DISTINCT dispositivo FROM lecturas", conn)['dispositivo'].tolist()
    except Exception as e:
        st.error(f"❌ Error al cargar datos iniciales: {e}")
        st.stop()
    
    if not fechas_disponibles:
        st.warning("⚠️ No hay datos disponibles en la base de datos.")
        st.stop()
    
    # Interfaz de usuario - Selectores de fecha con fechas disponibles
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_min = max(fechas_disponibles[-1], datetime.now().date() - timedelta(days=30))
        fecha_max = fechas_disponibles[0]
        
        fecha_inicio = st.date_input(
            "Fecha de inicio",
            value=fecha_max,
            min_value=fecha_min,
            max_value=fecha_max
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de fin",
            value=fecha_max,
            min_value=fecha_inicio,
            max_value=fecha_max
        )
    
    # Validar fechas
    if fecha_inicio not in fechas_disponibles:
        fechas_validas_inicio = [f for f in fechas_disponibles if f >= fecha_inicio]
        fecha_inicio = fechas_validas_inicio[0] if fechas_validas_inicio else fechas_disponibles[0]
    
    if fecha_fin not in fechas_disponibles:
        fechas_validas_fin = [f for f in fechas_disponibles if f <= fecha_fin]
        fecha_fin = fechas_validas_fin[-1] if fechas_validas_fin else fechas_disponibles[-1]
    
    # Selector de dispositivos
    dispositivos_seleccionados = st.multiselect(
        "Seleccionar sectores", 
        dispositivos, 
        default=dispositivos[:3] if len(dispositivos) >= 3 else dispositivos
    )

    if st.button("🔄 Recargar"):
        df = cargar_datos(fecha_inicio, fecha_fin, dispositivos_seleccionados)
        
        if df.empty:
            st.warning("No hay datos para el rango seleccionado.")
        else:
            # Convertir timestamp a datetime para Altair
            df['fecha_datetime'] = pd.to_datetime(df['timestamp'], format='%d-%m-%Y %H:%M')
            
            # Gráfica de líneas con puntos usando Altair
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X('fecha_datetime:T', title='Fecha y hora'),
                y=alt.Y('valor:Q', title='Presión (kg/cm²)'),
                color=alt.Color('dispositivo:N', title='Sector'),
                tooltip=['dispositivo', 'valor', 'timestamp']
            ).properties(
                title="Evolución de la presión en el tiempo",
                width='container',
                height=400
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
            # Tabla de datos SIN índice
            st.subheader("Datos detallados")
            st.dataframe(
                df[['dispositivo', 'valor', 'timestamp']].sort_values('timestamp', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            # Estadísticas
            st.subheader("Estadísticas por sector")
            stats = df.groupby('dispositivo')['valor'].agg(['min.', 'max.', 'mean', 'std']).round(2)
            stats.rename(columns={'Desv_Est': 'Desv. Est.'}, inplace=True)
            st.dataframe(stats, use_container_width=True)












