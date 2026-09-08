import os

path = 'C:/Users/MARCIO/Gestao_Fabrica_Alho/pages/1_Cadastros.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''    df_grupos_bd = fetch_all("SELECT g.id, g.nome, r.nome as rede_nome FROM grupos_clientes g JOIN redes_clientes r ON g.rede_id = r.id")
    
    with st.form("form_cliente", clear_on_submit=True):
        c1, c2, c3, c_nasc = st.columns(4)
        nome = c1.text_input("Razão Social")
        nome_fantasia = c2.text_input("Nome Fantasia")
        cnpj_cpf = c3.text_input("CNPJ/CPF")
        nascimento = c_nasc.date_input("Data de Nasc/Fundação", value=None, format="DD/MM/YYYY")
        
        c4, c5, c6 = st.columns(3)
        inscricao_estadual = c4.text_input("Inscrição Estadual")
        telefone = c5.text_input("Telefone")
        email = c6.text_input("E-mail")
        
        c7, c8, c9, c10 = st.columns([2, 1, 1, 1])
        endereco = c7.text_input("Endereço")
        bairro = c8.text_input("Bairro")
        cidade = c9.text_input("Cidade")
        uf = c10.text_input("UF")
        
        c11, c12, c13, c14 = st.columns(4)
        cep = c11.text_input("CEP")
        rede_clientes = c12.selectbox("Rede de Clientes", redes_opts)
        
        # Filtro de grupo baseado na rede escolhida não é trivial dentro do form streamlit no mesmo render sem re-run.
        # Solução simples: carregar todos os grupos ou o usuario digita/seleciona "Nenhum" e depois a gente salva.
        # Vamos listar todos e sugerir o preenchimento correto.
        grupos_opts = ["(Nenhum)"]
        if rede_clientes != "(Nenhuma)" and not df_grupos_bd.empty:
            grupos_opts += df_grupos_bd[df_grupos_bd['rede_nome'] == rede_clientes]['nome'].tolist()
        grupo_lojas = c13.selectbox("Grupo (Sub-rede)", grupos_opts)
        
        status = c14.selectbox("Status", ["ATIVO", "INATIVO"])
        
        c15, c16, c17 = st.columns(3)
        prazo_pagamento = c15.text_input("Prazo Pagamento (Ex: 45 DIAS)")
        rep_nome = c16.selectbox("Representante Responsável", rep_options)
        observacoes = c17.text_input("Observações")
        
        if st.form_submit_button("Cadastrar Cliente"):
            if nome:
                req_id = rep_dict.get(rep_nome, None)
                rede_val = rede_clientes if rede_clientes != "(Nenhuma)" else ""
                grupo_val = grupo_lojas if grupo_lojas != "(Nenhum)" else ""'''

new_block = '''    df_grupos_bd = fetch_all("SELECT g.id, g.nome, r.nome as rede_nome FROM grupos_clientes g JOIN redes_clientes r ON g.rede_id = r.id")
    
    st.markdown("##### Configuração de Rede do Cliente")
    rede_dinamica = st.selectbox("1. Selecione a Rede (Isso vai filtrar as opções de Grupo abaixo)", redes_opts)
    
    grupos_opts = ["(Nenhum)"]
    if rede_dinamica != "(Nenhuma)" and not df_grupos_bd.empty:
        grupos_opts += df_grupos_bd[df_grupos_bd['rede_nome'] == rede_dinamica]['nome'].tolist()

    with st.form("form_cliente", clear_on_submit=True):
        c1, c2, c3, c_nasc = st.columns(4)
        nome = c1.text_input("Razão Social")
        nome_fantasia = c2.text_input("Nome Fantasia")
        cnpj_cpf = c3.text_input("CNPJ/CPF")
        nascimento = c_nasc.date_input("Data de Nasc/Fundação", value=None, format="DD/MM/YYYY")
        
        c4, c5, c6 = st.columns(3)
        inscricao_estadual = c4.text_input("Inscrição Estadual")
        telefone = c5.text_input("Telefone")
        email = c6.text_input("E-mail")
        
        c7, c8, c9, c10 = st.columns([2, 1, 1, 1])
        endereco = c7.text_input("Endereço")
        bairro = c8.text_input("Bairro")
        cidade = c9.text_input("Cidade")
        uf = c10.text_input("UF")
        
        c11, c12, c13 = st.columns(3)
        cep = c11.text_input("CEP")
        grupo_lojas = c12.selectbox("2. Grupo (Sub-rede)", grupos_opts)
        status = c13.selectbox("Status", ["ATIVO", "INATIVO"])
        
        c14, c15, c16 = st.columns(3)
        prazo_pagamento = c14.text_input("Prazo Pagamento (Ex: 45 DIAS)")
        rep_nome = c15.selectbox("Representante Responsável", rep_options)
        observacoes = c16.text_input("Observações")
        
        st.info(f"Rede Vinculada a este cliente: **{rede_dinamica}**")
        
        if st.form_submit_button("Cadastrar Cliente"):
            if nome:
                req_id = rep_dict.get(rep_nome, None)
                rede_val = rede_dinamica if rede_dinamica != "(Nenhuma)" else ""
                grupo_val = grupo_lojas if grupo_lojas != "(Nenhum)" else ""'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Sucesso!")
else:
    print("Block not found!")
