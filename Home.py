import streamlit as st
import time

# --- CONFIGURAÇÃO DA PÁGINA (PORTAL) ---
st.set_page_config(page_title="Blue System | Acesso", page_icon="🟦", layout="centered")

# --- ESTILO CSS (O MESMO PADRÃO ELITE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background-color: #0b1120; color: #e6f1ff; font-family: 'Inter', sans-serif; }
    
    /* Logo Central */
    .blue-logo-login { 
        font-family: 'Inter', sans-serif; font-weight: 200; font-size: 4rem; 
        color: #e6f1ff; letter-spacing: -3px; text-align: center; margin-top: 50px;
        text-shadow: 0 0 20px rgba(0, 242, 255, 0.4);
    }
    .blue-dot { color: #00f2ff; font-weight: bold; }
    
    /* Caixa de Login */
    .login-box {
        background: linear-gradient(145deg, #161b2e 0%, #0b1120 100%);
        padding: 40px; border-radius: 20px; border: 1px solid rgba(0, 242, 255, 0.1);
        box-shadow: 0 20px 50px rgba(0,0,0,0.5); text-align: center;
    }
    
    /* Inputs */
    .stTextInput input {
        background-color: #1f2937 !important; color: #fff !important; 
        border: 1px solid #374151 !important; border-radius: 8px; text-align: center;
    }
    
    /* Botão Entrar */
    .stButton > button {
        background: linear-gradient(90deg, #00f2ff 0%, #0066ff 100%); 
        color: #fff; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase;
        width: 100%; height: 50px; transition: all 0.3s ease; box-shadow: 0 0 15px rgba(0, 242, 255, 0.3);
    }
    .stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(0, 242, 255, 0.6); }
    
    /* Cards de Seleção */
    .module-card {
        padding: 20px; border-radius: 12px; background: #1e293b; border: 1px solid #334155;
        text-align: center; cursor: pointer; transition: all 0.3s; margin-bottom: 15px;
    }
    .module-card:hover { border-color: #00f2ff; transform: translateX(5px); }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_password():
    if st.session_state.password == "blue2026": # <--- SUA SENHA AQUI
        st.session_state.logged_in = True
        del st.session_state.password
    else:
        st.error("Senha incorreta.")

# --- TELA ---
st.markdown("<div class='blue-logo-login'>blue<span class='blue-dot'>.</span></div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; letter-spacing: 3px; color: #00f2ff; opacity: 0.7; text-transform: uppercase; margin-bottom: 40px;'>Operating System</p>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    # TELA DE LOGIN
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.text_input("CHAVE DE ACESSO", type="password", key="password", on_change=check_password)
        st.button("ACESSAR SISTEMA", on_click=check_password)

else:
    # TELA DE SELEÇÃO (DASHBOARD)
    st.success(f"Bem-vinda, {st.session_state.get('user_name', 'Gestora')}.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("💰 DEPARTAMENTO FINANCEIRO")
        if st.button("ACESSAR FINANCEIRO >>"):
            st.switch_page("pages/1_💰_Financeiro.py")
            
    with col2:
        st.info("💎 DEPARTAMENTO COMERCIAL")
        if st.button("ACESSAR COMERCIAL >>"):
            st.switch_page("pages/2_💎_Comercial.py")
            
    st.markdown("---")
    if st.button("Sair / Logout"):
        st.session_state.logged_in = False
        st.rerun()
