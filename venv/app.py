import streamlit as st
import io
import json
import subprocess
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# Importa as dependências do Firebase do arquivo firebase_client.py
from firebase_client import install

# ---- INSTALAÇÃOa DE DEPENDÊNCIAS DO FIREBASE ----
try:
    from firebase_admin import credentials, firestore, initialize_app, auth
except ImportError:
    st.info("Instalando a biblioteca firebase-admin...")
    install("firebase-admin")
    from firebase_admin import credentials, firestore, initialize_app, auth

# ---- FIREBASE & FIRESTORE SETUP ----
db = None
auth_client = None
cred = None

try:
    if '__firebase_config' not in globals():
        st.error("Variável de configuração do Firebase não encontrada. Verifique as configurações do ambiente.")
    else:
        firebase_config = json.loads(__firebase_config)
        if isinstance(firebase_config, str):
            firebase_config = json.loads(firebase_config)
        cred = credentials.Certificate(firebase_config)
except json.JSONDecodeError:
    st.error("Erro ao decodificar a configuração do Firebase. A configuração não é um JSON válido.")
except Exception as e:
    st.error(f"Erro ao carregar a configuração do Firebase: {e}")

if cred:
    try:
        initialize_app(cred)
        db = firestore.client()
        auth_client = auth
    except ValueError:
        st.info("Firebase já está inicializado.")
        db = firestore.client()
        auth_client = auth
    except Exception as e:
        st.error(f"Erro ao inicializar o Firebase: {e}")

st.set_page_config(page_title="Estimador de Obras - MVP", layout="wide")

# ---- GLOBAL STATE ----
if 'show_download_buttons' not in st.session_state:
    st.session_state['show_download_buttons'] = False

st.title("🏗️ Estimador de Obras — MVP")

# ---------------------------
# Plaster calculation function
# ---------------------------
def calculate_plaster(length, height, sides, thickness_cm, yield_bag, bag_price, labor_price_m2, sand_ratio=4):
    """
    Calculates the costs and materials for wall plaster.
    """
    area = length * height * sides
    thickness_m = thickness_cm / 100
    volume = area * thickness_m

    cement_bags = area / yield_bag
    cement_cost = cement_bags * bag_price

    cement_volume = cement_bags * 0.035
    sand_volume = cement_volume * sand_ratio

    labor_cost = area * labor_price_m2

    return {
        "area": area,
        "volume": volume,
        "cement_bags": cement_bags,
        "cement_cost": cement_cost,
        "sand_volume": sand_volume,
        "labor_cost": labor_cost,
        "total_cost": cement_cost + labor_cost
    }

# ---------------------------
# Streamlit Interface
# ---------------------------
st.subheader("🧱 Cálculo de Reboco de Parede")

length = st.number_input("Comprimento da parede (m)", value=8.0, step=0.5)
height = st.number_input("Altura da parede (m)", value=2.2, step=0.1)
sides = st.selectbox(
    "Lados a serem rebocados",
    options=[1, 2],
    format_func=lambda x: "Apenas um lado" if x == 1 else "Ambos os lados"
)
thickness = st.number_input("Espessura do reboco (cm)", value=2.0, step=0.5)
yield_rate = st.number_input("Rendimento do saco de cimento (m²)", value=4.5, step=0.1)
bag_price = st.number_input("Preço do saco de cimento (R$)", value=35.0, step=1.0)
labor_price = st.number_input("Preço da mão de obra por m² (R$)", value=25.0, step=1.0)

if st.button("Calcular Reboco"):
    result = calculate_plaster(length, height, sides, thickness, yield_rate, bag_price, labor_price)

    st.success(f"Área Total: **{result['area']:.2f} m²**")
    st.write(f"Volume de Reboco: **{result['volume']:.3f} m³**")
    st.write(f"Sacos de Cimento: **{result['cement_bags']:.1f} sacos** (R$ {result['cement_cost']:.2f})")
    st.write(f"Volume de Areia: **{result['sand_volume']:.3f} m³**")
    st.write(f"Custo da Mão de Obra: **R$ {result['labor_cost']:.2f}**")
    st.markdown(f"### 💰 Custo Total Estimado: R$ {result['total_cost']:.2f}")

    if st.button("💾 Salvar Estimativa no Banco de Dados"):
        if not db:
            st.error("Não é possível salvar. Banco de dados não disponível.")
        else:
            user_id = "default_user"
            app_id = __app_id if '__app_id' in globals() else 'default_app_id'
            
            try:
                estimate_ref = db.collection(f"artifacts/{app_id}/users/{user_id}/estimates").add({
                    "user_id": user_id,
                    "description": f"Reboco de parede ({length}x{height}m)",
                    "value": result['total_cost'],
                    "created_at": datetime.utcnow(),
                    "details": result
                })
                st.success(f"✅ Estimativa salva com sucesso! ID: {estimate_ref[1].id}")
                st.session_state['show_download_buttons'] = True
            except Exception as e:
                st.error(f"Erro ao salvar a estimativa: {e}")

    if st.session_state.get('show_download_buttons'):
        
        # ---- DOWNLOAD DE PDF ----
        def create_pdf_bytes_plaster(result):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            x, y = 50, 800
            c.setFont("Helvetica-Bold", 14)
            c.drawString(x, y, "Estimativa de Obra — Reboco")
            y -= 30
            c.setFont("Helvetica", 10)
            c.drawString(x, y, f"Área Total: {result['area']:.2f} m²")
            y -= 15
            c.drawString(x, y, f"Volume de Reboco: {result['volume']:.3f} m³")
            y -= 15
            c.drawString(x, y, f"Sacos de Cimento: **{result['cement_bags']:.1f} sacos** (R$ {result['cement_cost']:.2f})")
            y -= 15
            c.drawString(x, y, f"Volume de Areia: **{result['sand_volume']:.3f} m³**")
            y -= 15
            c.drawString(x, y, f"Custo da Mão de Obra: **R$ {result['labor_cost']:.2f}**")
            y -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, f"Custo Total Estimado: R$ {result['total_cost']:.2f}")
            c.save()
            buffer.seek(0)
            return buffer.getvalue()

        pdf_bytes = create_pdf_bytes_plaster(result)
        st.download_button("📄 Baixar Estimativa em PDF", data=pdf_bytes, file_name="plaster_estimate.pdf", mime="application/pdf")

# ---- HISTÓRICO DE ORÇAMENTOS SALVOS ----
st.subheader("📜 Orçamentos Salvos")

if not db:
    st.warning("Não é possível exibir os orçamentos. Banco de dados não disponível.")
else:
    user_id = "default_user"
    app_id = __app_id if '__app_id' in globals() else 'default_app_id'

    try:
        estimates_stream = db.collection(f"artifacts/{app_id}/users/{user_id}/estimates").stream()
        estimates = [doc.to_dict() for doc in estimates_stream]
    
        if estimates:
            for e in estimates:
                created_at = e.get('created_at', datetime.utcnow())
                if hasattr(created_at, 'strftime'):
                    created_at_str = created_at.strftime('%d/%m/%Y %H:%M')
                else:
                    created_at_str = "N/A"
                
                with st.expander(f"Estimativa de Reboco - {created_at_str}"):
                    st.write(f"**Descrição:** {e['description']}")
                    st.write(f"**Valor:** R$ {e['value']:.2f}")
                    if 'details' in e:
                        st.subheader("Detalhes")
                        st.write(f"Área Total: **{e['details']['area']:.2f} m²**")
                        st.write(f"Volume de Reboco: **{e['details']['volume']:.3f} m³**")
                        st.write(f"Sacos de Cimento: **{e['details']['cement_bags']:.1f} sacos** (R$ {e['details']['cement_cost']:.2f})")
                        st.write(f"Volume de Areia: **{e['details']['sand_volume']:.3f} m³**")
                        st.write(f"Custo da Mão de Obra: **R$ {e['details']['labor_cost']:.2f}**")
        else:
            st.info("Nenhuma estimativa foi salva ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar as estimativas: {e}")
