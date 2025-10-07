# utils/helpers.py
import os
import streamlit as st
import base64

def get_image_base64(image_path):
    """Convierte una imagen a base64."""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def add_logo_sidebar():
    """Agrega el logo de CIATEQ fijo abajo a la izquierda."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(project_root, "assets", "LOGO CIATEQ.png")
    
    logo_base64 = get_image_base64(logo_path)
    
    # if logo_base64:
    #     st.sidebar.markdown(
    #         f"""
    #         <div style="
    #             position: fixed;
    #             bottom: 10px;
    #             left: 15px;
    #             width: 100px;
    #             height: 100px;
    #             z-index: 1000;
    #             display: flex;
    #             align-items: center;
    #             justify-content: center;
    #         ">
    #             <img src='data:image/png;base64,{logo_base64}' 
    #                  width='100' 
    #                  style="border-radius: 8px;">
    #         </div>
    #         """,
    #         unsafe_allow_html=True
    #     )
    
    # Texto arriba a la derecha
    # st.sidebar.markdown(
    #     """
    #     <div style="
    #         position: fixed;
    #         top: 10px;
    #         right: 15px;
    #         z-index: 999;
    #         text-align: center;
    #         color: white;
    #         font-size: 0.7em;
    #         background-color: #111;
    #         padding: 5px 10px;
    #         border-radius: 8px;
    #     ">
    #         © 2025 CIATEQ®
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )