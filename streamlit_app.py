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
HORA_MEXICO = timedelta(hours=-6)

# ==============================
# GITHUB
# ==============================
GITHUB_USER = "AlarmasCiateq"
REPO_NAME = "mi-mapa-sectores"
BRANCH = "main"

ESTADO_JSON_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/data/estado_sectores.json"
)

DB_RELEASE_API = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/releases/latest"
DB_DOWNLOAD_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/releases/download/latest/hidro_datos.db"

# ==============================
# CONFIG
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
    if st.button("📊 Análisis histórico"):
        st.session_state.vista_actual = "analisis"
        st.rerun()

st.divider()

# ==============================
# MAPA TIEMPO REAL
# ==============================
if st.session_state.vista_actual == "interactivo":

    st.subheader("💧 Presión en tiempo real")
    st_autorefresh(interval=60000, key="reload")

    def interpolar_color(valor):
        pct = max(0, min(valor / MAX_PRESION, 1))
        r = int(255 * pct)
        g = int(255 * (1 - pct))
        return f"#{r:02x}{g:02x}00"

    estado = requests.get(ESTADO_JSON_URL).json()

    with open("data/geojson/sector_hidraulico.geojson", encoding="utf-8") as f:
        geojson = json.load(f)

    m = folium.Map(location=[24.117124, -110.358397], zoom_start=12)
    m.add_child(Fullscreen())

    for f in geojson["features"]:
        nombre = f["properties"]["name"]
        data = estado.get(nombre, {})
        valor = data.get("valor", 0)
        timestamp = data.get("timestamp", "N/A")

        geom = shape(f["geometry"]).centroid

        folium.Marker(
            [geom.y, geom.x],
            icon=folium.DivIcon(html=f"<b>{valor:.2f}</b>")
        ).add_to(m)

        folium.GeoJson(
            f,
            style_function=lambda x, v=valor: {
                "fillColor": interpolar_color(v),
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6
            },
            tooltip=f"{nombre}<br>{valor:.2f} kg/cm²<br>{timestamp}"
        ).add_to(m)

    st_folium(m, height=550)

# ==============================
# ANÁLISIS HISTÓRICO
# ==============================
else:

    st.subheader("📊 Análisis Histórico de Presión en Sectores")

    @st.cache_data(ttl=300)
    def descargar_db():
        # Obtener info de la release
        r = requests.get(DB_RELEASE_URL, timeout=15)
        if r.status_code != 200:
            raise RuntimeError("Error al obtener info de la Release")

        release_info = r.json()

        # Buscar SIEMPRE el asset correcto
        asset = next(
            a for a in release_info["assets"]
            if a["name"] == "sectores.db"
        )

        # Fecha real del archivo (no de descarga)
        fecha_github_utc = asset["updated_at"]
        fecha_github = (
            datetime.strptime(fecha_github_utc, "%Y-%m-%dT%H:%M:%SZ")
            + HORA_MEXICO
        )

        # Descargar archivo
        r_file = requests.get(asset["browser_download_url"], timeout=30)

        db_path = "temp_db.db"
        with open(db_path, "wb") as f:
            f.write(r_file.content)

        st.info(
            "Base de datos tomada de GitHub Release. "
            "Última actualización del archivo (México GMT-6): "
            f"{fecha_github.strftime('%d/%m/%Y %H:%M')}"
        )

        return db_path

    db_path = descargar_db()

    def cargar_datos():
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(
                "SELECT * FROM lecturas ORDER BY id ASC",
                conn
            )

        # Timestamp como texto -> datetime seguro
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            format="%d-%m-%Y %H:%M",
            errors="coerce"
        )

        # Rellenar posibles huecos sin romper orden
        df["timestamp"] = df["timestamp"].fillna(method="ffill")

        return df

    df = cargar_datos()

    dispositivos = df["dispositivo"].unique().tolist()

    dispositivos_sel = st.multiselect(
        "Sectores",
        dispositivos,
        default=dispositivos[:3]
    )

    if st.button("🔄 Cargar"):

        df_sel = df[df["dispositivo"].isin(dispositivos_sel)]

        if not df_sel.empty:
            # Último dato REAL
            ultima_fecha = df_sel["timestamp"].max()

            # Ventana visible de 24 horas hacia atrás
            inicio_visible = ultima_fecha - pd.Timedelta(days=1)

            df_visible = df_sel[df_sel["timestamp"] >= inicio_visible]
        else:
            df_visible = df_sel

        df_visible["fecha_str"] = df_visible["timestamp"].dt.strftime(
            "%d/%m/%y %H:%M:%S"
        )

        chart = (
            alt.Chart(df_visible)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "timestamp:T",
                    title="Fecha y hora",
                    axis=alt.Axis(
                        format="%d/%m/%y %H:%M:%S",
                        grid=True
                    )
                ),
                y=alt.Y(
                    "valor:Q",
                    title="Presión (kg/cm²)",
                    axis=alt.Axis(grid=True)
                ),
                color=alt.Color(
                    "dispositivo:N",
                    legend=alt.Legend(
                        title="Sector",
                        orient="bottom"
                    )
                ),
                tooltip=[
                    alt.Tooltip("dispositivo:N", title="Sector"),
                    alt.Tooltip("fecha_str:N", title="Fecha"),
                    alt.Tooltip("valor:Q", title="Presión", format=".2f")
                ]
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)


