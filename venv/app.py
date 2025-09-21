import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

# ---- BANCO DE DADOS ----
from db import get_session
from models import Estimate, LineItem, Orcamento

# Inicializa a sessão do banco de dados
session: Session = next(get_session())

st.set_page_config(page_title="Estimador de Obras - MVP", layout="wide")

# ---- ESTADO GLOBAL ----
if 'items' not in st.session_state:
    st.session_state['items'] = []

st.title("🏗️ Estimador de Obras — MVP")

# ---------------------------
# Função para cálculo do reboco
# ---------------------------
def calcular_reboco(comprimento, altura, espessura_cm, rendimento_saco, preco_saco, preco_mao_obra_m2, traco_areia=4):
    """
    Calcula os custos e materiais para o reboco de uma parede.

    Args:
        comprimento (float): Comprimento da parede em metros.
        altura (float): Altura da parede em metros.
        espessura_cm (float): Espessura do reboco em centímetros.
        rendimento_saco (float): Rendimento de um saco de cimento em m².
        preco_saco (float): Preço de um saco de cimento.
        preco_mao_obra_m2 (float): Preço da mão de obra por m².
        traco_areia (int, optional): Traço de areia em relação ao cimento. Padrão para 4.

    Returns:
        dict: Um dicionário com todos os resultados do cálculo.
    """
    area = comprimento * altura
    espessura_m = espessura_cm / 100
    volume = area * espessura_m

    sacos_cimento = area / rendimento_saco
    custo_cimento = sacos_cimento * preco_saco

    volume_cimento = sacos_cimento * 0.035  # 0.035 m³ por saco
    volume_areia = volume_cimento * traco_areia

    custo_mao_obra = area * preco_mao_obra_m2

    return {
        "area": area,
        "volume": volume,
        "sacos_cimento": sacos_cimento,
        "custo_cimento": custo_cimento,
        "volume_areia": volume_areia,
        "custo_mao_obra": custo_mao_obra,
        "custo_total": custo_cimento + custo_mao_obra
    }

# ---------------------------
# Interface Streamlit do Reboco
# ---------------------------
st.subheader("🧱 Cálculo de Reboco de Muro")

comprimento = st.number_input("Comprimento do muro (m)", value=8.0, step=0.5)
altura = st.number_input("Altura do muro (m)", value=2.2, step=0.1)
espessura = st.number_input("Espessura do reboco (cm)", value=2.0, step=0.5)
rendimento = st.number_input("Rendimento por saco de cimento (m²)", value=4.5, step=0.1)
preco_saco = st.number_input("Preço do saco de cimento (R$)", value=35.0, step=1.0)
preco_mao_obra = st.number_input("Preço da mão de obra por m² (R$)", value=25.0, step=1.0)

if st.button("Calcular Reboco"):
    resultado = calcular_reboco(comprimento, altura, espessura, rendimento, preco_saco, preco_mao_obra)

    st.success(f"Área Total: **{resultado['area']:.2f} m²**")
    st.write(f"Volume de Reboco: **{resultado['volume']:.3f} m³**")
    st.write(f"Sacos de Cimento: **{resultado['sacos_cimento']:.1f} sacos** (R$ {resultado['custo_cimento']:.2f})")
    st.write(f"Volume de Areia: **{resultado['volume_areia']:.3f} m³**")
    st.write(f"Custo de Mão de Obra: **R$ {resultado['custo_mao_obra']:.2f}**")
    st.markdown(f"### 💰 Custo Total Estimado: R$ {resultado['custo_total']:.2f}")

    # Opção de salvar no banco de dados
    if st.button("💾 Salvar Orçamento de Reboco no Banco"):
        novo_orcamento = Orcamento(
            descricao=f"Reboco de muro ({comprimento}x{altura}m)",
            valor=resultado['custo_total']
        )
        session.add(novo_orcamento)
        session.commit()
        st.success("✅ Orçamento de Reboco salvo com sucesso!")

st.markdown("---")

# ---- BARRA LATERAL (CONFIGURAÇÕES) ----
with st.sidebar:
    st.header("Configurações")
    st.session_state['labor_rate'] = st.number_input("Valor por hora de mão-de-obra (R$)", value=25.0, step=1.0)
    st.session_state['tax_pct'] = st.number_input("Imposto (%)", value=0.0, step=0.1)
    st.session_state['overhead_pct'] = st.number_input("Despesas/Overhead (%)", value=10.0, step=0.1)
    st.session_state['profit_pct'] = st.number_input("Margem de Lucro (%)", value=10.0, step=0.1)

# ---- FORMULÁRIO DE ITENS ----
with st.form("adiciona_item"):
    st.subheader("Adicionar Item ao Orçamento")
    desc = st.text_input("Descrição")
    qty = st.number_input("Quantidade", min_value=0.0, value=1.0, step=0.1)
    unit = st.text_input("Unidade", value="un")
    unit_price = st.number_input("Preço Unitário (R$)", min_value=0.0, value=0.0, step=0.1)
    labor_hours = st.number_input("Horas de Mão de Obra por Unidade", min_value=0.0, value=0.0, step=0.1)
    add = st.form_submit_button("Adicionar Item")
    if add:
        st.session_state['items'].append({
            "desc": desc,
            "qty": float(qty),
            "unit": unit,
            "unit_price": float(unit_price),
            "labor_hours": float(labor_hours)
        })

# ---- EXIBE ITENS ----
if st.session_state['items']:
    df = pd.DataFrame(st.session_state['items'])
    df['material_cost'] = df['qty'] * df['unit_price']
    df['labor_cost'] = df['qty'] * df['labor_hours'] * st.session_state['labor_rate']
    df['subtotal'] = df['material_cost'] + df['labor_cost']

    st.subheader("Itens Adicionados")
    df_display = df.rename(columns={
        'desc': 'Descrição',
        'qty': 'Quantidade',
        'unit': 'Unidade',
        'unit_price': 'Preço Unitário',
        'labor_hours': 'Horas de Mão de Obra',
        'material_cost': 'Custo de Material',
        'labor_cost': 'Custo de Mão de Obra',
        'subtotal': 'Subtotal'
    })
    st.dataframe(df_display[['Descrição','Quantidade','Unidade','Preço Unitário','Horas de Mão de Obra','Custo de Material','Custo de Mão de Obra','Subtotal']],
                 use_container_width=True)

    # ---- CÁLCULOS ----
    subtotal = float(df['subtotal'].sum())
    overhead = subtotal * (st.session_state['overhead_pct']/100)
    profit = subtotal * (st.session_state['profit_pct']/100)
    tax = (subtotal + overhead + profit) * (st.session_state['tax_pct']/100)
    total = subtotal + overhead + profit + tax

    st.markdown(f"**Subtotal:** R$ {subtotal:,.2f}")
    st.markdown(f"**Overhead ({st.session_state['overhead_pct']}%):** R$ {overhead:,.2f}")
    st.markdown(f"**Lucro ({st.session_state['profit_pct']}%):** R$ {profit:,.2f}")
    st.markdown(f"**Imposto ({st.session_state['tax_pct']}%):** R$ {tax:,.2f}")
    st.markdown(f"### 💰 Total: R$ {total:,.2f}")

    # ---- BOTÃO DE SALVAR NO BANCO ----
    if st.button("💾 Salvar Orçamento no Banco"):
        estimate = Estimate(client="Cliente Padrão")
        session.add(estimate)
        session.commit()

        for row in df.to_dict(orient="records"):
            item = LineItem(
                estimate_id=estimate.id,
                description=row['desc'],
                qty=row['qty'],
                unit=row['unit'],
                unit_price=row['unit_price'],
                labor_hours=row['labor_hours']
            )
            session.add(item)
        session.commit()
        st.success(f"✅ Orçamento salvo com ID {estimate.id}")
        st.session_state['items'] = []

    # ---- DOWNLOAD CSV ----
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Itens (CSV)", data=csv, file_name="itens.csv", mime="text/csv")

    # ---- DOWNLOAD PDF ----
    def create_pdf_bytes(df, subtotal, overhead, profit, tax, total):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        x, y = 50, 800
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Orçamento de Obra — MVP")
        y -= 30
        c.setFont("Helvetica", 10)
        for idx, row in df.iterrows():
            text = f"{idx+1}. {row['desc']} — {row['qty']}{row['unit']} x R$ {row['unit_price']:.2f} — {row['labor_hours']}h/un"
            c.drawString(x, y, text)
            y -= 15
            if y < 80:
                c.showPage()
                y = 800
        y -= 10
        c.drawString(x, y, f"Subtotal: R$ {subtotal:,.2f}")
        y -= 15
        c.drawString(x, y, f"Despesas/Overhead: R$ {overhead:,.2f}")
        y -= 15
        c.drawString(x, y, f"Lucro: R$ {profit:,.2f}")
        y -= 15
        c.drawString(x, y, f"Impostos: R$ {tax:,.2f}")
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, f"Total: R$ {total:,.2f}")
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    pdf_bytes = create_pdf_bytes(df, subtotal, overhead, profit, tax, total)
    st.download_button("📄 Baixar Orçamento (PDF)", data=pdf_bytes, file_name="orcamento.pdf", mime="application/pdf")

# ---- HISTÓRICO DE ORÇAMENTOS ----
st.subheader("📜 Orçamentos Salvos")
estimates = session.query(Estimate).all()
orcamentos = session.query(Orcamento).all()

if estimates or orcamentos:
    for e in estimates:
        with st.expander(f"Orçamento Geral #{e.id} - {e.created_at.strftime('%d/%m/%Y %H:%M')}"):
            st.markdown(f"**Cliente:** {e.client}")
            data = [[item.description, item.qty, item.unit, item.unit_price, item.labor_hours] for item in e.items]
            df_items = pd.DataFrame(data, columns=["Descrição", "Qtd", "Unidade", "Preço Unitário", "Horas Mão de Obra"])
            st.dataframe(df_items, use_container_width=True)

    for o in orcamentos:
        with st.expander(f"Orçamento de Reboco #{o.id} - {o.created_at.strftime('%d/%m/%Y %H:%M')}"):
            st.write(f"**Descrição:** {o.descricao}")
            st.write(f"**Valor:** R$ {o.valor:.2f}")

else:
    st.info("Nenhum orçamento foi salvo ainda.")
