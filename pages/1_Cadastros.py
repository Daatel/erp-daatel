import streamlit as st
import pandas as pd
from database import run_query, fetch_all, registrar_log_acesso
from estilo import carregar_estilo
from datetime import date

st.set_page_config(page_title="Cadastros Base", page_icon="📝", layout="wide")
carregar_estilo()

st.title("📝 Cadastros Inteligentes")

tab_empresa, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab_fp, tab_ft = st.tabs([
    "🏢 Minha Empresa", "Produtos", "Clientes", "Fornecedores", "Regras de Comissão", 
    "Plano de Contas", "Contas Bancárias", "Maquinário", "Usuários", "Redes e Grupos",
    "💳 Formas de Pagamento", "🧪 Fichas Técnicas"
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
        
        st.markdown("### 🤖 Configuração do Robô de Relatórios (Telegram)")
        st.caption("Crie um Bot com o @BotFather no Telegram para receber o resumo diário de fechamento financeiro e de vendas.")
        e_tel1, e_tel2 = st.columns(2)
        telegram_token = e_tel1.text_input("Token do Bot Telegram", value=emp.get('telegram_token', '') or '', type="password", help="Ex: 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
        telegram_chat_id = e_tel2.text_input("ID do Chat Telegram (Seu Chat ID)", value=emp.get('telegram_chat_id', '') or '', help="Ex: 987654321. Você pode obter seu ID conversando com o @userinfobot no Telegram.")
        
        if st.form_submit_button("Salvar Dados da Empresa"):
            run_query("""
                UPDATE empresa_config 
                SET razao_social=?, nome_fantasia=?, cnpj=?, endereco_completo=?, telefone=?, email=?,
                    inscricao_estadual=?, inscricao_municipal=?, cep=?, instagram=?, website=?,
                    telegram_token=?, telegram_chat_id=?
                WHERE id=?
            """, (r_social, n_fantasia, cnpj_emp, end_emp, telefone_emp, email_emp, ie_emp, im_emp, cep_emp, insta_emp, web_emp, telegram_token, telegram_chat_id, emp['id']))
            st.success("Dados da Empresa e credenciais de Telegram atualizados!")
            import time; time.sleep(1); st.rerun()

    # Botões de Teste de Disparo dos Relatórios
    if emp.get('telegram_token') and emp.get('telegram_chat_id'):
        st.markdown("---")
        st.markdown("#### 🧪 Testes de Conectividade de Relatórios")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            if st.button("📲 Enviar Relatório de Profilaxia (Auditoria)", use_container_width=True):
                from database import enviar_relatorio_profilaxia_async
                enviar_relatorio_profilaxia_async()
                st.success("✅ Solicitado! O relatório de profilaxia está sendo processado em background. Verifique seu Telegram em alguns instantes.")
                    
        with col_t2:
            if st.button("📊 Enviar Resumo do Dia do CEO (Cockpit)", use_container_width=True):
                from database import enviar_relatorio_resumo_executivo_async
                enviar_relatorio_resumo_executivo_async()
                st.success("✅ Solicitado! O resumo executivo do CEO está sendo gerado em background. Verifique seu Telegram em alguns instantes.")

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
                                    chave_pix_val = row.get('Código Pix', row.get('Chave Pix', ''))
                                    
                                    rep_nome = row.get('Representante', '')
                                    rep_id = rep_id_map.get(rep_nome, None) if rep_nome else None
                                    
                                    # Tentar achar correspondência para prazo_pag
                                    fp_id_val = None
                                    if prazo_pag:
                                        df_match = fetch_all("SELECT id FROM formas_pagamento WHERE UPPER(TRIM(nome)) = ?", (prazo_pag.strip().upper(),))
                                        if not df_match.empty:
                                            fp_id_val = int(df_match.iloc[0]['id'])

                                    query_insert = """INSERT INTO clientes 
                                               (nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual, 
                                                bairro, cep, cidade, uf, email, observacoes, status, rede_clientes, 
                                                grupo_lojas, prazo_pagamento, representante_id, data_nascimento, prazo_pagamento_dias, taxa_descarga, regras_descarga, chave_pix, forma_pagamento_id) 
                                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                                    
                                    run_query(query_insert, (
                                        razao, telefone, endereco, nome_fantasia, cnpj, insc_estadual,
                                        bairro, cep, cidade, uf, email, observacoes, status_val, rede_val,
                                        grupo_val, prazo_pag, rep_id, None, 30, 0.0, "", chave_pix_val, fp_id_val
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
        
        c11, c12, c13, c_pix = st.columns(4)
        cep = c11.text_input("CEP")
        grupo_lojas = c12.selectbox("2. Grupo (Sub-rede)", grupos_opts)
        status = c13.selectbox("Status", ["ATIVO", "INATIVO"])
        chave_pix = c_pix.text_input("Código Pix")
        
        c14, c16, c17 = st.columns(3)
        # Buscar formas de pagamento
        df_fp_list = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
        fp_opts = {}
        if not df_fp_list.empty:
            for _, r in df_fp_list.iterrows():
                fp_opts[r['nome']] = (r['id'], r['parcelas'])

        fp_selecionada = c14.selectbox("Forma de Pagamento Padrão", list(fp_opts.keys()))
        
        if fp_selecionada:
            fp_id_val, fp_parc_val = fp_opts[fp_selecionada]
            import re
            first_day = 0
            nums = re.findall(r'\d+', fp_parc_val)
            if nums:
                first_day = int(nums[0])
        else:
            fp_id_val = None
            fp_selecionada = ""
            first_day = 30
            
        rep_nome = c16.selectbox("Representante Responsável", rep_options)
        observacoes = c17.text_input("Observações")
        
        st.info(f"Rede Vinculada a este client: **{rede_dinamica}**")
        
        st.markdown("##### Logística e Descarga")
        c18, c19 = st.columns([1, 3])
        taxa_descarga = c18.number_input("Taxa de Descarga (R$)", min_value=0.0, step=10.0, help="Valor cobrado pelo CD/Cliente para descarregar o caminhão.")
        regras_descarga = c19.text_input("Regras e Horários de Descarga", help="Ex: Descarga Paletizada, Horário Noturno, Agendamento.")
        
        if st.form_submit_button("Cadastrar Cliente"):
            if nome:
                nome_limpo = nome.strip().upper()
                # 1. Validar se o nome já existe
                chk_nome = fetch_all("SELECT id FROM clientes WHERE UPPER(TRIM(nome)) = ?", (nome_limpo,))
                
                # 2. Validar CNPJ/CPF se preenchido
                chk_cnpj = pd.DataFrame()
                cnpj_val = cnpj_cpf.strip() if cnpj_cpf else ""
                if cnpj_val:
                    chk_cnpj = fetch_all("SELECT id FROM clientes WHERE TRIM(cnpj_cpf) = ?", (cnpj_val,))
                
                if not chk_nome.empty:
                    st.error(f"⚠️ Já existe um cliente cadastrado com o nome '{nome.strip()}'. Se forem clientes diferentes, diferencie-os no nome (ex: '{nome.strip()} RJ', '{nome.strip()} - Filial').")
                elif not chk_cnpj.empty:
                    st.error(f"⚠️ Já existe um cliente cadastrado com o CNPJ/CPF '{cnpj_val}'.")
                else:
                    req_id = rep_dict.get(rep_nome, None)
                    rede_val = rede_dinamica if rede_dinamica != "(Nenhuma)" else ""
                    grupo_val = grupo_lojas if grupo_lojas != "(Nenhum)" else ""
                    
                    query = """INSERT INTO clientes 
                               (nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual, 
                                bairro, cep, cidade, uf, email, observacoes, status, rede_clientes, 
                                grupo_lojas, prazo_pagamento, representante_id, data_nascimento, prazo_pagamento_dias, taxa_descarga, regras_descarga, chave_pix, forma_pagamento_id) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    
                    run_query(query, (
                        nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual,
                        bairro, cep, cidade, uf, email, observacoes, status, rede_val,
                        grupo_val, fp_selecionada, req_id, nascimento, first_day, taxa_descarga, regras_descarga, chave_pix, fp_id_val
                    ))
                    st.success("Cliente cadastrado com sucesso!")
                    import time; time.sleep(1); st.rerun()
            else:
                st.error("Por favor, preencha a Razão Social.")
                
    st.markdown("---")
    st.subheader("Clientes Cadastrados")
    df_clientes = fetch_all("""
        SELECT c.id, c.nome as 'Razão Social', c.cnpj_cpf as 'CNPJ/CPF', c.cidade as 'Cidade', c.uf as 'UF', 
               c.rede_clientes as 'Rede', c.grupo_lojas as 'Grupo', COALESCE(fp.nome, c.prazo_pagamento) as 'Forma Pagto',
               c.status as 'Status', f.nome as 'Representante',
               c.taxa_descarga as 'Taxa Descarga (R$)', c.regras_descarga as 'Regras Descarga', c.chave_pix as 'Código Pix'
        FROM clientes c
        LEFT JOIN funcionarios f ON c.representante_id = f.id
        LEFT JOIN formas_pagamento fp ON c.forma_pagamento_id = fp.id
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
                    
                    df_reps_edit = fetch_all("SELECT id, nome FROM funcionarios WHERE cargo LIKE '%Representante%' OR cargo LIKE '%Vendedor%'")
                    rep_options_edit = ["(Nenhum/Direto)"] + df_reps_edit['nome'].tolist() if not df_reps_edit.empty else ["(Nenhum/Direto)"]
                    rep_dict_edit = dict(zip(df_reps_edit['nome'], df_reps_edit['id'])) if not df_reps_edit.empty else {}
                    rep_reverse_dict_edit = dict(zip(df_reps_edit['id'], df_reps_edit['nome'])) if not df_reps_edit.empty else {}

                    with st.form("edit_cli"):
                        ec1, ec2, ec3, ec_n = st.columns(4)
                        enome = ec1.text_input("Razão Social", cb['nome'])
                        enome_fantasia = ec2.text_input("Nome Fantasia", cb['nome_fantasia'] if cb['nome_fantasia'] else "")
                        edoc = ec3.text_input("CNPJ/CPF", cb['cnpj_cpf'] if cb['cnpj_cpf'] else "")
                        
                        try:
                            val_nasc = pd.to_datetime(cb['data_nascimento']).date() if pd.notnull(cb['data_nascimento']) else None
                        except:
                            val_nasc = None
                        enascimento = ec_n.date_input("Data de Nasc/Fundação", value=val_nasc, format="DD/MM/YYYY")
                        
                        ec4, ec5, ec6 = st.columns(3)
                        eie = ec4.text_input("Inscrição Estadual", cb['inscricao_estadual'] if cb['inscricao_estadual'] else "")
                        etelefone = ec5.text_input("Telefone", cb['telefone'] if cb['telefone'] else "")
                        eemail = ec6.text_input("E-mail", cb['email'] if cb['email'] else "")
                        
                        ec7, ec8, ec9, ec10 = st.columns([2, 1, 1, 1])
                        eendereco = ec7.text_input("Endereço", cb['endereco'] if cb['endereco'] else "")
                        ebairro = ec8.text_input("Bairro", cb['bairro'] if cb['bairro'] else "")
                        ecidade = ec9.text_input("Cidade", cb['cidade'] if cb['cidade'] else "")
                        euf = ec10.text_input("UF", cb['uf'] if cb['uf'] else "")
                        
                        ec11, ec12, ec13, ec_pix = st.columns(4)
                        ecep = ec11.text_input("CEP", cb['cep'] if cb['cep'] else "")
                        erede = ec12.text_input("Rede", cb['rede_clientes'] if cb['rede_clientes'] else "")
                        egrupo_lojas = ec13.text_input("Grupo (Sub-rede)", cb['grupo_lojas'] if cb['grupo_lojas'] else "")
                        echave_pix = ec_pix.text_input("Código Pix", cb['chave_pix'] if cb['chave_pix'] else "")
                        
                        # Buscar formas de pagamento
                        df_fp_list_edit = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
                        fp_opts_edit = {}
                        if not df_fp_list_edit.empty:
                            for _, r in df_fp_list_edit.iterrows():
                                fp_opts_edit[r['nome']] = (r['id'], r['parcelas'])
                        
                        # Pegar valor atual
                        fp_atual_nome = cb['prazo_pagamento']
                        if cb['forma_pagamento_id']:
                            df_cur_fp = fetch_all("SELECT nome FROM formas_pagamento WHERE id=?", (int(cb['forma_pagamento_id']),))
                            if not df_cur_fp.empty:
                                fp_atual_nome = df_cur_fp.iloc[0]['nome']
                        
                        idx_fp = 0
                        if fp_atual_nome in fp_opts_edit:
                            idx_fp = list(fp_opts_edit.keys()).index(fp_atual_nome)
                        
                        ec14, ec16, ec17 = st.columns(3)
                        efp_selecionada = ec14.selectbox("Forma de Pagamento Padrão", list(fp_opts_edit.keys()), index=idx_fp, key=f"efp_{cid}")
                        
                        if efp_selecionada:
                            efp_id_val, efp_parc_val = fp_opts_edit[efp_selecionada]
                            import re
                            efirst_day = 0
                            nums = re.findall(r'\d+', efp_parc_val)
                            if nums:
                                efirst_day = int(nums[0])
                        else:
                            efp_id_val = None
                            efp_selecionada = ""
                            efirst_day = 30
                            
                        rep_default = rep_reverse_dict_edit.get(cb['representante_id'], "(Nenhum/Direto)")
                        idx_rep = rep_options_edit.index(rep_default) if rep_default in rep_options_edit else 0
                        erep_nome = ec16.selectbox("Vendedor Responsável", rep_options_edit, index=idx_rep)
                        
                        eobs = ec17.text_input("Observações", cb['observacoes'] if cb['observacoes'] else "")
                        
                        c_stts = ["ATIVO", "INATIVO"]
                        d_stts = cb['status'] if cb['status'] in c_stts else "ATIVO"
                        estatus = st.selectbox("Status da Conta", c_stts, index=c_stts.index(d_stts))
                        
                        st.markdown("##### Logística e Descarga")
                        ec_l1, ec_l2 = st.columns([1, 3])
                        etaxa = ec_l1.number_input("Taxa de Descarga (R$)", value=float(cb['taxa_descarga']) if pd.notnull(cb['taxa_descarga']) else 0.0, step=10.0)
                        eregras = ec_l2.text_input("Regras/Horários de Descarga", cb['regras_descarga'] if cb['regras_descarga'] else "")
                        
                        if st.form_submit_button("Salvar Cliente"):
                            enome_limpo = enome.strip().upper()
                            # 1. Validar se o nome já existe em outro cliente
                            chk_nome_edit = fetch_all("SELECT id FROM clientes WHERE UPPER(TRIM(nome)) = ? AND id != ?", (enome_limpo, cid))
                            
                            # 2. Validar se o CNPJ/CPF já existe em outro cliente
                            chk_cnpj_edit = pd.DataFrame()
                            edoc_val = edoc.strip() if edoc else ""
                            if edoc_val:
                                chk_cnpj_edit = fetch_all("SELECT id FROM clientes WHERE TRIM(cnpj_cpf) = ? AND id != ?", (edoc_val, cid))
                            
                            if not chk_nome_edit.empty:
                                st.error(f"⚠️ Já existe outro cliente cadastrado com o nome '{enome.strip()}'. Para salvar, diferencie-o (ex: '{enome.strip()} RJ', '{enome.strip()} - Filial').")
                            elif not chk_cnpj_edit.empty:
                                st.error(f"⚠️ Já existe outro cliente cadastrado com o CNPJ/CPF '{edoc_val}'.")
                            else:
                                nasc_str = enascimento.strftime("%Y-%m-%d") if enascimento else None
                                rep_id_val = rep_dict_edit.get(erep_nome, None) if erep_nome != "(Nenhum/Direto)" else None
                                
                                run_query("""
                                    UPDATE clientes 
                                    SET nome=?, nome_fantasia=?, cnpj_cpf=?, data_nascimento=?, inscricao_estadual=?,
                                        telefone=?, email=?, endereco=?, bairro=?, cidade=?, uf=?, cep=?, rede_clientes=?, grupo_lojas=?,
                                        status=?, chave_pix=?, prazo_pagamento=?, prazo_pagamento_dias=?, representante_id=?,
                                        observacoes=?, taxa_descarga=?, regras_descarga=?, forma_pagamento_id=? 
                                    WHERE id=?
                                """, (enome, enome_fantasia, edoc, nasc_str, eie,
                                      etelefone, eemail, eendereco, ebairro, ecidade, euf, ecep, erede, egrupo_lojas,
                                      estatus, echave_pix, efp_selecionada, efirst_day, rep_id_val,
                                      eobs, etaxa, eregras, efp_id_val, cid))
                                st.success("Cliente alterado com sucesso!")
                                import time; time.sleep(1); st.rerun()
                            import time; time.sleep(1); st.rerun()

# ======= FORNECEDORES =======
with tab3:
    st.subheader("Cadastro de Fornecedores")
    
    df_planos = fetch_all("SELECT id, nome FROM planos_de_contas ORDER BY nome")
    planos_options = df_planos['nome'].tolist() if not df_planos.empty else []
    planos_dict = dict(zip(df_planos['nome'], df_planos['id'])) if not df_planos.empty else {}
    planos_reverse_dict = dict(zip(df_planos['id'], df_planos['nome'])) if not df_planos.empty else {}
    
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
            plano_id_val = planos_dict.get(plano_de_contas, None) if plano_de_contas != "(Nenhum/Outro)" else None
        else:
            plano_de_contas = c13.text_input("Plano de Contas")
            plano_id_val = None
            
        df_fp_list = fetch_all("SELECT id, nome FROM formas_pagamento ORDER BY id ASC")
        fp_opts = {}
        if not df_fp_list.empty:
            for _, r in df_fp_list.iterrows():
                fp_opts[r['nome']] = r['id']
                
        col_prazo, col_pix = st.columns(2)
        fp_selecionada = col_prazo.selectbox("Condição/Prazo Pagamento Padrão", list(fp_opts.keys()), key="forn_fp_sel")
        fp_id_val = fp_opts.get(fp_selecionada, None)
        chave_pix = col_pix.text_input("Código Pix")
            
        if st.form_submit_button("Cadastrar Fornecedor"):
            if plano_de_contas == "(Nenhum/Outro)":
                plano_de_contas = ""
                
            if nome and nome_fantasia:
                nome_limpo = nome.strip().upper()
                chk_nome = fetch_all("SELECT id FROM fornecedores WHERE UPPER(TRIM(nome)) = ?", (nome_limpo,))
                
                chk_cnpj = pd.DataFrame()
                cnpj_val = cnpj_cpf.strip() if cnpj_cpf else ""
                if cnpj_val:
                    chk_cnpj = fetch_all("SELECT id FROM fornecedores WHERE TRIM(cnpj_cpf) = ?", (cnpj_val,))
                
                if not chk_nome.empty:
                    st.error(f"⚠️ Já existe um fornecedor cadastrado com a Razão Social/Nome '{nome.strip()}'. Se forem fornecedores diferentes, diferencie-os no nome (ex: '{nome.strip()} RJ', '{nome.strip()} - Filial').")
                elif not chk_cnpj.empty:
                    st.error(f"⚠️ Já existe um fornecedor cadastrado com o CNPJ/CPF '{cnpj_val}'.")
                else:
                    query = """INSERT INTO fornecedores 
                               (nome, telefone, cnpj_cpf, nome_fantasia, inscricao_estadual,
                                endereco, bairro, cep, cidade, uf, email, plano_de_contas, status, prazo_pagamento, chave_pix, plano_conta_id, forma_pagamento_id) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    
                    run_query(query, (
                        nome, telefone, cnpj_cpf, nome_fantasia, inscricao_estadual,
                        endereco, bairro, cep, cidade, uf, email, plano_de_contas, status, fp_selecionada, chave_pix, plano_id_val, fp_id_val
                    ))
                    st.success("Fornecedor cadastrado com sucesso!")
                    import time; time.sleep(1); st.rerun()
            else:
                st.error("Atenção: Razão Social e Nome Fantasia são obrigatórios.")
                
    st.markdown("---")
    st.subheader("Fornecedores Cadastrados")
    df_fornecedores = fetch_all("SELECT id, nome as 'Razão Social', nome_fantasia as 'Nome Fantasia', cnpj_cpf as 'CNPJ', prazo_pagamento as 'Prazo Padrão', status as 'Status', chave_pix as 'Código Pix', plano_conta_id FROM fornecedores")
    if not df_fornecedores.empty:
        export_btn(df_fornecedores.drop(columns=['plano_conta_id']), 'fornecedores.csv')
        st.dataframe(df_fornecedores.drop(columns=['plano_conta_id']), width="stretch", hide_index=True)
        
        with st.expander("✏️ Editar ou Inativar Fornecedor"):
            opts_forn = {}
            for _, r in df_fornecedores.iterrows():
                lbl = f"ID {r['id']} | {r['Nome Fantasia']} ({r['Status']})"
                opts_forn[lbl] = r['id']
                
            f_sel = st.selectbox("Selecione o Fornecedor:", list(opts_forn.keys()))
            if f_sel:
                fid = opts_forn[f_sel]
                f_data = fetch_all("SELECT * FROM fornecedores WHERE id=?", (fid,))
                if not f_data.empty:
                    fb = f_data.iloc[0]
                    with st.form("edit_forn"):
                        ef1, ef2, ef3 = st.columns(3)
                        enome = ef1.text_input("Razão Social / Nome", fb['nome'])
                        efantasia = ef2.text_input("Nome Fantasia", fb['nome_fantasia'])
                        edoc = ef3.text_input("CNPJ/CPF", fb['cnpj_cpf'] if fb['cnpj_cpf'] else "")
                        
                        ef4, ef5, ef6 = st.columns(3)
                        eie = ef4.text_input("Inscrição Estadual", fb.get('inscricao_estadual', '') if fb.get('inscricao_estadual') else "")
                        etelefone = ef5.text_input("Telefone", fb.get('telefone', '') if fb.get('telefone') else "")
                        eemail = ef6.text_input("E-mail", fb.get('email', '') if fb.get('email') else "")
                        
                        ef7, ef8, ef9, ef10 = st.columns([2, 1, 1, 1])
                        eendereco = ef7.text_input("Endereço", fb.get('endereco', '') if fb.get('endereco') else "")
                        ebairro = ef8.text_input("Bairro", fb.get('bairro', '') if fb.get('bairro') else "")
                        ecidade = ef9.text_input("Cidade", fb.get('cidade', '') if fb.get('cidade') else "")
                        euf = ef10.text_input("UF", fb.get('uf', '') if fb.get('uf') else "")
                        
                        ef11, ef12, ef13 = st.columns(3)
                        ecep = ef11.text_input("CEP", fb.get('cep', '') if fb.get('cep') else "")
                        
                        f_stts = ["ATIVO", "INATIVO"]
                        d_stts = fb['status'] if fb['status'] in f_stts else "ATIVO"
                        estatus = ef12.selectbox("Status", f_stts, index=f_stts.index(d_stts))
                        
                        if planos_options:
                            d_plano_id = fb.get('plano_conta_id') if 'plano_conta_id' in fb else None
                            d_plano = planos_reverse_dict.get(d_plano_id, fb.get('plano_de_contas', '')) if d_plano_id is not None else fb.get('plano_de_contas', '')
                            idx_plano = planos_options.index(d_plano) + 1 if d_plano in planos_options else 0
                            eplano_de_contas = ef13.selectbox("Plano de Contas", ["(Nenhum/Outro)"] + planos_options, index=idx_plano)
                            eplano_id_val = planos_dict.get(eplano_de_contas, None) if eplano_de_contas != "(Nenhum/Outro)" else None
                        else:
                            eplano_de_contas = ef13.text_input("Plano de Contas", fb.get('plano_de_contas', '') if fb.get('plano_de_contas') else "")
                            eplano_id_val = None
                            
                        df_fp_list_edit = fetch_all("SELECT id, nome FROM formas_pagamento ORDER BY id ASC")
                        fp_opts_edit = {}
                        if not df_fp_list_edit.empty:
                            for _, r in df_fp_list_edit.iterrows():
                                fp_opts_edit[r['nome']] = r['id']
                        
                        col_eprazo, col_epix = st.columns(2)
                        
                        d_fp_id = fb.get('forma_pagamento_id') if 'forma_pagamento_id' in fb else None
                        d_fp_nome = ""
                        if d_fp_id is not None and pd.notna(d_fp_id):
                            df_cur_fp = fetch_all("SELECT nome FROM formas_pagamento WHERE id=?", (int(d_fp_id),))
                            if not df_cur_fp.empty:
                                d_fp_nome = df_cur_fp.iloc[0]['nome']
                        
                        if not d_fp_nome:
                            d_fp_nome = fb.get('prazo_pagamento', '')
                            
                        idx_fp = list(fp_opts_edit.keys()).index(d_fp_nome) if d_fp_nome in fp_opts_edit else 0
                        efp_selecionada = col_eprazo.selectbox("Condição/Prazo Pagamento Padrão", list(fp_opts_edit.keys()), index=idx_fp, key="forn_efp_sel")
                        efp_id_val = fp_opts_edit.get(efp_selecionada, None)
                        echave_pix = col_epix.text_input("Código Pix", fb.get('chave_pix', '') if fb.get('chave_pix') else "")
                        
                        if st.form_submit_button("Salvar Fornecedor"):
                            if eplano_de_contas == "(Nenhum/Outro)":
                                eplano_de_contas = ""
                                
                            if enome and efantasia:
                                enome_limpo = enome.strip().upper()
                                chk_nome = fetch_all("SELECT id FROM fornecedores WHERE UPPER(TRIM(nome)) = ? AND id != ?", (enome_limpo, fid))
                                
                                chk_cnpj = pd.DataFrame()
                                ecnpj_val = edoc.strip() if edoc else ""
                                if ecnpj_val:
                                    chk_cnpj = fetch_all("SELECT id FROM fornecedores WHERE TRIM(cnpj_cpf) = ? AND id != ?", (ecnpj_val, fid))
                                
                                if not chk_nome.empty:
                                    st.error(f"⚠️ Já existe outro fornecedor cadastrado com a Razão Social/Nome '{enome.strip()}'. Se forem fornecedores diferentes, diferencie-os no nome.")
                                elif not chk_cnpj.empty:
                                    st.error(f"⚠️ Já existe outro fornecedor cadastrado com o CNPJ/CPF '{ecnpj_val}'.")
                                else:
                                    run_query("""
                                        UPDATE fornecedores 
                                        SET nome=?, nome_fantasia=?, cnpj_cpf=?, inscricao_estadual=?, telefone=?, email=?,
                                            endereco=?, bairro=?, cidade=?, uf=?, cep=?, status=?, plano_de_contas=?, prazo_pagamento=?, chave_pix=?, plano_conta_id=?, forma_pagamento_id=? 
                                        WHERE id=?
                                    """, (enome, efantasia, edoc, eie, etelefone, eemail, eendereco, ebairro, ecidade, euf, ecep, estatus, eplano_de_contas, efp_selecionada, echave_pix, eplano_id_val, efp_id_val, fid))
                                    st.success("Fornecedor cadastrado com sucesso!")
                                    import time; time.sleep(1); st.rerun()
                            else:
                                st.error("Atenção: Razão Social e Nome Fantasia são obrigatórios.")

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
    SELECT c.id, f.nome as "Repr", COALESCE(p.nome, 'TODOS') as "Produto", c.rede_clientes as 'Rede', 
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
    with st.form("form_contas_bancarias", clear_on_submit=True):
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
    if st.session_state.get('user_role') != 'ADMIN':
        st.warning("🔒 Acesso restrito. Somente Administradores podem gerenciar usuários do sistema.")
        st.stop()
    st.subheader("Governança: Acessos ao Sistema")
    from database import hash_password
    
    # Mapeamento de Perfis/Roles
    ROLE_MAP = {
        "Administrador Geral": "ADMIN",
        "Comercial / Rotas": "VENDAS",
        "Operador Máquina": "PRODUCAO",
        "Engenharia P&D": "PRODUCAO",
        "Tesouraria": "FINANCEIRO",
        "Suprimentos / Compras": "COMPRAS",
        "Logística / Expedição": "LOGISTICA"
    }
    ROLE_LABELS = {
        "ADMIN": "Administrador Geral",
        "VENDAS": "Comercial / Rotas",
        "PRODUCAO": "Operador Máquina",
        "FINANCEIRO": "Tesouraria",
        "COMPRAS": "Suprimentos / Compras",
        "LOGISTICA": "Logística / Expedição"
    }

    # Carrega funcionários ativos para vinculação
    df_func_disp = fetch_all("SELECT id, nome, cargo FROM funcionarios WHERE status='ATIVO' ORDER BY nome")
    func_options = ["(Sem Vínculo/Interno)"]
    func_map = {}
    if not df_func_disp.empty:
        for _, r in df_func_disp.iterrows():
            lbl = f"{r['nome']} ({r['cargo']}) - ID #{r['id']}"
            func_options.append(lbl)
            func_map[lbl] = int(r['id'])

    with st.form("form_usr", clear_on_submit=True):
        cu1, cu2, cu3, cu4, cu5 = st.columns(5)
        nome_usr = cu1.text_input("Nome de Exibição")
        mail_usr = cu2.text_input("Login/E-mail")
        pwd_usr = cu3.text_input("Senha", type="password")
        nivel_label = cu4.selectbox("Hierarquia / Perfil", list(ROLE_MAP.keys()))
        vinculo_func = cu5.selectbox("Vincular Colaborador", func_options)
        
        if st.form_submit_button("Registrar Credencial"):
            if not nome_usr or not mail_usr or not pwd_usr:
                st.error("Por favor, preencha todos os campos obrigatórios (Nome, Login/E-mail, Senha).")
            else:
                # Verifica duplicidade de e-mail
                chk_email = fetch_all("SELECT id FROM usuarios WHERE email=?", (mail_usr,))
                if not chk_email.empty:
                    st.error("Erro: Este e-mail/login já está cadastrado.")
                else:
                    role_code = ROLE_MAP[nivel_label]
                    hashed_pwd = hash_password(pwd_usr)
                    func_id = func_map.get(vinculo_func, None)
                    
                    # Se for vincular colaborador, verifica se ele já tem um usuário
                    if func_id:
                        chk_vinc = fetch_all("SELECT id FROM usuarios WHERE funcionario_id=?", (func_id,))
                        if not chk_vinc.empty:
                            st.error("Erro: Este colaborador já possui um usuário vinculado.")
                        else:
                            run_query("""
                                INSERT INTO usuarios (nome, email, senha, nivel_permissao, status, funcionario_id)
                                VALUES (?, ?, ?, ?, 'ATIVO', ?)
                            """, (nome_usr, mail_usr, hashed_pwd, role_code, func_id))
                            registrar_log_acesso(
                                st.session_state.get('user_id'), st.session_state.get('logged_user', ''),
                                st.session_state.get('logged_user', ''),
                                'CRIAR_USUARIO', f"Usuário criado: {mail_usr} | Perfil: {role_code} | Vinculado a func_id={func_id}"
                            )
                            st.success("Licença ativada com sucesso!")
                            import time; time.sleep(1); st.rerun()
                    else:
                        run_query("""
                            INSERT INTO usuarios (nome, email, senha, nivel_permissao, status, funcionario_id)
                            VALUES (?, ?, ?, ?, 'ATIVO', NULL)
                        """, (nome_usr, mail_usr, hashed_pwd, role_code))
                        registrar_log_acesso(
                            st.session_state.get('user_id'), st.session_state.get('logged_user', ''),
                            st.session_state.get('logged_user', ''),
                            'CRIAR_USUARIO', f"Usuário criado: {mail_usr} | Perfil: {role_code} | Sem vínculo"
                        )
                        st.success("Licença ativada com sucesso!")
                        import time; time.sleep(1); st.rerun()

    st.markdown("---")
    st.subheader("Gerenciamento de Acessos")
    
    # Carrega usuários cadastrados exibindo dados do funcionário vinculado
    df_usr = fetch_all("""
        SELECT u.id, u.nome as 'Usuário', u.email as 'Login', u.nivel_permissao as 'Hierarquia_Cod',
               u.status as 'Status', f.nome as 'Colaborador Vinculado'
        FROM usuarios u
        LEFT JOIN funcionarios f ON u.funcionario_id = f.id
    """)
    
    if not df_usr.empty:
        # Traduz a sigla de hierarquia para exibição amigável
        df_usr['Hierarquia'] = df_usr['Hierarquia_Cod'].map(lambda x: ROLE_LABELS.get(x, x))
        df_usr_display = df_usr[['id', 'Usuário', 'Login', 'Hierarquia', 'Colaborador Vinculado', 'Status']]
        st.dataframe(df_usr_display, hide_index=True, width="stretch")

        # Área de Edição/Inativação de Usuários
        with st.expander("✏️ Editar ou Inativar Usuário"):
            opts_usr = {f"ID {r['id']} | {r['Usuário']} ({r['Login']})": r['id'] for _, r in df_usr.iterrows()}
            u_sel = st.selectbox("Selecione o Usuário:", list(opts_usr.keys()))
            if u_sel:
                uid = opts_usr[u_sel]
                u_data = fetch_all("SELECT * FROM usuarios WHERE id=?", (uid,))
                if not u_data.empty:
                    ub = u_data.iloc[0]

                    # --- Verifica vínculo e histórico FORA do form (banners contextuais antes de qualquer ação) ---
                    func_id_atual = ub.get('funcionario_id')
                    df_hist = fetch_all("SELECT COUNT(*) as total FROM audit_log_acesso WHERE usuario_id = ?", (uid,))
                    tem_historico = not df_hist.empty and int(df_hist.iloc[0]['total']) > 0

                    # Banner 1: colaborador vinculado (imutável)
                    if func_id_atual:
                        df_func_nome = fetch_all("SELECT nome, cargo FROM funcionarios WHERE id=?", (func_id_atual,))
                        nome_func = f"{df_func_nome.iloc[0]['nome']} ({df_func_nome.iloc[0]['cargo']})" if not df_func_nome.empty else f"ID #{func_id_atual}"
                        st.info(
                            f"👤 **Colaborador vinculado:** {nome_func}\n\n"
                            "🔒 O vínculo com o colaborador **não pode ser alterado**. "
                            "Caso precise corrigir: inative este usuário e crie um novo com o vínculo correto."
                        )
                    else:
                        st.info("👤 **Colaborador vinculado:** Nenhum (usuário interno/genérico)")

                    # Banner 2: histórico de ações (define se exclusão está disponível)
                    if tem_historico:
                        st.warning(
                            "📋 **Este usuário possui histórico de ações no sistema.**\n\n"
                            "Para remover o acesso: use **Inativar** no campo Status abaixo. "
                            "O botão Excluir está desabilitado para preservar a rastreabilidade."
                        )
                    else:
                        st.success("✅ Sem histórico de ações. Este usuário pode ser **excluído permanentemente** se necessário.")

                    with st.form("edit_usr"):
                        eu1, eu2, eu3, eu4, eu5 = st.columns(5)
                        e_nome = eu1.text_input("Nome de Exibição", ub['nome'])
                        e_mail = eu2.text_input("Login/E-mail", ub['email'])
                        e_pwd = eu3.text_input("Nova Senha (deixe em branco para manter)", type="password")

                        cur_role_label = ROLE_LABELS.get(ub['nivel_permissao'], "Administrador Geral")
                        role_list = list(ROLE_MAP.keys())
                        e_role_label = eu4.selectbox("Hierarquia", role_list, index=role_list.index(cur_role_label) if cur_role_label in role_list else 0)

                        stts_opts = ["ATIVO", "INATIVO"]
                        cur_status = ub['status'] if ub['status'] in stts_opts else "ATIVO"
                        e_status = eu5.selectbox("Status", stts_opts, index=stts_opts.index(cur_status))

                        col_salvar, col_excluir = st.columns([3, 1])
                        salvar = col_salvar.form_submit_button("Salvar Alterações", use_container_width=True)
                        excluir = col_excluir.form_submit_button(
                            "🗑️ Excluir", use_container_width=True,
                            type="secondary", disabled=tem_historico
                        )

                        if salvar:
                            if not e_nome or not e_mail:
                                st.error("Nome e E-mail de login são obrigatórios.")
                            else:
                                role_code = ROLE_MAP[e_role_label]
                                if e_pwd.strip():
                                    hashed_pwd = hash_password(e_pwd.strip())
                                    run_query("""
                                        UPDATE usuarios
                                        SET nome=?, email=?, senha=?, nivel_permissao=?, status=?
                                        WHERE id=?
                                    """, (e_nome, e_mail, hashed_pwd, role_code, e_status, uid))
                                else:
                                    run_query("""
                                        UPDATE usuarios
                                        SET nome=?, email=?, nivel_permissao=?, status=?
                                        WHERE id=?
                                    """, (e_nome, e_mail, role_code, e_status, uid))
                                st.success("Usuário atualizado com sucesso!")
                                registrar_log_acesso(
                                    st.session_state.get('user_id'), st.session_state.get('logged_user', ''),
                                    st.session_state.get('logged_user', ''),
                                    'EDITAR_USUARIO', f"Usuário editado: {e_mail} | Novo perfil: {role_code} | Status: {e_status}"
                                )
                                import time; time.sleep(1); st.rerun()

                        if excluir:
                            run_query("DELETE FROM usuarios WHERE id=?", (uid,))
                            registrar_log_acesso(
                                st.session_state.get('user_id'), st.session_state.get('logged_user', ''),
                                st.session_state.get('logged_user', ''),
                                'EXCLUIR_USUARIO', f"Usuário excluído: {ub['email']} | Nome: {ub['nome']}"
                            )
                            st.success(f"Usuário '{ub['nome']}' excluído com sucesso.")
                            import time; time.sleep(1); st.rerun()

# ======= RESET DE SENHA (apenas ADMIN) =======
st.markdown("---")
st.subheader("🔐 Reset de Senha de Usuário")
st.caption("Gera um código temporário de 6 dígitos (válido por 30 minutos) enviado ao Telegram do administrador. Repasse o código ao colaborador para que ele mesmo defina a nova senha.")

from database import gerar_token_reset, validar_token_reset, consumir_token_reset, enviar_mensagem_telegram

with st.expander("📨 Gerar Código de Reset para um Colaborador"):
    df_usr_reset = fetch_all("""
        SELECT u.id, u.nome, u.email FROM usuarios u WHERE u.status = 'ATIVO' ORDER BY u.nome
    """)
    if not df_usr_reset.empty:
        opts_reset = {f"{r['nome']} ({r['email']})": (int(r['id']), r['email'], r['nome']) for _, r in df_usr_reset.iterrows()}
        u_reset_sel = st.selectbox("Selecione o usuário:", list(opts_reset.keys()), key="sel_reset_usr")
        if st.button("📤 Gerar e Enviar Código via Telegram", key="btn_gerar_token"):
            uid_r, email_r, nome_r = opts_reset[u_reset_sel]
            token_r = gerar_token_reset(uid_r)
            msg = (
                f"🔐 <b>Reset de Senha — ERP Alho</b>\n"
                f"Colaborador: <b>{nome_r}</b>\n"
                f"Código temporário: <code>{token_r}</code>\n"
                f"\u26a0️ Válido por <b>30 minutos</b>. Após usar, o código é descartado.\n"
                f"Instrua o colaborador a acessar a tela de login e clicar em <i>Esqueci minha senha</i>."
            )
            ok, err = enviar_mensagem_telegram(msg)
            if ok:
                registrar_log_acesso(
                    st.session_state.get('user_id'), st.session_state.get('logged_user', ''),
                    st.session_state.get('logged_user', ''),
                    'RESET_SENHA_SOLICITADO', f"Token gerado para: {email_r}"
                )
                st.success(f"✅ Código enviado ao Telegram! Repasse-o a {nome_r}.")
            else:
                st.warning(f"⚠️ Telegram não configurado ou erro no envio: {err}")
                st.info(f"📝 Código gerado (anote e repasse manualmente): **{token_r}**")
    else:
        st.info("Nenhum usuário ativo encontrado.")

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




# ======= FORMAS DE PAGAMENTO =======
with tab_fp:
    st.subheader("💳 Cadastro de Formas de Pagamento")
    st.markdown("Gerencie as condições e prazos de pagamento disponíveis no ERP para vendas e faturamento.")
    
    col_fp_1, col_fp_2 = st.columns(2)
    
    with col_fp_1:
        with st.form("form_forma_pagto", clear_on_submit=True):
            st.markdown("##### ➕ Nova Forma de Pagamento")
            fp_nome = st.text_input("Nome da Forma (Ex: 30/45/60 dias)")
            fp_parcelas = st.text_input("Regra de Dias (Ex: 30,45,60)", help="Valores em dias separados por vírgula. Ex: À vista use 0. 30 dias use 30. 30 e 60 dias use 30,60")
            
            if st.form_submit_button("Salvar Forma de Pagamento"):
                if fp_nome and fp_parcelas:
                    import re
                    regra_limpa = fp_parcelas.strip().replace(" ", "")
                    if not re.match(r'^\d+(,\d+)*$', regra_limpa):
                        st.error("⚠️ A regra de dias deve conter apenas números separados por vírgulas (Ex: '0' ou '30' ou '30,60,90').")
                    else:
                        chk = fetch_all("SELECT id FROM formas_pagamento WHERE nome=?", (fp_nome.strip(),))
                        if chk.empty:
                            run_query("INSERT INTO formas_pagamento (nome, parcelas) VALUES (?, ?)", (fp_nome.strip(), regra_limpa))
                            st.success("Forma de pagamento cadastrada com sucesso!")
                            import time; time.sleep(1); st.rerun()
                        else:
                            st.error("⚠️ Já existe uma forma de pagamento com este nome.")
                else:
                    st.error("⚠️ Preencha todos os campos obrigatórios.")
                    
    with col_fp_2:
        st.markdown("##### Prazos Ativos no Sistema")
        df_fp = fetch_all("SELECT id, nome as 'Descrição', parcelas as 'Regra (Dias)' FROM formas_pagamento ORDER BY id ASC")
        if not df_fp.empty:
            st.dataframe(df_fp, hide_index=True, use_container_width=True)
            
            fp_ids = df_fp['id'].tolist()
            fp_descricoes = df_fp['Descrição'].tolist()
            dict_fp_del = dict(zip(fp_descricoes, fp_ids))
            
            st.markdown("---")
            st.markdown("##### 🗑️ Excluir Forma de Pagamento")
            fp_para_excluir = st.selectbox("Selecione para excluir:", ["-- SELECIONE --"] + fp_descricoes, key="sb_fp_delete")
            if fp_para_excluir != "-- SELECIONE --":
                fp_id_del = dict_fp_del[fp_para_excluir]
                if st.button("Confirmar Exclusão", type="primary", key="btn_fp_delete"):
                    chk_uso_cli = fetch_all("SELECT id FROM clientes WHERE forma_pagamento_id=?", (fp_id_del,))
                    chk_uso_ven = fetch_all("SELECT id FROM vendas WHERE forma_pagamento_id=?", (fp_id_del,))
                    
                    if not chk_uso_cli.empty or not chk_uso_ven.empty:
                        st.error("⚠️ Não é permitido excluir esta forma de pagamento pois ela já está vinculada a clientes ou vendas cadastrados.")
                    else:
                        run_query("DELETE FROM formas_pagamento WHERE id=?", (fp_id_del,))
                        st.success("Forma de pagamento excluída com sucesso!")
                        import time; time.sleep(1); st.rerun()
        else:
            st.info("Nenhuma forma de pagamento cadastrada.")

# ======= FICHAS TÉCNICAS (BOM) =======
with tab_ft:
    st.subheader("🧪 Fichas Técnicas de Produção")
    st.markdown(
        "A **Ficha Técnica** é a receita de cada produto final: quais insumos (MP + embalagens) "
        "são consumidos por unidade produzida. O módulo de Produção carrega isso automaticamente."
    )

    # Carrega listas de produtos
    df_pf_ft  = fetch_all("SELECT id, nome, unidade_medida FROM produtos WHERE is_materia_prima=FALSE ORDER BY nome")
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
