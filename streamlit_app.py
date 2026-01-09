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

# --- CONFIGURACIÓN ---
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

# ==============================
# VISTA 1: MAPA TIEMPO REAL
# ==============================
if st.session_state.vista_actual == "interactivo":

    st.subheader("💧 Presión en Sectores Hidráulicos en Tiempo Real")
    st_autorefresh(interval=60000, key="data_reloader")

    def interpolar_color(valor):
        pct = max(0.0, min(valor / MAX_PRESION, 1.0))
        r = int(255 * pct)
        g = int(255 * (1 - pct))
        return f"#{r:02x}{g:02x}00"

    def cargar_estado():
        try:
            return requests.get(ESTADO_JSON_URL, timeout=10).json()
        except:
            return {}

    geojson_path = "data/geojson/sector_hidraulico.geojson"
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    estado = cargar_estado()

    m = folium.Map(location=[24.117124, -110.358397], zoom_start=12)
    m.add_child(Fullscreen())

    for feature in geojson["features"]:
        nombre = feature["properties"].get("name", "")
        data = estado.get(nombre, {})
        valor = data.get("valor", 0.0)

        geom = shape(feature["geometry"]).centroid

        folium.GeoJson(
            feature,
            style_function=lambda x, v=valor: {
                "fillColor": interpolar_color(v),
                "color": "#000",
                "weight": 1.5,
                "fillOpacity": 0.6
            },
            tooltip=f"{nombre}: {valor:.2f} kg/cm²"
        ).add_to(m)

        folium.Marker(
            [geom.y, geom.x],
            icon=folium.DivIcon(
                html=f"<b>{valor:.2f}</b>"
            )
        ).add_to(m)

    st_folium(m, height=550, width="100%")

# ==============================
# VISTA 2: HISTÓRICO VIDEO
# ==============================
elif st.session_state.vista_actual == "historico":

    st.subheader("💧 Evolución Histórica")

    fechas = [date.today() - timedelta(days=i) for i in range(10)]

    seleccion = st.selectbox(
        "Selecciona un día",
        fechas,
        format_func=lambda f: f.strftime("%d-%m-%Y")
    )

    st.video(
        f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{seleccion}.mp4"
    )

# ==============================
# VISTA 3: ANÁLISIS DE DATOS
# ==============================
else:

    st.subheader("📊 Análisis Histórico de Presión")

    @st.cache_data(ttl=300)
    def descargar_db():
        r = requests.get(DB_URL, timeout=15)
        db_path = "temp.db"
        with open(db_path, "wb") as f:
            f.write(r.content)
        return db_path

    db_path = descargar_db()

    with sqlite3.connect(db_path) as conn:
        dispositivos = pd.read_sql(
            "SELECT DISTINCT dispositivo FROM lecturas", conn
        )["dispositivo"].tolist()

    seleccion = st.multiselect(
        "Sectores",
        dispositivos,
        default=dispositivos[:3]
    )

    if st.button("🔄 Cargar"):

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM lecturas", conn)

        # ---- CONVERSIÓN DE FECHA ----
        df["fecha"] = pd.to_datetime(
            df["timestamp"], format="%d-%m-%Y %H:%M"
        )

        # ---- FECHA FORMATEADA EN ESPAÑOL PARA TOOLTIP ----
        df["fecha_str"] = df["fecha"].dt.strftime("%d/%m/%y %H:%M:%S")

        df = df[df["dispositivo"].isin(seleccion)]

        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "fecha:T",
                    title="Fecha y hora",
                    axis=alt.Axis(
                        format="%d/%m/%y\n%H:%M:%S",
                        labelAngle=0
                    )
                ),
                y=alt.Y("valor:Q", title="Presión (kg/cm²)"),
                color=alt.Color("dispositivo:N", title="Sector"),
                tooltip=[
                    alt.Tooltip("dispositivo:N", title="Sector"),
                    alt.Tooltip("fecha_str:N", title="Fecha"),
                    alt.Tooltip("valor:Q", title="Presión", format=".2f")
                ]
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)
