import os
import streamlit as st
import folium
import json
import requests
from datetime import date, timedelta, datetime
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from shapely.geometry import shape
import pandas as pd
import sqlite3
import altair as alt

MAX_PRESION = 3.0

# ==============================
# FUENTES DE DATOS (GITHUB)
# ==============================
GITHUB_USER = "AlarmasCiateq"
REPO_NAME = "mi-mapa-sectores"
BRANCH = "main"

ESTADO_JSON_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/data/estado_sectores.json"
)

DB_URL = "https://github.com/AlarmasCiateq/mi-mapa-sectores/releases/download/latest/hidro_datos.db"

# --- CONFIGURACIÓN ---
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

# --- NAVEGACIÓN ---
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "interactivo"

if st.session_state.vista_actual == "interactivo":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬 Ir a evolución histórica"):
            st.session_state.vista_actual = "historico"
            st.rerun()
    with col2:
        if st.button("📊 Ir a análisis de datos"):
            st.session_state.vista_actual = "analisis"
            st.rerun()

elif st.session_state.vista_actual == "historico":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱ Ir al mapa en tiempo real"):
            st.session_state.vista_actual = "interactivo"
            st.rerun()
    with col2:
        if st.button("📊 Ir a análisis de datos"):
            st.session_state.vista_actual = "analisis"
            st.rerun()

else:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱ Ir al mapa en tiempo real"):
            st.session_state.vista_actual = "interactivo"
            st.rerun()
    with col2:
        if st.button("🎬 Ir a evolución histórica"):
            st.session_state.vista_actual = "historico"
            st.rerun()

st.divider()

# ==============================
# VISTA 1: MAPA EN TIEMPO REAL
# ==============================
if st.session_state.vista_actual == "interactivo":

    st.subheader("💧 Presión en Sectores Hidráulicos en Tiempo Real")
    st_autorefresh(interval=60000, key="data_reloader")

    def interpolar_color(valor):
        pct = max(0.0, min(valor / MAX_PRESION, 1.0))
        r = int(255 * pct)
        g = int(255 * (1 - pct))
        return f"#{r:02x}{g:02x}00"

    def cargar_estado_desde_github():
        try:
            r = requests.get(ESTADO_JSON_URL, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            st.warning(f"No se pudo cargar datos: {e}")
            return {}

    geojson_path = "data/geojson/sector_hidraulico.geojson"
    if not os.path.exists(geojson_path):
        st.error(f"❌ GeoJSON no encontrado: {geojson_path}")
        st.stop()

    if "geojson_data" not in st.session_state:
        with open(geojson_path, "r", encoding="utf-8") as f:
            st.session_state.geojson_data = json.load(f)

    estado_presion_raw = cargar_estado_desde_github()

    centro = [24.117124, -110.358397]
    m = folium.Map(location=centro, zoom_start=12)
    m.add_child(Fullscreen(position='topleft'))

    for feature in st.session_state.geojson_data["features"]:
        nombre = feature["properties"].get("name", "Sin nombre")
        sector_data = estado_presion_raw.get(nombre, {})
        valor = sector_data.get("valor", 0.0)
        fill_color = interpolar_color(valor)
        fill_opacity = 0.2 + 0.5 * (valor / MAX_PRESION)
        timestamp = sector_data.get("timestamp", "N/A")
        rssi = sector_data.get("rssi", "N/A")

        geom = shape(feature["geometry"])
        centro_poligono = geom.centroid

        folium.Marker(
            location=[centro_poligono.y, centro_poligono.x],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:black;text-align:center">{valor:.2f}kg/cm²</div>'
            )
        ).add_to(m)

        tooltip_html = f"""
        <b>{nombre}</b>
        <table style="font-size:11px">
        <tr><td>Presión:</td><td>{valor:.2f}kg/cm²</td></tr>
        <tr><td>Hora:</td><td>{timestamp}</td></tr>
        <tr><td>RSSI:</td><td>{rssi}</td></tr>
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

    st_folium(m, width="100%", height=550)

# ==============================
# VISTA 2: EVOLUCIÓN HISTÓRICA
# ==============================
elif st.session_state.vista_actual == "historico":

    st.subheader("💧 Evolución de Presión en Sectores Hidráulicos")

    @st.cache_data(ttl=3600)
    def obtener_fechas_disponibles():
        fechas = []
        hoy = date.today()
        for i in range(60):
            f = hoy - timedelta(days=i)
            url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{f}.mp4"
            try:
                if requests.head(url, timeout=3).status_code == 200:
                    fechas.append(f)
            except:
                pass
        return fechas

    fechas = obtener_fechas_disponibles()
    if not fechas:
        st.warning("⚠️ No hay videos disponibles.")
        st.stop()

    seleccion = st.selectbox(
        "Selecciona un día:",
        options=fechas,
        format_func=lambda f: f.strftime("%d-%m-%Y")
    )

    video_url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{seleccion}.mp4"

    st.markdown(
        f"""
        <video src="{video_url}" controls style="width:100%; border-radius:8px;"></video>
        """,
        unsafe_allow_html=True
    )

# ==============================
# VISTA 3: ANÁLISIS DE DATOS
# ==============================
else:

    st.subheader("📊 Análisis Histórico de Presión en Sectores")

    @st.cache_data(ttl=300)
    def descargar_db():
        r = requests.get(DB_URL, timeout=15)
        if r.status_code != 200:
            raise RuntimeError("Error al descargar BD")

        db_path = "temp_db.db"
        with open(db_path, "wb") as f:
            f.write(r.content)

        return db_path

    db_path = descargar_db()

    with sqlite3.connect(db_path) as conn:
        dispositivos = pd.read_sql(
            "SELECT DISTINCT dispositivo FROM lecturas",
            conn
        )["dispositivo"].tolist()

    dispositivos_sel = st.multiselect(
        "Sectores",
        dispositivos,
        default=dispositivos[:3]
    )

    if st.button("🔄 Cargar"):

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM lecturas", conn)

        df["fecha"] = pd.to_datetime(
            df["timestamp"],
            format="%d-%m-%Y %H:%M"
        )

        df["fecha_str"] = df["fecha"].dt.strftime("%d/%m/%y %H:%M:%S")

        df = df[df["dispositivo"].isin(dispositivos_sel)]

        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "fecha:T",
                    title="Fecha y hora",
                    axis=alt.Axis(format="%d/%m/%y\n%H:%M:%S", labelAngle=0)
                ),
                y=alt.Y("valor:Q", title="Presión (kg/cm²)"),
                color="dispositivo:N",
                tooltip=[
                    alt.Tooltip("dispositivo:N", title="Sector"),
                    alt.Tooltip("fecha_str:N", title="Fecha"),
                    alt.Tooltip("valor:Q", title="Presión", format=".2f")
                ]
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)
