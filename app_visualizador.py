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

# --- OBTENER FECHAS CON VIDEO ---
@st.cache_data(ttl=3600)
def obtener_fechas_disponibles():
    fechas = []
    hoy = date.today()
    for i in range(60):  # Buscar en últimos 60 días
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

# --- CONVERTIR FECHAS A FORMATO LEGIBLE ---
def fecha_a_texto(fecha):
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    dia_semana = dias_semana[fecha.weekday()]
    return f"{dia_semana} {fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"

# Crear opciones para el selectbox
opciones = {fecha_a_texto(f): f for f in fechas_disponibles}
nombres_opciones = list(opciones.keys())

# --- ETIQUETA + SELECTBOX EN LA MISMA LÍNEA ---
col1, col2 = st.columns([2, 3])  # Ajusta proporción si quieres

with col1:
    st.markdown("**Selecciona un día para ver la evolución:**")

with col2:
    seleccion_texto = st.selectbox(
        "Fecha",  # etiqueta invisible (oculta con CSS)
        options=nombres_opciones,
        index=0,  # más reciente
        label_visibility="collapsed"  # ← oculta la etiqueta del selectbox
    )

# Obtener la fecha real
fecha_seleccionada = opciones[seleccion_texto]

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
