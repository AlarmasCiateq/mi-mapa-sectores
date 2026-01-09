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

DB_URL = "https://github.com/AlarmasCiateq/mi-mapa-sectores/releases/download/latest/hidro_datos.db"

# ==============================
# CONFIG STREAMLIT
# ==============================
st.set_page_config(
    page_title="Sectores Hidráulicos CIATEQ",
    page_icon="💧",
    layout="centered"
)

# ==============================
# NAVEGACIÓN
# ==============================
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "interactivo"

col1, col2 = st.columns(2)
with col1:
    if st.button("⏱ Mapa en tiempo real"):
        st.session_state.vista_actual = "interactivo"
        st.rerun()
with col2:
    if st.button("📊 Análisis de datos"):
        st.session_state.vista_actual = "analisis"
        st.rerun()

st.divider()

# ==============================
# VISTA 1: MAPA TIEMPO REAL
# ==============================
if st.session_state.vista_actual == "interactivo":

    st.subheader("💧 Presión en Sectores Hidráulicos en Tiempo Real")
    st_autorefresh(interval=60000, key="refresh")

    def interpolar_color(valor):
        pct = max(0.0, min(valor / MAX_PRESION, 1.0))
        r = int(255 * pct)
        g = int(255 * (1 - pct))
        return f"#{r:02x}{g:02x}00"

    def cargar_estado():
        r = requests.get(ESTADO_JSON_URL, timeout=10)
        r.raise_for_status()
        return r.json()

    geojson_path = "data/geojson/sector_hidraulico.geojson"
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    estado = cargar_estado()

    m = folium.Map(location=[24.117124, -110.358397], zoom_start=12)
    m.add_child(Fullscreen())

    for feature in geojson_data["features"]:
        nombre = feature["properties"]["name"]
        data = estado.get(nombre, {})
        valor = data.get("valor", 0.0)
        timestamp = data.get("timestamp", "N/A")
        rssi = data.get("rssi", "N/A")

        geom = shape(feature["geometry"])
        centro = geom.centroid

        tooltip = f"""
        <b>{nombre}</b><br>
        Presión: {valor:.2f} kg/cm²<br>
        Hora: {timestamp}<br>
        RSSI: {rssi}
        """

        folium.GeoJson(
            feature,
            style_function=lambda x, v=valor: {
                "fillColor": interpolar_color(v),
                "color": "#000",
                "weight": 1.2,
                "fillOpacity": 0.6
            },
            tooltip=tooltip
        ).add_to(m)

        folium.Marker(
            [centro.y, centro.x],
            icon=folium.DivIcon(html=f"<b>{valor:.2f}</b>")
        ).add_to(m)

    st_folium(m, width="100%", height=550)

# ==============================
# VISTA 2: ANÁLISIS DE DATOS
# ==============================
else:

    st.subheader("📊 Análisis Histórico de Presión")

    @st.cache_data(ttl=300)
    def descargar_db():
        r = requests.get(DB_URL, timeout=15)
        r.raise_for_status()
        path = "temp.db"
        with open(path, "wb") as f:
            f.write(r.content)
        return path

    db_path = descargar_db()

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql("SELECT * FROM lecturas", conn)

    df["fecha"] = pd.to_datetime(
        df["timestamp"],
        format="%d-%m-%Y %H:%M"
    )

    df["fecha_str"] = df["fecha"].dt.strftime("%d/%m/%y %H:%M:%S")

    dispositivos = sorted(df["dispositivo"].unique())

    seleccion = st.multiselect(
        "Sectores",
        dispositivos,
        default=dispositivos[:3]
    )

    df = df[df["dispositivo"].isin(seleccion)]

    fecha_max = df["fecha"].max()
    fecha_min = fecha_max - timedelta(days=1)

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "fecha:T",
                scale=alt.Scale(domain=[fecha_min, fecha_max]),
                axis=alt.Axis(
                    format="%d/%m/%y %H:%M:%S",
                    grid=True,
                    gridColor="#b0b0b0",
                    gridOpacity=0.4
                )
            ),
            y=alt.Y(
                "valor:Q",
                title="Presión (kg/cm²)",
                axis=alt.Axis(
                    grid=True,
                    gridColor="#b0b0b0",
                    gridOpacity=0.4
                )
            ),
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
