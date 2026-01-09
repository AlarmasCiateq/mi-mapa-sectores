import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ================== CONFIGURACIÓN DE PÁGINA ==================
st.set_page_config(
    page_title="Gráfica de Presión",
    layout="wide"
)

# ================== CARGA DE DATOS ==================
@st.cache_data
def cargar_datos():
    df = pd.read_csv("datos.csv")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df

df = cargar_datos()

# ================== INTERFAZ ==================
st.title("Histórico de Presión")

if st.button("Graficar"):
    # Rango total
    fecha_max = df["fecha"].max()
    fecha_min = fecha_max - pd.Timedelta(days=1)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["presion"],
            mode="lines",
            name="Presión"
        )
    )

    fig.update_layout(
        xaxis=dict(
            title="Tiempo",
            range=[fecha_min, fecha_max],
            tickformat="%d/%m/%y\n%H:%M:%S",
            showgrid=True,
            gridcolor="lightgrey"
        ),
        yaxis=dict(
            title="Presión (kg/cm²)",
            showgrid=True,
            gridcolor="lightgrey"
        ),
        hovermode="x unified"
    )

    fig.update_traces(
        hovertemplate="%{x|%d/%m/%y %H:%M:%S}<br>Presión: %{y}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)
