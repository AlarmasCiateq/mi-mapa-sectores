import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Evolución Presión Hidráulica", layout="wide")
st.title("💧 Evolución de Sectores Hidráulicos")

hoy = date.today()
min_fecha = hoy - timedelta(days=30)
fecha_seleccionada = st.date_input(
    "Selecciona un día para ver la evolución",
    value=hoy,
    min_value=min_fecha,
    max_value=hoy
)

GITHUB_USER = "AlarmasCiateq" 
video_url = f"https://{GITHUB_USER}.github.io/mi-mapa-sectores/hidro-videos/presion_{fecha_seleccionada}.mp4"

st.video(video_url)

st.caption("Los videos se generan diariamente a partir de capturas cada 5 minutos.")
