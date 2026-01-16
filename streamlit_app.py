# import os
# import streamlit as st
# import folium
# import json
# import requests
# from datetime import date, timedelta, datetime
# from folium.plugins import Fullscreen
# from streamlit_folium import st_folium
# from streamlit_autorefresh import st_autorefresh
# from shapely.geometry import shape
# import pandas as pd
# import sqlite3
# import altair as alt

# MAX_PRESION = 3.0
# HORA_MEXICO = timedelta(hours=-6)

# # ==============================
# # FUENTES DE DATOS (GITHUB)
# # ==============================
# GITHUB_USER = "AlarmasCiateq"
# REPO_NAME = "mi-mapa-sectores"
# BRANCH = "main"

# ESTADO_JSON_URL = (
# f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/data/estado_sectores.json"
# )

# DB_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/releases/latest"
# DB_DOWNLOAD_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/releases/download/latest/hidro_datos.db"

# # --- CONFIGURACIÓN ---
# st.set_page_config(
# page_title="Sectores Hidráulicos CIATEQ",
# page_icon="💧",
# layout="centered"
# )

# # --- MARCA DE AGUA ---
# st.markdown(
# """
# <div style="
#     position: fixed;
#     top: 10px;
#     right: 18px;
#     z-index: 999999999;
#     color: white;
#     font-size: 1.3em;
#     background-color: #111;
#     padding: 5px 10px;
#     border-radius: 8px;
#     box-shadow: 0 2px 4px rgba(0,0,0,0.2);
# ">
#     💧 CIATEQ® 💦 2025 ©
# </div>
# """,
# unsafe_allow_html=True
# )

# # --- NAVEGACIÓN ---
# if "vista_actual" not in st.session_state:
# st.session_state.vista_actual = "interactivo"

# if st.session_state.vista_actual == "interactivo":
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("🎬 Ir a evolución histórica"):
#         st.session_state.vista_actual = "historico"
#         st.rerun()
# with col2:
#     if st.button("📊 Ir a análisis de datos"):
#         st.session_state.vista_actual = "analisis"
#         st.rerun()

# elif st.session_state.vista_actual == "historico":
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("⏱ Ir al mapa en tiempo real"):
#         st.session_state.vista_actual = "interactivo"
#         st.rerun()
# with col2:
#     if st.button("📊 Ir a análisis de datos"):
#         st.session_state.vista_actual = "analisis"
#         st.rerun()

# else:
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("⏱ Ir al mapa en tiempo real"):
#         st.session_state.vista_actual = "interactivo"
#         st.rerun()
# with col2:
#     if st.button("🎬 Ir a evolución histórica"):
#         st.session_state.vista_actual = "historico"
#         st.rerun()

# st.divider()

# # ==============================
# # VISTA 1: MAPA EN TIEMPO REAL
# # ==============================


# # def cargar_estado_desde_github():
# #     try:
# #         r = requests.get(ESTADO_JSON_URL, timeout=10)
# #         r.raise_for_status()
# #         return r.json()
# #     except Exception as e:
# #         st.warning(f"No se pudo cargar datos: {e}")
# #         return {}

# # def cargar_estado_desde_github():
# #     try:
# #         # Obtener la release más reciente
# #         r = requests.get(
# #             f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/releases/latest",
# #             timeout=10
# #         )
# #         r.raise_for_status()
# #         release = r.json()

# #         # Buscar el asset "estado_sectores.json"
# #         asset = next((a for a in release["assets"] if a["name"] == "estado_sectores.json"), None)
# #         if not asset:
# #             st.warning("Archivo estado_sectores.json no encontrado en la Release.")
# #             return {}

# #         # Descargar el JSON
# #         json_resp = requests.get(asset["browser_download_url"], timeout=10)
# #         json_resp.raise_for_status()
# #         return json_resp.json()
# # ==============================
# # VISTA 1: MAPA EN TIEMPO REAL
# # ==============================
# if st.session_state.vista_actual == "interactivo":

#     st.subheader("💧 Presión en Sectores Hidráulicos en Tiempo Real")
#     st_autorefresh(interval=60000, key="data_reloader")  # Refresca cada 60 segundos

#     def interpolar_color(valor):
#         pct = max(0.0, min(valor / MAX_PRESION, 1.0))
#         r = int(255 * pct)
#         g = int(255 * (1 - pct))
#         return f"#{r:02x}{g:02x}00"

#     def cargar_estado_desde_github():
#         # Inicializar caché si no existe
#         if "estado_sectores_cache" not in st.session_state:
#             st.session_state["estado_sectores_cache"] = None

#         try:
#             # Obtener la release más reciente
#             r = requests.get(
#                 f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/releases/latest",
#                 timeout=10
#             )
#             r.raise_for_status()
#             release = r.json()

#             # Buscar el asset "estado_sectores.json"
#             asset = next((a for a in release["assets"] if a["name"] == "estado_sectores.json"), None)
#             if not asset:
#                 # No está el archivo → mantener estado anterior
#                 pass
#             else:
#                 # Descargar y validar el JSON
#                 json_resp = requests.get(asset["browser_download_url"], timeout=10)
#                 json_resp.raise_for_status()
#                 nuevo_estado = json_resp.json()

#                 if isinstance(nuevo_estado, dict):
#                     st.session_state["estado_sectores_cache"] = nuevo_estado
#                     return nuevo_estado

#         except Exception:
#             # Cualquier error (red, timeout, JSON inválido, etc.) → ignorar silenciosamente
#             pass

#         # Devolver último estado bueno, o {} si nunca se ha cargado nada
#         cached = st.session_state["estado_sectores_cache"]
#         return cached if cached is not None else {}

#     geojson_path = "data/geojson/sector_hidraulico.geojson"
#     if not os.path.exists(geojson_path):
#         st.error(f"❌ GeoJSON no encontrado: {geojson_path}")
#         st.stop()

#     if "geojson_data" not in st.session_state:
#         with open(geojson_path, "r", encoding="utf-8") as f:
#             st.session_state.geojson_data = json.load(f)

#     estado_presion_raw = cargar_estado_desde_github()

#     centro = [24.117124, -110.358397]
#     m = folium.Map(location=centro, zoom_start=12)
#     m.add_child(Fullscreen(position='topleft'))

#     for feature in st.session_state.geojson_data["features"]:
#         nombre = feature["properties"].get("name", "Sin nombre")
#         sector_data = estado_presion_raw.get(nombre, {})
#         valor = sector_data.get("valor", 0.0)
#         fill_color = interpolar_color(valor)
#         fill_opacity = 0.2 + 0.5 * (valor / MAX_PRESION)
#         timestamp = sector_data.get("timestamp", "N/A")
#         rssi = sector_data.get("rssi", "N/A")

#         geom = shape(feature["geometry"])
#         centro_poligono = geom.centroid

#         folium.Marker(
#             location=[centro_poligono.y, centro_poligono.x],
#             icon=folium.DivIcon(
#                 html=f'<div style="font-size:10px;font-weight:bold;color:black;text-align:center">{valor:.2f}kg/cm²</div>'
#             )
#         ).add_to(m)

#         tooltip_html = f"""
#         <b>{nombre}</b>
#         <table style="font-size:11px">
#         <tr><td>Presión:</td><td>{valor:.2f}kg/cm²</td></tr>
#         <tr><td>Hora:</td><td>{timestamp}</td></tr>
#         <tr><td>RSSI:</td><td>{rssi}</td></tr>
#         </table>
#         """

#         folium.GeoJson(
#             feature,
#             style_function=lambda x, fc=fill_color, fo=fill_opacity: {
#                 "fillColor": fc,
#                 "color": "#000",
#                 "weight": 1.5,
#                 "fillOpacity": fo
#             },
#             tooltip=folium.Tooltip(tooltip_html, sticky=True)
#         ).add_to(m)

#     st_folium(m, width="100%", height=550)
    
# # ==============================
# # VISTA 2: EVOLUCIÓN HISTÓRICA
# # ==============================
# elif st.session_state.vista_actual == "historico":

#     st.subheader("💧 Evolución de Presión en Sectores Hidráulicos")

#     @st.cache_data(ttl=3600)
#     def obtener_fechas_disponibles():
#         fechas = []
#         hoy = date.today()
#         for i in range(60):
#             f = hoy - timedelta(days=i)
#             url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{f}.mp4"
#             try:
#                 if requests.head(url, timeout=3).status_code == 200:
#                     fechas.append(f)
#             except:
#                 pass
#         return fechas

#     fechas = obtener_fechas_disponibles()
#     if not fechas:
#         st.warning("⚠️ No hay videos disponibles.")
#         st.stop()

#     seleccion = st.selectbox(
#         "Selecciona un día:",
#         options=fechas,
#         format_func=lambda f: f.strftime("%d-%m-%Y")
#     )

#     video_url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{seleccion}.mp4"

#     st.markdown(
#         f"""
#         <video src="{video_url}" controls style="width:100%; border-radius:8px;"></video>
#         """,
#         unsafe_allow_html=True
#     )
# # # ==============================
# # # VISTA 3: ANÁLISIS DE DATOS
# # # ==============================
# # else:

# #     st.subheader("📊 Análisis Histórico de Presión en Sectores")

# #     @st.cache_data(ttl=300)
# #     def descargar_db():
# #         r = requests.get(DB_RELEASE_URL, timeout=15)
# #         r.raise_for_status()
# #         release_info = r.json()

# #         asset = release_info["assets"][0]
# #         fecha_github = (
# #             datetime.strptime(asset["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
# #             + HORA_MEXICO
# #         )

# #         r_file = requests.get(asset["browser_download_url"], timeout=15)
# #         db_path = "temp_db.db"
# #         with open(db_path, "wb") as f:
# #             f.write(r_file.content)

# #         st.info(
# #             f"Base de datos tomada de GitHub Release. "
# #             f"Fecha de subida (México GMT-6): {fecha_github.strftime('%d/%m/%Y %H:%M')}"
# #         )

# #         return db_path

# #     db_path = descargar_db()

# #     def cargar_datos():
# #         with sqlite3.connect(db_path) as conn:
# #             df = pd.read_sql(
# #                 "SELECT * FROM lecturas ORDER BY id ASC",
# #                 conn
# #             )

# #         df["timestamp"] = pd.to_datetime(
# #             df["timestamp"],
# #             errors="coerce"
# #         ) + HORA_MEXICO

# #         df = df.dropna(subset=["timestamp"])
# #         return df

# #     df = cargar_datos()

# #     dispositivos = df["dispositivo"].unique().tolist()

# #     dispositivos_sel = st.multiselect(
# #         "Sectores",
# #         dispositivos,
# #         default=dispositivos[:3]
# #     )

# #     if st.button("🔄 Cargar"):

# #         df_sel = df[df["dispositivo"].isin(dispositivos_sel)]

# #         if not df_sel.empty:
# #             ultima = df_sel["timestamp"].max()
# #             inicio = ultima - pd.Timedelta(hours=24)
# #         else:
# #             ultima = None
# #             inicio = None

# #         df_sel["fecha_str"] = df_sel["timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S")

# #         chart = (
# #             alt.Chart(df_sel)
# #             .mark_line(point=True)
# #             .encode(
# #                 x=alt.X(
# #                     "timestamp:T",
# #                     title="Fecha y hora",
# #                     scale=alt.Scale(domain=[inicio, ultima])
# #                 ),
# #                 y=alt.Y(
# #                     "valor:Q",
# #                     title="Presión (kg/cm²)"
# #                 ),
# #                 color=alt.Color(
# #                     "dispositivo:N",
# #                     legend=alt.Legend(title="Sector", orient="bottom")
# #                 ),
# #                 tooltip=[
# #                     alt.Tooltip("dispositivo:N", title="Sector"),
# #                     alt.Tooltip("fecha_str:N", title="Fecha"),
# #                     alt.Tooltip("valor:Q", title="Presión", format=".2f")
# #                 ]
# #             )
# #             .interactive()
# #         )

# #         st.altair_chart(chart, use_container_width=True)

# # ==============================
# # VISTA 3: ANÁLISIS DE DATOS
# # ==============================
# else:

#     st.subheader("📊 Análisis Histórico de Presión en Sectores")

#     @st.cache_data(ttl=300)
#     def descargar_db():
#         r = requests.get(DB_RELEASE_URL, timeout=15)
#         r.raise_for_status()
#         release_info = r.json()

#         # Buscar EXPLÍCITAMENTE el archivo correcto
#         asset = next(
#             a for a in release_info["assets"]
#             if a["name"] == "sectores.db"
#         )

#         fecha_github = (
#             datetime.strptime(asset["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
#             + HORA_MEXICO
#         )

#         r_file = requests.get(asset["browser_download_url"], timeout=30)
#         db_path = "temp_db.db"
#         with open(db_path, "wb") as f:
#             f.write(r_file.content)

#         st.info(
#             "Última actualización de Base de datos "
#             f"(México GMT-6): "
#             f"{fecha_github.strftime('%d/%m/%Y %H:%M')}"
#         )

#         return db_path

#     db_path = descargar_db()

#     def cargar_datos():
#         with sqlite3.connect(db_path) as conn:
#             df = pd.read_sql(
#                 "SELECT * FROM lecturas ORDER BY id ASC",
#                 conn
#             )

#         # El timestamp YA está en hora local → no volver a moverlo
#         df["timestamp"] = pd.to_datetime(
#             df["timestamp"],
#             format="%d-%m-%Y %H:%M",
#             errors="coerce"
#         )

#         df = df.dropna(subset=["timestamp"])
#         return df

#     df = cargar_datos()

#     dispositivos = df["dispositivo"].unique().tolist()

#     dispositivos_sel = st.multiselect(
#         "Sectores",
#         dispositivos,
#         default=dispositivos[:3]
#     )

#     if st.button("🔄 Cargar"):

#         df_sel = df[df["dispositivo"].isin(dispositivos_sel)]

#         if not df_sel.empty:
#             ultima = df_sel["timestamp"].max()
#             inicio = ultima - pd.Timedelta(hours=24)
#         else:
#             ultima = None
#             inicio = None

#         df_sel["fecha_str"] = df_sel["timestamp"].dt.strftime(
#             "%d/%m/%Y %H:%M:%S"
#         )

#         chart = (
#             alt.Chart(df_sel)
#             .mark_line(point=True)
#             .encode(
#                 x=alt.X(
#                     "timestamp:T",
#                     title="Fecha y hora",
#                     scale=alt.Scale(domain=[inicio, ultima])
#                 ),
#                 y=alt.Y(
#                     "valor:Q",
#                     title="Presión (kg/cm²)"
#                 ),
#                 color=alt.Color(
#                     "dispositivo:N",
#                     legend=alt.Legend(
#                         title="Sector",
#                         orient="bottom"
#                     )
#                 ),
#                 tooltip=[
#                     alt.Tooltip("dispositivo:N", title="Sector"),
#                     alt.Tooltip("fecha_str:N", title="Fecha"),
#                     alt.Tooltip("valor:Q", title="Presión", format=".2f")
#                 ]
#             )
#             .interactive()
#         )

#         st.altair_chart(chart, use_container_width=True)


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
# FUENTES DE DATOS (GITHUB)
# ==============================
GITHUB_USER = "AlarmasCiateq"
REPO_NAME = "mi-mapa-sectores"
BRANCH = "main"

# URLs corregidas: ¡SIN ESPACIOS!
ESTADO_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/data/estado_sectores.json"
DB_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/releases/latest"

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Sectores Hidráulicos CIATEQ",
    page_icon="💧",
    layout="centered"
)

st.markdown(
    """
    <style>
        /* Ocultar TODO el encabezado superior de Streamlit (menú hamburguesa, etc.) */
        [data-testid="stHeader"] {
            display: none !important;
        }

        /* Ocultar el pie de página completo (incluyendo "Deployed with Streamlit") */
        [data-testid="stFooter"] {
            display: none !important;
        }

        /* Refuerzo: ocultar cualquier botón flotante en esquinas */
        .streamlit-footer,
        .stAppDeployButton,
        div[title="View fullscreen"],
        button[title="View fullscreen"] {
            display: none !important;
        }

        /* Asegurar que nada se salga del contenedor principal */
        #MainMenu, footer, header {
            visibility: hidden !important;
        }
    </style>
    """,
    unsafe_allow_html=True
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

# --- NAVEGACIÓN ---
if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "interactivo"

if st.session_state.vista_actual == "interactivo":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬 Ir a evolución histórica"):
            st.session_state.vista_actual = "historico"
            st.rerun()
    with col2:
        if st.button("📊 Ir a análisis de datos"):
            st.session_state.vista_actual = "analisis"
            st.rerun()

elif st.session_state.vista_actual == "historico":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱ Ir al mapa en tiempo real"):
            st.session_state.vista_actual = "interactivo"
            st.rerun()
    with col2:
        if st.button("📊 Ir a análisis de datos"):
            st.session_state.vista_actual = "analisis"
            st.rerun()

else:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱ Ir al mapa en tiempo real"):
            st.session_state.vista_actual = "interactivo"
            st.rerun()
    with col2:
        if st.button("🎬 Ir a evolución histórica"):
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
        if "estado_sectores_cache" not in st.session_state:
            st.session_state["estado_sectores_cache"] = None
    
        try:
            # Obtener la release más reciente
            r = requests.get(
                f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/releases/latest",
                timeout=10
            )
            r.raise_for_status()
            release = r.json()
    
            # Filtrar assets que sean JSON y tengan el patrón correcto
            assets_json = [
                a for a in release["assets"]
                if a["name"].startswith("estado_sectores_") and a["name"].endswith(".json")
            ]
    
            if not assets_json:
                # No hay ningún JSON versionado → mantener estado anterior
                pass
            else:
                # Ordenar por fecha de actualización (más reciente primero)
                assets_json.sort(key=lambda x: x["updated_at"], reverse=True)
                latest_asset = assets_json[0]
    
                # Descargar con anti-caché
                download_url = latest_asset["browser_download_url"]
                anti_cache_url = f"{download_url}?t={int(datetime.now().timestamp())}"
    
                json_resp = requests.get(anti_cache_url, timeout=10)
                json_resp.raise_for_status()
                nuevo_estado = json_resp.json()
    
                if isinstance(nuevo_estado, dict):
                    st.session_state["estado_sectores_cache"] = nuevo_estado
                    return nuevo_estado
    
        except Exception:
            # Silencioso ante cualquier error
            pass
    
        # Devolver caché o vacío si nunca se cargó
        cached = st.session_state["estado_sectores_cache"]
        return cached if cached is not None else {}
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
        valor = sector_data.get("valor", 0.0)
        fill_color = interpolar_color(valor)
        fill_opacity = 0.2 + 0.5 * (valor / MAX_PRESION)
        timestamp = sector_data.get("timestamp", "N/A")
        rssi = sector_data.get("rssi", "N/A")

        geom = shape(feature["geometry"])
        centro_poligono = geom.centroid

        folium.Marker(
            location=[centro_poligono.y, centro_poligono.x],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:black;text-align:center">{valor:.2f}kg/cm²</div>'
            )
        ).add_to(m)

        tooltip_html = f"""
        <b>{nombre}</b>
        <table style="font-size:11px">
        <tr><td>Presión:</td><td>{valor:.2f}kg/cm²</td></tr>
        <tr><td>Hora:</td><td>{timestamp}</td></tr>
        <tr><td>RSSI:</td><td>{rssi}</td></tr>
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
    
# ==============================
# VISTA 2: EVOLUCIÓN HISTÓRICA
# ==============================
elif st.session_state.vista_actual == "historico":

    st.subheader("💧 Evolución de Presión en Sectores Hidráulicos")

    @st.cache_data(ttl=3600)
    def obtener_fechas_disponibles():
        fechas = []
        hoy = date.today()
        for i in range(60):
            f = hoy - timedelta(days=i)
            url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{f}.mp4"
            try:
                if requests.head(url, timeout=3).status_code == 200:
                    fechas.append(f)
            except:
                pass
        return fechas

    fechas = obtener_fechas_disponibles()
    if not fechas:
        st.warning("⚠️ No hay videos disponibles.")
        st.stop()

    seleccion = st.selectbox(
        "Selecciona un día:",
        options=fechas,
        format_func=lambda f: f.strftime("%d-%m-%Y")
    )

    video_url = f"https://{GITHUB_USER}.github.io/{REPO_NAME}/hidro-videos/presion_{seleccion}.mp4"

    st.markdown(
        f"""
        <video src="{video_url}" controls style="width:100%; border-radius:8px;"></video>
        """,
        unsafe_allow_html=True
    )

# ==============================
# VISTA 3: ANÁLISIS DE DATOS
# ==============================
else:

    st.subheader("📊 Análisis Histórico de Presión en Sectores")

    @st.cache_data(ttl=300)
    def descargar_db():
        try:
            r = requests.get(DB_RELEASE_URL, timeout=15)
            # No usar r.raise_for_status() directamente; manejar el estado
            if r.status_code != 200:
                st.error("⚠️ No se pudo acceder a la Release de GitHub. Código de error: " + str(r.status_code))
                st.stop()

            release_info = r.json()

            # Verificar que haya assets
            assets = release_info.get("assets", [])
            if not assets:
                st.error("❌ No hay archivos en la Release. Espera a que el monitor suba los datos.")
                st.stop()

            # Buscar EXPLÍCITAMENTE el archivo correcto
            asset = None
            for a in assets:
                if a["name"] == "sectores.db":
                    asset = a
                    break

            if not asset:
                st.error("❌ No se encontró 'sectores.db' en la Release.")
                st.stop()

            fecha_github = (
                datetime.strptime(asset["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                + HORA_MEXICO
            )

            r_file = requests.get(asset["browser_download_url"], timeout=30)
            if r_file.status_code != 200:
                st.error("❌ Error al descargar la base de datos.")
                st.stop()

            db_path = "temp_db.db"
            with open(db_path, "wb") as f:
                f.write(r_file.content)

            st.info(
                "Última actualización de Base de datos "
                f"(México GMT-6): "
                f"{fecha_github.strftime('%d/%m/%Y %H:%M')}"
            )

            return db_path

        except requests.exceptions.Timeout:
            st.error("⏰ Tiempo de espera agotado al conectar con GitHub.")
            st.stop()
        except requests.exceptions.RequestException as e:
            st.error("🌐 Error de red al acceder a GitHub.")
            st.stop()
        except ValueError:
            st.error("📅 Error al procesar la fecha de la Release.")
            st.stop()
        except Exception as e:
            st.error("⚠️ Error inesperado al cargar la base de datos.")
            st.stop()

    db_path = descargar_db()

    def cargar_datos():
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(
                "SELECT * FROM lecturas ORDER BY id ASC",
                conn
            )

        # El timestamp YA está en hora local → no volver a moverlo
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            format="%d-%m-%Y %H:%M",
            errors="coerce"
        )

        df = df.dropna(subset=["timestamp"])
        return df

    df = cargar_datos()

    dispositivos = df["dispositivo"].unique().tolist()

    dispositivos_sel = st.multiselect(
        "Sectores",
        dispositivos,
        default=dispositivos[:3]
    )

    if st.button("🔄 Cargar"):

        df_sel = df[df["dispositivo"].isin(dispositivos_sel)]

        if not df_sel.empty:
            ultima = df_sel["timestamp"].max()
            inicio = ultima - pd.Timedelta(hours=24)
        else:
            ultima = None
            inicio = None

        df_sel["fecha_str"] = df_sel["timestamp"].dt.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        chart = (
            alt.Chart(df_sel)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "timestamp:T",
                    title="Fecha y hora",
                    scale=alt.Scale(domain=[inicio, ultima])
                ),
                y=alt.Y(
                    "valor:Q",
                    title="Presión (kg/cm²)"
                ),
                color=alt.Color(
                    "dispositivo:N",
                    legend=alt.Legend(
                        title="Sector",
                        orient="bottom"
                    )
                ),
                tooltip=[
                    alt.Tooltip("dispositivo:N", title="Sector"),
                    alt.Tooltip("fecha_str:N", title="Fecha"),
                    alt.Tooltip("valor:Q", title="Presión", format=".2f")
                ]
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)



