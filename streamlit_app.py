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

# ==============================
# CONFIGURACIÓN GITHUB
# ==============================
GITHUB_USER = "AlarmasCiateq"
REPO_NAME = "mi-mapa-sectores"
BRANCH = "main"

ESTADO_JSON_URL = (
    f"https://raw.githubusercontent.com/"
    f"{GITHUB_USER}/{REPO_NAME}/{BRANCH}/data/estado_sectores.json"
)

DB_URL = (
    f"https://raw.githubusercontent.com/"
    f"{GITHUB_USER}/{REPO_NAME}/{BRANCH}/data/hidro_datos.db"
)

# --- CONFIGURACIÓN ÚNICA ---
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

# --- BOTÓN DE NAVEGACIÓN ---
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "interactivo"

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

else:
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
    st_autorefresh(interval=60000, key="data_reloader")

    def interpolar_color(valor):
        pct = max(0.0, min(valor / MAX_PRESION, 1.0))
        r = int(255 * pct)
        g = int(255 * (1 - pct))
        return f"#{r:02x}{g:02x}00"

    def cargar_estado_desde_github():
        try:
            response = requests.get(ESTADO_JSON_URL, timeout=10)
            response.raise_for_status()
            return response.json()
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
        valor_entrada = sector_data.get("valor", 0.0)
        fill_color = interpolar_color(valor_entrada)
        fill_opacity = 0.2 + 0.5 * (valor_entrada / MAX_PRESION)
        timestamp = sector_data.get("timestamp", "N/A")
        rssi = sector_data.get("rssi", "N/A")

        geom = shape(feature["geometry"])
        centro_poligono = geom.centroid

        folium.Marker(
            location=[centro_poligono.y, centro_poligono.x],
            icon=folium.DivIcon(
                html=f'''
                <div style="
                    font-size:10px;
                    font-weight:bold;
                    color:black;
                    text-align:center;
                ">
                    {valor_entrada:.2f}kg/cm²
                </div>
                '''
            )
        ).add_to(m)

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

    st_folium(m, width="100%", height=550)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Color:** 0 ➡ 🟢 -- {MAX_PRESION} ➡ 🔴")
    with col2:
        st.markdown("**Opacidad:** 20% (baja) - 70% (alta)")

# ======
