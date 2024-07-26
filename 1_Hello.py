import streamlit as st
from _init_ import start_app

st.set_page_config(
    page_title="Multi Modal Authentication Demo App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)
start_app()
st.header("UNIVERSITY OF ZIMBABWE", divider='rainbow')
col1, col2 = st.columns(2)

with col1:
    st.image('assets/logo.png', width=300)

with col2:
    st.markdown(
        """
                ### Student Details
                - Name: Linos Judah Tafireyi
                - Student Number: R053007M
                - Programme: MSC In Cybersecurity
                ### Topic
                A mutative multimodal biometric authentication models to enhance data 
                security in online customer banking systems.
            """
    )
