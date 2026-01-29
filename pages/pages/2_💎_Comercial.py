import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta
import numpy as np

# --- BLOQUEIO DE SEGURANÇA ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Acesso não autorizado. Por favor, faça login.")
    st.stop()
# -----------------------------

# --- 1. CONFIGURAÇÃO VISUAL "ELITE" ---
st.set_page_config(page_title="blue . Commercial", layout="wide", page_icon="🟦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp { background-color: #0b1120; color: #e6f1ff; font-family: 'Inter', sans-serif; }
    
    /* Logo Premium */
    .blue-logo { font-family: 'Inter', sans-serif; font-weight: 200; font-size: 3.5rem; color: #e6f1ff; letter-spacing: -3px; margin-bottom: -15px; text-shadow: 0 0 10px rgba(0, 242, 255, 0.3); }
    .blue-dot { color: #00f2ff; font-weight: bold; }
    .blue-sub { font-family: 'Inter', sans-serif; font-weight: 400; font-size: 0.9rem; letter-spacing: 4px; color: #00f2ff; text-transform: uppercase; margin-left: 5px; opacity: 0.9; }
    
    /* Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #161b2e 0%, #0b1120 100%);
        border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800 !important; color: #fff !important; }
    
    /* Status Tags na Tabela */
    .status-tag { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(90deg, #00f2ff 0%, #0066ff 100%); 
        color: #fff; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase;
        width: 100%; transition: all 0.3s ease;
    }
    .stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(0, 242, 255, 0.5); }
    
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stDateInput input, .stTextArea textarea {
        background-color: #1f2937 !important; color: #fff !important; border: 1px solid #374151 !important; border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DADOS & CRM ---
DATA_FILE_CRM = "comercial_blue.csv"

def load_crm():
    if os.path.exists(DATA_FILE_CRM):
        return pd.read_csv(DATA_FILE_CRM)
    else:
        # Dados Iniciais (Exemplo Baseado no PDF)
        return pd.DataFrame({
            "Nome": ["Laita Biano", "Maria Exemplo"],
            "Status": ["Em Negociação", "Fechado"],
            "Data Consulta": [datetime.now().strftime("%Y-%m-%d"), "2026-01-10"],
            "Hospital": ["Copa Star", "Perinatal"],
            "Valor Total": [50000.00, 42000.00],
            "Pago": [0.00, 42000.00],
            "Plano Saúde": ["Não", "Sim (Reembolso)"],
            "Obs": ["Gostou do Dr., avaliando formas de pgto.", "Cirurgia marcada Fev/26"]
        })

def save_crm(df):
    df.to_csv(DATA_FILE_CRM, index=False)

if 'crm' not in st.session_state: st.session_state.crm = load_crm()
df = st.session_state.crm.copy()

# Cálculo de Funil
total_leads = len(df)
fechados = len(df[df['Status'] == "Fechado"])
conversao = (fechados / total_leads * 100) if total_leads > 0 else 0
pendente_pgto = df['Valor Total'].sum() - df['Pago'].sum()

# --- 3. INTERFACE LATERAL ---
with st.sidebar:
    st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Commercial Intelligence</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 🎯 Performance")
    c1, c2 = st.columns(2)
    c1.metric("Conversão", f"{conversao:.1f}%")
    c2.metric("Pacientes", f"{total_leads}")
    st.metric("A Receber (Pipeline)", f"R$ {pendente_pgto:,.2f}")
    
    st.markdown("---")
    menu = st.radio("MENU", ["Pipeline & Gestão", "Simulador de Orçamento", "Blue AI (Sales Coach)", "Integrações"])
    
    st.markdown("---")
    # Botão Rápido TimeTree (ALTERADO AQUI)
    agenda_url = "https://treeapp.com/" 
    st.markdown(f"""
    <a href="{agenda_url}" target="_blank" style="text-decoration: none;">
        <div style="background: #1e293b; color: #fff; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #00f2ff;">
        📅 Agendar (TimeTree)
        </div>
    </a>
    """, unsafe_allow_html=True)

# --- ABA 1: PIPELINE & GESTÃO ---
if menu == "Pipeline & Gestão":
    st.title("Gestão de Pacientes")
    
    # Filtros
    c1, c2, c3 = st.columns([1, 1, 2])
    f_status = c1.multiselect("Status", ["Primeira Consulta", "Em Negociação", "Pensando", "Fechado", "Cirurgia Realizada", "Lost"])
    f_hosp = c2.multiselect("Hospital", ["Copa Star", "Perinatal", "Barra D'or", "Outro"])
    search = c3.text_input("Buscar Paciente")
    
    df_view = df.copy()
    if f_status: df_view = df_view[df_view['Status'].isin(f_status)]
    if f_hosp: df_view = df_view[df_view['Hospital'].isin(f_hosp)]
    if search: df_view = df_view[df_view['Nome'].str.contains(search, case=False)]

    # Kanban Simplificado (Métricas por Status)
    st.markdown("#### 📊 Status do Funil")
    cols = st.columns(4)
    status_counts = df['Status'].value_counts()
    cols[0].metric("1ª Consulta", status_counts.get("Primeira Consulta", 0))
    cols[1].metric("Em Negociação", status_counts.get("Em Negociação", 0))
    cols[2].metric("Fechados", status_counts.get("Fechado", 0))
    cols[3].metric("Aguardando Decisão", status_counts.get("Pensando", 0))
    
    st.markdown("---")
    
    # Tabela Editável (O Coração do CRM)
    st.info("💡 Edite o status, valores e pagamentos diretamente na tabela abaixo.")
    
    edited_df = st.data_editor(
        df_view,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Valor Total": st.column_config.NumberColumn(format="R$ %.2f"),
            "Pago": st.column_config.NumberColumn(format="R$ %.2f"),
            "Status": st.column_config.SelectboxColumn(
                options=["Primeira Consulta", "Em Negociação", "Pensando", "Fechado", "Cirurgia Realizada", "Lost"],
                required=True
            ),
            "Hospital": st.column_config.SelectboxColumn(options=["Copa Star", "Perinatal", "Barra D'or", "Outro"]),
            "Plano Saúde": st.column_config.SelectboxColumn(options=["Não", "Sim (Reembolso)", "Sim (Direto)"]),
            "Data Consulta": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Obs": st.column_config.TextColumn(width="large")
        }
    )
    
    if not edited_df.equals(df_view):
        if st.button("💾 ATUALIZAR CRM", type="primary"):
            st.session_state.crm = edited_df
            save_crm(st.session_state.crm)
            st.success("Base de pacientes atualizada!")
            st.rerun()

# --- ABA 2: SIMULADOR DE ORÇAMENTO ---
elif menu == "Simulador de Orçamento":
    st.title("Simulador de Cirurgia LipeDefinition®")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("1. Equipe & Estrutura")
        # Valores baseados no PDF Laita Biano
        v_anestesia = st.number_input("Anestesista", value=4000.0)
        v_auxiliar = st.number_input("Cirurgião Auxiliar", value=3000.0)
        v_instrument = st.number_input("Instrumentadora", value=1150.0)
        
        hosp_opt = st.selectbox("Hospital", ["Perinatal Barra", "Barra D'or", "Copa Star", "Outro"])
        # Lógica de preços do PDF
        if hosp_opt == "Perinatal Barra": v_hosp = 5988.00
        elif hosp_opt == "Barra D'or": v_hosp = 14000.92
        elif hosp_opt == "Copa Star": v_hosp = 23108.00
        else: v_hosp = 0.0
        v_hosp_input = st.number_input("Valor Hospital (Estimado)", value=v_hosp)
        
    with c2:
        st.subheader("2. Tecnologias & Pós")
        chk_argo = st.checkbox("Argoplasma®", value=True)
        chk_morph = st.checkbox("Morpheus®", value=True)
        
        v_argo = st.number_input("Valor Argoplasma", value=17700.0 if chk_argo else 0.0)
        v_morph = st.number_input("Valor Morpheus", value=17700.0 if chk_morph else 0.0)
        
        v_fisio = st.number_input("Fisioterapia (15 sessões)", value=10050.0)
        v_extra = st.number_input("Outros (Meias, Compressor)", value=2000.0)

    st.markdown("---")
    
    # Cálculos Finais
    total_equipe = v_anestesia + v_auxiliar + v_instrument
    total_tec = v_argo + v_morph + v_fisio + v_extra
    grand_total = total_equipe + total_tec + v_hosp_input
    
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        st.markdown("### Resumo do Investimento")
        st.write(f"**Equipe Cirúrgica:** R$ {total_equipe:,.2f}")
        st.write(f"**Hospital ({hosp_opt}):** R$ {v_hosp_input:,.2f}")
        st.write(f"**Tecnologias e Pós:** R$ {total_tec:,.2f}")
        
    with col_res2:
        st.markdown(f"""
        <div style="background: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #00f2ff; text-align: center;">
            <p style="color: #94a3b8; font-size: 0.9rem; text-transform: uppercase;">INVESTIMENTO TOTAL ESTIMADO</p>
            <p style="color: #fff; font-size: 2.5rem; font-weight: bold;">R$ {grand_total:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        desconto = st.slider("Aplicar Desconto (%)", 0, 20, 0)
        if desconto > 0:
            val_desc = grand_total * (1 - (desconto/100))
            st.success(f"Valor com Desconto: R$ {val_desc:,.2f}")
            if st.button("Copiar Proposta para CRM"):
                new_lead = {"Nome": "Novo Paciente (Simulação)", "Status": "Em Negociação", "Valor Total": val_desc, "Hospital": hosp_opt, "Pago": 0.0, "Data Consulta": datetime.now().strftime("%Y-%m-%d"), "Obs": "Orçamento gerado via Simulador"}
                st.session_state.crm = pd.concat([st.session_state.crm, pd.DataFrame([new_lead])], ignore_index=True)
                save_crm(st.session_state.crm)
                st.toast("Enviado para o Pipeline!", icon="✅")

# --- ABA 3: BLUE AI (SALES COACH) ---
elif menu == "Blue AI (Sales Coach)":
    st.title("🤖 Blue Sales Intelligence")
    st.caption("Assistente de IA para contorno de objeções e scripts de alta conversão.")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Cenário")
        objecao = st.selectbox("Objeção Principal", [
            "Achou o valor alto",
            "Vai pensar/Falar com marido",
            "Quer fazer pelo plano (sem reembolso)",
            "Comparando com outro médico",
            "Medo do pós-operatório"
        ])
        perfil = st.selectbox("Perfil da Paciente", ["Analítica (quer dados)", "Emocional (quer sonho)", "Executiva (quer rapidez)"])
        
    with c2:
        st.subheader("Gerar Resposta (Simulação Gemini)")
        if st.button("✨ Gerar Script de Venda"):
            resposta = ""
            if "valor alto" in objecao.lower():
                resposta = """**Sugestão (Valor x Preço):** "Entendo, [Nome]. Realmente é um investimento. Porém, estamos falando do método *LipeDefinition®* com tecnologias que tratam a flacidez. Se dividirmos esse valor pelo tempo que você convive com o Lipedema, o custo é mínimo perto da sua liberdade." """
            elif "marido" in objecao.lower():
                resposta = """**Sugestão (Marido):** "É uma decisão familiar importante. O que acha de trazê-lo no retorno? Quando eles entendem que é saúde e não só estética, tornam-se os maiores apoiadores." """
            else:
                resposta = """**Sugestão:** "Lembre-se da segurança da Blue Clinic e dos hospitais de ponta. Qual sua maior dúvida para fecharmos hoje?" """
            
            st.info(resposta)

# --- ABA 4: INTEGRAÇÕES ---
elif menu == "Integrações":
    st.title("Central de Conectividade")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### 📊 Google Sheets")
        st.write("Sincronização com planilhas.")
        st.caption("Backup automático ativado.")
        
    with c2:
        st.markdown("### 📅 TimeTree Agenda") # ALTERADO AQUI
        st.write("Agendamento de cirurgias.")
        st.success("Status: Conectado (TreeApp)")
        if st.button("Abrir Agenda TimeTree"):
             st.markdown(f"<meta http-equiv='refresh' content='0; url={agenda_url}'>", unsafe_allow_html=True)
            
    with c3:
        st.markdown("### 🤖 Gemini AI")
        st.write("Inteligência Artificial para scripts.")
        st.success("Status: Simulado (Demo)")
