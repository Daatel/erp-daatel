import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import run_query, fetch_all

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Pessoas", page_icon="👥", layout="wide")

from estilo import carregar_estilo
carregar_estilo()

st.title("👥 Pessoas e Folha de Pagamento")

df_vendedores = fetch_all("SELECT id, nome, gatilho_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%'")

tab_cadastro, tab_aprovacoes, tab1, tab2, tab_beneficios, tab3, tab4 = st.tabs([
    "📝 Cadastro de Colaboradores",
    "⚡ Cadastro Rápido",
    "Visão Geral (Quadro)",
    "Folha de Pagamento",
    "🚌 Benefícios Semanais",
    "💎 Central de Comissões",
    "🖨️ Extrato Mensal do Vendedor"
])

# ======= CADASTRO DE COLABORADORES =======
with tab_cadastro:

    with st.expander("💡 Dica: Use o Cadastro Rápido via WhatsApp. Informações Aqui.", expanded=False):
        st.markdown("""
        ### ⚡ Cadastro Rápido — o jeito mais fácil de integrar um novo colaborador

        Em vez de digitar todos os dados manualmente aqui, você pode usar a aba **⚡ Cadastro Rápido** para
        enviar um link de autopreenchimento direto para o candidato pelo **WhatsApp**.

        ---

        #### 📲 Como funciona em 3 passos

        **1. Vá até a aba ⚡ Cadastro Rápido**
        - Digite o nome do candidato e o número do WhatsApp dele.
        - Clique em **"📨 Enviar via WhatsApp"** — o sistema abre o WhatsApp com uma mensagem já pronta contendo o link da ficha de admissão.

        **2. O candidato preenche pelo celular**
        - Ele acessa a página de admissão **sem precisar de login**.
        - Preenche os dados pessoais, documentos e informações bancárias no próprio celular.
        - Pode ser feito enquanto está aqui na empresa ou de casa, sem papel.

        **3. Você aprova na mesma aba ⚡ Cadastro Rápido**
        - Os dados chegam automaticamente para revisão logo abaixo do botão de envio.
        - Selecione o candidato, confira as informações, preencha os dados contratuais (cargo, salário, jornada).
        - Clique em **"✔️ APROVAR E CONTRATAR"** — o colaborador vai direto para o quadro de ativos.

        ---
        > 💡 **Quando usar o cadastro manual desta aba?** Quando você já tem todos os dados em mãos e quer
        > cadastrar diretamente, sem envolver o candidato no processo.
        """)
        st.divider()

    opc = st.radio("Ação:", ["Cadastrar Novo Colaborador", "Editar Colaborador Cadastrado"], horizontal=True, key="colab_action_radio")
    if opc == "Cadastrar Novo Colaborador":
        st.subheader("Ficha de Registro de Novo Colaborador")
        with st.form("form_func_new", clear_on_submit=True):
            # Expander 1: Identificação
            with st.expander("👤 Bloco 1: Identificação e Contato", expanded=True):
                col1, col2 = st.columns(2)
                nome = col1.text_input("Nome Completo", key="reg_nome")
                nascimento = col2.date_input("Data de Nascimento", value=date(1990, 1, 1), format="DD/MM/YYYY", key="reg_nasc")
                col3, col4, col5 = st.columns(3)
                genero = col3.selectbox("Gênero", ["Não Informar", "Masculino", "Feminino", "Outro"], key="reg_genero")
                estado_civil = col4.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"], key="reg_civil")
                nacionalidade = col5.text_input("Nacionalidade / Naturalidade", value="Brasileira", key="reg_nac")
                col6, col7 = st.columns(2)
                nome_mae = col6.text_input("Nome da Mãe", key="reg_mae")
                nome_pai = col7.text_input("Nome do Pai", key="reg_pai")
                col8, col9 = st.columns([3, 1])
                endereco = col8.text_input("Endereço Completo (Rua/Av, Nº, Compl)", key="reg_end")
                cep = col9.text_input("CEP", key="reg_cep")
                col10, col11, col12 = st.columns(3)
                bairro = col10.text_input("Bairro", key="reg_bairro")
                cidade_uf = col11.text_input("Cidade - UF", key="reg_cidade")
                telefone = col12.text_input("Telefone / Celular (WhatsApp)", key="reg_tel")
                col13, col14 = st.columns(2)
                email = col13.text_input("E-mail Pessoal", key="reg_email")
                contato_emergencia = col14.text_input("Contato de Emergência (Nome, Parentesco, Tel)", key="reg_emerg")

            # Expander 2: Documentação
            with st.expander("📇 Bloco 2: Documentação e eSocial", expanded=False):
                col1, col2, col3 = st.columns(3)
                cnpj_cpf = col1.text_input("CPF / CNPJ", key="reg_cpf")
                rg = col2.text_input("RG (Número / Órgão / Emissão)", key="reg_rg")
                pis_pasep = col3.text_input("PIS / PASEP", key="reg_pis")
                col4, col5 = st.columns(2)
                ctps = col4.text_input("CTPS (Número / Série / UF)", key="reg_ctps")
                titulo_eleitor = col5.text_input("Título de Eleitor (Nº / Zona / Seção)", key="reg_titulo")
                cnh = st.text_input("CNH (Nº / Categoria / Validade)", key="reg_cnh")

            # Expander 3: Dados Bancários
            with st.expander("💰 Bloco 3: Dados Bancários e Dependentes", expanded=False):
                col1, col2, col3 = st.columns(3)
                dados_bancarios = col1.text_input("Banco / Agência / Conta", key="reg_banco")
                tipo_conta = col2.selectbox("Tipo de Conta", ["Corrente", "Salário", "Poupança"], key="reg_tconta")
                chave_pix = col3.text_input("Código Pix (Opcional)", key="reg_pix")
                col4, col5 = st.columns(2)
                dependente1 = col4.text_input("Dependente 1 (Nome / CPF / Nasc.)", key="reg_dep1")
                dependente2 = col5.text_input("Dependente 2 (Nome / CPF / Nasc.)", key="reg_dep2")

            # Expander 4: Dados Contratuais
            with st.expander("👔 Bloco 4: Dados Contratuais e Jornada", expanded=False):
                col1, col2, col3 = st.columns(3)
                cargo = col1.selectbox("Cargo / Função", ["Operário", "Vendedor", "Gerente", "Administrativo", "Representante Comercial"], key="reg_cargo")
                departamento = col2.text_input("Departamento / Área", key="reg_dept")
                regime = col3.selectbox("Regime de Contratação", ["CLT", "PJ", "Estágio", "Autônomo", "Diarista", "Outro"], key="reg_regime")
                col4, col5, col6 = st.columns(3)
                modelo_trabalho = col4.selectbox("Modelo de Trabalho", ["Presencial", "Híbrido", "Remoto"], key="reg_mt")
                admissao = col5.date_input("Data de Admissão", value=date.today(), format="DD/MM/YYYY", key="reg_adm")
                termino = col6.date_input("Data de Término (Opcional)", value=None, format="DD/MM/YYYY", key="reg_term")
                col7, col8, col9 = st.columns(3)
                carga_horaria = col7.text_input("Carga Horária Semanal (Ex: 44h)", key="reg_carga")
                horario_trabalho = col8.text_input("Horário de Trabalho (Ex: Entrada / Saída / Intervalo)", key="reg_horario")
                escala = col9.text_input("Dias da Semana / Escala (Ex: Segunda a Sexta)", key="reg_escala")

            # Expander 5: Remuneração
            with st.expander("💸 Bloco 5: Remuneração, Variável e Benefícios", expanded=False):
                col1, col2 = st.columns(2)
                salario = col1.number_input("Remuneração Fixa / Bolsa Auxílio (R$)", min_value=0.0, step=100.0, key="reg_sal")
                adicionais = col2.multiselect("Adicionais Legais", ["Não aplicável", "Periculosidade", "Insalubridade", "Noturno"], default=["Não aplicável"], key="reg_adicionais")
                adicionais_str = ",".join(adicionais)
                col3, col4 = st.columns(2)
                comissionamento = col3.selectbox("Comissionamento?", ["Não", "Sim"], key="reg_comiss")
                comissao_regra = col4.text_input("Regra de Comissão (Se Sim)", key="reg_comregra")
                col5, col6, col7 = st.columns(3)
                gatilho_com = col5.text_input("Gatilho e Pagamento da Comissão", key="reg_gatcom")
                bonus = col6.text_input("Bônus / Premiações por Meta (Regra/KPI)", key="reg_bonus")
                adiantamento = col7.text_input("Política de Adiantamento (Vale)", key="reg_valem")
                st.markdown("🚌 **Benefícios e Custos de Transporte / Refeição**")
                col8, col9 = st.columns(2)
                val_transp = col8.number_input("Vale Transporte / Passagem Diária (R$)", min_value=0.0, step=1.0, key="reg_vt")
                vt_desc = col9.selectbox("Desconto Vale Transporte", ["Sem desconto", "Com desconto"], key="reg_vtdesc")
                col10, col11 = st.columns(2)
                val_refei = col10.number_input("Vale Alimentação / Refeição Diário (R$)", min_value=0.0, step=1.0, key="reg_vr")
                vr_desc = col11.selectbox("Desconto Refeição / Alimentação", ["Sem desconto", "Com desconto"], key="reg_vrdesc")
                ajuda_custo = st.number_input("Ajuda de Custo Mensal (R$)", min_value=0.0, step=50.0, key="reg_ajuda")

            # Expander 6: Ferramentas
            with st.expander("💻 Bloco 6: Ferramentas e Termos de Aceite", expanded=False):
                equipamentos = st.multiselect("Equipamentos e Acessos Fornecidos", ["Notebook", "Celular", "Acesso a ERP/CRM", "Uniforme"], key="reg_equip")
                equipamentos_str = ",".join(equipamentos)
                st.markdown("##### **TERMO DE CIÊNCIA E AUTORIZAÇÃO (LGPD)**")
                st.caption(
                    "Declaro que as informações acima são verdadeiras e autorizo o uso dos meus dados pessoais pela empresa "
                    "exclusivamente para fins de registro de funcionários, cumprimento de obrigigações legais, processamento de "
                    "folha de pagamento e gestão de benefícios, em conformidade com a Lei Geral de Proteção de Dados (LGPD)."
                )
                aceite_lgpd = st.checkbox("Aceito os termos da LGPD e autorizo o processamento dos meus dados.", value=False, key="reg_lgpd")

            if st.form_submit_button("Cadastrar Colaborador", type="primary"):
                if not nome:
                    st.error("Por favor, preencha o Nome Completo.")
                elif not aceite_lgpd:
                    st.error("É necessário aceitar os termos da LGPD para realizar o cadastro.")
                else:
                    comiss_int = 1 if comissionamento == "Sim" else 0
                    aceite_int = 1 if aceite_lgpd else 0
                    run_query(
                        """INSERT INTO funcionarios 
                           (nome, cargo, salario_base, regime_contratacao, data_admissao, data_nascimento, ajuda_custo, status, data_termino, cnpj_cpf, telefone, email, valor_transporte, valor_refeicao,
                            genero, estado_civil, nacionalidade_naturalidade, nome_mae, nome_pai, endereco, bairro, cidade_uf, cep, contato_emergencia, rg, pis_pasep, ctps, titulo_eleitor, cnh,
                            dados_bancarios, tipo_conta, chave_pix, dependente1, dependente2, departamento, modelo_trabalho, carga_horaria_semanal, horario_trabalho, escala_trabalho,
                            adicionais_legais, comissionamento, comissao_regra, gatilho_pagamento_comissao, bonus_premiacao, politica_adiantamento, vt_desconto, vr_desconto, equipamentos_fornecidos, aceite_lgpd) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, 'ATIVO', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (nome, cargo, salario, regime, admissao, nascimento, ajuda_custo, termino, cnpj_cpf, telefone, email, val_transp, val_refei,
                         genero, estado_civil, nacionalidade, nome_mae, nome_pai, endereco, bairro, cidade_uf, cep, contato_emergencia, rg, pis_pasep, ctps, titulo_eleitor, cnh,
                         dados_bancarios, tipo_conta, chave_pix, dependente1, dependente2, departamento, modelo_trabalho, carga_horaria, horario_trabalho, escala,
                         adicionais_str, comiss_int, comissao_regra, gatilho_com, bonus, adiantamento, vt_desc, vr_desc, equipamentos_str, aceite_int)
                    )
                    st.success(f"Colaborador {nome} cadastrado com sucesso!")
                    import time; time.sleep(1); st.rerun()

    else:
        st.subheader("Editar Cadastro de Colaborador")
        df_func_edit = fetch_all("SELECT id, nome, cargo FROM funcionarios ORDER BY nome")
        if df_func_edit.empty:
            st.warning("Nenhum colaborador cadastrado.")
        else:
            opts_f = {f"{r['id']} - {r['nome']} ({r['cargo']})": r['id'] for _, r in df_func_edit.iterrows()}
            f_sel = st.selectbox("Selecione o Colaborador para editar:", list(opts_f.keys()), key="edit_colab_select")
            if f_sel:
                f_id = opts_f[f_sel]
                f_data = fetch_all("SELECT * FROM funcionarios WHERE id=?", (f_id,)).iloc[0]
                
                with st.form("form_func_edit"):
                    # Expander 1: Identificação
                    with st.expander("👤 Bloco 1: Identificação e Contato", expanded=True):
                        col1, col2 = st.columns(2)
                        ef_nome = col1.text_input("Nome Completo", f_data['nome'])
                        dt_nasc = pd.to_datetime(f_data['data_nascimento']).date() if pd.notnull(f_data['data_nascimento']) else date(1990, 1, 1)
                        ef_nascimento = col2.date_input("Data de Nascimento", value=dt_nasc, format="DD/MM/YYYY")
                        
                        g_opts = ["Não Informar", "Masculino", "Feminino", "Outro"]
                        db_g = f_data.get('genero', 'Não Informar')
                        if db_g not in g_opts: db_g = "Não Informar"
                        
                        ec_opts = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
                        db_ec = f_data.get('estado_civil', 'Solteiro(a)')
                        if db_ec not in ec_opts: db_ec = "Solteiro(a)"
                        
                        col3, col4, col5 = st.columns(3)
                        ef_genero = col3.selectbox("Gênero", g_opts, index=g_opts.index(db_g))
                        ef_estado_civil = col4.selectbox("Estado Civil", ec_opts, index=ec_opts.index(db_ec))
                        ef_nacionalidade = col5.text_input("Nacionalidade / Naturalidade", f_data.get('nacionalidade_naturalidade', 'Brasileira') or 'Brasileira')
                        
                        col6, col7 = st.columns(2)
                        ef_nome_mae = col6.text_input("Nome da Mãe", f_data.get('nome_mae', '') or '')
                        ef_nome_pai = col7.text_input("Nome do Pai", f_data.get('nome_pai', '') or '')
                        
                        col8, col9 = st.columns([3, 1])
                        ef_endereco = col8.text_input("Endereço Completo (Rua/Av, Nº, Compl)", f_data.get('endereco', '') or '')
                        ef_cep = col9.text_input("CEP", f_data.get('cep', '') or '')
                        
                        col10, col11, col12 = st.columns(3)
                        ef_bairro = col10.text_input("Bairro", f_data.get('bairro', '') or '')
                        ef_cidade_uf = col11.text_input("Cidade - UF", f_data.get('cidade_uf', '') or '')
                        ef_telefone = col12.text_input("Telefone / Celular (WhatsApp)", f_data.get('telefone', '') or '')
                        
                        col13, col14 = st.columns(2)
                        ef_email = col13.text_input("E-mail Pessoal", f_data.get('email', '') or '')
                        ef_emergencia = col14.text_input("Contato de Emergência (Nome, Parentesco, Tel)", f_data.get('contato_emergencia', '') or '')

                    # Expander 2: Documentação
                    with st.expander("📇 Bloco 2: Documentação e eSocial", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        ef_cnpj = col1.text_input("CPF / CNPJ", f_data.get('cnpj_cpf', '') or '')
                        ef_rg = col2.text_input("RG (Número / Órgão / Emissão)", f_data.get('rg', '') or '')
                        ef_pis = col3.text_input("PIS / PASEP", f_data.get('pis_pasep', '') or '')
                        col4, col5 = st.columns(2)
                        ef_ctps = col4.text_input("CTPS (Número / Série / UF)", f_data.get('ctps', '') or '')
                        ef_titulo = col5.text_input("Título de Eleitor (Nº / Zona / Seção)", f_data.get('titulo_eleitor', '') or '')
                        ef_cnh = st.text_input("CNH (Nº / Categoria / Validade)", f_data.get('cnh', '') or '')

                    # Expander 3: Dados Bancários
                    with st.expander("💰 Bloco 3: Dados Bancários e Dependentes", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        ef_banco = col1.text_input("Banco / Agência / Conta", f_data.get('dados_bancarios', '') or '')
                        tc_opts = ["Corrente", "Salário", "Poupança"]
                        db_tc = f_data.get('tipo_conta', 'Corrente')
                        if db_tc not in tc_opts: db_tc = "Corrente"
                        ef_tipo_conta = col2.selectbox("Tipo de Conta", tc_opts, index=tc_opts.index(db_tc))
                        ef_pix = col3.text_input("Código Pix (Opcional)", f_data.get('chave_pix', '') or '')
                        col4, col5 = st.columns(2)
                        ef_dep1 = col4.text_input("Dependente 1 (Nome / CPF / Nasc.)", f_data.get('dependente1', '') or '')
                        ef_dep2 = col5.text_input("Dependente 2 (Nome / CPF / Nasc.)", f_data.get('dependente2', '') or '')

                    # Expander 4: Dados Contratuais
                    with st.expander("👔 Bloco 4: Dados Contratuais e Jornada", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        c_lst = ["Operário", "Vendedor", "Gerente", "Administrativo", "Representante Comercial"]
                        ef_cargo = col1.selectbox("Cargo / Função", c_lst, index=c_lst.index(f_data['cargo']) if f_data['cargo'] in c_lst else 0)
                        ef_dept = col2.text_input("Departamento / Área", f_data.get('departamento', '') or '')
                        reg_opts = ["CLT", "PJ", "Estágio", "Autônomo", "Diarista", "Outro"]
                        db_reg = f_data.get('regime_contratacao', 'CLT')
                        if db_reg not in reg_opts: db_reg = "CLT"
                        ef_regime = col3.selectbox("Regime de Contratação", reg_opts, index=reg_opts.index(db_reg))
                        
                        col4, col5, col6 = st.columns(3)
                        mt_opts = ["Presencial", "Híbrido", "Remoto"]
                        db_mt = f_data.get('modelo_trabalho', 'Presencial')
                        if db_mt not in mt_opts: db_mt = "Presencial"
                        ef_modelo = col4.selectbox("Modelo de Trabalho", mt_opts, index=mt_opts.index(db_mt))
                        
                        dt_adm = pd.to_datetime(f_data['data_admissao']).date() if pd.notnull(f_data['data_admissao']) else date.today()
                        ef_admissao = col5.date_input("Data de Admissão", value=dt_adm, format="DD/MM/YYYY")
                        dt_term = pd.to_datetime(f_data['data_termino']).date() if pd.notnull(f_data['data_termino']) else None
                        ef_termino = col6.date_input("Data de Término (Opcional)", value=dt_term, format="DD/MM/YYYY")
                        
                        col7, col8, col9 = st.columns(3)
                        ef_carga = col7.text_input("Carga Horária Semanal", f_data.get('carga_horaria_semanal', '') or '')
                        ef_horario = col8.text_input("Horário de Trabalho", f_data.get('horario_trabalho', '') or '')
                        ef_escala = col9.text_input("Dias da Semana / Escala", f_data.get('escala_trabalho', '') or '')

                    # Expander 5: Remuneração
                    with st.expander("💸 Bloco 5: Remuneração, Variável e Benefícios", expanded=False):
                        col1, col2 = st.columns(2)
                        ef_salario = col1.number_input("Remuneração Fixa / Bolsa Auxílio (R$)", value=float(f_data['salario_base']))
                        
                        ad_opts = ["Não aplicável", "Periculosidade", "Insalubridade", "Noturno"]
                        db_ad = f_data.get('adicionais_legais', 'Não aplicável') or 'Não aplicável'
                        db_ad_list = [x.strip() for x in db_ad.split(",") if x.strip()]
                        ef_adicionais = col2.multiselect("Adicionais Legais", ad_opts, default=db_ad_list)
                        ef_adicionais_str = ",".join(ef_adicionais)
                        
                        col3, col4 = st.columns(2)
                        ef_comiss = col3.selectbox("Comissionamento?", ["Não", "Sim"], index=1 if f_data.get('comissionamento', 0) == 1 else 0)
                        ef_comiss_regra = col4.text_input("Regra de Comissão (Se Sim)", f_data.get('comissao_regra', '') or '')
                        
                        col5, col6, col7 = st.columns(3)
                        ef_gatilho = col5.text_input("Gatilho e Pagamento da Comissão", f_data.get('gatilho_pagamento_comissao', '') or '')
                        ef_bonus = col6.text_input("Bônus / Premiações por Meta (Regra/KPI)", f_data.get('bonus_premiacao', '') or '')
                        ef_adiant = col7.text_input("Política de Adiantamento (Vale)", f_data.get('politica_adiantamento', '') or '')
                        
                        st.markdown("🚌 **Benefícios e Custos de Transporte / Refeição**")
                        col8, col9 = st.columns(2)
                        ef_val_transp = col8.number_input("Vale Transporte / Passagem Diária (R$)", value=float(f_data.get('valor_transporte', 0.0) or 0.0), step=1.0)
                        
                        vtd_opts = ["Sem desconto", "Com desconto"]
                        db_vtd = f_data.get('vt_desconto', 'Sem desconto')
                        if db_vtd not in vtd_opts: db_vtd = "Sem desconto"
                        ef_vt_desc = col9.selectbox("Desconto Vale Transporte", vtd_opts, index=vtd_opts.index(db_vtd))
                        
                        col10, col11 = st.columns(2)
                        ef_val_refei = col10.number_input("Vale Alimentação / Refeição Diário (R$)", value=float(f_data.get('valor_refeicao', 0.0) or 0.0), step=1.0)
                        
                        vrd_opts = ["Sem desconto", "Com desconto"]
                        db_vrd = f_data.get('vr_desconto', 'Sem desconto')
                        if db_vrd not in vrd_opts: db_vrd = "Sem desconto"
                        ef_vr_desc = col11.selectbox("Desconto Refeição / Alimentação", vrd_opts, index=vrd_opts.index(db_vrd))
                        
                        ef_ajuda = st.number_input("Ajuda de Custo Mensal (R$)", value=float(f_data.get('ajuda_custo', 0.0) or 0.0), step=50.0)

                    # Expander 6: Ferramentas
                    with st.expander("💻 Bloco 6: Ferramentas e Termos de Aceite", expanded=False):
                        eq_opts = ["Notebook", "Celular", "Acesso a ERP/CRM", "Uniforme"]
                        db_eq = f_data.get('equipamentos_fornecidos', '') or ''
                        db_eq_list = [x.strip() for x in db_eq.split(",") if x.strip()]
                        ef_equip = st.multiselect("Equipamentos e Acessos Fornecidos", eq_opts, default=db_eq_list)
                        ef_equip_str = ",".join(ef_equip)
                        
                        stts_opts = ["ATIVO", "INATIVO"]
                        db_stts = f_data.get('status', 'ATIVO')
                        if db_stts not in stts_opts: db_stts = "ATIVO"
                        ef_status = st.selectbox("Status Geral do Colaborador", stts_opts, index=stts_opts.index(db_stts))

                    if st.form_submit_button("Salvar Modificações", type="primary"):
                        if not ef_nome:
                            st.error("O Nome Completo é obrigatório.")
                        else:
                            comiss_int = 1 if ef_comiss == "Sim" else 0
                            run_query(
                                """UPDATE funcionarios SET 
                                   nome=?, cargo=?, salario_base=?, regime_contratacao=?, data_admissao=?, data_nascimento=?, ajuda_custo=?, status=?, data_termino=?, cnpj_cpf=?, telefone=?, email=?, valor_transporte=?, valor_refeicao=?,
                                   genero=?, estado_civil=?, nacionalidade_naturalidade=?, nome_mae=?, nome_pai=?, endereco=?, bairro=?, cidade_uf=?, cep=?, contato_emergencia=?, rg=?, pis_pasep=?, ctps=?, titulo_eleitor=?, cnh=?,
                                   dados_bancarios=?, tipo_conta=?, chave_pix=?, dependente1=?, dependente2=?, departamento=?, modelo_trabalho=?, carga_horaria_semanal=?, horario_trabalho=?, escala_trabalho=?,
                                   adicionais_legais=?, comissionamento=?, comissao_regra=?, gatilho_pagamento_comissao=?, bonus_premiacao=?, politica_adiantamento=?, vt_desconto=?, vr_desconto=?, equipamentos_fornecidos=?
                                   WHERE id=?""",
                                (ef_nome, ef_cargo, ef_salario, ef_regime, ef_admissao, ef_nascimento, ef_ajuda, ef_status, ef_termino, ef_cnpj, ef_telefone, ef_email, ef_val_transp, ef_val_refei,
                                 ef_genero, ef_estado_civil, ef_nacionalidade, ef_nome_mae, ef_nome_pai, ef_endereco, ef_bairro, ef_cidade_uf, ef_cep, ef_emergencia, ef_rg, ef_pis, ef_ctps, ef_titulo, ef_cnh,
                                 ef_banco, ef_tipo_conta, ef_pix, ef_dep1, ef_dep2, ef_dept, ef_modelo, ef_carga, ef_horario, ef_escala,
                                 ef_adicionais_str, comiss_int, ef_comiss_regra, ef_gatilho, ef_bonus, ef_adiant, ef_vt_desc, ef_vr_desc, ef_equip_str, f_id)
                            )
                            st.success("Modificações salvas com sucesso!")
                            import time; time.sleep(1); st.rerun()

# ======= CADASTRO RÁPIDO =======
import urllib.parse
import re

LINK_ADMISSAO = "https://daatel-erp.streamlit.app/Ficha_de_Admissao"

with tab_aprovacoes:
    # --- Bloco de envio WhatsApp compacto ---
    st.markdown("#### 📲 Enviar Ficha de Admissão por WhatsApp")
    cw1, cw2, cw3 = st.columns([3, 3, 2])
    _nome_cand = cw1.text_input("Nome do candidato", placeholder="Ex: João Silva", label_visibility="visible", key="cad_rap_nome").strip()
    _tel_cand  = cw2.text_input("WhatsApp (com DDD)", placeholder="Ex: 11999998888", label_visibility="visible", key="cad_rap_tel").strip()

    _saudacao = f"Olá, {_nome_cand}!" if _nome_cand else "Olá! Seja muito bem-vindo(a)!"
    _msg = (
        f"{_saudacao}\n"
        "Estamos felizes em ter você conosco e pedimos que você preencha seu cadastro.\n"
        "É bem simples e rápido! Clique no link abaixo:\n"
        f"🔗 {LINK_ADMISSAO}\n\n"
        "💡 Tenha em mãos:\n"
        "- RG, CPF e PIS / PASEP\n"
        "- Comprovante de Residência recente\n"
        "- Dados Bancários ou Código Pix\n\n"
        "Qualquer dúvida, é só chamar aqui! 😊"
    )
    _tel_limpo = re.sub(r'\D', '', _tel_cand)
    if _tel_limpo and not _tel_limpo.startswith('55') and len(_tel_limpo) >= 10:
        _tel_limpo = '55' + _tel_limpo
    _wa_link = f"https://wa.me/{_tel_limpo}/?text={urllib.parse.quote(_msg)}" if _tel_limpo else None

    with cw3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)  # alinha verticalmente com inputs
        if _wa_link:
            st.link_button("📨 Enviar via WhatsApp", url=_wa_link, type="primary", use_container_width=True)
        else:
            st.button("📨 Enviar via WhatsApp", disabled=True, use_container_width=True, key="cad_rap_btn_dis")

    st.divider()

    # --- Painel de aprovação de pré-cadastros ---
    st.subheader("📋 Pré-Cadastros Aguardando Aprovação")
    st.caption("Revise os dados enviados pelos candidatos, preencha as informações contratuais e aprove para inseri-los no quadro de funcionários.")
    
    # Busca pré-cadastros com status 'PENDENTE'
    df_pendentes = fetch_all("SELECT id, nome, criado_em FROM pre_cadastros WHERE status = 'PENDENTE' ORDER BY criado_em DESC")
    
    if df_pendentes.empty:
        st.info("Nenhum pré-cadastro pendente para aprovação no momento.")
    else:
        # Dicionário de candidatos para o selectbox
        cand_opts = {f"{r['nome']} (Enviado em: {pd.to_datetime(r['criado_em']).strftime('%d/%m/%Y %H:%M')})": r['id'] for _, r in df_pendentes.iterrows()}
        cand_sel = st.selectbox("Selecione o Candidato para Revisão:", list(cand_opts.keys()))
        cand_id = cand_opts[cand_sel]
        
        # Carrega todos os dados do candidato selecionado
        df_cand_data = fetch_all("SELECT * FROM pre_cadastros WHERE id = ?", (cand_id,))
        if not df_cand_data.empty:
            cand = df_cand_data.iloc[0]
            
            with st.form("form_aprovar_admissao"):
                st.markdown("### 👤 1. Dados Pessoais e de Contato (Enviados pelo Candidato)")
                col1, col2 = st.columns(2)
                c_nome = col1.text_input("Nome Completo *", value=cand['nome'] or "")
                c_nascimento = col2.date_input("Data de Nascimento", value=pd.to_datetime(cand['data_nascimento']).date() if cand['data_nascimento'] else date(1995, 1, 1), format="DD/MM/YYYY")
                
                col3, col4, col5 = st.columns(3)
                c_genero = col3.selectbox("Gênero", ["Não Informar", "Masculino", "Feminino", "Outro"], index=["Não Informar", "Masculino", "Feminino", "Outro"].index(cand['genero'] or "Não Informar"))
                c_estado_civil = col4.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"], index=["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"].index(cand['estado_civil'] or "Solteiro(a)"))
                c_nacionalidade = col5.text_input("Nacionalidade / Naturalidade", value=cand['nacionalidade_naturalidade'] or "Brasileira")
                
                col6, col7 = st.columns(2)
                c_nome_mae = col6.text_input("Nome da Mãe", value=cand['nome_mae'] or "")
                c_nome_pai = col7.text_input("Nome do Pai", value=cand['nome_pai'] or "")
                
                col8, col9 = st.columns([3, 1])
                c_endereco = col8.text_input("Endereço Completo", value=cand['endereco'] or "")
                c_cep = col9.text_input("CEP", value=cand['cep'] or "")
                
                col10, col11, col12 = st.columns(3)
                c_bairro = col10.text_input("Bairro", value=cand['bairro'] or "")
                c_cidade_uf = col11.text_input("Cidade - UF", value=cand['cidade_uf'] or "")
                c_telefone = col12.text_input("Telefone / WhatsApp *", value=cand['telefone'] or "")
                
                c_email = st.text_input("E-mail Pessoal *", value=cand['email'] or "")
                c_contato_emergencia = st.text_input("Contato de Emergência", value=cand['contato_emergencia'] or "")
                
                st.markdown("### 📇 2. Documentação e eSocial (Enviados pelo Candidato)")
                col13, col14, col15 = st.columns(3)
                c_cnpj_cpf = col13.text_input("CPF *", value=cand['cnpj_cpf'] or "")
                c_rg = col14.text_input("RG", value=cand['rg'] or "")
                c_pis_pasep = col15.text_input("PIS / PASEP", value=cand['pis_pasep'] or "")
                
                col16, col17, col18 = st.columns(3)
                c_ctps = col16.text_input("CTPS", value=cand['ctps'] or "")
                c_titulo_eleitor = col17.text_input("Título de Eleitor", value=cand['titulo_eleitor'] or "")
                c_cnh = col18.text_input("CNH", value=cand['cnh'] or "")
                
                st.markdown("### 💰 3. Dados Bancários e Dependentes (Enviados pelo Candidato)")
                col19, col20, col21 = st.columns(3)
                c_dados_bancarios = col19.text_input("Banco, Agência e Conta", value=cand['dados_bancarios'] or "")
                c_tipo_conta = col20.selectbox("Tipo de Conta", ["Corrente", "Salário", "Poupança"], index=["Corrente", "Salário", "Poupança"].index(cand['tipo_conta'] or "Corrente"))
                c_chave_pix = col21.text_input("Código Pix", value=cand['chave_pix'] or "")
                
                col22, col23 = st.columns(2)
                c_dependente1 = col22.text_input("Dependente 1", value=cand['dependente1'] or "")
                c_dependente2 = col23.text_input("Dependente 2", value=cand['dependente2'] or "")
                
                st.markdown("### 👔 4. Dados Contratuais e Benefícios (Preenchido pelo RH)")
                col24, col25, col26 = st.columns(3)
                c_cargo = col24.selectbox("Cargo / Função *", ["Operário", "Vendedor", "Gerente", "Administrativo", "Representante Comercial"], key="aprov_cargo")
                c_departamento = col25.text_input("Departamento / Área", value="Produção", key="aprov_dept").strip()
                c_regime = col26.selectbox("Regime de Contratação *", ["CLT", "PJ", "Estágio", "Autônomo", "Diarista", "Outro"], key="aprov_regime")
                
                col27, col28, col29 = st.columns(3)
                c_modelo_trabalho = col27.selectbox("Modelo de Trabalho", ["Presencial", "Híbrido", "Remoto"], key="aprov_modelo")
                c_admissao = col28.date_input("Data de Admissão", value=date.today(), format="DD/MM/YYYY", key="aprov_adm")
                c_termino = col29.date_input("Data de Término (Opcional)", value=None, format="DD/MM/YYYY", key="aprov_term")
                
                col30, col31, col32 = st.columns(3)
                c_carga_horaria = col30.text_input("Carga Horária Semanal", value="44h", key="aprov_carga")
                c_horario_trabalho = col31.text_input("Horário de Trabalho", value="08:00 às 18:00", key="aprov_horario")
                c_escala = col32.text_input("Dias da Semana / Escala", value="Segunda a Sexta", key="aprov_escala")
                
                st.markdown("💸 **Remuneração e Benefícios**")
                col33, col34 = st.columns(2)
                c_salario = col33.number_input("Remuneração Fixa (R$) *", min_value=0.0, step=100.0, key="aprov_sal")
                c_adicionais = col34.multiselect("Adicionais Legais", ["Não aplicável", "Periculosidade", "Insalubridade", "Noturno"], default=["Não aplicável"], key="aprov_adicionais")
                c_adicionais_str = ",".join(c_adicionais)
                
                col35, col36 = st.columns(2)
                c_comissionamento = col35.selectbox("Comissionamento?", ["Não", "Sim"], key="aprov_comiss")
                c_comissao_regra = col36.text_input("Regra de Comissão (Se Sim)", key="aprov_comregra")
                
                col37, col38, col39 = st.columns(3)
                c_gatilho_com = col37.text_input("Gatilho e Pagamento", key="aprov_gatcom")
                c_bonus = col38.text_input("Bônus / Premiações", key="aprov_bonus")
                c_adiantamento = col39.text_input("Política de Adiantamento", key="aprov_valem")
                
                col40, col41 = st.columns(2)
                c_val_transp = col40.number_input("Vale Transporte / Passagem Diária (R$)", min_value=0.0, step=1.0, key="aprov_vt")
                c_vt_desc = col41.selectbox("Desconto Vale Transporte", ["Sem desconto", "Com desconto"], key="aprov_vtdesc")
                
                col42, col43 = st.columns(2)
                c_val_refei = col42.number_input("Vale Alimentação / Refeição Diário (R$)", min_value=0.0, step=1.0, key="aprov_vr")
                c_vr_desc = col43.selectbox("Desconto Refeição / Alimentação", ["Sem desconto", "Com desconto"], key="aprov_vrdesc")
                
                c_ajuda_custo = st.number_input("Ajuda de Custo Mensal (R$)", min_value=0.0, step=50.0, key="aprov_ajuda")
                c_equipamentos = st.multiselect("Equipamentos Fornecidos", ["Notebook", "Celular", "Acesso a ERP/CRM", "Uniforme"], key="aprov_equip")
                c_equipamentos_str = ",".join(c_equipamentos)
                
                col_btn1, col_btn2 = st.columns(2)
                aprovar = col_btn1.form_submit_button("✔️ APROVAR E CONTRATAR", type="primary", use_container_width=True)
                rejeitar = col_btn2.form_submit_button("❌ REJEITAR CADASTRO", use_container_width=True)
                
                if aprovar:
                    if not c_nome:
                        st.error("Por favor, preencha o Nome Completo.")
                    elif not c_cnpj_cpf:
                        st.error("Por favor, preencha o CPF.")
                    elif not c_telefone:
                        st.error("Por favor, preencha o Telefone.")
                    elif not c_email:
                        st.error("Por favor, preencha o E-mail.")
                    elif c_salario <= 0.0:
                        st.error("Por favor, preencha a Remuneração Fixa.")
                    else:
                        # Insere o colaborador no quadro oficial de funcionários
                        comiss_int = 1 if c_comissionamento == "Sim" else 0
                        run_query(
                            """INSERT INTO funcionarios 
                               (nome, cargo, salario_base, regime_contratacao, data_admissao, data_nascimento, ajuda_custo, status, data_termino, cnpj_cpf, telefone, email, valor_transporte, valor_refeicao,
                                genero, estado_civil, nacionalidade_naturalidade, nome_mae, nome_pai, endereco, bairro, cidade_uf, cep, contato_emergencia, rg, pis_pasep, ctps, titulo_eleitor, cnh,
                                dados_bancarios, tipo_conta, chave_pix, dependente1, dependente2, departamento, modelo_trabalho, carga_horaria_semanal, horario_trabalho, escala_trabalho,
                                adicionais_legais, comissionamento, comissao_regra, gatilho_pagamento_comissao, bonus_premiacao, politica_adiantamento, vt_desconto, vr_desconto, equipamentos_fornecidos, aceite_lgpd) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, 'ATIVO', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                            (c_nome, c_cargo, c_salario, c_regime, c_admissao, c_nascimento, c_ajuda_custo, c_termino, c_cnpj_cpf, c_telefone, c_email, c_val_transp, c_val_refei,
                             c_genero, c_estado_civil, c_nacionalidade, c_nome_mae, c_nome_pai, c_endereco, c_bairro, c_cidade_uf, c_cep, c_contato_emergencia, c_rg, c_pis_pasep, c_ctps, c_titulo_eleitor, c_cnh,
                             c_dados_bancarios, c_tipo_conta, c_chave_pix, c_dependente1, c_dependente2, c_departamento, c_modelo_trabalho, c_carga_horaria, c_horario_trabalho, c_escala,
                             c_adicionais_str, comiss_int, c_comissao_regra, c_gatilho_com, c_bonus, c_adiantamento, c_vt_desc, c_vr_desc, c_equipamentos_str)
                        )
                        
                        # Atualiza o status do pré-cadastro para APROVADO
                        run_query("UPDATE pre_cadastros SET status = 'APROVADO' WHERE id = ?", (cand_id,))
                        
                        st.success(f"Sucesso! {c_nome} foi oficialmente contratado(a) e adicionado(a) ao quadro de funcionários.")
                        import time; time.sleep(1.5); st.rerun()
                        
                if rejeitar:
                    # Marca o pré-cadastro como REJEITADO
                    run_query("UPDATE pre_cadastros SET status = 'REJEITADO' WHERE id = ?", (cand_id,))
                    st.warning("O pré-cadastro selecionado foi rejeitado e arquivado.")
                    import time; time.sleep(1.5); st.rerun()

# ======= QUADRO DE COLABORADORES =======
with tab1:
    st.subheader("Quadro Geral de Colaboradores")
    
    filtro_status = st.radio("Filtrar por Status:", ["Ativos", "Inativos", "Todos"], horizontal=True, index=0, key="quadro_status_radio")
    
    query_colab = "SELECT id, nome, cargo, status, data_admissao, data_termino, salario_base, ajuda_custo, outros_descricao, outros_valor, regime_contratacao FROM funcionarios WHERE 1=1"
    if filtro_status == "Ativos":
        query_colab += " AND status='ATIVO'"
    elif filtro_status == "Inativos":
        query_colab += " AND status='INATIVO'"
        
    df_func = fetch_all(query_colab)
    
    if not df_func.empty:
        df_display = df_func.rename(columns={
            'nome': 'Nome', 'cargo': 'Cargo', 'status': 'Status',
            'data_admissao': 'Início', 'data_termino': 'Término',
            'salario_base': 'Rem. Fixa', 'ajuda_custo': 'Ajuda Custo', 
            'outros_descricao': 'Outros (Ref)', 'outros_valor': 'Outros (Valor)', 
            'regime_contratacao': 'Regime'
        })
        
        df_display['Início'] = pd.to_datetime(df_display['Início'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
        df_display['Término'] = pd.to_datetime(df_display['Término'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
        
        st.dataframe(df_display, width='stretch', hide_index=True)
        
        csv = df_display.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            label="📥 Exportar Lista de Colaboradores (CSV)",
            data=csv,
            file_name='colaboradores.csv',
            mime='text/csv',
            key="quadro_export_csv"
        )
    else:
        st.info("Nenhum colaborador encontrado com este filtro.")

# ======= HELPER: CÁLCULOS DE FOLHA =======
def _calc_folha(sal_base, ajuda, outros, vt_bruto, vt_desc_flag, vr_diario, vr_desc_flag, dias, regime, faltas=0, adiantamento=0.0):
    desc_faltas = round((sal_base / 30.0) * faltas, 2)
    desc_dsr = round((sal_base / 30.0) * faltas, 2) if regime == 'CLT' else 0.0
    bruto = max(0.0, sal_base - desc_faltas - desc_dsr + ajuda + outros)
    if bruto <= 1621.00:
        inss = bruto * 0.075
    elif bruto <= 2902.84:
        inss = (bruto * 0.09) - 24.32
    elif bruto <= 4354.27:
        inss = (bruto * 0.12) - 111.40
    elif bruto <= 8475.55:
        inss = (bruto * 0.14) - 198.49
    else:
        inss = 988.09
    base_ir = max(0.0, bruto - inss)
    if bruto <= 5000.00:
        irrf = 0.0
    else:
        if base_ir <= 2428.80: std = 0.0
        elif base_ir <= 2826.65: std = (base_ir * 0.075) - 182.16
        elif base_ir <= 3751.05: std = (base_ir * 0.15)  - 394.16
        elif base_ir <= 4664.68: std = (base_ir * 0.225) - 675.49
        else: std = (base_ir * 0.275) - 908.73
        if bruto <= 7350.00:
            irrf = max(0.0, std - max(0.0, 978.62 - (0.133145 * base_ir)))
        else:
            irrf = std
    desc_vt  = min(0.06 * sal_base, vt_bruto) if (regime == 'CLT' and vt_desc_flag == 'Com desconto') else 0.0
    vt_liq   = max(0.0, vt_bruto - desc_vt)
    
    vr_bruto = vr_diario * max(0, dias - faltas)
    desc_vr  = round(0.20 * vr_bruto, 2) if (regime == 'CLT' and vr_desc_flag == 'Com desconto') else 0.0
    vr_liq   = max(0.0, vr_bruto - desc_vr)
    
    encargo  = round(0.28 * bruto, 2) if regime == 'CLT' else 0.0
    liq_func = max(0.0, bruto - inss - irrf - desc_vt - desc_vr - adiantamento)
    custo    = round(liq_func + adiantamento + vt_bruto + vr_bruto + encargo, 2)
    return dict(bruto=round(bruto,2), inss=round(inss,2), irrf=round(irrf,2),
                desc_vt=round(desc_vt,2), vt_liq=round(vt_liq,2),
                desc_vr=round(desc_vr,2), vr_liq=round(vr_liq,2), vr_bruto=round(vr_bruto,2),
                encargo=round(encargo,2), liquido_func=round(liq_func,2), custo_empresa=custo,
                desconto_faltas=desc_faltas, desconto_dsr=desc_dsr, adiantamento=round(adiantamento,2))

# ======= PAGAMENTO =======
with tab2:
    st.subheader("Folha de Pagamento")
    subtab_ind, subtab_lote = st.tabs(["📋 Individual", "📊 Fechamento em Lote"])

    df_func2 = fetch_all("""
        SELECT id, nome, salario_base, ajuda_custo, outros_valor,
               regime_contratacao, valor_transporte, valor_refeicao,
               vt_desconto, vr_desconto, cnpj_cpf, dados_bancarios, chave_pix,
               politica_adiantamento
        FROM funcionarios
        WHERE status='ATIVO' AND regime_contratacao NOT IN ('PJ', 'Autônomo')
    """)

    # ---- SUB-TAB 1: INDIVIDUAL ----
    with subtab_ind:
        if df_func2.empty:
            st.warning("Cadastre colaboradores CLT ou Diaristas ativos primeiro na aba Cadastro.")
        else:
            func_dict    = dict(zip(df_func2['nome'], df_func2['id']))
            salario_dict = dict(zip(df_func2['nome'], df_func2['salario_base']))
            ajuda_dict   = dict(zip(df_func2['nome'], df_func2['ajuda_custo']))
            outros_dict  = dict(zip(df_func2['nome'], df_func2['outros_valor']))
            regime_dict  = dict(zip(df_func2['nome'], df_func2['regime_contratacao']))
            transp_dict  = dict(zip(df_func2['nome'], df_func2['valor_transporte']))
            refeicao_dict= dict(zip(df_func2['nome'], df_func2['valor_refeicao']))
            vt_desc_dict = dict(zip(df_func2['nome'], df_func2['vt_desconto']))
            vr_desc_dict = dict(zip(df_func2['nome'], df_func2['vr_desconto']))

            nome_pgto  = st.selectbox("Selecione o Colaborador (Apenas Ativos)", list(func_dict.keys()), key="pgto_func_select")
            emp_regime = regime_dict.get(nome_pgto, 'CLT')
            base_sal   = float(salario_dict[nome_pgto] or 0.0)
            base_ajuda = float(ajuda_dict[nome_pgto]   or 0.0)
            base_outros= float(outros_dict[nome_pgto]  or 0.0)
            base_vt    = float(transp_dict.get(nome_pgto, 0.0) or 0.0)
            base_vr_d  = float(refeicao_dict.get(nome_pgto, 0.0) or 0.0)
            db_vt_desc = vt_desc_dict.get(nome_pgto, 'Sem desconto')
            db_vr_desc = vr_desc_dict.get(nome_pgto, 'Sem desconto')
            _f = _calc_folha(base_sal, base_ajuda, base_outros, base_vt * 22, db_vt_desc, base_vr_d, db_vr_desc, 22, emp_regime)

            with st.form("form_pagamento", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                data_pgto = col1.date_input("Data de Pagamento", value=date.today(), format="DD/MM/YYYY")
                mes_ref   = col2.text_input("Mês Referência (Ex: 03/2026)", value=data_pgto.strftime("%m/%Y"))
                sal_base  = col3.number_input("Rem. Fixa (R$)", min_value=0.0, value=base_sal, step=10.0)
                st.markdown("##### Outras Verbas, Absenteísmo e Encargos")
                col4, col5, col_days, col_faltas = st.columns(4)
                ajuda  = col4.number_input("Ajuda de Custo (R$)", min_value=0.0, value=base_ajuda, step=10.0)
                outros = col5.number_input("Outros Valores (R$)", min_value=0.0, value=base_outros, step=10.0)
                dias_trab = col_days.number_input("Dias Previstos", min_value=1, max_value=31, value=22, step=1)
                faltas = col_faltas.number_input("Faltas (Dias)", min_value=0, max_value=31, value=0, step=1)
                
                # Recalcula com valores provisórios/editados da tela (adiantamento inicial = 0.0)
                _f_calc = _calc_folha(sal_base, ajuda, outros, base_vt * max(0, dias_trab - faltas), db_vt_desc, base_vr_d, db_vr_desc, dias_trab, emp_regime, faltas, 0.0)
                
                col_vt, col_vr, col_adiant, col_enc = st.columns(4)
                vt_pago    = col_vt.number_input("Vale Transporte (R$)", min_value=0.0, value=_f_calc['vt_liq'], step=10.0)
                vr_pago    = col_vr.number_input("Vale Refeição (R$)", min_value=0.0, value=_f_calc['vr_bruto'], step=10.0)
                adiant_pago = col_adiant.number_input("Adiantamento (Vale) (R$)", min_value=0.0, value=0.0, step=50.0)
                custo_previ= col_enc.number_input("Encargo Patronal (R$)", min_value=0.0, value=_f_calc['encargo'], step=10.0)
                
                # O total desembolsado pela empresa desconta as faltas, DSR, descontos de VT/VR recolhidos em folha e desconta o adiantamento (pois já foi pago no meio do mês)
                _f_calc = _calc_folha(sal_base, ajuda, outros, vt_pago, db_vt_desc, base_vr_d, db_vr_desc, dias_trab, emp_regime, faltas, adiant_pago)
                valor_total = max(0.0, sal_base - _f_calc['desconto_faltas'] - _f_calc['desconto_dsr'] - _f_calc['desc_vt'] - _f_calc['desc_vr'] - adiant_pago) + ajuda + outros + vt_pago + vr_pago + custo_previ + adiant_pago
                if emp_regime == 'CLT':
                    st.info(
                        f"**Demonstrativo do Colaborador (CLT):**\n"
                        f"- Salário Base: R$ {sal_base:,.2f}\n"
                        f"- Desconto Faltas ({faltas} dias): -R$ {_f_calc['desconto_faltas']:,.2f}\n"
                        f"- Desconto DSR s/ Faltas: -R$ {_f_calc['desconto_dsr']:,.2f}\n"
                        f"- Salário Bruto: R$ {_f_calc['bruto']:,.2f}\n"
                        f"- Desconto INSS: -R$ {_f_calc['inss']:,.2f}\n"
                        f"- Desconto IRRF: -R$ {_f_calc['irrf']:,.2f}\n"
                        f"- Desconto VT (6%): -R$ {_f_calc['desc_vt']:,.2f}\n"
                        f"- Desconto VR (20%): -R$ {_f_calc['desc_vr']:,.2f}\n"
                        f"- Desconto Adiantamento (Vale): -R$ {_f_calc['adiantamento']:,.2f}\n"
                        f"**Salário Líquido Estimado a Receber:** R$ {_f_calc['liquido_func']:,.2f}"
                    )
                st.info(f"**Total Desembolsado pelo Caixa da Empresa (Fechamento):** R$ {valor_total:,.2f}")
                if st.form_submit_button("Registrar Pagamento"):
                    if valor_total > 0:
                        _f_final = _calc_folha(sal_base, ajuda, outros, vt_pago, db_vt_desc, base_vr_d, db_vr_desc, dias_trab, emp_regime, faltas, adiant_pago)
                        run_query(
                            """INSERT INTO rh_pagamentos
                               (funcionario_id, data_pagamento, mes_referencia, salario_base_pago,
                                passagem, refeicao, custo_previdenciario, valor_total_pago,
                                desc_inss, desc_irrf, desc_vt, desc_vr, valor_liquido_funcionario,
                                tipo_fechamento, faltas, desconto_faltas, desconto_dsr, adiantamento)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INDIVIDUAL', ?, ?, ?, ?)""",
                            (func_dict[nome_pgto], data_pgto, mes_ref, sal_base,
                             vt_pago + ajuda + outros, vr_pago, custo_previ, valor_total,
                             _f_final['inss'], _f_final['irrf'], _f_final['desc_vt'], _f_final['desc_vr'], _f_final['liquido_func'],
                             faltas, _f_final['desconto_faltas'], _f_final['desconto_dsr'], _f_final['adiantamento'])
                        )
                        run_query(
                            "INSERT INTO fluxo_caixa (data, tipo, categoria, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                            (data_pgto, "Saída", "Folha de Pagamento", valor_total,
                             f"Pagamento Rem. Fixa e Benefícios ({mes_ref}) - {nome_pgto} ({faltas} faltas, {adiant_pago} vale)")
                        )
                        st.success("Pagamento lançado com sucesso e adicionado ao fluxo de caixa!")
                        import time; time.sleep(1); st.rerun()

            st.markdown("---")
            st.subheader("Histórico de Pagamentos")
            df_pgtos = fetch_all('''
                SELECT p.id as ID, f.nome as Colaborador, p.data_pagamento as "Data Pgto",
                       p.mes_referencia as "Mes", p.salario_base_pago as "Rem. Fixa",
                       COALESCE(p.faltas, 0) as "Faltas",
                       COALESCE(p.desconto_faltas, 0.0) as "Dedução Faltas (R$)",
                       COALESCE(p.desconto_dsr, 0.0) as "Dedução DSR (R$)",
                       COALESCE(p.desc_vt, 0.0) as "Desc. VT (R$)",
                       COALESCE(p.desc_vr, 0.0) as "Desc. VR (R$)",
                       COALESCE(p.adiantamento, 0.0) as "Vale (Adiant.) (R$)",
                       p.passagem as "Ajuda/Outros", p.refeicao as "Refeicao",
                       p.custo_previdenciario as "Encargos", p.valor_total_pago as "Total Pago (R$)",
                       COALESCE(p.tipo_fechamento, 'INDIVIDUAL') as "Tipo"
                FROM rh_pagamentos p JOIN funcionarios f ON p.funcionario_id = f.id
                ORDER BY p.data_pagamento DESC
            ''')
            if not df_pgtos.empty:
                df_pgtos['Data Pgto'] = pd.to_datetime(df_pgtos['Data Pgto']).dt.strftime('%d/%m/%Y')
                st.dataframe(df_pgtos, width="stretch", hide_index=True)
                st.download_button("📥 Exportar Histórico (CSV)",
                    data=df_pgtos.to_csv(index=False, sep=';').encode('utf-8-sig'),
                    file_name='historico_pagamentos.csv', mime='text/csv')

    # ---- SUB-TAB 2: FECHAMENTO EM LOTE ----
    with subtab_lote:
        st.markdown("#### 📊 Fechamento Mensal em Lote")
        st.caption("Calcule a folha de todos os colaboradores ativos, ajuste o que precisar e feche o mês com um clique.")

        def _get_default_adiantamento(sal_base, politica):
            if not politica:
                return 0.0
            p_str = str(politica).strip().lower()
            if '40%' in p_str or '40' in p_str:
                return round(sal_base * 0.40, 2)
            import re
            numeros = re.findall(r'\d+(?:\.\d+)?', p_str.replace(',', '.'))
            if numeros:
                try:
                    val = float(numeros[0])
                    if val < 1.0:
                        return round(sal_base * val, 2)
                    return val
                except ValueError:
                    pass
            return 0.0

        if df_func2.empty:
            st.warning("Nenhum colaborador CLT ou Diarista ativo cadastrado.")
        else:
            cl1, cl2, cl3 = st.columns([2, 2, 2])
            mes_lote  = cl1.text_input("Mês de Referência (MM/AAAA)", value=date.today().strftime("%m/%Y"), key="lote_mes")
            data_lote = cl2.date_input("Data de Pagamento", value=date.today(), format="DD/MM/YYYY", key="lote_data")
            dias_pad  = cl3.number_input("Dias trabalhados (padrão)", min_value=1, max_value=31, value=22, step=1, key="lote_dias")

            if st.button("🔄 Calcular Folha do Mês", type="primary", key="lote_calcular"):
                st.session_state['lote_calculado']  = True
                st.session_state['lote_mes_ref']    = mes_lote
                st.session_state['lote_data_pgto']  = str(data_lote)
                st.session_state['lote_dias_pad']   = int(dias_pad)

            if st.session_state.get('lote_calculado'):
                _mes  = st.session_state['lote_mes_ref']
                _data = st.session_state['lote_data_pgto']
                _dias = st.session_state['lote_dias_pad']

                df_exist = fetch_all("SELECT 1 FROM rh_pagamentos WHERE mes_referencia = ? LIMIT 1", (_mes,))
                ja_fechado = not df_exist.empty

                # Monta dados da folha
                rows = []
                for _, r in df_func2.iterrows():
                    sal = float(r['salario_base'] or 0.0)
                    ajd = float(r['ajuda_custo']  or 0.0)
                    out = float(r['outros_valor']  or 0.0)
                    vtb = float(r['valor_transporte'] or 0.0)
                    vrd = float(r['valor_refeicao']   or 0.0)
                    vtf = str(r['vt_desconto'] or 'Sem desconto')
                    vrf = str(r['vr_desconto'] or 'Sem desconto')
                    reg = str(r['regime_contratacao'] or 'CLT')
                    politica = r.get('politica_adiantamento', '') or ''
                    adiant_padrao = _get_default_adiantamento(sal, politica)
                    # Faltas padrão inicial = 0
                    f   = _calc_folha(sal, ajd, out, vtb * _dias, vtf, vrd, vrf, _dias, reg, 0, adiant_padrao)
                    rows.append({
                        '_id':          int(r['id']),
                        'Nome':         str(r['nome']),
                        'Regime':       reg,
                        'CPF':          str(r['cnpj_cpf']      or ''),
                        'Banco/Ag/Cc':  str(r['dados_bancarios'] or ''),
                        'Chave PIX':    str(r['chave_pix']     or ''),
                        'Dias':         _dias,
                        'Faltas':       0,
                        'Vale':         adiant_padrao,
                        'DSR Desc.':    f['desconto_dsr'],
                        'Desc. VT':     f['desc_vt'],
                        'Desc. VR':     f['desc_vr'],
                        'Rem. Fixa':    sal,
                        'Ajuda Custo':  ajd,
                        'VT Liq.':      f['vt_liq'],
                        'VR':           f['vr_bruto'],
                        'Bruto':        f['bruto'],
                        'INSS':         f['inss'],
                        'IRRF':         f['irrf'],
                        'Liq. Func.':   f['liquido_func'],
                        'Enc. Patronal':f['encargo'],
                        'Custo Empresa':f['custo_empresa'],
                        '_vt_desc':     vtf,
                        '_vr_desc':     vrf,
                        '_vt_bruto':    vtb,
                        '_vr_diario':   vrd,
                        '_politica_adiant': politica,
                    })

                df_lote = pd.DataFrame(rows)
                col_edit = ['Dias', 'Faltas', 'Rem. Fixa', 'Ajuda Custo', 'Vale', 'VT Liq.', 'VR']
                col_calc = ['DSR Desc.', 'Desc. VT', 'Desc. VR', 'Bruto', 'INSS', 'IRRF', 'Liq. Func.', 'Enc. Patronal', 'Custo Empresa']
                col_info = ['Nome', 'Regime', 'CPF', 'Banco/Ag/Cc', 'Chave PIX']

                col_cfg = {}
                col_cfg['Nome']       = st.column_config.TextColumn("Nome", disabled=True)
                col_cfg['Regime']     = st.column_config.TextColumn("Regime", disabled=True, width="small")
                col_cfg['CPF']        = st.column_config.TextColumn("CPF", disabled=True)
                col_cfg['Banco/Ag/Cc']= st.column_config.TextColumn("Banco/Ag/Cc", disabled=True)
                col_cfg['Chave PIX']  = st.column_config.TextColumn("Chave PIX", disabled=True)
                col_cfg['Dias']       = st.column_config.NumberColumn("Dias", min_value=1, max_value=31, step=1, width="small")
                col_cfg['Faltas']     = st.column_config.NumberColumn("Faltas", min_value=0, max_value=31, step=1, width="small")
                col_cfg['Vale']       = st.column_config.NumberColumn("Vale", min_value=0.0, format="R$ %.2f")
                for c in ['Rem. Fixa', 'Ajuda Custo', 'VT Liq.', 'VR']:
                    col_cfg[c] = st.column_config.NumberColumn(c, format="R$ %.2f")
                for c in col_calc:
                    col_cfg[c] = st.column_config.NumberColumn(c, format="R$ %.2f", disabled=True)

                st.markdown("**✏️ Colunas editáveis:** Dias, Faltas, Rem. Fixa, Ajuda Custo, Vale, VT e VR — Desconto de Faltas/DSR/Vales, INSS/IRRF recalculados automaticamente.")
                df_editado = st.data_editor(
                    df_lote.drop(columns=['_id', '_vt_desc', '_vr_desc', '_vt_bruto', '_vr_diario', '_politica_adiant']),
                    column_config=col_cfg,
                    disabled=col_info + col_calc,
                    hide_index=True,
                    use_container_width=True,
                    key="lote_editor"
                )

                # Recalcula com valores editados pelo RH
                rows_final = []
                for i, row in df_editado.iterrows():
                    orig  = df_lote.iloc[i]
                    sal_e = float(row['Rem. Fixa'])
                    ajd_e = float(row['Ajuda Custo'])
                    vt_e  = float(row['VT Liq.'])
                    vr_e  = float(row['VR'])
                    dias_e= int(row['Dias'])
                    faltas_e = int(row['Faltas'])
                    adiant_e = float(row['Vale'])
                    reg_e = str(orig['Regime'])
                    
                    vt_desc_flag = str(orig['_vt_desc'])
                    vr_desc_flag = str(orig['_vr_desc'])
                    
                    f2    = _calc_folha(sal_e, ajd_e, 0, vt_e, vt_desc_flag, vr_e / max(1, dias_e - faltas_e), vr_desc_flag, dias_e, reg_e, faltas_e, adiant_e)
                    liq_e = f2['liquido_func']
                    rows_final.append({
                        '_id': int(orig['_id']), 'nome': str(orig['Nome']),
                        'cpf': str(orig['CPF']), 'banco': str(orig['Banco/Ag/Cc']),
                        'pix': str(orig['Chave PIX']), 'regime': reg_e,
                        'sal': sal_e, 'ajuda': ajd_e, 'vt': vt_e, 'vr': vr_e,
                        'inss': f2['inss'], 'irrf': f2['irrf'], 'enc': f2['encargo'],
                        'liq': liq_e, 'custo': f2['custo_empresa'],
                        'faltas': faltas_e, 'desc_faltas': f2['desconto_faltas'],
                        'desc_dsr': f2['desconto_dsr'],
                        'desc_vt': f2['desc_vt'],
                        'desc_vr': f2['desc_vr'],
                        'bruto': f2['bruto'],
                        'adiantamento': adiant_e
                    })

                total_liq   = sum(r['liq']  for r in rows_final)
                total_folha = sum(r['custo'] for r in rows_final)

                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("👥 Colaboradores", len(rows_final))
                mc2.metric("💳 Total Líquido (Funcionários)", f"R$ {total_liq:,.2f}")
                mc3.metric("🏭 Custo Total Empresa", f"R$ {total_folha:,.2f}")

                st.markdown("---")
                bc1, bc2 = st.columns(2)

                with bc1:
                    if not ja_fechado:
                        if st.button("✅ Fechar Folha do Mês", type="primary", use_container_width=True, key="lote_fechar"):
                            import time as _t
                            for r in rows_final:
                                run_query(
                                    """INSERT INTO rh_pagamentos
                                       (funcionario_id, data_pagamento, mes_referencia,
                                        salario_base_pago, passagem, refeicao, custo_previdenciario,
                                        valor_total_pago, desc_inss, desc_irrf, desc_vt, desc_vr,
                                        valor_liquido_funcionario, tipo_fechamento,
                                        faltas, desconto_faltas, desconto_dsr, adiantamento)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'LOTE', ?, ?, ?, ?)""",
                                    (r['_id'], _data, _mes, r['sal'],
                                     r['vt'] + r['ajuda'], r['vr'], r['enc'], r['custo'],
                                     r['inss'], r['irrf'], r['desc_vt'], r['desc_vr'], r['liq'],
                                     r['faltas'], r['desc_faltas'], r['desc_dsr'], r['adiantamento'])
                                )
                            run_query(
                                "INSERT INTO fluxo_caixa (data, tipo, categoria, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                                (_data, "Saída", "Folha de Pagamento", total_folha,
                                 f"Fechamento de Folha em Lote — {_mes} ({len(rows_final)} colaboradores)")
                            )
                            st.success(f"✅ Folha de {_mes} fechada! {len(rows_final)} colaboradores — Total: R$ {total_folha:,.2f}")
                            st.session_state['lote_calculado'] = False
                            _t.sleep(1.5); st.rerun()
                    else:
                        st.button("✅ Folha já fechada para este mês", disabled=True, use_container_width=True)

                with bc2:
                    csv_rows = [{'Nome': r['nome'], 'CPF': r['cpf'], 'Banco_Ag_Cc': r['banco'],
                                 'Chave_PIX': r['pix'], 'Regime': r['regime'], 'Mes_Ref': _mes,
                                 'Faltas': r['faltas'],
                                 'Desconto_Faltas_R$': f"{r['desc_faltas']:.2f}".replace('.',','),
                                 'Desconto_DSR_R$':    f"{r['desc_dsr']:.2f}".replace('.',','),
                                 'Vale_Adiantamento_R$': f"{r['adiantamento']:.2f}".replace('.',','),
                                 'Desconto_VT_R$':     f"{r['desc_vt']:.2f}".replace('.',','),
                                 'Desconto_VR_R$':     f"{r['desc_vr']:.2f}".replace('.',','),
                                 'Bruto_R$':     f"{r['bruto']:.2f}".replace('.',','),
                                 'INSS_R$':      f"{r['inss']:.2f}".replace('.',','),
                                 'IRRF_R$':      f"{r['irrf']:.2f}".replace('.',','),
                                 'Liquido_Func_R$': f"{r['liq']:.2f}".replace('.',','),
                                 'VT_R$':        f"{r['vt']:.2f}".replace('.',','),
                                 'VR_R$':        f"{r['vr']:.2f}".replace('.',','),
                                 'Enc_Patronal_R$': f"{r['enc']:.2f}".replace('.',','),
                                 'Custo_Empresa_R$': f"{r['custo']:.2f}".replace('.',',')}
                                for r in rows_final]
                    csv_banco = pd.DataFrame(csv_rows).to_csv(index=False, sep=';').encode('utf-8-sig')
                    st.download_button(
                        "📥 Exportar CSV para Banco",
                        data=csv_banco,
                        file_name=f"folha_{_mes.replace('/','_')}.csv",
                        mime='text/csv',
                        use_container_width=True,
                        key="lote_csv"
                    )

    # ---- TAB: BENEFÍCIOS SEMANAIS ----
    with tab_beneficios:
        df_ativos = fetch_all("SELECT id, nome, valor_transporte, valor_refeicao FROM funcionarios WHERE status='ATIVO'")
        
        if df_ativos.empty:
            st.info("Nenhum colaborador ativo cadastrado no sistema.")
        else:
            from datetime import date, timedelta
            
            df_pc_b = fetch_all("SELECT id, codigo, nome FROM planos_de_contas WHERE categoria NOT IN ('RECEITA', 'RECEITA_NAO_OP') ORDER BY codigo")
            op_pc_b = {}
            default_idx_pc = 0
            if not df_pc_b.empty:
                for idx_pc, r in df_pc_b.iterrows():
                    op_pc_b[f"{r['codigo']} - {r['nome']}"] = r['id']
                    if r['codigo'] == '2.3.6':
                        default_idx_pc = idx_pc
                        
            # Layout de colunas proporcional e equilibrado
            col_b1, col_b2, col_b3, col_b4 = st.columns([2.5, 1.2, 1.2, 1.1])
            pc_sel_b = col_b1.selectbox("Plano de Contas", list(op_pc_b.keys()), index=default_idx_pc, key="ben_pc_sel")
            
            # Seleção do intervalo semanal de pagamento
            hoje = date.today()
            default_start = hoje - timedelta(days=hoje.weekday()) if hoje.weekday() < 5 else hoje
            default_end = default_start + timedelta(days=4)
            
            data_ini = col_b2.date_input("Início da Semana", value=default_start, format="DD/MM/YYYY", key="ben_data_ini")
            data_fim = col_b3.date_input("Fim da Semana", value=default_end, format="DD/MM/YYYY", key="ben_data_fim")
            venc_b = col_b4.date_input("Vencimento", value=data_fim, format="DD/MM/YYYY", key="ben_venc_sel")
            
            # Descrição dinâmica baseada nas datas
            data_ini_str = data_ini.strftime("%d/%m")
            data_fim_str = data_fim.strftime("%d/%m")
            default_desc = f"Pgto passagem e refeição - Período: {data_ini_str} a {data_fim_str}"
            
            desc_modelo_b = st.text_input("Descrição / Histórico do Lançamento", value=default_desc, key="ben_desc_modelo")
            
            # Monta DataFrame inicial para o data_editor
            rows_b = []
            for _, r in df_ativos.iterrows():
                vt_diario = float(r['valor_transporte'] or 0.0)
                vr_diario = float(r['valor_refeicao'] or 0.0)
                
                vt_semanal = round(vt_diario * 5.0, 2)
                vr_semanal = round(vr_diario * 5.0, 2)
                
                rows_b.append({
                    "Gerar?": True,
                    "Funcionario ID": int(r['id']),
                    "Colaborador": str(r['nome']),
                    "Passagem R$": vt_semanal,
                    "Alimentação R$": vr_semanal
                })
                
            df_editor_b = pd.DataFrame(rows_b)
            
            st.markdown("**Ajuste os valores para cada colaborador conforme necessário (desmarque os que não devem receber esta semana):**")
            edited_df_b = st.data_editor(
                df_editor_b,
                hide_index=True,
                column_config={
                    "Gerar?": st.column_config.CheckboxColumn("Gerar?", default=True),
                    "Funcionario ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                    "Colaborador": st.column_config.TextColumn("Colaborador", disabled=True),
                    "Passagem R$": st.column_config.NumberColumn("Passagem R$", format="%.2f", min_value=0.0),
                    "Alimentação R$": st.column_config.NumberColumn("Alimentação R$", format="%.2f", min_value=0.0)
                },
                use_container_width=True,
                key="editor_beneficios_semanais"
            )
            
            if st.button("💾 Gerar Lançamentos de Benefícios", type="primary", use_container_width=True, key="btn_gerar_beneficios"):
                pc_id_b = op_pc_b[pc_sel_b]
                venc_str_b = venc_b.strftime("%Y-%m-%d")
                
                gerados_vt = 0
                gerados_vr = 0
                
                with st.spinner("Registrando lançamentos no Contas a Pagar..."):
                    for _, r in edited_df_b.iterrows():
                        if not r["Gerar?"]:
                            continue
                            
                        nome_c = r["Colaborador"]
                        val_vt = float(r["Passagem R$"])
                        val_vr = float(r["Alimentação R$"])
                        
                        # Lança Passagem se > 0
                        if val_vt > 0.0:
                            desc_vt = f"{desc_modelo_b} - VT - {nome_c}"
                            run_query(
                                "INSERT INTO contas_a_pagar (plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
                                (pc_id_b, desc_vt, val_vt, venc_str_b)
                            )
                            gerados_vt += 1
                            
                        # Lança Alimentação se > 0
                        if val_vr > 0.0:
                            desc_vr = f"{desc_modelo_b} - VR - {nome_c}"
                            run_query(
                                "INSERT INTO contas_a_pagar (plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
                                (pc_id_b, desc_vr, val_vr, venc_str_b)
                            )
                            gerados_vr += 1
                            
                st.success(f"✅ Lançamentos concluídos: {gerados_vt} de passagem e {gerados_vr} de alimentação gerados com sucesso!")
                import time; time.sleep(1.5); st.rerun()


# ======= 3. COMISSÕES =======
with tab3:
    st.subheader("Malha Contábil: Repasse de Comissões e Representantes")
    st.markdown("""
    > **Políticas de Governança Comercial:** 
    > As comissões são provisionadas dinamicamente à medida que as vendas são faturadas ou liquidadas. 
    > No entanto, para evitar dispersão de caixa, elas **não são pagas individualmente**. 
    > Utilize esta Central de Fechamento para auditar os lançamentos mensais, conferir as travas de recebimento, **abater devoluções/sangrias comerciais** e **autorizar um repasse consolidado único** para a conta de cada representante na data de vencimento acordada.
    """)
    
    hoje = date.today()
    
    col_f1, col_f2 = st.columns(2)
    mes_filtro = col_f1.selectbox("Apontamento Cíclico (Mês Base)", [hoje.strftime('%Y-%m'), (hoje - timedelta(days=30)).strftime('%Y-%m')], key="com_mes_filtro")
    
    df_vends_list = fetch_all("SELECT id, nome, gatilho_comissao, dia_vencimento_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%' ORDER BY nome")
    if df_vends_list.empty:
        st.warning("Cadastre representantes comerciais no RH primeiro.")
    else:
        vendedor_opts = {r['nome']: r for _, r in df_vends_list.iterrows()}
        vendedor_sel = col_f2.selectbox("Selecione o Vendedor / Rota para Auditoria", list(vendedor_opts.keys()))
        
        vendedor_obj = vendedor_opts[vendedor_sel]
        v_id = vendedor_obj['id']
        vendedor_nome = vendedor_obj['nome']
        v_gatilho = str(vendedor_obj['gatilho_comissao'] or 'FATURAMENTO').upper()
        v_dia_venc = int(vendedor_obj['dia_vencimento_comissao'] or 31)
        
        # Query detalhada de vendas e comissões daquele vendedor no mês selecionado
        q_com = '''
            SELECT v.id as 'Doc', c.nome as 'K-Account', v.data as 'Data Lançada', 
                   COALESCE(cr.status, 'N/A') as 'Tit_Receb', v.valor_total as 'Vendido Bruto R$', 
                   v.comissao_valor as 'Retencao'
            FROM vendas v
            JOIN clientes c ON v.cliente_id=c.id
            LEFT JOIN contas_a_receber cr ON cr.venda_id=v.id
            WHERE v.vendedor_id = ? AND strftime('%Y-%m', v.data) = ? AND v.status = 'FATURADO'
            ORDER BY v.id DESC
        '''
        df_com = fetch_all(q_com, (v_id, mes_filtro))
        
        # --- CÁLCULO DE ESTORNOS POR DEVOLUÇÕES / DESCONTOS ---
        estornos_list = []
        total_estorno_comissao = 0.0
        
        df_devs = fetch_all('''
            SELECT d.id, d.data, c.nome as cliente_nome, p.nome as produto_nome, 
                   d.valor_financeiro_abatido, COALESCE(c.rede_clientes, '') as rede_clientes, 
                   d.produto_id, d.motivo
            FROM devolucoes d
            JOIN clientes c ON d.cliente_id = c.id
            JOIN produtos p ON d.produto_id = p.id
            WHERE c.representante_id = ? AND strftime('%Y-%m', d.data) = ?
        ''', (v_id, mes_filtro))
        
        for idx, r in df_devs.iterrows():
            val_dev = float(r['valor_financeiro_abatido'] or 0.0)
            prod_id = int(r['produto_id'])
            rede_c = r['rede_clientes']
            if not rede_c: rede_c = "TODOS"
            
            # Fetch rule
            df_regra = fetch_all('''
                SELECT percentual 
                FROM comissoes_regras 
                WHERE vendedor_id = ? 
                  AND (produto_id = ? OR produto_id IS NULL)
                  AND (rede_clientes = ? OR rede_clientes = 'TODOS')
                ORDER BY (CASE WHEN produto_id = ? THEN 2 ELSE 1 END) DESC,
                         (CASE WHEN rede_clientes = ? THEN 2 ELSE 1 END) DESC
                LIMIT 1
            ''', (v_id, prod_id, rede_c, prod_id, rede_c))
            
            perc = float(df_regra.iloc[0]['percentual']) if not df_regra.empty else 0.0
            if perc <= 0.0:
                perc = 5.0 # Fallback padrão de segurança
                
            estorno_val = val_dev * (perc / 100.0)
            total_estorno_comissao += estorno_val
            
            estornos_list.append({
                "ID": int(r['id']),
                "Data": pd.to_datetime(r['data']).strftime('%d/%m/%Y'),
                "Cliente": r['cliente_nome'],
                "Produto": r['produto_nome'],
                "Motivo": r['motivo'],
                "Valor Avariado": val_dev,
                "Comissão Estornada": estorno_val
            })
            
        if df_com.empty and len(estornos_list) == 0:
            st.info(f"Nenhuma atividade comercial (vendas ou devoluções) registrada para **{vendedor_nome}** na competência **{mes_filtro}**.")
        else:
            # Determina o status da comissão para cada item
            total_vendido = 0.0
            total_comissao = 0.0
            total_liberado = 0.0
            
            if not df_com.empty:
                df_com['Status Comissão'] = ""
                df_com['Liberada_Float'] = 0.0
                
                for idx, r in df_com.iterrows():
                    val_com = float(r['Retencao'] or 0.0)
                    status_tit = str(r['Tit_Receb']).upper()
                    
                    # Se gatilho for faturamento, libera direto
                    if "LIQUIDAÇÃO" not in v_gatilho:
                        df_com.at[idx, 'Status Comissão'] = "✔️ Liberada (Faturamento)"
                        df_com.at[idx, 'Liberada_Float'] = val_com
                    else:
                        # Se for liquidação de título, depende se o título está RECEBIDO
                        if status_tit == "RECEBIDO":
                            df_com.at[idx, 'Status Comissão'] = "✔️ Liberada (Pago pelo Cliente)"
                            df_com.at[idx, 'Liberada_Float'] = val_com
                        else:
                            df_com.at[idx, 'Status Comissão'] = "🚫 Travada (Aguardando Recebimento)"
                            df_com.at[idx, 'Liberada_Float'] = 0.0
                
                total_vendido = df_com['Vendido Bruto R$'].sum()
                total_comissao = df_com['Retencao'].sum()
                total_liberado = df_com['Liberada_Float'].sum()
            
            total_bloqueado = total_comissao - total_liberado
            repasse_liquido = max(0.0, total_liberado - total_estorno_comissao)
            
            # Exibir resumo em Cards de KPI
            st.markdown("### 🧮 Saldo Consolidado e Auditoria")
            
            kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
            kpi_c1.metric("Vendido Bruto Total", format_brl(total_vendido))
            kpi_c2.metric("Comissão Gross Provisão", format_brl(total_comissao))
            kpi_c3.metric("(-) Estornos p/ Devoluções", f"- {format_brl(total_estorno_comissao)}", delta_color="inverse")
            kpi_c4.metric("SALDO LÍQUIDO LIBERADO", format_brl(repasse_liquido), help="Pronto para repasse (Comissão Liberada menos Estornos de Devoluções)")
            
            # Detalhamento de Comissão Travada (Aguardando Recebimento)
            if total_bloqueado > 0.0:
                st.info(f"💡 **Nota de Caixa:** Além do saldo liberado, o vendedor possui **{format_brl(total_bloqueado)}** em comissões travadas aguardando a liquidação dos boletos pelos clientes.")
            
            # Tabela principal de conferência (Se houver vendas)
            if not df_com.empty:
                st.markdown("#### 🔍 Extrato Detalhado de Títulos e Repasses (Vendas)")
                df_view = df_com.copy()
                df_view['Data Lançada'] = pd.to_datetime(df_view['Data Lançada'], errors='coerce').dt.strftime('%d/%m/%Y')
                df_view['Vendido Bruto R$'] = df_view['Vendido Bruto R$'].apply(format_brl)
                df_view['Comissão R$'] = df_view['Retencao'].apply(format_brl)
                df_view['Tit. Receb.'] = df_view['Tit_Receb'].map({'RECEBIDO': '🟢 PAGO', 'PENDENTE': '🔴 EM ABERTO', 'N/A': '⚪ N/A'})
                
                df_view_final = df_view[['Doc', 'K-Account', 'Data Lançada', 'Tit. Receb.', 'Vendido Bruto R$', 'Comissão R$', 'Status Comissão']]
                st.dataframe(df_view_final, hide_index=True, width="stretch")
            
            # Tabela de Estornos de Devolução (Se houver)
            if len(estornos_list) > 0:
                st.markdown("#### 📉 Extrato Detalhado de Devoluções e Reversões (Deduções)")
                df_view_dev = pd.DataFrame(estornos_list)
                df_view_dev_fmt = df_view_dev.copy()
                df_view_dev_fmt['Valor Avariado'] = df_view_dev_fmt['Valor Avariado'].apply(format_brl)
                df_view_dev_fmt['Comissão Estornada'] = df_view_dev_fmt['Comissão Estornada'].apply(format_brl)
                st.dataframe(df_view_dev_fmt, hide_index=True, width="stretch")
            
            # Painel de Fechamento e Envio para Contas a Pagar
            st.markdown("---")
            st.markdown("### 🔒 Autorização e Repasse Consolidado")
            
            if repasse_liquido <= 0.0:
                st.info("Não há saldo líquido positivo de comissão liberado para fechamento comercial nesta competência.")
            else:
                # 1. Verifica se já existe repasse consolidado no Contas a Pagar
                desc_consolidada_prefix = f"Repasse de Comissão Consolidada - {vendedor_nome} - Ref. {mes_filtro}"
                df_rep_existe = fetch_all("SELECT id, valor, status, data_vencimento FROM contas_a_pagar WHERE descricao LIKE ?", (f"%{desc_consolidada_prefix}%",))
                
                if not df_rep_existe.empty:
                    rep_id = df_rep_existe.iloc[0]['id']
                    rep_val = float(df_rep_existe.iloc[0]['valor'])
                    rep_status = df_rep_existe.iloc[0]['status']
                    rep_venc = df_rep_existe.iloc[0]['data_vencimento']
                    rep_venc_dt = pd.to_datetime(rep_venc).strftime('%d/%m/%Y')
                    
                    st.success(f"✅ **Folha de Comissões Já Autorizada:** Esta competência foi fechada anteriormente. "
                               f"Foi gerada a Obrigação ID #{rep_id} no valor líquido de **{format_brl(rep_val)}**, "
                               f"com status **'{rep_status}'** e vencimento acordado para **{rep_venc_dt}**.")
                else:
                    # Calcula data de vencimento acordada (dia do mês seguinte)
                    import calendar
                    partes = mes_filtro.split('-')
                    ano = int(partes[0])
                    mes = int(partes[1])
                    mes_seg = mes + 1
                    ano_seg = ano
                    if mes_seg > 12:
                        mes_seg = 1
                        ano_seg += 1
                    ultimo_dia = calendar.monthrange(ano_seg, mes_seg)[1]
                    dia_final = min(v_dia_venc, ultimo_dia)
                    venc_consolidado = date(ano_seg, mes_seg, dia_final)
                    
                    st.warning(f"⚠️ **Folha de Comissões Pendente:** O repasse líquido acumulado de **{format_brl(repasse_liquido)}** "
                               f"referente a competência **{mes_filtro}** (já descontados os estornos de devoluções) ainda não foi enviado para o Contas a Pagar.")
                    st.markdown(f"- **Total Bruto Liberado:** {format_brl(total_liberado)}")
                    st.markdown(f"- **Total de Abatimentos/Devoluções:** - {format_brl(total_estorno_comissao)}")
                    st.markdown(f"- **Data acordada de pagamento:** `{venc_consolidado.strftime('%d/%m/%Y')}` (Dia {v_dia_venc} do mês seguinte)")
                    st.markdown(f"- **Regra de Repasse do Representante:** `{v_gatilho}`")
                    
                    if st.button("🔒 Fechar Competência & Autorizar Payout Único", type="primary", use_container_width=True):
                        # Pega plano de conta para repasse de comissão
                        p_c_comissao = fetch_all("SELECT id FROM planos_de_contas WHERE codigo = '2.2.3' OR nome LIKE '%Comiss%' LIMIT 1")
                        pc_com_id = int(p_c_comissao.iloc[0]['id']) if not p_c_comissao.empty else None
                        
                        desc_comissao_final = f"{desc_consolidada_prefix} | Venc. acordado: dia {v_dia_venc}/mês seg. | (Bruto: {format_brl(total_liberado)} - Estornos: {format_brl(total_estorno_comissao)})"
                        
                        run_query('''
                            INSERT INTO contas_a_pagar (plano_conta_id, descricao, valor, data_vencimento, status)
                            VALUES (?, ?, ?, ?, 'PENDENTE')
                        ''', (pc_com_id, desc_comissao_final, repasse_liquido, venc_consolidado.strftime("%Y-%m-%d")))
                        
                        st.success(f"Folha consolidada fechada e autorizada para repasse. Obrigação comercial líquida de {format_brl(repasse_liquido)} enviada ao Contas a Pagar com vencimento em {venc_consolidado.strftime('%d/%m/%Y')}.")
                        import time; time.sleep(2.0); st.rerun()

# ======= 4. EXTRATO DO VENDEDOR =======
with tab4:
    st.subheader("🖨️ Emissão de Extrato Mensal Analítico")
    st.markdown("Gere o relatório detalhado para o Vendedor cobrar suas notas (Apenas Pedidos Faturados).")
    
    if not df_vendedores.empty:
        colE1, colE2 = st.columns(2)
        v_opts_ext = {f"{r['nome']}": r for _, r in df_vendedores.iterrows()}
        vend_str = colE1.selectbox("Selecione o Vendedor / Rota", list(v_opts_ext.keys()), key="extrato_vend")
        mes_ext = colE2.selectbox("Mês de Competência", [hoje.strftime('%Y-%m'), (hoje - timedelta(days=30)).strftime('%Y-%m')], key="extrato_mes")
        
        if st.button("Gerar Extrato Analítico", type="primary"):
            vend_obj = v_opts_ext[vend_str]
            v_id = vend_obj['id']
            v_gatilho = vend_obj['gatilho_comissao']
            
            q_ext = '''
                SELECT v.id as 'Doc ERP', v.tipo_documento as 'Dcto', v.numero_documento as 'Série', v.data as 'Data Emissão', 
                       c.nome as 'Cliente', p.nome as 'Produto', 
                       v.valor_total as 'Valor Faturado (R$)', v.comissao_valor as 'Comissão Bruta (R$)', 
                       cr.data_vencimento as 'Vencimento Título', cr.status as 'Status Título'
                FROM vendas v
                JOIN clientes c ON v.cliente_id=c.id
                JOIN produtos p ON v.produto_id=p.id
                LEFT JOIN contas_a_receber cr ON cr.venda_id=v.id
                WHERE v.vendedor_id = ? AND strftime('%Y-%m', v.data) = ? AND v.status = 'FATURADO'
            '''
            df_ext = fetch_all(q_ext, (v_id, mes_ext))
            
            st.markdown("---")
            st.markdown(f"### 📄 EXTRATO COMERCIAL - {vend_str.upper()}")
            
            if df_ext.empty:
                st.warning("Nenhum faturamento registrado para este vendedor no mês solicitado.")
            else:
                total_faturado = 0.0
                total_bloqueado = 0.0
                total_liberado = 0.0
                
                df_ext['Situação do Pagamento'] = "A PROCESSAR"
                
                for idx, row in df_ext.iterrows():
                    v_fat = float(row['Valor Faturado (R$)'])
                    c_bruta = float(row['Comissão Bruta (R$)'])
                    stat_titulo = str(row['Status Título']).upper()
                    
                    total_faturado += v_fat
                    
                    if v_gatilho == "LIQUIDAÇÃO DE TITULO":
                        if "PENDENTE" in stat_titulo:
                            total_bloqueado += c_bruta
                            df_ext.at[idx, 'Situação do Pagamento'] = "🚫 BLOQUEADO (Aguarda Cliente Pagar)"
                        else:
                            total_liberado += c_bruta
                            df_ext.at[idx, 'Situação do Pagamento'] = "✔️ LIBERADO"
                    else: 
                        total_liberado += c_bruta
                        df_ext.at[idx, 'Situação do Pagamento'] = "✔️ LIBERADO (Faturado)"
                
                df_ext['Data Emissão'] = pd.to_datetime(df_ext['Data Emissão'], errors='coerce').dt.strftime('%d/%m/%Y')
                df_ext['Vencimento Título'] = pd.to_datetime(df_ext['Vencimento Título'], errors='coerce').dt.strftime('%d/%m/%Y')
                
                for col in ['Valor Faturado (R$)', 'Comissão Bruta (R$)']:
                    df_ext[col] = df_ext[col].apply(format_brl)
                
                st.dataframe(df_ext, hide_index=True, width="stretch")
                
                st.markdown("#### ⚖️ Resumo do Extrato")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Carteira Girada", format_brl(total_faturado))
                r2.error(f"Comissão Bloqueada: {format_brl(total_bloqueado)}")
                r3.success(f"Comissão Paga/Pronta: {format_brl(total_liberado)}")
                r4.info(f"Obrigação Total: {format_brl(total_liberado + total_bloqueado)}")
