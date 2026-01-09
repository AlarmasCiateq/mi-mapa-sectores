import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
from datetime import timedelta

# =========================
# CONFIGURACIÓN STREAMLIT
# =========================
st.set_page_config(layout="wide")

# =========================
# CARGA DE DATOS
# =========================
@st.cache_data
def cargar_datos():
    conn = sqlite3.connect("lecturas.db", check_same_thread=False)
    df = pd.read_sql(
        """
        SELECT dispositivo, valor, timestamp
        FROM lecturas
        ORDER BY timestamp
        """,
        conn
    )
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


df = cargar_datos()

# =========================
# BOTÓN (NO SE TOCA)
# =========================
if st.button("Graficar"):
    if df.empty:
        st.warning("No hay datos para mostrar")
        st.stop()

    # =========================
    # CÁLCULO DEL RANGO 24 H
    # =========================
    ultimo_timestamp = df["timestamp"].max()
    inicio_ventana = ultimo_timestamp - timedelta(days=1)

    # =========================
    # GRÁFICA
    # =========================
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["valor"],
            mode="lines",
            name="Presión (kg/cm²)"
        )
    )

    fig.update_layout(
        xaxis=dict(
            range=[inicio_ventana, ultimo_timestamp],
            title="Fecha y hora",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.4)"
        ),
        yaxis=dict(
            title="Presión (kg/cm²)",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.4)"
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=60, r=30, t=40, b=80),
        autosize=True
    )

    st.plotly_chart(fig, use_container_width=True)
