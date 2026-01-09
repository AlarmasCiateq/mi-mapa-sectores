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

DB_URL = (
    "https://github.com/AlarmasCiateq/mi-mapa-sectores/releases/download/latest/hidro_datos.db"
)

# ==============================
# CONFIGURACIÓN
# ==============================
st.set_page_config(
    page_title="Sectores Hidráulicos CIATEQ",
    page_icon="💧",
    layout="centered"
)

# ==============================
# MARCA DE AGUA
# ==============================
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
    ">
        💧 CIATEQ® 💦 2025 ©
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
# NAVEGACIÓN
# ==============================
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "interactivo"

col1, col2 = st.columns(2)

with col1:
    if st.button("⏱ Mapa tiempo real"):
        st.session_state.vista_actual = "interactivo"
        st.rerun()

with col2:
    if st.button("🎬 Evolución histórica"):
        st.session_state.vista_actual = "historico"
        st.rerun()

if st.button("📊 Análisis de datos"):
    st.session_state.vista_actual = "analisis"
    st.rerun()

st.divider()

# ==============================
# VISTA 1: MAPA
# ==============================
if st.session_state.vista_actual == "interactivo":

    st.subheader("💧 Presión en Sectores Hidráulicos en Tiempo Real")
    st_autorefresh(interval=60000, key="reload")

    def interpolar_color(valor):
        pct = max(0.0, min(valor / MAX_PRESION, 1.0))
        r = int(255 * pct)
        g = int(255 * (1 - pct))
        return f"#{r:02x}{g:02x}00"

    def cargar_estado():
        try:
            r = requests.get(ESTADO_JSON_URL, timeout=10)
            r.raise_for_status()
            return r.json()
        except:
            return {}

    geojson_path = "data/geojson/sector_hidraulico.geojson"
    if not os.path.exists(geojson_path):
        st.error("GeoJSON no encontrado")
        st.stop()

    with open(geojson_path, encoding="utf-8") as f:
        geojson_data = json.load(f)

    estado = cargar_estado()

    m = folium.Map(location=[24.117124, -110.358397], zoom_start=12)
    m.add_child(Fullscreen())

    for feature in geojson_data["features"]:
        nombre = feature["properties"].get("name", "N/A")
        data = estado.get(nombre, {})
        valor = float(data.get("valor", 0))
        timestamp = data.get("timestamp", "N/A")
        rssi = data.get("rssi", "N/A")

        geom = shape(feature["geometry"])
        centro = geom.centroid

        folium.Marker(
            [centro.y, centro.x],
            icon=folium.DivIcon(
                html=f"<div style='font-size:10px;font-weight:bold'>{valor:.2f}</div>"
            )
        ).add_to(m)

        folium.GeoJson(
            feature,
            style_function=lambda x, v=valor: {
                "fillColor": interpolar_color(v),
                "color": "#000",
                "weight": 1.2,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(
                f"""
                <b>{nombre}</b><br>
                Presión: {valor:.2f} kg/cm²<br>
                Hora: {timestamp}<br>
                RSSI: {rssi}
                """,
                sticky=True,
            ),
        ).add_to(m)

    st_folium(m, width="100%", height=550)

# ==============================
# VISTA 2: VIDEO
# ==============================
elif st.session_state.vista_actual == "historico":

    st.subheader("💧 Evolución Histórica")

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

    if not fechas:
        st.warning("No hay videos disponibles")
        st.stop()

    seleccion = st.selectbox(
        "Selecciona un día",
        fechas,
        format_func=lambda x: x.strftime("%d-%m-%Y"),
    )

    st.markdown(
        f"""
        <video src="https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{seleccion}.mp4"
               controls style="width:100%; border-radius:8px;"></video>
        """,
        unsafe_allow_html=True,
    )

# ==============================
# VISTA 3: ANÁLISIS (FIX REAL)
# ==============================
else:

    st.subheader("📊 Presión – últimas 24 h")

    @st.cache_data(ttl=300)
    def cargar_datos():
        db_path = "temp_db.db"
        r = requests.get(DB_URL, timeout=15)
        r.raise_for_status()

        with open(db_path, "wb") as f:
            f.write(r.content)

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(
                "SELECT dispositivo, valor, timestamp FROM lecturas",
                conn,
            )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            format="%d-%m-%Y %H:%M",
            errors="coerce"
        )

        df = df.dropna(subset=["timestamp"])
        return df

    df = cargar_datos()

    ultimo = df["timestamp"].max()
    inicio = ultimo - timedelta(days=1)

    df = df[df["timestamp"] >= inicio]

    dispositivos = sorted(df["dispositivo"].unique())

    seleccion = st.multiselect(
        "Sectores",
        dispositivos,
        default=dispositivos[:3],
    )

    df = df[df["dispositivo"].isin(seleccion)]

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("timestamp:T", title="Fecha y hora"),
            y=alt.Y("valor:Q", title="Presión (kg/cm²)"),
            color=alt.Color("dispositivo:N", legend=alt.Legend(orient="bottom")),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Fecha"),
                alt.Tooltip("valor:Q", format=".2f"),
            ],
        )
        .properties(height=350)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)
