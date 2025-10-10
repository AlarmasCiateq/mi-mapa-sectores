import streamlit as st
from datetime import date, timedelta
import requests

st.set_page_config(page_title="Evolución Presión Hidráulica")

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

st.subheader("💧 Evolución de Sectores Hidráulicos")

GITHUB_USER = "alarmasciateq"
REPO_NAME = "mi-mapa-sectores"

# --- OBTENER LISTA DE FECHAS CON VIDEO ---
@st.cache_data(ttl=3600)  # Cache por 1 hora
def obtener_fechas_disponibles():
    """Obtiene las fechas para las que existen videos en GitHub"""
    fechas = []
    hoy = date.today()
    # Buscar en los últimos 30 días
    for i in range(30):
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
    st.warning("⚠️ No hay videos disponibles en los últimos 30 días.")
    st.stop()

# --- DATE_INPUT ALINEADO HORIZONTALMENTE ---
st.markdown(
    """
    <style>
    /* Alinear etiqueta y selector en la misma línea */
    div[data-testid="stDateInput"] label {
        display: inline-block !important;
        margin-right: 10px !important;
        vertical-align: middle !important;
        font-weight: bold !important;
    }
    div[data-testid="stDateInput"] div[data-testid="stDateInputRoot"] {
        display: inline-block !important;
        vertical-align: middle !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Usar la fecha más reciente como valor por defecto
fecha_por_defecto = fechas_disponibles[0]
fecha_seleccionada = st.date_input(
    "Selecciona un día para ver la evolución:",
    value=fecha_por_defecto,
    min_value=min(fechas_disponibles),
    max_value=max(fechas_disponibles)
)

# Solo permitir fechas disponibles
if fecha_seleccionada not in fechas_disponibles:
    st.info("ℹ️ La fecha seleccionada no tiene video disponible. Se mostrará la más reciente.")
    fecha_seleccionada = fecha_por_defecto

# --- MOSTRAR VIDEO ---
video_url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{fecha_seleccionada}.mp4"

st.markdown(
    f"""
    <div style="display: flex; justify-content: center; width: 100%; margin-top: 20px;">
        <video 
            src="{video_url}" 
            controls 
            style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        </video>
    </div>
    <p style="text-align: center; color: #666; font-size: 0.9em; margin-top: 10px;">
        Si no ves el video, <a href="{video_url}" target="_blank">haz clic aquí para abrirlo directamente</a>.
    </p>
    """,
    unsafe_allow_html=True
)

# --- LISTA DE FECHAS DISPONIBLES (opcional, para depuración) ---
# with st.expander("Fechas con video disponibles"):
#     st.write([f.isoformat() for f in fechas_disponibles])
