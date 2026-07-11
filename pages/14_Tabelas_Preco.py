import streamlit as st
import pandas as pd
from datetime import date
from database import run_query, fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="Tabelas de Preço", page_icon="🏷️", layout="wide")
carregar_estilo()

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
h1 {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    margin-top: -15px !important;
    margin-bottom: 0px !important;
    color: #1e293b !important;
}
</style>
<h1>Tabelas de Preço</h1>
""", unsafe_allow_html=True)


def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Carregar dados básicos
df_clientes = fetch_all("SELECT id, nome, rede_clientes, prazo_pagamento, representante_id FROM clientes WHERE status='ATIVO'")
df_produtos = fetch_all("SELECT id, nome, preco_venda_base FROM produtos WHERE is_materia_prima = FALSE")

col_t1, col_t2 = st.columns(2)

p_opts_tab = {f"{r['nome']}": r['id'] for _, r in df_produtos.iterrows()}
if p_opts_tab:
    prod_selecionado = col_t1.selectbox("1. Selecione o Produto", list(p_opts_tab.keys()), key="tab_prod")
    
    tipo_entidade = col_t2.selectbox("2. Nível da Regra (Hierarquia)", ["CLIENTE", "GRUPO", "REDE"], key="tab_tipo")
    
    lista_entidades = []
    
    if tipo_entidade == "CLIENTE":
        col_v1, col_v2 = st.columns(2)
        lista_entidades = df_clientes['nome'].tolist() if not df_clientes.empty else []
        nome_aba_cadastro = "🏭 Cadastro de Clientes"
        
        if not lista_entidades:
            entidade_nome = col_v1.selectbox("3. Vínculo (Selecione o Cliente)", ["(Nenhum registrado)"], key="tab_ent", disabled=True)
            st.warning(f"⚠️ **Nenhum cliente** cadastrado no sistema! Acesse o menu **Cadastros** e use a aba **{nome_aba_cadastro}** para registrá-los primeiro.")
        else:
            entidade_nome = col_v1.selectbox("3. Vínculo (Selecione o Cliente)", ["(Selecione)"] + lista_entidades, key="tab_ent")
        
        preco_tabela = col_v2.number_input("4. Preço Acordado (R$)", min_value=0.01, step=0.1, key="tab_preco")
        
    elif tipo_entidade == "REDE":
        col_v1, col_v2 = st.columns(2)
        df_r = fetch_all("SELECT nome FROM redes_clientes")
        lista_entidades = df_r['nome'].tolist() if not df_r.empty else []
        nome_aba_cadastro = "🏢 Redes e Grupos"
        
        if not lista_entidades:
            entidade_nome = col_v1.selectbox("3. Vínculo (Selecione a Rede)", ["(Nenhum registrado)"], key="tab_ent", disabled=True)
            st.warning(f"⚠️ **Nenhuma rede** cadastrada no sistema! Acesse o menu **Cadastros** e use a aba **{nome_aba_cadastro}** para registrá-las primeiro.")
        else:
            entidade_nome = col_v1.selectbox("3. Vínculo (Selecione a Rede)", ["(Selecione)"] + lista_entidades, key="tab_ent")
            
        preco_tabela = col_v2.number_input("4. Preço Acordado (R$)", min_value=0.01, step=0.1, key="tab_preco")
        
    elif tipo_entidade == "GRUPO":
        col_v1, col_v2, col_v3 = st.columns(3)
        df_r = fetch_all("SELECT nome FROM redes_clientes")
        redes_list = df_r['nome'].tolist() if not df_r.empty else []
        
        if not redes_list:
            st.warning("⚠️ **Nenhuma rede** cadastrada no sistema! Para cadastrar grupos, você precisa cadastrar redes primeiro na aba **🏢 Redes e Grupos** de **Cadastros**.")
            rede_selecionada = col_v1.selectbox("3. Rede do Grupo", ["(Nenhuma cadastrada)"], key="tab_rede_grupo", disabled=True)
            entidade_nome = col_v2.selectbox("4. Vínculo (Selecione o Grupo)", ["(Nenhuma rede)"], key="tab_ent", disabled=True)
            preco_tabela = col_v3.number_input("5. Preço Acordado (R$)", min_value=0.01, step=0.1, key="tab_preco", disabled=True)
        else:
            rede_selecionada = col_v1.selectbox("3. Selecione a Rede Matriz:", ["(Selecione)"] + redes_list, key="tab_rede_grupo")
            
            if rede_selecionada == "(Selecione)":
                entidade_nome = col_v2.selectbox("4. Vínculo (Selecione o Grupo)", ["(Selecione a Rede)"], key="tab_ent", disabled=True)
                preco_tabela = col_v3.number_input("5. Preço Acordado (R$)", min_value=0.01, step=0.1, key="tab_preco", disabled=True)
                st.info("💡 Por favor, **selecione a Rede Matriz** para carregar os grupos associados.")
            else:
                df_g = fetch_all("""
                    SELECT g.nome 
                    FROM grupos_clientes g
                    JOIN redes_clientes r ON g.rede_id = r.id
                    WHERE r.nome = ?
                """, (rede_selecionada,))
                lista_entidades = df_g['nome'].tolist() if not df_g.empty else []
                
                if not lista_entidades:
                    st.warning(f"⚠️ **Nenhum grupo** cadastrado sob a rede **'{rede_selecionada}'**! Acesse o menu **Cadastros** e use a aba **🏢 Redes e Grupos** para criar sub-grupos.")
                    entidade_nome = col_v2.selectbox("4. Vínculo (Selecione o Grupo)", ["(Nenhum grupo cadastrado)"], key="tab_ent", disabled=True)
                    preco_tabela = col_v3.number_input("5. Preço Acordado (R$)", min_value=0.01, step=0.1, key="tab_preco", disabled=True)
                else:
                    entidade_nome = col_v2.selectbox("4. Vínculo (Selecione o Grupo)", ["(Selecione)"] + lista_entidades, key="tab_ent")
                    preco_tabela = col_v3.number_input("5. Preço Acordado (R$)", min_value=0.01, step=0.1, key="tab_preco")
    
    st.markdown("##### Acordos e Rebates (%)")
    col_r1, col_r2, col_r3 = st.columns(3)
    pct_contrato = col_r1.number_input("% Contrato", min_value=0.0, step=0.1, value=0.0)
    pct_auxiliar = col_r2.number_input("% Comissões Auxiliares", min_value=0.0, step=0.1, value=0.0)
    pct_logistica = col_r3.number_input("% Acordo Logístico", min_value=0.0, step=0.1, value=0.0)
    
    if st.button("Salvar Tabela Ativa", type="primary"):
        if entidade_nome == "(Selecione)" or not lista_entidades:
            st.error("Selecione um vínculo válido.")
        else:
            prod_id = p_opts_tab[prod_selecionado]
            
            check_conflito = fetch_all("SELECT id FROM tabelas_preco WHERE produto_id=? AND tipo_entidade=? AND entidade_nome=? AND status='ATIVO'", 
                                       (prod_id, tipo_entidade, entidade_nome))
            
            if not check_conflito.empty:
                st.error(f"🛑 ERRO: Já existe uma tabela ATIVA para {tipo_entidade} '{entidade_nome}' neste produto. Inative a tabela anterior primeiro no Histórico abaixo.")
            else:
                run_query("INSERT INTO tabelas_preco (produto_id, tipo_entidade, entidade_nome, preco, pct_contrato, pct_comissao_auxiliar, pct_acordo_logistico) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (prod_id, tipo_entidade, entidade_nome, preco_tabela, pct_contrato, pct_auxiliar, pct_logistica))
                st.success("Tabela de Preços criada com sucesso!")
                import time; time.sleep(1); st.rerun()

st.markdown("---")
st.subheader("Histórico de Tabelas e Auditoria")
df_tabelas = fetch_all('''
    SELECT t.id as ID, p.nome as Produto, t.tipo_entidade as Nível, t.entidade_nome as Vínculo, 
           t.preco as 'Preço (R$)', 
           t.pct_contrato as '% Contrato', t.pct_comissao_auxiliar as '% Auxiliar', t.pct_acordo_logistico as '% Logist',
           t.data_criacao as 'Data', t.status as Status
    FROM tabelas_preco t
    JOIN produtos p ON t.produto_id = p.id
    ORDER BY t.status ASC, t.id DESC
''')

if not df_tabelas.empty:
    df_tabelas['Data'] = pd.to_datetime(df_tabelas['Data']).dt.strftime('%d/%m/%Y %H:%M')
    df_tabelas['Preço (R$)'] = df_tabelas['Preço (R$)'].apply(format_brl)
    
    def color_status(row):
        if row['Status'] == 'ATIVO': return ['background-color: #e6ffe6; color: black'] * len(row)
        return ['background-color: #ffe6e6; color: black'] * len(row)
        
    st.dataframe(df_tabelas.style.apply(color_status, axis=1), hide_index=True, width="stretch")
    
    with st.expander("🚫 Inativar Tabela Definitivamente"):
        st.markdown("Uma tabela inativada sai de circulação imediatamente, mas seu registro permanece para fins de auditoria antifraude.")
        opts_inativar = {}
        for _, r in df_tabelas[df_tabelas['Status'] == 'ATIVO'].iterrows():
            opts_inativar[f"ID {r['ID']} - {r['Vínculo']} ({r['Produto']})"] = r['ID']
            
        if opts_inativar:
            t_sel = st.selectbox("Selecione a tabela para inativar:", list(opts_inativar.keys()))
            if st.button("Inativar Regra", type="primary"):
                run_query("UPDATE tabelas_preco SET status='INATIVO' WHERE id=?", (opts_inativar[t_sel],))
                st.success("Tabela inativada! Ela não será mais sugerida nas novas vendas.")
                import time; time.sleep(1); st.rerun()
        else:
            st.info("Nenhuma tabela ativa no momento.")
else:
    st.info("Nenhuma tabela de preço customizada foi cadastrada ainda.")
