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

    st.subheader("📊 Análisis histórico")

    @st.cache_data(ttl=300)
@st.cache_data(ttl=300)
def descargar_db():
    r = requests.get(DB_RELEASE_URL, timeout=15)
    if r.status_code != 200:
        raise RuntimeError("Error al obtener info de la release")

    release_info = r.json()

    asset = next(
        a for a in release_info["assets"]
        if a["name"] == "sectores.db"
    )

    fecha_github_utc = asset["updated_at"]
    fecha_github = (
        datetime.strptime(fecha_github_utc, "%Y-%m-%dT%H:%M:%SZ")
        + HORA_MEXICO
    )

    r_file = requests.get(asset["browser_download_url"], timeout=30)

    db_path = "temp_db.db"
    with open(db_path, "wb") as f:
        f.write(r_file.content)

    st.info(
        f"Base de datos tomada de GitHub Release. "
        f"Última actualización del archivo (México GMT-6): "
        f"{fecha_github.strftime('%d/%m/%Y %H:%M')}"
    )

    return db_path


    db_path = descargar_db()

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql("SELECT * FROM lecturas ORDER BY id ASC", conn)

    # timestamp como texto → datetime
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="%d-%m-%Y %H:%M",
        errors="coerce"
    ) + HORA_MEXICO

    dispositivos = sorted(df["dispositivo"].unique())

    seleccion = st.multiselect(
        "Sectores",
        dispositivos,
        default=dispositivos[:3]
    )

    df_sel = df[df["dispositivo"].isin(seleccion)]

    if df_sel.empty:
        st.warning("No hay datos")
        st.stop()

    ultima = df_sel["timestamp"].max()
    inicio_24h = ultima - pd.Timedelta(hours=24)

    base = alt.Chart(df_sel).mark_line().encode(
        x=alt.X(
            "timestamp:T",
            scale=alt.Scale(domain=[inicio_24h, ultima]),
            title="Tiempo"
        ),
        y=alt.Y("valor:Q", title="Presión (kg/cm²)"),
        color=alt.Color("dispositivo:N", title="Sector"),
        tooltip=["dispositivo", "valor", "timestamp"]
    ).interactive()

    st.altair_chart(base, use_container_width=True)

