import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import requests
import pdfplumber
import numpy as np
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO VISUAL PRO (HIGH TICKET) ---
st.set_page_config(page_title="blue . Gestão Financeira", layout="wide", page_icon="🟦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp { background-color: #0b1120; color: #e6f1ff; font-family: 'Inter', sans-serif; }
    
    /* Logo Premium */
    .blue-logo { font-family: 'Inter', sans-serif; font-weight: 200; font-size: 3.5rem; color: #e6f1ff; letter-spacing: -3px; margin-bottom: -15px; text-shadow: 0 0 10px rgba(0, 242, 255, 0.3); }
    .blue-dot { color: #00f2ff; font-weight: bold; }
    .blue-sub { font-family: 'Inter', sans-serif; font-weight: 400; font-size: 0.9rem; letter-spacing: 4px; color: #00f2ff; text-transform: uppercase; margin-left: 5px; opacity: 0.9; }
    
    /* Métricas HUD */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #161b2e 0%, #0b1120 100%);
        border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800 !important; color: #fff !important; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 1px; }

    /* Botões */
    .stButton > button {
        background: linear-gradient(90deg, #00f2ff 0%, #0066ff 100%); 
        color: #fff; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase;
        transition: all 0.3s ease;
    }
    .stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(0, 242, 255, 0.5); }

    /* Inputs e Tabelas */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] { border: 1px solid #1f2937; border-radius: 10px; background-color: #111827; }
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stDateInput input, .stTextArea textarea {
        background-color: #1f2937 !important; color: #fff !important; border: 1px solid #374151 !important; border-radius: 8px;
    }
    
    /* Status Box */
    .status-box {
        padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 1.2rem; margin-bottom: 20px;
        text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    /* Link Externo */
    .external-link-btn {
        display: inline-block; width: 100%; padding: 0.8rem 1rem;
        background-color: #1e293b; color: #00f2ff !important; text-align: center;
        border: 1px solid #00f2ff; border-radius: 8px; text-decoration: none;
        font-weight: 600; transition: all 0.3s ease;
    }
    .external-link-btn:hover { background-color: #00f2ff; color: #fff !important; }

    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INTELIGÊNCIA DE DADOS ---
DATA_FILE = "financeiro_blue.csv"

HISTORICO_FILES = [
    "fechamento-de-caixa-57191-6a9ad554-2fa6-41ba-b652-ea0b4c6805e9.xlsx - sheet1.csv",
    "fechamento-de-caixa-57191-83a36dcc-011c-4146-a04a-1c7fb0101e42.xlsx - sheet1.csv",
    "fechamento-de-caixa-57191-f6c1cd85-0cf2-4258-9503-b1120442cbb3.xlsx - sheet1.csv"
]

def smart_categorize(row):
    text = (str(row.get('Descrição', '')) + " " + str(row.get('Categoria', '')) + " " + str(row.get('Subcategoria', ''))).lower()
    if 'lipedema' in text: return 'Consulta Lipedema'
    if 'cirurgia' in text: return 'Cirurgia'
    if 'consulta' in text: return 'Consulta Clínica'
    if any(x in text for x in ['botox', 'preenchimento', 'cosmiatria', 'estetica', 'harmonização', 'laser', 'procedimento']): return 'Procedimento Estético'
    if any(x in text for x in ['remedio', 'medicamento', 'farmacia', 'drogaria', 'estoque', 'vacina']): return 'Estoque/Medicamento'
    if any(x in text for x in ['material', 'luva', 'gaze', 'seringa']): return 'Material Cirúrgico'
    if any(x in text for x in ['aluguel', 'condominio', 'luz', 'agua', 'internet', 'vivo', 'claro', 'telefonia', 'energia']): return 'Custos Fixos'
    if any(x in text for x in ['pro-labore', 'pro labore', 'salario', 'folha', '13', 'ferias', 'colaborador']): return 'Pessoal/Salários'
    if any(x in text for x in ['sangria', 'retirada', 'sócio', 'distribuição', 'cofre']): return 'Retirada de Caixa/Sangria'
    if any(x in text for x in ['taxa', 'imposto', 'simples', 'das', 'banco']): return 'Impostos/Taxas'
    original = row.get('Categoria', '')
    return original if original and original != 'nan' else 'Outros'

def normalize_columns(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    mapping = {
        'vencimento': 'Data', 'data de pagamento': 'Data', 'pagamento': 'Data', 'dt': 'Data', 'date': 'Data', 'data': 'Data', 'dia': 'Data',
        'valor líquido r$': 'Valor', 'valor original r$': 'Valor', 'valor_pago': 'Valor', 'total': 'Valor', 'amount': 'Valor', 'valor': 'Valor', 
        'vl pago': 'Valor', 'valor$': 'Valor', 'valor $': 'Valor', 'valor (r$)': 'Valor', 'valor r$': 'Valor', 'vl.': 'Valor', 'preço': 'Valor',
        'pago a / recebido de': 'Subcategoria', 'favorecido': 'Subcategoria', 'cliente': 'Subcategoria', 'paciente': 'Subcategoria', 'nome': 'Subcategoria', 'fornecedor': 'Subcategoria',
        'descrição': 'Descrição', 'histórico': 'Descrição', 'description': 'Descrição', 'procedimento': 'Descrição', 'obs': 'Descrição'
    }
    df = df.rename(columns=mapping)
    df = df.loc[:, ~df.columns.duplicated()]
    
    required_cols = ["Data", "Tipo", "Categoria", "Subcategoria", "Descrição", "Valor", "Status", "Forma Pagamento"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = datetime.now() if col == "Data" else (0.0 if col == "Valor" else "")

    def clean_currency(x):
        if isinstance(x, (int, float)): return float(x)
        if pd.isna(x) or str(x).strip() == '': return 0.0
        s = str(x).replace('R$', '').replace('$', '').replace(' ', '')
        if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
        elif ',' in s: s = s.replace(',', '.')
        try: return float(s)
        except: return 0.0
        
    df['Valor'] = df['Valor'].apply(clean_currency)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data'])

    def determine_type(row):
        valor = row['Valor']
        desc = (str(row.get('Descrição', '')) + " " + str(row.get('Tipo', '')) + " " + str(row.get('Subcategoria', ''))).lower()
        if valor < 0: return 'Saída'
        keywords_saida = ['saída', 'saida', 'despesa', 'débito', 'debito', 'sangria', 'pagamento', 'pgto', 'pago', 'compra', 'boleto', 'conta', 'tarifa', 'taxa', 'imposto', 'retirada', 'fornecedor', 'aluguel', 'luz', 'agua', 'salario', 'pro-labore']
        if any(k in desc for k in keywords_saida): return 'Saída'
        return 'Entrada'

    df['Tipo'] = df.apply(determine_type, axis=1)
    df['Valor'] = df['Valor'].abs()
    
    if 'Categoria' not in df.columns or df['Categoria'].isnull().all():
         df['Categoria'] = df.apply(smart_categorize, axis=1)
    else:
         df['Categoria'] = df.apply(lambda row: smart_categorize(row) if row['Categoria'] in ['', 'Outros', 'nan', None] else row['Categoria'], axis=1)

    df['Mês'] = df['Data'].dt.strftime("%Y-%m")
    df['Ano'] = df['Data'].dt.year.astype(int)
    return df

def init_db_from_history():
    dfs = []
    found = 0
    for file in HISTORICO_FILES:
        if os.path.exists(file):
            try:
                try: df_t = pd.read_csv(file)
                except: df_t = pd.read_csv(file, sep=';')
                if not df_t.empty:
                    dfs.append(normalize_columns(df_t))
                    found += 1
            except: pass
    if dfs:
        full_df = pd.concat(dfs, ignore_index=True).sort_values(by="Data")
        save_data(full_df)
        return True, found
    return False, 0

def load_data():
    if not os.path.exists(DATA_FILE):
        success, count = init_db_from_history()
        if success: st.toast(f"Banco restaurado de {count} arquivos!", icon="♻️")
    if os.path.exists(DATA_FILE):
        return normalize_columns(pd.read_csv(DATA_FILE))
    return pd.DataFrame(columns=["Data", "Tipo", "Categoria", "Subcategoria", "Descrição", "Valor", "Status", "Forma Pagamento", "Mês", "Ano"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_market_data():
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL"
        r = requests.get(url, timeout=2).json()
        return float(r['USDBRL']['bid']), float(r['USDBRL']['pctChange']), float(r['EURBRL']['bid']), float(r['EURBRL']['pctChange'])
    except: return None, 0, None, 0

# --- 3. RECIBO (ASSINATURA LIMPA) ---
class PDFReceipt(FPDF):
    def header(self):
        self.set_font('Arial', '', 32)
        self.set_text_color(0, 0, 0)
        self.cell(0, 15, 'blue .', 0, 1, 'C')
        self.ln(5)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.1)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(10)

def generate_receipt_pro(tipo, nome_contraparte, valor, referente, data_recibo):
    pdf = PDFReceipt()
    pdf.add_page()
    pdf.set_y(50)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(20, 20, 20)
    titulo = "COMPROVANTE" if tipo == "Pagamento" else "RECIBO"
    pdf.cell(0, 10, titulo, 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 28)
    pdf.cell(0, 15, f"R$ {valor:,.2f}", 0, 1, 'C')
    pdf.ln(15)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(60, 60, 60)
    cnpj_blue, nome_blue = "48.459.860/0001-14", "BLUE CLINICA MEDICA E CIRURGICA LTDA"
    if tipo == "Recebimento":
        texto = f"Recebemos de {nome_contraparte.upper()}, a quantia de R$ {valor:,.2f}, referente a: {referente}."
        p1_lbl, p1_nom = "Pagador:", nome_contraparte.upper()
        p2_lbl, p2_nom = "Beneficiário:", f"{nome_blue} - CNPJ: {cnpj_blue}"
    else:
        texto = f"Pagamos a {nome_contraparte.upper()}, a quantia de R$ {valor:,.2f}, referente a: {referente}."
        p1_lbl, p1_nom = "Pagador:", f"{nome_blue}"
        p2_lbl, p2_nom = "Beneficiário:", nome_contraparte.upper()
    pdf.set_x(25)
    pdf.multi_cell(160, 8, texto.encode('latin-1', 'replace').decode('latin-1'), 0, 'C')
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(95, 5, p1_lbl.encode('latin-1', 'replace').decode('latin-1'), 0, 0, 'L')
    pdf.cell(95, 5, p2_lbl.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'L')
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 5, p1_nom.encode('latin-1', 'replace').decode('latin-1'), 0, 0, 'L')
    pdf.cell(95, 5, p2_nom.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'L')
    pdf.set_y(230)
    pdf.cell(0, 5, f"Rio de Janeiro, {data_recibo.strftime('%d de %B de %Y')}", 0, 1, 'C')
    pdf.ln(20)
    pdf.cell(0, 5, "__________________________________________________", 0, 1, 'C')
    pdf.cell(0, 5, "Assinatura", 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1', 'replace')

def read_any_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            try: return pd.read_csv(uploaded_file)
            except: return pd.read_csv(uploaded_file, sep=';')
        elif uploaded_file.name.endswith(('.xls', '.xlsx')): return pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.pdf'):
            with pdfplumber.open(uploaded_file) as pdf:
                text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
            return pd.DataFrame({'Dados Extraídos': text.split('\n')})
    except: return pd.DataFrame()

# --- 4. APLICAÇÃO ---
if 'db' not in st.session_state: st.session_state.db = load_data()
df = st.session_state.db.copy()

if 'cofre_valor' not in st.session_state: st.session_state.cofre_valor = 0.0

with st.sidebar:
    st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Gestão Financeira Pro</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    usd, usd_var, eur, eur_var = get_market_data()
    if usd:
        st.caption("🌐 MERCADO (TEMPO REAL)")
        c1, c2 = st.columns(2)
        c1.metric("USD", f"R$ {usd:.2f}", f"{usd_var}%")
        c2.metric("EUR", f"R$ {eur:.2f}", f"{eur_var}%")
        st.markdown("---")
    
    st.caption("🔒 CONTROLE DE COFRE (DINHEIRO)")
    st.session_state.cofre_valor = st.number_input("Valor Físico (R$)", min_value=0.0, value=st.session_state.cofre_valor, step=100.0)
    st.markdown(f"**Total Disponível:** R$ {st.session_state.cofre_valor:,.2f}")
    st.markdown("---")

    menu = st.radio("MENU", ["Dashboard & Analytics", "Data Center (Lançamentos)", "Automação & Conciliação"], index=0)
    st.markdown("---")
    st.markdown("""<a href="https://www.nfse.gov.br/EmissorNacional/Login?ReturnUrl=%2fEmissorNacional" target="_blank" class="external-link-btn">🏢 Emissor Nacional NFSe</a>""", unsafe_allow_html=True)

# --- DASHBOARD ---
if menu == "Dashboard & Analytics":
    t1, t2 = st.tabs(["📊 Visão Geral", "📈 Análise"])
    with t1:
        try:
            receita = df[df['Tipo'] == "Entrada"]['Valor'].sum()
            despesa = df[df['Tipo'] == "Saída"]['Valor'].sum()
            saldo_operacional = receita - despesa
            saldo_total = saldo_operacional + st.session_state.cofre_valor
            
            if saldo_total < 0: s_msg, s_cor, s_bg = "CRÍTICO 🚨", "#ff3333", "rgba(255, 51, 51, 0.2)"
            elif 0 <= saldo_total < 20000: s_msg, s_cor, s_bg = "EM EQUILÍBRIO ⚠️", "#ffcc00", "rgba(255, 204, 0, 0.2)"
            elif 20000 <= saldo_total < 150000: s_msg, s_cor, s_bg = "SAUDÁVEL ✅", "#00ff88", "rgba(0, 255, 136, 0.2)"
            else: s_msg, s_cor, s_bg = "EXCELENTE 💎", "#00f2ff", "rgba(0, 242, 255, 0.2)"
            
            st.markdown(f"""<div class="status-box" style="background-color: {s_bg}; color: {s_cor}; border: 1px solid {s_cor};">STATUS FINANCEIRO: {s_msg}</div>""", unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Receita", f"R$ {receita:,.2f}", delta="Entradas")
            c2.metric("Despesas", f"R$ {despesa:,.2f}", delta="-Saídas", delta_color="inverse")
            c3.metric("Saldo Banco", f"R$ {saldo_operacional:,.2f}")
            c4.metric("Patrimônio (c/ Cofre)", f"R$ {saldo_total:,.2f}")
            st.markdown("---")
            
            cg1, cg2 = st.columns([1, 2])
            with cg1:
                st.subheader("Balanço")
                fig_d = go.Figure(data=[go.Pie(labels=['Entradas', 'Saídas'], values=[receita, despesa], hole=.7, marker=dict(colors=['#00ff88', '#ff3333']), textinfo='percent')])
                fig_d.add_annotation(text=f"Lucro<br>R${saldo_operacional:,.0f}", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="white"))
                fig_d.update_layout(template="plotly_dark", showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_d, use_container_width=True)
            with cg2:
                st.subheader("Fluxo Mensal")
                df_c = df.groupby(['Ano', 'Mês']).agg({'Valor': lambda x: x[df.loc[x.index, 'Tipo']=='Entrada'].sum() - x[df.loc[x.index, 'Tipo']=='Saída'].sum()}).reset_index()
                if not df_c.empty:
                    df_c['Sort'] = df_c['Ano'].astype(str) + df_c['Mês']
                    df_c = df_c.sort_values('Sort')
                    fig = go.Figure(go.Scatter(x=df_c['Mês'] + "/" + df_c['Ano'].astype(str), y=df_c['Valor'], mode='lines+markers', fill='tozeroy', line=dict(color='#00f2ff', width=3), fillcolor='rgba(0, 242, 255, 0.1)'))
                    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig, use_container_width=True)
        except: st.warning("Processando...")

# --- DATA CENTER ---
elif menu == "Data Center (Lançamentos)":
    st.title("Data Center & Filtros")
    c1, c2, c3 = st.columns(3)
    ft_tipo = c1.multiselect("Filtrar Tipo", ["Entrada", "Saída"])
    ft_cat = c2.multiselect("Filtrar Categoria", df['Categoria'].unique())
    ft_search = c3.text_input("Buscar (Nome/Descrição)")
    
    df_view = df.copy()
    if ft_tipo: df_view = df_view[df_view['Tipo'].isin(ft_tipo)]
    if ft_cat: df_view = df_view[df_view['Categoria'].isin(ft_cat)]
    if ft_search: df_view = df_view[df_view['Descrição'].str.contains(ft_search, case=False, na=False) | df_view['Subcategoria'].str.contains(ft_search, case=False, na=False)]

    st.markdown("### ➕ Novo Lançamento Manual")
    with st.form("manual_add", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        n_dt = c1.date_input("Data", datetime.now())
        n_tipo = c2.selectbox("Tipo", ["Entrada", "Saída"])
        n_val = c3.number_input("Valor R$", min_value=0.0)
        n_cat = c4.selectbox("Categoria", ["Consulta Clínica", "Cirurgia", "Procedimento Estético", "Custos Fixos", "Pessoal/Salários", "Outros"])
        n_desc = st.text_input("Descrição / Paciente")
        if st.form_submit_button("Adicionar Lançamento"):
            row = {"Data": pd.to_datetime(n_dt), "Tipo": n_tipo, "Valor": n_val, "Categoria": n_cat, "Descrição": n_desc, "Subcategoria": "Manual", "Status": "Pago"}
            st.session_state.db = pd.concat([st.session_state.db, normalize_columns(pd.DataFrame([row]))], ignore_index=True)
            save_data(st.session_state.db)
            st.success("Adicionado!")
            st.rerun()
            
    st.markdown("### 📝 Editor de Dados (Tabela)")
    edited = st.data_editor(
        df_view.sort_values("Data", ascending=False), use_container_width=True, num_rows="dynamic",
        column_config={"Valor": st.column_config.NumberColumn(format="R$ %.2f"), "Data": st.column_config.DateColumn(format="DD/MM/YYYY")}
    )
    
    c_save, c_export = st.columns([1, 1])
    if not edited.equals(df_view):
        if c_save.button("💾 SALVAR EDIÇÕES NA TABELA", type="primary"):
            if len(df_view) == len(df):
                edited['Data'] = pd.to_datetime(edited['Data'])
                edited['Mês'] = edited['Data'].dt.strftime("%Y-%m")
                edited['Ano'] = edited['Data'].dt.year
                st.session_state.db = edited
                save_data(edited)
                st.success("Salvo!")
                st.rerun()
            else: st.warning("Para editar, remova os filtros antes.")
    csv = df_view.to_csv(index=False).encode('utf-8')
    c_export.download_button("⬇️ EXPORTAR RELATÓRIO (CSV)", csv, "relatorio_financeiro.csv", "text/csv")

# --- AUTOMAÇÃO ---
elif menu == "Automação & Conciliação":
    t1, t2, t3 = st.tabs(["🧾 Recibos", "📥 Importar Arquivos", "⚖️ Conciliação Bancária"])
    
    with t1:
        if 'pdf_buffer' not in st.session_state: st.session_state.pdf_buffer = None
        with st.form("recibo"):
            tipo = st.radio("Tipo", ["Recebimento", "Pagamento"], horizontal=True)
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome")
            val = c2.number_input("Valor", min_value=0.0)
            ref = st.text_area("Referente a")
            dt_r = st.date_input("Data", datetime.now())
            if st.form_submit_button("Gerar PDF"):
                if nome and val > 0:
                    tipo_db = "Entrada" if tipo == "Recebimento" else "Saída"
                    row = {"Data": pd.to_datetime(dt_r), "Tipo": tipo_db, "Valor": val, "Subcategoria": nome, "Descrição": ref, "Categoria": smart_categorize({'Descrição': ref}), "Status": "Pago"}
                    st.session_state.db = pd.concat([st.session_state.db, normalize_columns(pd.DataFrame([row]))], ignore_index=True)
                    save_data(st.session_state.db)
                    st.session_state.pdf_buffer = generate_receipt_pro(tipo, nome, val, ref, dt_r)
                    st.session_state.pdf_name = f"Recibo_{nome}_{dt_r}.pdf"
                    st.success("Gerado!")
                else: st.error("Preencha os dados.")
        if st.session_state.pdf_buffer:
            st.download_button("⬇️ Baixar PDF", st.session_state.pdf_buffer, st.session_state.pdf_name, "application/pdf", type="primary")

    with t2:
        up = st.file_uploader("Arquivo (Excel/CSV/PDF)", type=['xlsx', 'csv', 'pdf'])
        if up:
            new = read_any_file(up)
            if not new.empty:
                # --- NOVIDADE: DETECTOR DE DUPLICATAS NA PRÉ-VISUALIZAÇÃO ---
                norm_preview = normalize_columns(new.copy())
                # Conta quantas vezes cada nome aparece no arquivo importado
                dup_counts = norm_preview['Subcategoria'].value_counts()
                
                # Cria coluna de alerta se aparecer > 1 vez
                def check_dup(nome):
                    if pd.isna(nome) or nome == '': return ""
                    count = dup_counts.get(nome, 0)
                    return f"⚠️ Repetido {count}x" if count > 1 else "Ok"
                
                norm_preview.insert(0, "⚠️ Atenção", norm_preview['Subcategoria'].apply(check_dup))
                
                st.markdown("### Pré-visualização (Verifique Alertas)")
                st.dataframe(norm_preview, use_container_width=True)
                
                if st.button("✅ Confirmar Importação"):
                    # Remove a coluna de alerta antes de salvar
                    final_df = norm_preview.drop(columns=["⚠️ Atenção"])
                    st.session_state.db = pd.concat([st.session_state.db, final_df], ignore_index=True)
                    save_data(st.session_state.db)
                    st.success("Importado com Sucesso!")
                    st.rerun()

    with t3:
        st.markdown("### ⚖️ Conciliação Bancária")
        f_banco = st.file_uploader("Extrato Bancário", type=['pdf', 'xlsx', 'csv'], key="banco")
        if f_banco:
            df_banco = normalize_columns(read_any_file(f_banco))
            if not df_banco.empty:
                min_d, max_d = df_banco['Data'].min(), df_banco['Data'].max()
                df_sys = df[(df['Data'] >= min_d) & (df['Data'] <= max_d)]
                sys_ent, sys_sai = df_sys[df_sys['Tipo']=='Entrada']['Valor'].sum(), df_sys[df_sys['Tipo']=='Saída']['Valor'].sum()
                ban_ent, ban_sai = df_banco[df_banco['Tipo']=='Entrada']['Valor'].sum(), df_banco[df_banco['Tipo']=='Saída']['Valor'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Sistema (Entrada)", f"R$ {sys_ent:,.2f}")
                c2.metric("Banco (Entrada)", f"R$ {ban_ent:,.2f}")
                c3.metric("Diferença", f"R$ {sys_ent - ban_ent:,.2f}", delta_color="off")
