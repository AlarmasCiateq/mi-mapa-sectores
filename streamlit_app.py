# streamlit_app.py
import os
import streamlit as st
import folium
import json
import requests
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from shapely.geometry import shape

MAX_PRESION = 3.0  # kg/cm²

# --- URL DEL ARCHIVO JSON EN GOOGLE DRIVE ---
GOOGLE_DRIVE_JSON_URL = "https://drive.google.com/uc?export=download&id=1lhOfMwDaJYsOHGZhoS3kNTNQ8WCZcfPW"

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Sectores Hidráulicos",
    page_icon="💧",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- MARCA FLOTANTE © 2025 CIATEQ® ---
st.markdown(
    """
    <div style="
        position: fixed;
        top: 10px;
        right: 15px;
        z-index: 999999999;
        color: white;
        font-size: 1.3em;
        background-color: #111;
        padding: 5px 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        font-family: 'Segoe UI', sans-serif;
    ">
        © 2025 CIATEQ®
    </div>
    """,
    unsafe_allow_html=True
)

# --- OCULTAR BOTÓN DEL SIDEBAR ---
st.html(
    """
    <div id="hide-sidebar-toggle"></div>
    <script>
        const observer = new MutationObserver(() => {
            const button = document.querySelector('button[data-testid="stSidebarHeaderToggle"]');
            if (button) {
                button.style.display = 'none !important';
                button.parentElement.style.visibility = 'hidden !important';
                button.parentElement.style.width = '0px !important';
                button.parentElement.style.padding = '0px !important';
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    </script>
    <style>
        button[data-testid="stSidebarHeaderToggle"] { display: none !important; }
        [data-testid="stSidebarHeader"] { display: none !important; }
    </style>
    """
)


# --- AUTOREFRESH CADA 10 SEGUNDOS ---
st_autorefresh(interval=60000, key="data_reloader")


# --- FUNCIONES ---
def interpolar_color(valor):
    """
    Interpola entre verde (0) y rojo (15)
    valor: float entre 0 y 15
    """
    # Normalizar de [0, 15] a [0, 1]
    pct = max(0.0, min(valor / MAX_PRESION, 1.0))  # Asegura que esté entre 0 y 1
    r = int(255 * pct)
    g = int(255 * (1 - pct))
    b = 0
    return f"#{r:02x}{g:02x}{b:02x}"

def obtener_limites_geograficos(geojson_data):
    """Extrae los límites geográficos del GeoJSON"""
    coords = []
    for feature in geojson_data["features"]:
        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            coords.extend(geom["coordinates"][0])
        elif geom["type"] == "MultiPolygon":
            for polygon in geom["coordinates"]:
                coords.extend(polygon[0])
    if not coords:
        return None
    lats = [c[1] for c in coords]
    lons = [c[0] for c in coords]
    return [(min(lats), min(lons)), (max(lats), max(lons))]

def cargar_estado_desde_drive():
    """Descarga estado_sectores.json desde Google Drive"""
    try:
        response = requests.get(GOOGLE_DRIVE_JSON_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"No se pudo cargar el estado desde Google Drive: {e}")
        return {}
    except json.JSONDecodeError as e:
        st.error(f"El archivo descargado no es un JSON válido: {e}")
        return {}

def mostrar_mapa():
    # Ruta al GeoJSON local (este SÍ debe estar en tu repositorio)
    geojson_path = "data/geojson/sector_hidraulico.geojson"

    # Validar que exista el GeoJSON
    if not os.path.exists(geojson_path):
        st.error(f"❌ No se encontró el archivo GeoJSON: {geojson_path}")
        return

    # Cargar GeoJSON una sola vez usando session_state
    if "geojson_data" not in st.session_state:
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                st.session_state.geojson_data = json.load(f)
        except Exception as e:
            st.error(f"❌ Error al leer GeoJSON: {e}")
            return

    # Cargar estado desde Google Drive
    estado_presion_raw = cargar_estado_desde_drive()

    # Configurar mapa
    centro = [24.117124, -110.358397]
    m = folium.Map(location=centro, zoom_start=12, name="main_map")
    m.add_child(Fullscreen(position='topleft'))

    # Añadir cada sector
    for feature in st.session_state.geojson_data["features"]:
        nombre = feature["properties"].get("name", "Sin nombre")
        sector_data = estado_presion_raw.get(nombre, {})
        valor_entrada = sector_data.get("valor", 0.0)
        fill_color = interpolar_color(valor_entrada)
        fill_opacity = 0.2 + 0.5 * (valor_entrada / MAX_PRESION)  # de 0.2 (0 kg/cm²) a 0.7 (15 kg/cm²)
        timestamp = sector_data.get("timestamp", "N/A")
        rssi = sector_data.get("rssi", "N/A")
        valor_con_unidad = f"{valor_entrada:.2f}kg/cm³"

        # Calcular centroide del polígono
        geom = shape(feature["geometry"])
        centro_poligono = geom.centroid

        # Etiqueta de presión sobre el sector
        folium.map.Marker(
            location=[centro_poligono.y, centro_poligono.x],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:black;text-align:center">{valor_con_unidad}</div>'
            )
        ).add_to(m)

        # Tooltip detallado
        tooltip_html = f"""
        <b>{nombre}</b>
        <table style="font-size: 11px; font-family: Arial, sans-serif;">
        <tr><td>Presión: </td><td>{valor_con_unidad}</td></tr>
        <tr><td>Hora: </td><td>{timestamp}</td></tr>
        <tr><td>RSSI: </td><td>{rssi}</td></tr>
        </table>
        """

        folium.GeoJson(
            feature,
            style_function=lambda x, fc=fill_color, fo=fill_opacity: {
                "fillColor": fc,
                "color": "#000000",
                "weight": 1.5,
                "fillOpacity": fo,
                "opacity": 0.8
            },
            tooltip=folium.Tooltip(tooltip_html, sticky=True)
        ).add_to(m)

    # CSS: maximizar tamaño del mapa
    st.markdown(
        """
        <style>
        .folium-map {
            height: 100vh !important;
            width: 100% !important;
            margin: 0;
            padding: 0;
        }
        .stApp {
            margin: 0;
            padding: 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Mostrar mapa
    st_folium(m, width="100%", height=550, key="mapa_principal")

# --- MOSTRAR MAPA ---
mostrar_mapa()

# --- LEYENDA ---
st.markdown("---")
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown(f"Color: **0**➡Verde -- **{MAX_PRESION}**➡Rojo")
with col2:

    st.markdown("**Opacidad:** Mínimo (20%) = baja presión - Máximo (70%) = alta presión")













