import streamlit as st
import pandas as pd
import altair as alt
from datetime import timedelta

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(layout="wide")

st.title("Análisis de Datos")

# =========================
# CARGA DE DATOS
# =========================
@st.cache_data
def cargar_datos():
    return pd.read_csv("datos.csv")  # usa tu archivo real

df = cargar_datos()

# =========================
# PREPROCESAMIENTO
# =========================
df["fecha"] = pd.to_datetime(df["timestamp"], format="%d-%m-%Y %H:%M")
df["fecha_str"] = df["fecha"].dt.strftime("%d/%m/%y %H:%M:%S")

# =========================
# SELECTOR DE DISPOSITIVOS
# =========================
dispositivos = sorted(df["dispositivo"].unique())
seleccion = st.multiselect(
    "Selecciona sectores",
    dispositivos,
    default=dispositivos
)

df = df[df["dispositivo"].isin(seleccion)]

# =========================
# RANGO DE 1 DÍA (ZOOM VISUAL)
# =========================
fecha_max = df["fecha"].max()
fecha_min = fecha_max - timedelta(days=1)

# =========================
# GRÁFICA
# =========================
chart = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "fecha:T",
            title="Fecha y hora",
            scale=alt.Scale(domain=[fecha_min, fecha_max]),
            axis=alt.Axis(
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
    .interactive()  # PAN / ZOOM SOLO VISUAL
)

st.altair_chart(chart, use_container_width=True)
