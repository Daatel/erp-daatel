import streamlit as st
from datetime import date
from database import run_query

st.set_page_config(page_title="Ficha de Admissão - Empório do Alho", page_icon="📝", layout="centered")

# Custom CSS para ocultar a sidebar e focar no formulário centralizado
st.markdown("""
<style>
    /* Ocultar barra lateral e botão de colapso */
    [data-testid="collapsedSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    /* Estilo do container principal */
    .block-container {
        max-width: 680px !important;
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
    /* Cores de fundo claras e legíveis */
    .stApp {
        background-color: #f8fafc !important; /* Slate 50 */
    }
    h1, h2, h3, h4, h5, p, label {
        color: #1e293b !important; /* Slate 800 */
    }
    /* Customizar inputs para fundo branco e borda suave */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input {
        color: #1e293b !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
    }
    /* Estilo do cabeçalho */
    .admissao-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 20px;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .admissao-header h1 {
        color: #ffffff !important;
        font-size: 24px;
        margin: 0;
        font-weight: 700;
    }
    .admissao-header p {
        color: #94a3b8 !important; /* Slate 400 */
        font-size: 14px;
        margin: 5px 0 0 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="admissao-header">
    <h1>Ficha de Pré-Cadastro de Colaborador</h1>
    <p>Empório do Alho - Sistema de Admissão de Talentos</p>
</div>
""", unsafe_allow_html=True)

st.info("Preencha todos os campos com atenção. Ao concluir, seus dados serão enviados diretamente para revisão do Departamento Pessoal.")

with st.form("form_pre_cadastro", clear_on_submit=True):
    
    # BLOCO 1: Identificação e Contato
    with st.expander("👤 Bloco 1: Identificação e Contato", expanded=True):
        nome = st.text_input("Nome Completo *").strip()
        col1, col2 = st.columns(2)
        nascimento = col1.date_input("Data de Nascimento", value=date(1995, 1, 1), format="DD/MM/YYYY")
        genero = col2.selectbox("Gênero", ["Não Informar", "Masculino", "Feminino", "Outro"])
        
        col3, col4 = st.columns(2)
        estado_civil = col3.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"])
        nacionalidade = col4.text_input("Nacionalidade / Naturalidade", value="Brasileira").strip()
        
        col5, col6 = st.columns(2)
        nome_mae = col5.text_input("Nome da Mãe").strip()
        nome_pai = col6.text_input("Nome do Pai").strip()
        
        col7, col8 = st.columns([3, 1])
        endereco = col7.text_input("Endereço Completo (Rua/Av, Número, Compl)").strip()
        cep = col8.text_input("CEP").strip()
        
        col9, col10, col11 = st.columns(3)
        bairro = col9.text_input("Bairro").strip()
        cidade_uf = col10.text_input("Cidade - UF").strip()
        telefone = col11.text_input("Telefone / WhatsApp *").strip()
        
        email = st.text_input("E-mail Pessoal *").strip()
        contato_emergencia = st.text_input("Contato de Emergência (Nome, Parentesco, Celular)").strip()

    # BLOCO 2: Documentação
    with st.expander("📇 Bloco 2: Documentação", expanded=False):
        col12, col13, col14 = st.columns(3)
        cnpj_cpf = col12.text_input("CPF *").strip()
        rg = col13.text_input("RG (Número, Órgão, Emissão)").strip()
        pis_pasep = col14.text_input("PIS / PASEP").strip()
        
        col15, col16, col17 = st.columns(3)
        ctps = col15.text_input("CTPS (Número, Série, UF)").strip()
        titulo_eleitor = col16.text_input("Título de Eleitor").strip()
        cnh = col17.text_input("CNH (Número, Categoria, Validade)").strip()

    # BLOCO 3: Dados Bancários e Dependentes
    with st.expander("💰 Bloco 3: Dados Bancários e Dependentes", expanded=False):
        col18, col19, col20 = st.columns(3)
        dados_bancarios = col18.text_input("Banco, Agência e Conta").strip()
        tipo_conta = col19.selectbox("Tipo de Conta", ["Corrente", "Salário", "Poupança"])
        chave_pix = col20.text_input("Chave PIX").strip()
        
        col21, col22 = st.columns(2)
        dependente1 = col21.text_input("Dependente 1 (Nome, CPF, Nascimento)").strip()
        dependente2 = col22.text_input("Dependente 2 (Nome, CPF, Nascimento)").strip()
        
        st.markdown("##### **TERMO DE CONSENTIMENTO (LGPD)**")
        st.caption(
            "Autorizo o processamento dos meus dados pessoais fornecidos acima para a finalidade "
            "exclusiva de qualificação cadastral, fins admissionais e elaboração de contrato de trabalho."
        )
        aceite_lgpd = st.checkbox("Aceito os termos da LGPD e autorizo o tratamento dos dados.", value=False)

    submit = st.form_submit_button("Enviar Ficha de Admissão", type="primary", use_container_width=True)
    
    if submit:
        if not nome:
            st.error("Por favor, preencha o Nome Completo.")
        elif not email:
            st.error("Por favor, preencha o E-mail Pessoal.")
        elif not telefone:
            st.error("Por favor, preencha o Telefone / WhatsApp.")
        elif not cnpj_cpf:
            st.error("Por favor, preencha o CPF.")
        elif not aceite_lgpd:
            st.error("Você precisa aceitar os termos da LGPD para enviar a ficha.")
        else:
            try:
                run_query(
                    """INSERT INTO pre_cadastros 
                       (nome, data_nascimento, genero, estado_civil, nacionalidade_naturalidade, nome_mae, nome_pai, 
                        endereco, bairro, cidade_uf, cep, telefone, email, contato_emergencia, cnpj_cpf, rg, 
                        pis_pasep, ctps, titulo_eleitor, cnh, dados_bancarios, tipo_conta, chave_pix, 
                        dependente1, dependente2, status, aceite_lgpd) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDENTE', 1)""",
                    (nome, nascimento, genero, estado_civil, nacionalidade, nome_mae, nome_pai,
                     endereco, bairro, cidade_uf, cep, telefone, email, contato_emergencia, cnpj_cpf, rg,
                     pis_pasep, ctps, titulo_eleitor, cnh, dados_bancarios, tipo_conta, chave_pix,
                     dependente1, dependente2)
                )
                st.success("🎉 Ficha enviada com sucesso! Seus dados foram encaminhados para análise do Departamento Pessoal.")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar informações: {e}")
