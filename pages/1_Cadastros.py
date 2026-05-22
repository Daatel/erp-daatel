import streamlit as st
import pandas as pd
from database import run_query, fetch_all
from estilo import carregar_estilo
from datetime import date

st.set_page_config(page_title="Cadastros Base", page_icon="📝", layout="wide")
carregar_estilo()

st.title("📝 Cadastros Inteligentes")

tab_empresa, tab1, tab2, tab3, tab10, tab4, tab5, tab6, tab7, tab8, tab9, tab_ft = st.tabs([
    "🏢 Minha Empresa", "Produtos", "Clientes", "Fornecedores", "Colaboradores", "Regras de Comissão", 
    "Plano de Contas", "Contas Bancárias", "Maquinário", "Usuários", "Redes e Grupos",
    "🧪 Fichas Técnicas"
])

with tab_empresa:
    st.subheader("Configurações da Empresa (Dona do Sistema)")
    st.markdown("Estes dados aparecerão em Contratos, Notas e Relatórios gerados pelo sistema.")
    
    df_empresa = fetch_all("SELECT * FROM empresa_config LIMIT 1")
    if df_empresa.empty:
        run_query("INSERT INTO empresa_config (razao_social, nome_fantasia, cnpj, endereco_completo) VALUES ('Empório do Alho LTDA', 'Empório do Alho', '00.000.000/0001-00', 'Endereço Completo')")
        df_empresa = fetch_all("SELECT * FROM empresa_config LIMIT 1")
        
    emp = df_empresa.iloc[0]
    
    with st.form("form_empresa"):
        e_c1, e_c2 = st.columns(2)
        r_social = e_c1.text_input("Razão Social", value=emp['razao_social'])
        n_fantasia = e_c2.text_input("Nome Fantasia", value=emp.get('nome_fantasia', ''))
        
        e_c3, e_c4, e_c5 = st.columns(3)
        cnpj_emp = e_c3.text_input("CNPJ", value=emp.get('cnpj', ''))
        ie_emp = e_c4.text_input("Inscrição Estadual", value=emp.get('inscricao_estadual', '') or '')
        im_emp = e_c5.text_input("Inscrição Municipal", value=emp.get('inscricao_municipal', '') or '')
        
        e_c6, e_c7, e_c8 = st.columns([1, 1, 2])
        cep_emp = e_c6.text_input("CEP", value=emp.get('cep', '') or '')
        telefone_emp = e_c7.text_input("Telefone", value=emp.get('telefone', '') or '')
        email_emp = e_c8.text_input("E-mail Contato", value=emp.get('email', '') or '')
        
        e_c9, e_c10 = st.columns(2)
        web_emp = e_c9.text_input("Website / Link", value=emp.get('website', '') or '')
        insta_emp = e_c10.text_input("Instagram", value=emp.get('instagram', '') or '')
        
        end_emp = st.text_input("Endereço Completo (Rua, Número, Bairro, Cidade-UF)", value=emp.get('endereco_completo', ''))
        
        if st.form_submit_button("Salvar Dados da Empresa"):
            run_query("""
                UPDATE empresa_config 
                SET razao_social=?, nome_fantasia=?, cnpj=?, endereco_completo=?, telefone=?, email=?,
                    inscricao_estadual=?, inscricao_municipal=?, cep=?, instagram=?, website=?
                WHERE id=?
            """, (r_social, n_fantasia, cnpj_emp, end_emp, telefone_emp, email_emp, ie_emp, im_emp, cep_emp, insta_emp, web_emp, emp['id']))
            st.success("Dados da Empresa atualizados! Os PDFs e relatórios já usarão os dados novos.")
            import time; time.sleep(1); st.rerun()

def export_btn(df, filename, label="📥 Exportar Lista (CSV)"):
    if not df.empty:
        csv = df.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(label=label, data=csv, file_name=filename, mime='text/csv')

# ======= PRODUTOS =======
with tab1:
    st.subheader("Cadastro de Produtos")
    
    with st.form("form_produto", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        nome_produto = col1.text_input("Nome do Produto")
        marca = col2.text_input("Marca")
        referencia = col3.text_input("Referência / Cód")
        
        col4, col5, col6, col_e1 = st.columns(4)
        ean = col4.text_input("EAN (Cód de Barras Unidade)")
        peso_volume = col5.text_input("Peso/Volume (Ex: 1 Kg, 500 g)")
        unidade_compra = col6.text_input("Unidade de Medida (Ex: Unid, Pct)")
        embalagem_master = col_e1.selectbox("Embalagem Master", ["Nenhuma", "Caixa", "Fardo"])
        
        col_e2, col_e3, col10, col_m = st.columns(4)
        unidades_por_fardo = col_e2.number_input("Qtde. Master", min_value=1, step=1, help="Quantidade de unidades dentro da embalagem master")
        cod_emb_master = col_e3.text_input("Cód. Emb. Master", help="Opcional. EAN ou Cód da Caixa/Fardo.")
        preco_venda_base = col10.number_input("Preço Venda Base (R$)", min_value=0.0, step=0.01)
        is_materia_prima = col_m.checkbox("É Matéria-Prima (Ex: Alho Cru)?")
        
        unidade_medida_sintetico = unidade_compra if unidade_compra else "un"
        tipo_embalagem = unidade_compra 
        
        if st.form_submit_button("Cadastrar Produto"):
            if nome_produto:
                run_query(
                    """INSERT INTO produtos 
                       (nome, unidade_medida, preco_venda_base, is_materia_prima, 
                        marca, peso_volume, referencia, ean, unidades_por_fardo, 
                        tipo_embalagem, embalagem_master, cod_emb_master) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    (nome_produto, unidade_medida_sintetico, preco_venda_base, True if is_materia_prima else False,
                     marca, peso_volume, referencia, ean, unidades_por_fardo, tipo_embalagem, embalagem_master, cod_emb_master)
                )
                st.success(f"Produto '{nome_produto}' cadastrado com sucesso!")
            else:
                st.error("Por favor, preencha o nome do produto.")
                
    st.markdown("---")
    st.subheader("Produtos Cadastrados")
    df_produtos = fetch_all("SELECT id, nome, marca, referencia, ean, peso_volume as 'Peso/Vol', unidade_medida as 'Unidade', embalagem_master as 'Emb. Master', unidades_por_fardo as 'Qtd. Master', custo_unidade as 'Custo Und', custo_fardo as 'Custo Master', preco_venda_base as 'Preço Venda', is_materia_prima FROM produtos")
    if not df_produtos.empty:
        df_produtos['is_materia_prima'] = df_produtos['is_materia_prima'].map({1: 'Sim', 0: 'Não', True: 'Sim', False: 'Não'})
        
        export_btn(df_produtos, 'produtos.csv')
        
        def format_brl(val):
            if pd.isna(val): return ""
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        df_produtos_view = df_produtos.copy()
        df_produtos_view['Custo Und'] = df_produtos_view['Custo Und'].apply(format_brl)
        df_produtos_view['Custo Master'] = df_produtos_view['Custo Master'].apply(format_brl)
        df_produtos_view['Preço Venda'] = df_produtos_view['Preço Venda'].apply(format_brl)
        
        st.dataframe(df_produtos_view, width="stretch", hide_index=True)
        
        with st.expander("✏️ Editar Informações Rápidas do Produto"):
            opts_p = {}
            for _, r in df_produtos.iterrows():
                lbl = f"ID {r['id']} | {r['nome']}"
                opts_p[lbl] = r['id']
            
            p_sel = st.selectbox("Selecione o Produto:", list(opts_p.keys()))
            if p_sel:
                pid = opts_p[p_sel]
                p_data = fetch_all("SELECT * FROM produtos WHERE id=?", (pid,))
                if not p_data.empty:
                    pb = p_data.iloc[0]
                    with st.form("edit_prod"):
                        ep1, ep2, ep3 = st.columns([2, 1, 1])
                        enome = ep1.text_input("Nome do Produto", pb['nome'])
                        emarca = ep2.text_input("Marca", pb['marca'] if pb['marca'] else "")
                        epreco = ep3.number_input("Preço Venda (R$)", value=float(pb['preco_venda_base']), min_value=0.0)
                        
                        ep5, ep6, ep_em1, ep_em2 = st.columns(4)
                        eunidade = ep5.text_input("Unidade de Medida (Ex: Kg, Unid, Caixa)", pb['unidade_medida'] if pb['unidade_medida'] else "")
                        
                        opts_emb = ["Nenhuma", "Caixa", "Fardo"]
                        val_emb = pb.get('embalagem_master') if 'embalagem_master' in pb else "Nenhuma"
                        eembalagem_master = ep6.selectbox("Embalagem Master", opts_emb, index=opts_emb.index(val_emb) if pd.notna(val_emb) and val_emb in opts_emb else 0)
                        
                        efator = ep_em1.number_input("Qtde. Master", value=int(pb['unidades_por_fardo']) if pb['unidades_por_fardo'] else 1, min_value=1)
                        ecod_master = ep_em2.text_input("Cód. Emb. Master", pb.get('cod_emb_master', '') if 'cod_emb_master' in pb and pd.notna(pb['cod_emb_master']) else "")
                        
                        ep8, ep9, ep10, ep11 = st.columns(4)
                        epeso = ep8.text_input("Peso/Volume", pb['peso_volume'] if pb['peso_volume'] else "")
                        eref = ep9.text_input("Referência", pb['referencia'] if pb['referencia'] else "")
                        emateria = ep10.checkbox("É Matéria-Prima?", value=bool(pb['is_materia_prima']))
                        eestoque_min = ep11.number_input("Estoque Mínimo (Alerta)", value=float(pb['estoque_minimo']) if pb['estoque_minimo'] else 0.0, min_value=0.0)
                        
                        if st.form_submit_button("Atualizar Produto"):
                            run_query("UPDATE produtos SET nome=?, marca=?, preco_venda_base=?, unidade_medida=?, unidades_por_fardo=?, peso_volume=?, referencia=?, is_materia_prima=?, estoque_minimo=?, embalagem_master=?, cod_emb_master=? WHERE id=?", 
                                      (enome, emarca, epreco, eunidade, efator, epeso, eref, True if emateria else False, eestoque_min, eembalagem_master, ecod_master, pid))
                            st.success("Produto atualizado!")
                            import time; time.sleep(1); st.rerun()

# ======= CLIENTES =======
with tab2:
    st.subheader("Cadastro de Clientes")
    
    # --- NOVO IMPORTADOR DE CLIENTES VIA CSV ---
    with st.expander("📥 Importação em Massa de Clientes (Planilha CSV)"):
        st.warning(
            "⚠️ **IMPORTANTE:** Para realizar a importação de clientes, certifique-se de que os seus **Representantes** (aba 'Colaboradores'), **Redes de Clientes** e **Grupos de Lojas** (aba 'Redes e Grupos') já estejam previamente cadastrados no sistema. A importação será bloqueada por segurança caso existam nomes na planilha não correspondentes aos registros prévios."
        )
        
        modelo_csv = (
            "Razão Social;Nome Fantasia;CNPJ/CPF;Inscrição Estadual;Endereço;Bairro;CEP;Cidade;UF;Telefone;E-mail;Observações;Status;Rede de Clientes;Grupo de Lojas;PRAZO DE PAGAMENTO;Representante\n"
            "Empresa Exemplo Ltda;Exemplo;00.000.000/0001-00;Isento;Rua das Flores 123;Centro;74000-000;Goiânia;GO;(62) 99999-9999;compras@exemplo.com;Entrega de manhã;ATIVO;;;;\n"
        )
        st.download_button(
            label="📥 Baixar Planilha CSV Modelo",
            data=modelo_csv.encode('utf-8-sig'),
            file_name="modelo_importacao_clientes.csv",
            mime="text/csv",
            help="Utilize este arquivo como modelo. Lembre-se de salvar em formato CSV (delimitado por vírgula ou ponto-e-vírgula)."
        )
        
        uploaded_file = st.file_uploader("Selecione o arquivo CSV de clientes para importação", type=["csv"], key="import_clientes_uploader")
        
        if uploaded_file is not None:
            try:
                import io
                content = uploaded_file.getvalue()
                try:
                    text_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    text_content = content.decode('latin-1')
                
                # Detectar separador
                primeira_linha = text_content.split('\n')[0]
                sep = ';' if ';' in primeira_linha else ','
                
                df_import = pd.read_csv(io.StringIO(text_content), sep=sep)
                df_import.columns = [str(c).strip() for c in df_import.columns]
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")
                df_import = None
                
            if df_import is not None:
                if 'Razão Social' not in df_import.columns:
                    st.error("❌ O arquivo não possui a coluna obrigatória **'Razão Social'**. Verifique a planilha modelo.")
                else:
                    # Limpeza rápida
                    def clean_val(x):
                        if pd.isna(x): return ""
                        v = str(x).strip()
                        return "" if v.lower() == "nan" else v
                        
                    for col in df_import.columns:
                        df_import[col] = df_import[col].apply(clean_val)
                        
                    st.success("📂 Arquivo de importação carregado!")
                    st.markdown("**Prévia dos Dados (Primeiras 10 linhas):**")
                    st.dataframe(df_import.head(10), use_container_width=True)
                    
                    # 1. Carregar dependências existentes no banco para validação
                    df_reps_db = fetch_all("SELECT id, nome FROM funcionarios")
                    existing_reps = set(df_reps_db['nome'].tolist()) if not df_reps_db.empty else set()
                    rep_id_map = dict(zip(df_reps_db['nome'], df_reps_db['id'])) if not df_reps_db.empty else {}
                    
                    df_redes_db = fetch_all("SELECT nome FROM redes_clientes")
                    existing_redes = set(df_redes_db['nome'].tolist()) if not df_redes_db.empty else set()
                    
                    df_grupos_db = fetch_all("SELECT nome FROM grupos_clientes")
                    existing_grupos = set(df_grupos_db['nome'].tolist()) if not df_grupos_db.empty else set()
                    
                    df_existing_cnpj = fetch_all("SELECT cnpj_cpf FROM clientes")
                    existing_cnpjs = set(df_existing_cnpj['cnpj_cpf'].tolist()) if not df_existing_cnpj.empty else set()
                    
                    # Listas para auditoria
                    missing_reps = set()
                    missing_redes = set()
                    missing_grupos = set()
                    duplicate_cnpjs = []
                    cnpjs_na_planilha = {}
                    
                    valid_rows_count = 0
                    
                    for idx, row in df_import.iterrows():
                        razao = row.get('Razão Social', '')
                        if not razao:
                            continue
                            
                        cnpj = row.get('CNPJ/CPF', '')
                        rep = row.get('Representante', '')
                        rede = row.get('Rede de Clientes', '')
                        grupo = row.get('Grupo de Lojas', '')
                        
                        # Duplicados
                        if cnpj:
                            if cnpj in existing_cnpjs:
                                duplicate_cnpjs.append(f"{razao} (CNPJ: {cnpj} - já cadastrado)")
                            elif cnpj in cnpjs_na_planilha:
                                duplicate_cnpjs.append(f"{razao} (CNPJ: {cnpj} - duplicado na planilha)")
                            else:
                                cnpjs_na_planilha[cnpj] = 1
                                
                        # Representantes pendentes
                        if rep and rep not in existing_reps:
                            missing_reps.add(rep)
                            
                        # Redes pendentes
                        if rede and rede not in existing_redes:
                            missing_redes.add(rede)
                            
                        # Grupos pendentes
                        if grupo and grupo not in existing_grupos:
                            missing_grupos.add(grupo)
                            
                        valid_rows_count += 1
                        
                    # Mostrar resultados da Validação
                    st.markdown("#### 🔍 Relatório de Validação e Consistência:")
                    is_blocked = False
                    
                    col_v1, col_v2, col_v3 = st.columns(3)
                    with col_v1:
                        if missing_reps:
                            st.error(f"❌ **Representantes Ausentes ({len(missing_reps)}):**\n" + "\n".join([f"- {r}" for r in sorted(missing_reps)]))
                            is_blocked = True
                        else:
                            st.success("✅ Representantes OK")
                            
                    with col_v2:
                        if missing_redes:
                            st.error(f"❌ **Redes Ausentes ({len(missing_redes)}):**\n" + "\n".join([f"- {r}" for r in sorted(missing_redes)]))
                            is_blocked = True
                        else:
                            st.success("✅ Redes de Clientes OK")
                            
                    with col_v3:
                        if missing_grupos:
                            st.error(f"❌ **Grupos de Lojas Ausentes ({len(missing_grupos)}):**\n" + "\n".join([f"- {g}" for g in sorted(missing_grupos)]))
                            is_blocked = True
                        else:
                            st.success("✅ Grupos de Lojas OK")
                            
                    if duplicate_cnpjs:
                        st.warning(f"⚠️ **Clientes a serem ignorados por CNPJ duplicado ({len(duplicate_cnpjs)}):**\n" + "\n".join([f"- {d}" for d in duplicate_cnpjs]))
                        
                    if is_blocked:
                        st.error("⚠️ **IMPORTAÇÃO BLOQUEADA:** Por segurança, realize o cadastro prévio das dependências ausentes apontadas acima nas abas correspondentes antes de prosseguir.")
                        st.button("Confirmar Importação de Clientes", disabled=True, use_container_width=True, key="btn_import_disabled")
                    else:
                        st.success("🎉 Planilha validada com sucesso! Todos os relacionamentos estão em conformidade com os cadastros prévios do ERP.")
                        limpar_banco = st.checkbox("🗑️ Excluir todos os clientes existentes atualmente no sistema antes de importar", value=False, key="import_limpar_banco")
                        
                        if st.button("Confirmar Importação de Clientes", use_container_width=True, type="primary", key="btn_import_active"):
                            try:
                                imported_count = 0
                                ignored_count = 0
                                
                                if limpar_banco:
                                    run_query("DELETE FROM clientes")
                                    
                                for idx, row in df_import.iterrows():
                                    razao = row.get('Razão Social', '')
                                    if not razao:
                                        continue
                                        
                                    cnpj = row.get('CNPJ/CPF', '')
                                    if not limpar_banco and cnpj and cnpj in existing_cnpjs:
                                        ignored_count += 1
                                        continue
                                        
                                    nome_fantasia = row.get('Nome Fantasia', '')
                                    insc_estadual = row.get('Inscrição Estadual', '')
                                    endereco = row.get('Endereço', '')
                                    bairro = row.get('Bairro', '')
                                    cep = row.get('CEP', '')
                                    cidade = row.get('Cidade', '')
                                    uf = row.get('UF', '')
                                    telefone = row.get('Telefone', '')
                                    email = row.get('E-mail', '')
                                    observacoes = row.get('Observações', '')
                                    status_val = row.get('Status', 'ATIVO')
                                    if not status_val: status_val = 'ATIVO'
                                    rede_val = row.get('Rede de Clientes', '')
                                    grupo_val = row.get('Grupo de Lojas', '')
                                    prazo_pag = row.get('PRAZO DE PAGAMENTO', '')
                                    
                                    rep_nome = row.get('Representante', '')
                                    rep_id = rep_id_map.get(rep_nome, None) if rep_nome else None
                                    
                                    query_insert = """INSERT INTO clientes 
                                               (nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual, 
                                                bairro, cep, cidade, uf, email, observacoes, status, rede_clientes, 
                                                grupo_lojas, prazo_pagamento, representante_id, data_nascimento, prazo_pagamento_dias, taxa_descarga, regras_descarga) 
                                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                                    
                                    run_query(query_insert, (
                                        razao, telefone, endereco, nome_fantasia, cnpj, insc_estadual,
                                        bairro, cep, cidade, uf, email, observacoes, status_val, rede_val,
                                        grupo_val, prazo_pag, rep_id, None, 30, 0.0, ""
                                    ))
                                    imported_count += 1
                                    
                                st.success(f"✅ Importação finalizada! {imported_count} novos clientes importados. {ignored_count} registros ignorados por duplicidade de CNPJ.")
                                import time; time.sleep(2); st.rerun()
                            except Exception as ex:
                                st.error(f"Erro ao inserir dados no banco: {ex}")
    # --- FIM DO NOVO IMPORTADOR ---
    
    df_reps = fetch_all("SELECT id, nome FROM funcionarios WHERE cargo LIKE '%Representante%' OR cargo LIKE '%Vendedor%'")
    rep_options = ["(Nenhum/Direto)"] + df_reps['nome'].tolist() if not df_reps.empty else ["(Nenhum/Direto)"]
    rep_dict = dict(zip(df_reps['nome'], df_reps['id'])) if not df_reps.empty else {}
    
    df_redes_bd = fetch_all("SELECT id, nome FROM redes_clientes ORDER BY nome")
    redes_opts = ["(Nenhuma)"] + df_redes_bd['nome'].tolist() if not df_redes_bd.empty else ["(Nenhuma)"]
    
    # We fetch all groups to filter via JS/Streamlit
    df_grupos_bd = fetch_all("SELECT g.id, g.nome, r.nome as rede_nome FROM grupos_clientes g JOIN redes_clientes r ON g.rede_id = r.id")
    
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
        
        c14, c15, c16, c17 = st.columns(4)
        prazo_pagamento = c14.text_input("Prazo Pagt. Texto (Ex: 30/60)")
        prazo_pagamento_dias = c15.number_input("Prazo Faturamento (Dias)", min_value=0, value=30, step=1, help="Usado para vencimento automático")
        rep_nome = c16.selectbox("Representante Responsável", rep_options)
        observacoes = c17.text_input("Observações")
        
        st.info(f"Rede Vinculada a este cliente: **{rede_dinamica}**")
        
        st.markdown("##### Logística e Descarga")
        c18, c19 = st.columns([1, 3])
        taxa_descarga = c18.number_input("Taxa de Descarga (R$)", min_value=0.0, step=10.0, help="Valor cobrado pelo CD/Cliente para descarregar o caminhão.")
        regras_descarga = c19.text_input("Regras e Horários de Descarga", help="Ex: Descarga Paletizada, Horário Noturno, Agendamento.")
        
        if st.form_submit_button("Cadastrar Cliente"):
            if nome:
                req_id = rep_dict.get(rep_nome, None)
                rede_val = rede_dinamica if rede_dinamica != "(Nenhuma)" else ""
                grupo_val = grupo_lojas if grupo_lojas != "(Nenhum)" else ""
                
                query = """INSERT INTO clientes 
                           (nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual, 
                            bairro, cep, cidade, uf, email, observacoes, status, rede_clientes, 
                            grupo_lojas, prazo_pagamento, representante_id, data_nascimento, prazo_pagamento_dias, taxa_descarga, regras_descarga) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                
                run_query(query, (
                    nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual,
                    bairro, cep, cidade, uf, email, observacoes, status, rede_val,
                    grupo_val, prazo_pagamento, req_id, nascimento, prazo_pagamento_dias, taxa_descarga, regras_descarga
                ))
                st.success("Cliente cadastrado com sucesso!")
            else:
                st.error("Por favor, preencha a Razão Social.")
                
    st.markdown("---")
    st.subheader("Clientes Cadastrados")
    df_clientes = fetch_all("""
        SELECT c.id, c.nome as 'Razão Social', c.cnpj_cpf as 'CNPJ/CPF', c.cidade as 'Cidade', c.uf as 'UF', 
               c.rede_clientes as 'Rede', c.grupo_lojas as 'Grupo', c.status as 'Status', f.nome as 'Representante',
               c.taxa_descarga as 'Taxa Descarga (R$)', c.regras_descarga as 'Regras Descarga'
        FROM clientes c
        LEFT JOIN funcionarios f ON c.representante_id = f.id
    """)
    if not df_clientes.empty:
        export_btn(df_clientes, 'clientes.csv')
        st.dataframe(df_clientes, width="stretch", hide_index=True)
        
        with st.expander("✏️ Editar ou Inativar Cliente"):
            opts_cli = {}
            for _, r in df_clientes.iterrows():
                lbl = f"ID {r['id']} | {r['Razão Social']} ({r['Status']})"
                opts_cli[lbl] = r['id']
                
            c_sel = st.selectbox("Selecione o Cliente:", list(opts_cli.keys()))
            if c_sel:
                cid = opts_cli[c_sel]
                c_data = fetch_all("SELECT * FROM clientes WHERE id=?", (cid,))
                if not c_data.empty:
                    cb = c_data.iloc[0]
                    with st.form("edit_cli"):
                        ec1, ec2, ec3 = st.columns(3)
                        enome = ec1.text_input("Razão Social", cb['nome'])
                        edoc = ec2.text_input("CNPJ/CPF", cb['cnpj_cpf'] if cb['cnpj_cpf'] else "")
                        erede = ec3.text_input("Rede", cb['rede_clientes'] if cb['rede_clientes'] else "")
                        
                        ec4, ec5, ec_dias = st.columns(3)
                        eprazo = ec4.text_input("Prazo Padrão", cb['prazo_pagamento'] if cb.get('prazo_pagamento') else "")
                        eprazo_dias = ec_dias.number_input("Prazo Faturamento (Dias)", value=int(cb.get('prazo_pagamento_dias', 30)) if 'prazo_pagamento_dias' in cb and pd.notnull(cb['prazo_pagamento_dias']) else 30)
                        
                        c_stts = ["ATIVO", "INATIVO"]
                        d_stts = cb['status'] if cb['status'] in c_stts else "ATIVO"
                        estatus = ec5.selectbox("Status da Conta", c_stts, index=c_stts.index(d_stts))
                        
                        st.markdown("##### Logística e Descarga")
                        ec_l1, ec_l2 = st.columns([1, 3])
                        etaxa = ec_l1.number_input("Taxa de Descarga (R$)", value=float(cb.get('taxa_descarga', 0.0)) if pd.notnull(cb.get('taxa_descarga')) else 0.0, step=10.0)
                        eregras = ec_l2.text_input("Regras/Horários de Descarga", cb.get('regras_descarga', '') if cb.get('regras_descarga') else "")
                        
                        if st.form_submit_button("Salvar Cliente"):
                            run_query("UPDATE clientes SET nome=?, cnpj_cpf=?, rede_clientes=?, prazo_pagamento=?, status=?, prazo_pagamento_dias=?, taxa_descarga=?, regras_descarga=? WHERE id=?", 
                                      (enome, edoc, erede, eprazo, estatus, eprazo_dias, etaxa, eregras, cid))
                            st.success("Cliente alterado!")
                            import time; time.sleep(1); st.rerun()

# ======= FORNECEDORES =======
with tab3:
    st.subheader("Cadastro de Fornecedores")
    
    df_planos = fetch_all("SELECT id, nome FROM planos_de_contas ORDER BY nome")
    planos_options = df_planos['nome'].tolist() if not df_planos.empty else []
    
    with st.form("form_fornecedor", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Razão Social / Nome")
        nome_fantasia = c2.text_input("Nome Fantasia")
        cnpj_cpf = c3.text_input("CNPJ/CPF")
        
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
        status = c12.selectbox("Status", ["ATIVO", "INATIVO"])
        
        if planos_options:
            plano_de_contas = c13.selectbox("Plano de Contas", ["(Nenhum/Outro)"] + planos_options)
        else:
            plano_de_contas = c13.text_input("Plano de Contas")
            
        prazo_pagamento = st.text_input("Condição/Prazo Pagamento Padrão (Ex: A Vista, 30/60, etc)")
            
        if st.form_submit_button("Cadastrar Fornecedor"):
            if plano_de_contas == "(Nenhum/Outro)":
                plano_de_contas = ""
                
            if nome and nome_fantasia:
                query = """INSERT INTO fornecedores 
                           (nome, telefone, cnpj_cpf, nome_fantasia, inscricao_estadual,
                            endereco, bairro, cep, cidade, uf, email, plano_de_contas, status, prazo_pagamento) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                
                run_query(query, (
                    nome, telefone, cnpj_cpf, nome_fantasia, inscricao_estadual,
                    endereco, bairro, cep, cidade, uf, email, plano_de_contas, status, prazo_pagamento
                ))
                st.success("Fornecedor cadastrado com sucesso!")
            else:
                st.error("Atenção: Razão Social e Nome Fantasia são obrigatórios.")
                
    st.markdown("---")
    st.subheader("Fornecedores Cadastrados")
    df_fornecedores = fetch_all("SELECT id, nome as 'Razão Social', nome_fantasia as 'Nome Fantasia', cnpj_cpf as 'CNPJ', prazo_pagamento as 'Prazo Padrão', status as 'Status' FROM fornecedores")
    if not df_fornecedores.empty:
        export_btn(df_fornecedores, 'fornecedores.csv')
        st.dataframe(df_fornecedores, width="stretch", hide_index=True)

# ======= REGRAS DE COMISSÃO =======
with tab4:
    st.subheader("Regras de Comissão Flexível")
    
    df_vendedores = fetch_all("SELECT id, nome FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%'")
    df_redes_regras = fetch_all("SELECT id, nome FROM redes_clientes")
    redes_options = ["TODOS"] + df_redes_regras['nome'].tolist() if not df_redes_regras.empty else ["TODOS"]
    
    if df_vendedores.empty:
        st.warning("Cadastre representantes comerciais no RH primeiro.")
    else:
        with st.form("form_comissao", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            
            vendedor_dict = dict(zip(df_vendedores['nome'], df_vendedores['id']))
            produto_dict = dict(zip(df_produtos['nome'], df_produtos['id'])) if not df_produtos.empty else {}
            
            prod_lista = ["TODOS"] + list(produto_dict.keys())
            
            nome_vend = col1.selectbox("Representante Responsável", list(vendedor_dict.keys()))
            nome_prod = col2.selectbox("Produto", prod_lista)
            nome_rede = col3.selectbox("Rede de Clientes", redes_options)
            percentual = col4.number_input("Comissão (%)", min_value=0.0, max_value=100.0, step=0.1)
            
            st.markdown("🎯 **Configurações Especiais da Regra**")
            col_g, col_mg, col_vmg = st.columns(3)
            tipo_comissao = col_g.selectbox("Tipo de Comissão", ["FATURAMENTO", "LIQUIDAÇÃO DE TITULO"])
            min_garantido = col_mg.checkbox("Possui Mínimo Garantido?")
            valor_min = col_vmg.number_input("Valor Mínimo (R$)", min_value=0.0, step=50.0)
            
            confirmar = st.checkbox("Confirmo os termos dessa Regra de Comissão.")
            if st.form_submit_button("Salvar Regra"):
                if confirmar:
                    vend_id = vendedor_dict[nome_vend]
                    prod_id = None if nome_prod == "TODOS" else produto_dict[nome_prod]
                    
                    prod_check = "produto_id IS NULL" if prod_id is None else f"produto_id={prod_id}"
                    check_query = f"SELECT id FROM comissoes_regras WHERE vendedor_id=? AND {prod_check} AND rede_clientes=?"
                    chk = fetch_all(check_query, (vend_id, nome_rede))
                    
                    min_val_bool = 1 if min_garantido else 0
                    
                    if not chk.empty:
                        run_query(f"UPDATE comissoes_regras SET percentual=?, gatilho_comissao=?, minimo_garantido=?, valor_minimo_garantido=? WHERE vendedor_id=? AND {prod_check} AND rede_clientes=?", 
                                  (percentual, tipo_comissao, min_val_bool, valor_min, vend_id, nome_rede))
                        st.success("Regra atualizada!")
                    else:
                        run_query("INSERT INTO comissoes_regras (vendedor_id, produto_id, rede_clientes, percentual, gatilho_comissao, minimo_garantido, valor_minimo_garantido) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (vend_id, prod_id, nome_rede, percentual, tipo_comissao, min_val_bool, valor_min))
                        st.success("Regra criada com sucesso!")
                    
                    import time; time.sleep(1); st.rerun()
                else:
                    st.error("Aviso: Marque a caixa de confirmação.")
                    
    st.markdown("---")
    st.subheader("Gerenciar Regras Cadastradas")
    df_regras = fetch_all('''
    SELECT c.id, f.nome as Repr, COALESCE(p.nome, 'TODOS') as Produto, c.rede_clientes as 'Rede', 
           c.percentual as "Comissão (%)", c.gatilho_comissao as 'Tipo', 
           c.minimo_garantido as 'Tem Min', c.valor_minimo_garantido as 'Vlr Min R$'
    FROM comissoes_regras c 
    JOIN funcionarios f ON c.vendedor_id = f.id
    LEFT JOIN produtos p ON c.produto_id = p.id
    ''')
    if not df_regras.empty:
        df_regras['Tem Min'] = df_regras['Tem Min'].map({1: 'Sim', 0: 'Não', True: 'Sim', False: 'Não'})
        export_btn(df_regras, 'regras_comissao.csv')
        st.dataframe(df_regras, width="stretch", hide_index=True)
        
        with st.expander("🗑️ Excluir Regra"): 
            opts_exc = {f"ID {row['id']} | {row['Repr']} | {row['Produto']}": row['id'] for _, row in df_regras.iterrows()}
            r_del = st.selectbox("Selecione a Regra:", list(opts_exc.keys()))
            if st.button("Excluir Regra"):
                run_query("DELETE FROM comissoes_regras WHERE id=?", (opts_exc[r_del],))
                st.rerun()

# ======= PLANO DE CONTAS =======
with tab5:
    st.subheader("Plano de Contas - Categorias do DRE")
    
    CATEGORIAS_MAP = {
        "Receita Operacional": "RECEITA",
        "Receita Não Operacional": "RECEITA_NAO_OP",
        "Custo Variável": "CUSTO_VAR",
        "Despesa Comercial / Marketing": "DESPESA_COM",
        "Despesa Fixa": "DESPESA_FIXA",
        "Despesa Administrativa": "DESPESA_ADM",
        "Despesa Não Operacional": "DESPESA_NAO_OP",
        "Investimento": "INVESTIMENTO"
    }

    with st.form("form_plano", clear_on_submit=True):
        col_code, col_cat, col_name = st.columns([1, 2, 3])
        codigo_conta = col_code.text_input("Código (Ex: 2.2.5)")
        categoria_label = col_cat.selectbox("Categoria", list(CATEGORIAS_MAP.keys()))
        nome_conta = col_name.text_input("Nome da Conta (Ex: Marketing)")
        
        if st.form_submit_button("Adicionar Nova Conta"):
            if not codigo_conta:
                st.error("Por favor, informe o Código da conta.")
            elif not nome_conta:
                st.error("Por favor, informe o Nome da conta.")
            else:
                db_categoria = CATEGORIAS_MAP[categoria_label]
                run_query("INSERT INTO planos_de_contas (codigo, categoria, nome) VALUES (?, ?, ?)", 
                          (codigo_conta.strip(), db_categoria, nome_conta.strip()))
                st.success("Conta adicionada!")
                import time; time.sleep(1); st.rerun()
                
    st.markdown("---")
    df_planos_view = fetch_all("SELECT id, codigo as 'Código', categoria as 'Categoria Financeira', nome as 'Nome da Conta' FROM planos_de_contas ORDER BY codigo, nome")
    if not df_planos_view.empty:
        export_btn(df_planos_view, 'plano_de_contas.csv')
        st.dataframe(df_planos_view, width="stretch", hide_index=True)

# ======= CONTAS BANCÁRIAS =======
with tab6:
    st.subheader("Cadastro de Contas Bancárias")
    with st.form("form_contas_bancarias"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Apelido da Conta")
        banco = c2.text_input("Nome do Banco")
        tipo_conta = c3.selectbox("Tipo de Conta", ["Corrente", "Poupança", "Espécie", "Aplicação"])
        
        c4, c5, c6 = st.columns(3)
        agencia = c4.text_input("Agência")
        conta_res = c5.text_input("Conta")
        saldo_inicial = c6.number_input("Saldo Inicial", value=0.0, step=0.01)
        
        if st.form_submit_button("Salvar Conta"):
            if nome:
                run_query("INSERT INTO contas_bancarias (nome, banco, agencia, conta, saldo_inicial, tipo_conta) VALUES (?, ?, ?, ?, ?, ?)",
                          (nome, banco, agencia, conta_res, saldo_inicial, tipo_conta))
                st.success("Conta adicionada!")
                import time; time.sleep(1); st.rerun()

    st.markdown("---")
    df_contas_view = fetch_all("SELECT id, nome as 'Nome/Apelido', banco as 'Banco', agencia as 'Agência', conta as 'Conta', tipo_conta as 'Tipo' FROM contas_bancarias")
    if not df_contas_view.empty:
        st.dataframe(df_contas_view, width="stretch", hide_index=True)

# ======= MAQUINÁRIO E IMOBILIZADO =======
with tab7:
    st.subheader("Ativos Fixos e Maquinário Fabril")
    with st.form("form_maquinario", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        nome_maq = col_m1.text_input("Nome da Máquina")
        data_aq_maq = col_m2.date_input("Data de Aquisição", format="DD/MM/YYYY")
        valor_aq = col_m3.number_input("Valor Pago na Aquisição (R$)", min_value=0.0, step=0.01)

        col_m4, col_m5, col_m6 = st.columns(3)
        vida_util = col_m4.number_input("Vida Útil Estimada (Anos)", min_value=0.0, value=10.0, step=0.5)
        dep_manual = col_m5.number_input("Depreciação Mensal R$", value=0.0, step=0.01)
        status_maq = col_m6.selectbox("Status", ["ATIVO", "INATIVO (Vendido/Quebrado)"])
        obs_maq = st.text_input("Observações")
        
        if st.form_submit_button("Imobilizar Patrimônio"):
            if nome_maq:
                if dep_manual <= 0 and vida_util > 0: dep_manual = valor_aq / (vida_util * 12)
                run_query("INSERT INTO maquinario (nome, valor_aquisicao, vida_util_anos, valor_depreciacao_mensal, data_aquisicao, status, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (nome_maq, valor_aq, vida_util, dep_manual, data_aq_maq, status_maq.split()[0], obs_maq))
                st.success("Ativo imobilizado!")
                import time; time.sleep(1); st.rerun()

    st.markdown("---")
    df_maq = fetch_all("SELECT id, nome as 'Máquina/Ativo', data_aquisicao as 'Data', valor_aquisicao as 'Valor R$', valor_depreciacao_mensal as 'Perda Mensal R$' FROM maquinario")
    if not df_maq.empty:
        df_maq['Data'] = pd.to_datetime(df_maq['Data']).dt.strftime('%d/%m/%Y')
        export_btn(df_maq, 'maquinario.csv')
        st.dataframe(df_maq, hide_index=True, width="stretch")

# ======= USUÁRIOS =======
with tab8:
    st.subheader("Governança: Acessos ao Sistema")
    with st.form("form_usr", clear_on_submit=True):
        cu1, cu2, cu3, cu4 = st.columns(4)
        nome_usr = cu1.text_input("Nome")
        mail_usr = cu2.text_input("Login/E-mail")
        pwd_usr = cu3.text_input("Senha", type="password")
        nivel_usr = cu4.selectbox("Hierarquia", ["Administrador Geral", "Engenharia P&D", "Operador Máquina", "Comercial / Rotas", "Tesouraria"])
        
        if st.form_submit_button("Registrar Credencial"):
            if nome_usr and mail_usr and pwd_usr:
                run_query("INSERT INTO usuarios (nome, email, senha, nivel_permissao, status) VALUES (?, ?, ?, ?, 'ATIVO')", (nome_usr, mail_usr, pwd_usr, nivel_usr))
                st.success("Licença ativada!")
                import time; time.sleep(1); st.rerun()

    st.markdown("---")
    df_usr = fetch_all("SELECT id, nome as 'Usuário', email as 'Login', nivel_permissao as 'Hierarquia', status as 'Status' FROM usuarios")
    if not df_usr.empty:
        st.dataframe(df_usr, hide_index=True, width="stretch")

# ======= REDES E GRUPOS =======
with tab9:
    st.subheader("Cadastro de Redes e Grupos de Clientes")
    colA, colB = st.columns(2)
    
    with colA:
        with st.form("form_rede", clear_on_submit=True):
            st.markdown("##### 🏢 Cadastrar Nova Rede")
            nome_rede = st.text_input("Nome da Rede (Ex: Atacadão, Assaí)")
            if st.form_submit_button("Salvar Rede"):
                if nome_rede:
                    chk = fetch_all("SELECT id FROM redes_clientes WHERE nome=?", (nome_rede,))
                    if chk.empty:
                        run_query("INSERT INTO redes_clientes (nome) VALUES (?)", (nome_rede,))
                        st.success("Rede cadastrada com sucesso!")
                        import time; time.sleep(1); st.rerun()
                    else:
                        st.error("Rede já existe.")
        
        df_r = fetch_all("SELECT id, nome as 'Rede' FROM redes_clientes")
        if not df_r.empty:
            st.dataframe(df_r, hide_index=True, use_container_width=True)

    with colB:
        with st.form("form_grupo", clear_on_submit=True):
            st.markdown("##### 🏬 Cadastrar Sub-Grupo (opcional)")
            rede_vinculada = st.selectbox("Rede Matriz", df_r['Rede'].tolist()) if not df_r.empty else st.selectbox("Rede Matriz", ["Nenhuma rede cadastrada"])
            nome_grupo = st.text_input("Nome do Grupo (Ex: Lojas Zona Sul)")
            
            if st.form_submit_button("Salvar Grupo"):
                if nome_grupo and not df_r.empty:
                    rede_id = int(fetch_all("SELECT id FROM redes_clientes WHERE nome=?", (rede_vinculada,)).iloc[0]['id'])
                    run_query("INSERT INTO grupos_clientes (rede_id, nome) VALUES (?, ?)", (rede_id, nome_grupo))
                    st.success("Grupo cadastrado com sucesso!")
                    import time; time.sleep(1); st.rerun()
                    
        df_g = fetch_all("SELECT g.id, g.nome as 'Grupo', r.nome as 'Rede Matriz' FROM grupos_clientes g JOIN redes_clientes r ON g.rede_id = r.id")
        if not df_g.empty:
            st.dataframe(df_g, hide_index=True, use_container_width=True)


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

# ======= FICHAS TÉCNICAS (BOM) =======
with tab_ft:
    st.subheader("🧪 Fichas Técnicas de Produção")
    st.markdown(
        "A **Ficha Técnica** é a receita de cada produto final: quais insumos (MP + embalagens) "
        "são consumidos por unidade produzida. O módulo de Produção carrega isso automaticamente."
    )

    # Carrega listas de produtos
    df_pf_ft  = fetch_all("SELECT id, nome, unidade_medida FROM produtos WHERE is_materia_prima=0 ORDER BY nome")
    df_ins_ft = fetch_all("SELECT id, nome, unidade_medida, is_materia_prima FROM produtos ORDER BY is_materia_prima DESC, nome")

    if df_pf_ft.empty:
        st.warning("Cadastre produtos finais primeiro (aba Produtos).")
        st.stop()

    pf_dict_ft  = {f"{r['nome']}": r for _, r in df_pf_ft.iterrows()}
    ins_dict_ft = {f"{r['nome']} ({r['unidade_medida']})": r for _, r in df_ins_ft.iterrows()}

    # ── Criação / Edição de Ficha ─────────────────────────────────────────────
    st.markdown("### 1️⃣ Selecione o Produto Final")
    produto_ft_sel = st.selectbox(
        "Produto que será fabricado:", list(pf_dict_ft.keys()), key="ft_produto_sel"
    )
    pf_row_ft = pf_dict_ft[produto_ft_sel]
    pf_id_ft  = int(pf_row_ft['id'])

    # Verifica se já existe ficha para este produto
    df_ficha_exist = fetch_all(
        "SELECT id, rendimento_percentual, observacoes FROM fichas_tecnicas WHERE produto_id=?",
        (pf_id_ft,)
    )
    ficha_id_ft = None
    if not df_ficha_exist.empty:
        ficha_id_ft = int(df_ficha_exist.iloc[0]['id'])
        rend_atual  = float(df_ficha_exist.iloc[0]['rendimento_percentual'])
        obs_atual   = df_ficha_exist.iloc[0]['observacoes'] or ""
        st.success(f"✅ Ficha Técnica existente para **{produto_ft_sel}** (ID #{ficha_id_ft})")
    else:
        rend_atual = 70.0
        obs_atual  = ""
        st.info(f"📋 Nenhuma Ficha Técnica cadastrada ainda para **{produto_ft_sel}**. Crie abaixo.")

    # ── Cabeçalho da Ficha ────────────────────────────────────────────────────
    st.markdown("### 2️⃣ Parâmetros Gerais da Receita")
    ft_c1, ft_c2 = st.columns([1, 3])
    rendimento_ft = ft_c1.number_input(
        "Rendimento (%)",
        min_value=1.0, max_value=100.0,
        value=rend_atual, step=0.5,
        help="% de aproveitamento da matéria-prima bruta. Ex: 70% → 1,4 kg de MP bruta para 1 kg de produto.",
        key="ft_rendimento"
    )
    obs_ft = ft_c2.text_input("Observações da Receita", value=obs_atual, key="ft_obs")

    # ── Itens da Ficha ────────────────────────────────────────────────────────
    st.markdown("### 3️⃣ Ingredientes (Insumos por unidade produzida)")
    st.caption(
        f"Informe **quanto de cada insumo é consumido para produzir 1 {pf_row_ft['unidade_medida']} "
        f"de {produto_ft_sel}**."
    )

    # Carrega itens existentes
    itens_existentes = []
    if ficha_id_ft:
        df_itens_ft = fetch_all("""
            SELECT fti.id, p.nome as insumo_nome, p.unidade_medida as unidade,
                   fti.quantidade_por_unidade, fti.tipo, fti.insumo_id
            FROM fichas_tecnicas_itens fti
            JOIN produtos p ON fti.insumo_id = p.id
            WHERE fti.ficha_id = ?
            ORDER BY fti.tipo DESC, p.nome
        """, (ficha_id_ft,))
        if not df_itens_ft.empty:
            st.markdown("**Ingredientes cadastrados:**")
            for _, item_ft in df_itens_ft.iterrows():
                col_ft_a, col_ft_b, col_ft_c = st.columns([3, 1, 1])
                col_ft_a.markdown(
                    f"{'🌾' if item_ft['tipo']=='MP' else '📦'} **{item_ft['insumo_nome']}** "
                    f"({item_ft['unidade']})"
                )
                col_ft_b.metric("Qtd / unidade", f"{item_ft['quantidade_por_unidade']:.4f}")
                if col_ft_c.button("🗑️ Remover", key=f"del_ft_{item_ft['id']}"):
                    run_query("DELETE FROM fichas_tecnicas_itens WHERE id=?", (item_ft['id'],))
                    import time; time.sleep(0.3); st.rerun()
            st.markdown("---")

    # ── Adicionar novo ingrediente ────────────────────────────────────────────
    st.markdown("**➕ Adicionar ingrediente:**")
    aic1, aic2, aic3 = st.columns([3, 1, 1])
    ins_sel_ft  = aic1.selectbox("Insumo / Matéria-Prima", list(ins_dict_ft.keys()), key="ft_ins_sel")
    qtd_por_un  = aic2.number_input(
        f"Qtd por 1 {pf_row_ft['unidade_medida']}",
        min_value=0.0001, step=0.001, format="%.4f", value=1.0, key="ft_qtd"
    )
    tipo_ins_ft = aic3.selectbox("Tipo", ["MP", "EMBALAGEM", "INSUMO"], key="ft_tipo")

    if st.button("➕ Adicionar Ingrediente", use_container_width=True):
        ins_row_sel = ins_dict_ft[ins_sel_ft]
        ins_id_sel  = int(ins_row_sel['id'])

        # Garante que a ficha existe (cria se necessário)
        if not ficha_id_ft:
            run_query(
                "INSERT INTO fichas_tecnicas (produto_id, rendimento_percentual, observacoes) VALUES (?,?,?)",
                (pf_id_ft, rendimento_ft, obs_ft)
            )
            df_nova = fetch_all(
                "SELECT id FROM fichas_tecnicas WHERE produto_id=?", (pf_id_ft,)
            )
            ficha_id_ft = int(df_nova.iloc[0]['id'])

        # Atualiza cabeçalho
        run_query(
            "UPDATE fichas_tecnicas SET rendimento_percentual=?, observacoes=? WHERE id=?",
            (rendimento_ft, obs_ft, ficha_id_ft)
        )
        # Insere item
        run_query(
            "INSERT INTO fichas_tecnicas_itens (ficha_id, insumo_id, quantidade_por_unidade, tipo) VALUES (?,?,?,?)",
            (ficha_id_ft, ins_id_sel, qtd_por_un, tipo_ins_ft)
        )
        st.success(f"Ingrediente '{ins_sel_ft}' adicionado!")
        import time; time.sleep(0.3); st.rerun()

    # ── Salvar cabeçalho (rendimento / obs) ───────────────────────────────────
    if ficha_id_ft:
        if st.button("💾 Salvar Rendimento e Observações", key="ft_salvar_cab"):
            run_query(
                "UPDATE fichas_tecnicas SET rendimento_percentual=?, observacoes=? WHERE id=?",
                (rendimento_ft, obs_ft, ficha_id_ft)
            )
            st.success("Ficha Técnica atualizada!")
            import time; time.sleep(0.5); st.rerun()

    # ── Excluir ficha completa ────────────────────────────────────────────────
    if ficha_id_ft:
        st.markdown("---")
        with st.expander("🗑️ Excluir Ficha Técnica completa"):
            st.warning("Isso apaga a receita e todos os ingredientes deste produto.")
            if st.button("Excluir Ficha Técnica", type="primary"):
                run_query("DELETE FROM fichas_tecnicas_itens WHERE ficha_id=?", (ficha_id_ft,))
                run_query("DELETE FROM fichas_tecnicas WHERE id=?", (ficha_id_ft,))
                st.success("Ficha excluída.")
                import time; time.sleep(0.5); st.rerun()

    # ── Visão geral de todas as fichas ───────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Visão Geral — Todas as Fichas Técnicas")
    df_all_fichas = fetch_all("""
        SELECT p.nome as 'Produto Final', p.unidade_medida as 'Unid.',
               ft.rendimento_percentual as 'Rendimento (%)',
               COUNT(fti.id) as 'Qtd Ingredientes',
               ft.observacoes as 'Obs'
        FROM fichas_tecnicas ft
        JOIN produtos p ON ft.produto_id = p.id
        LEFT JOIN fichas_tecnicas_itens fti ON fti.ficha_id = ft.id
        GROUP BY ft.id
        ORDER BY p.nome
    """)
    if df_all_fichas.empty:
        st.info("Nenhuma ficha técnica cadastrada ainda.")
    else:
        st.dataframe(df_all_fichas, hide_index=True, use_container_width=True)
        st.caption(
            "💡 **Dica:** Produtos sem ficha técnica ainda aparecem aqui apenas quando criados. "
            "O módulo de Produção usa a ficha para sugerir quantidades automaticamente."
        )
