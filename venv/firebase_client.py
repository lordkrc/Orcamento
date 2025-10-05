import streamlit as st
import subprocess
import sys

# ---- INSTALAÇÃO DE DEPENDÊNCIAS ----
def install(package):
    """Instala uma biblioteca se ela ainda não estiver presente."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from firebase_admin import credentials, firestore, initialize_app, auth
except ImportError:
    st.info("Instalando a biblioteca firebase-admin...")
    install("firebase-admin")
    from firebase_admin import credentials, firestore, initialize_app, auth
