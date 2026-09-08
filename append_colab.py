import os

path = 'C:/Users/MARCIO/Gestao_Fabrica_Alho/pages/1_Cadastros.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace tabs definition
old_tabs = '''tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Produtos", "Clientes", "Fornecedores", "Regras de Comissão", 
    "Plano de Contas", "Contas Bancárias", "Maquinário", "Usuários", "Redes e Grupos"
])'''

new_tabs = '''tab1, tab2, tab3, tab10, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Produtos", "Clientes", "Fornecedores", "Colaboradores", "Regras de Comissão", 
    "Plano de Contas", "Contas Bancárias", "Maquinário", "Usuários", "Redes e Grupos"
])'''

if old_tabs in content:
    content = content.replace(old_tabs, new_tabs)
else:
    print('Tabs definition not found')

# Append Colaboradores code
colab_code = '''

# ======= COLABORADORES =======
with tab10:
    st.subheader("Cadastro de Novo Colaborador")
    with st.form("form_func", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        nome = col1.text_input("Nome Completo")
        cargo = col2.selectbox("Cargo", ["Operário", "Vendedor", "Gerente", "Administrativo", "Representante Comercial"])
        regime = col3.selectbox("Regime de Contratação", ["CLT", "Autônomo", "PJ", "Diarista"])
        
        col4, col5, col6, col_t = st.columns(4)
        salario = col4.number_input("Rem. Fixa (Salário Base R$)", min_value=0.0, step=100.0)
        admissao = col5.date_input("Data de Início", value=date.today(), format="DD/MM/YYYY")
        nascimento = col6.date_input("Data de Nascimento", value=date(1990, 1, 1), format="DD/MM/YYYY")
        termino = col_t.date_input("Data de Término (Opcional)", value=None, format="DD/MM/YYYY")
        
        st.markdown("🎯 **Outras Remunerações Fixas**")
        col7, col8, col9 = st.columns(3)
        ajuda_custo = col7.number_input("Ajuda de Custo (R$)", min_value=0.0, step=50.0)
        outros_desc = col8.text_input("Outros (Descrição)")
        outros_valor = col9.number_input("Outros (Valor R$)", min_value=0.0, step=50.0)
        
        if st.form_submit_button("Cadastrar Colaborador"):
            if nome and salario >= 0:
                run_query(
                    """INSERT INTO funcionarios 
                       (nome, cargo, salario_base, regime_contratacao, data_admissao, data_nascimento, ajuda_custo, outros_descricao, outros_valor, status, data_termino) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ATIVO', ?)""",
                    (nome, cargo, salario, regime, admissao, nascimento, ajuda_custo, outros_desc, outros_valor, termino)
                )
                st.success(f"Colaborador {nome} cadastrado com sucesso!")
                import time; time.sleep(1); st.rerun()

    st.markdown("---")
    st.subheader("Editar Cadastro de Colaboradores")
    df_func_edit = fetch_all("SELECT id, nome, cargo FROM funcionarios")
    if not df_func_edit.empty:
        opts_f = {f"{r['id']} - {r['nome']} ({r['cargo']})": r['id'] for _, r in df_func_edit.iterrows()}
        f_sel = st.selectbox("Selecione o Colaborador para editar:", list(opts_f.keys()))
        if f_sel:
            f_id = opts_f[f_sel]
            f_data = fetch_all("SELECT * FROM funcionarios WHERE id=?", (f_id,)).iloc[0]
            with st.form("f_edit"):
                e_col1, e_col2, e_stts = st.columns(3)
                ef_nome = e_col1.text_input("Nome", f_data['nome'])
                c_lst = ["Operário", "Vendedor", "Gerente", "Administrativo", "Representante Comercial"]
                ef_c = e_col2.selectbox("Cargo", c_lst, index=c_lst.index(f_data['cargo']) if f_data['cargo'] in c_lst else 0)
                
                stts_opts = ["ATIVO", "INATIVO"]
                d_stts = f_data.get('status', 'ATIVO')
                if d_stts not in stts_opts: d_stts = "ATIVO"
                ef_status = e_stts.selectbox("Status", stts_opts, index=stts_opts.index(d_stts))
                
                e_col3, e_col4, e_term = st.columns(3)
                ef_sal = e_col3.number_input("Rem. Fixa (R$)", value=float(f_data['salario_base']))
                ef_ajuda = e_col4.number_input("Ajuda de Custo (R$)", value=float(f_data['ajuda_custo'] or 0.0))
                
                dt_term_val = pd.to_datetime(f_data['data_termino']).date() if pd.notnull(f_data['data_termino']) else None
                ef_termino = e_term.date_input("Data de Término (Opcional)", value=dt_term_val, format="DD/MM/YYYY")
                
                e_col5, e_col6 = st.columns(2)
                ef_odesc = e_col5.text_input("Outros (Descrição)", f_data['outros_descricao'] if f_data['outros_descricao'] else "")
                ef_ovalor = e_col6.number_input("Outros (Valor R$)", value=float(f_data['outros_valor'] or 0.0))
                
                if st.form_submit_button("Salvar Modificações"):
                    run_query("UPDATE funcionarios SET nome=?, cargo=?, salario_base=?, ajuda_custo=?, outros_descricao=?, outros_valor=?, status=?, data_termino=? WHERE id=?", 
                              (ef_nome, ef_c, ef_sal, ef_ajuda, ef_odesc, ef_ovalor, ef_status, ef_termino, f_id))
                    import time; time.sleep(1); st.rerun()
'''

content += colab_code

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
