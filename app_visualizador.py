import streamlit as st
from datetime import date, timedelta

# ❌ QUITA layout="wide"
st.set_page_config(page_title="Evolución Presión Hidráulica")

st.title("💧 Evolución de Sectores Hidráulicos")

GITHUB_USER = "alarmasciateq"  # ← tu usuario real

st.markdown(
    """
    <div style="
        position: fixed;
        top: 10px;
        right: 15px;
        width: 220px;
        background-color: #111111;
        padding: 8px 12px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        z-index: 9999;  /* Máximo nivel */
        text-align: center;
        color: white;
        font-family: 'Segoe UI', sans-serif;
        pointer-events: none; /* Evita interferencia con clics */
        transition: all 0.2s ease;
    ">
        <p style='
            margin: 0; 
            color: #782e44; 
            font-size: 1.1em; 
            font-weight: 600;
            letter-spacing: 0.5px;
        '>
            CIATEQ 💦
        </p>
        <p style='
            color: #aaa; 
            font-size: 0.65em; 
            margin: 0; 
            line-height: 1.2;
        '>
            © 2025 Todos los derechos reservados
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

hoy = date.today()
min_fecha = hoy - timedelta(days=30)
fecha_seleccionada = st.date_input(
    "Selecciona un día para ver la evolución",
    value=hoy,
    min_value=min_fecha,
    max_value=hoy
)

video_url = f"https://{GITHUB_USER}.github.io/mi-mapa-sectores/hidro-videos/presion_{fecha_seleccionada}.mp4"

# ✅ VIDEO RESPONSIVO CON TAMAÑO MÁXIMO
st.markdown(
    f"""
    <div style="display: flex; justify-content: center; width: 100%;">
        <video 
            src="{video_url}" 
            controls 
            style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;"
            onerror="this.style.display='none';">
        </video>
    </div>
    <p style="text-align: center; color: #666; font-size: 0.9em;">
        Si no ves el video, <a href="{video_url}" target="_blank">haz clic aquí para abrirlo directamente</a>.
    </p>
    """,
    unsafe_allow_html=True
)

st.caption("Los videos se generan diariamente a partir de capturas cada 5 minutos.")



