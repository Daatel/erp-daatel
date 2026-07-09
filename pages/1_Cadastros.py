import streamlit as st
import pandas as pd
from database import run_query, fetch_all, registrar_log_acesso
from estilo import carregar_estilo
from datetime import date

st.set_page_config(page_title="Cadastros Base", page_icon="📝", layout="wide")
carregar_estilo()

st.markdown("""
<style>
/* Remove padding do topo da página do Streamlit para subir tudo de forma limpa e sem cortar o texto */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
</style>
<h1 style='font-size: 2.2rem; font-weight: 700; margin-top: -15px; margin-bottom: 20px; color: #1e293b;'>
Cadastros Inteligentes
</h1>
""", unsafe_allow_html=True)

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

    st.markdown("---")
    st.markdown("### 📦 Parâmetros de Estoque & CMV")
    
    is_pg = "DATABASE_URL" in st.secrets
    from database import db_connection
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracoes_sistema WHERE chave = %s" if is_pg else "SELECT valor FROM configuracoes_sistema WHERE chave = ?", ("modo_estoque",))
        row = cursor.fetchone()
        modo_atual = row[0] if row else "LOTE"
        
    novo_modo = st.selectbox(
        "Modo de controle de estoque / CMV",
        options=["SIMPLIFICADO", "LOTE"],
        index=0 if modo_atual == "SIMPLIFICADO" else 1,
        help="SIMPLIFICADO: usa custo cadastrado no produto, sem controle de lote (Recomendado para Fase 1). LOTE: controle FIFO por lote físico (Fase 2+)."
    )
    
    if novo_modo == "LOTE":
        st.warning("⚠️ **Atenção:** A ativação do modo **LOTE** (Fase 2) exige o controle rigoroso de rastreabilidade física de OPs e compras. É **obrigatoriamente necessário realizar um inventário físico de abertura** para registrar os saldos e validades reais no estoque antes de iniciar a operação nesse modo.")
    else:
        st.info("💡 **Modo Simplificado Ativo:** O CMV será apurado com base no Custo Médio (ou Custo Padrão/Unitário) cadastrado no Produto, simplificando a operação de faturamento e PDV na Fase 1.")
        
    if st.button("Salvar Configuração de Estoque", type="primary"):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE configuracoes_sistema SET valor = %s WHERE chave = 'modo_estoque'" if is_pg else
                "UPDATE configuracoes_sistema SET valor = ? WHERE chave = 'modo_estoque'",
                (novo_modo,)
            )
            conn.commit()
        st.success(f"Configuração atualizada! Modo de estoque definido como: **{novo_modo}**")
        st.cache_data.clear()
        import time; time.sleep(1.5); st.rerun()

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
        
        col_c1, col_c2, _ = st.columns(3)
        custo_medio = col_c1.number_input("Custo Médio Simplificado (R$)", min_value=0.0, step=0.01, help="Utilizado no cálculo do CMV no modo SIMPLIFICADO.")
        
        unidade_medida_sintetico = unidade_compra if unidade_compra else "un"
        tipo_embalagem = unidade_compra 
        
        if st.form_submit_button("Cadastrar Produto"):
            if nome_produto:
                run_query(
                    """INSERT INTO produtos 
                       (nome, unidade_medida, preco_venda_base, is_materia_prima, 
                        marca, peso_volume, referencia, ean, unidades_por_fardo, 
                        tipo_embalagem, embalagem_master, cod_emb_master, custo_medio) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    (nome_produto, unidade_medida_sintetico, preco_venda_base, True if is_materia_prima else False,
                     marca, peso_volume, referencia, ean, unidades_por_fardo, tipo_embalagem, embalagem_master, cod_emb_master, custo_medio)
                )
                st.success(f"Produto '{nome_produto}' cadastrado com sucesso!")
            else:
                st.error("Por favor, preencha o nome do produto.")
                
    st.markdown("---")
    st.subheader("Produtos Cadastrados")
    df_produtos = fetch_all("SELECT id, nome, marca, referencia, ean, peso_volume as 'Peso/Vol', unidade_medida as 'Unidade', embalagem_master as 'Emb. Master', unidades_por_fardo as 'Qtd. Master', custo_unidade as 'Custo Und', custo_medio as 'Custo Médio', custo_fardo as 'Custo Master', preco_venda_base as 'Preço Venda', is_materia_prima FROM produtos")
    if not df_produtos.empty:
        df_produtos['is_materia_prima'] = df_produtos['is_materia_prima'].map({1: 'Sim', 0: 'Não', True: 'Sim', False: 'Não'})
        
        export_btn(df_produtos, 'produtos.csv')
        
        def format_brl(val):
            if pd.isna(val): return ""
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        df_produtos_view = df_produtos.copy()
        df_produtos_view['Custo Und'] = df_produtos_view['Custo Und'].apply(format_brl)
        df_produtos_view['Custo Médio'] = df_produtos_view['Custo Médio'].apply(format_brl)
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
                        
                        ep_c1, _ = st.columns(2)
                        ecusto_medio = ep_c1.number_input("Custo Médio Simplificado (R$)", value=float(pb.get('custo_medio') or 0.0), min_value=0.0, step=0.01)
                        
                        if st.form_submit_button("Atualizar Produto"):
                            run_query("UPDATE produtos SET nome=?, marca=?, preco_venda_base=?, unidade_medida=?, unidades_por_fardo=?, peso_volume=?, referencia=?, is_materia_prima=?, estoque_minimo=?, embalagem_master=?, cod_emb_master=?, custo_medio=? WHERE id=?", 
                                      (enome, emarca, epreco, eunidade, efator, epeso, eref, True if emateria else False, eestoque_min, eembalagem_master, ecod_master, ecusto_medio, pid))
    # ======= CLIENTES =======
with tab2:
    # 1. Funções Auxiliares
    def buscar_cnpj_api(cnpj_val):
        import requests
        cnpj_clean = "".join(filter(str.isdigit, cnpj_val))
        if len(cnpj_clean) != 14:
            return {"error": "CNPJ inválido. Deve conter 14 dígitos."}
        try:
            r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}", timeout=8)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return {"error": "CNPJ não encontrado."}
            else:
                return {"error": f"Erro na consulta (status {r.status_code})."}
        except Exception as e:
            return {"error": f"Erro de conexão com a API: {str(e)}"}

    def gerar_pdf_clientes(df_pdf):
        from fpdf import FPDF
        import unicodedata
        
        class PDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 14)
                self.cell(0, 10, "EMPORIO DO ALHO - RELATORIO DE CLIENTES", new_x="LMARGIN", new_y="NEXT", align="C")
                self.ln(5)
                
        pdf = PDF()
        pdf.add_page()
        
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.cell(10, 7, "ID", border=1, align="C")
        pdf.cell(50, 7, "Razao Social", border=1)
        pdf.cell(32, 7, "CNPJ/CPF", border=1)
        pdf.cell(30, 7, "Cidade/UF", border=1)
        pdf.cell(28, 7, "Representante", border=1)
        pdf.cell(40, 7, "Forma Pagto", border=1, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Helvetica", "", 7.5)
        for _, r in df_pdf.iterrows():
            cid_uf = f"{r.get('Cidade') or ''}/{r.get('UF') or ''}"
            
            # Limpeza de acentos para compatibilidade com Helvetica
            razao = "".join(ch for ch in unicodedata.normalize('NFKD', str(r.get('Razão Social') or '')) if unicodedata.category(ch) != 'Mn')
            cnpj = str(r.get('CNPJ/CPF') or '')
            rep = "".join(ch for ch in unicodedata.normalize('NFKD', str(r.get('Representante') or '')) if unicodedata.category(ch) != 'Mn')
            fp = "".join(ch for ch in unicodedata.normalize('NFKD', str(r.get('Forma Pagto') or '')) if unicodedata.category(ch) != 'Mn')
            cid_uf_clean = "".join(ch for ch in unicodedata.normalize('NFKD', cid_uf) if unicodedata.category(ch) != 'Mn')
            
            pdf.cell(10, 6, str(r.get('id', '')), border=1, align="C")
            pdf.cell(50, 6, razao[:28], border=1)
            pdf.cell(32, 6, cnpj, border=1)
            pdf.cell(30, 6, cid_uf_clean[:18], border=1)
            pdf.cell(28, 6, rep[:15], border=1)
            pdf.cell(40, 6, fp[:22], border=1, new_x="LMARGIN", new_y="NEXT")
            
        return bytes(pdf.output())

    def carregar_dados_edicao(client_id):
        df_cb = fetch_all("SELECT * FROM clientes WHERE id = ?", (client_id,))
        if not df_cb.empty:
            cb = df_cb.iloc[0]
            st.session_state["cli_cnpj"] = cb.get("cnpj_cpf") or ""
            st.session_state["cli_nome"] = cb.get("nome") or ""
            st.session_state["cli_nome_fantasia"] = cb.get("nome_fantasia") or ""
            try:
                st.session_state["cli_data_nascimento"] = pd.to_datetime(cb["data_nascimento"]).date() if pd.notnull(cb["data_nascimento"]) else None
            except:
                st.session_state["cli_data_nascimento"] = None
            st.session_state["cli_inscricao_estadual"] = cb.get("inscricao_estadual") or ""
            st.session_state["cli_telefone"] = cb.get("telefone") or ""
            st.session_state["cli_email"] = cb.get("email") or ""
            st.session_state["cli_endereco"] = cb.get("endereco") or ""
            st.session_state["cli_bairro"] = cb.get("bairro") or ""
            st.session_state["cli_cidade"] = cb.get("cidade") or ""
            st.session_state["cli_uf"] = cb.get("uf") or ""
            st.session_state["cli_cep"] = cb.get("cep") or ""
            st.session_state["cli_rede"] = cb.get("rede_clientes") or "(Nenhuma)"
            st.session_state["cli_grupo"] = cb.get("grupo_lojas") or "(Nenhum)"
            st.session_state["cli_chave_pix"] = cb.get("chave_pix") or ""
            st.session_state["cli_forma_pagamento_id"] = cb.get("forma_pagamento_id")
            st.session_state["cli_representante_id"] = cb.get("representante_id")
            st.session_state["cli_observacoes"] = cb.get("observacoes") or ""
            st.session_state["cli_taxa_descarga"] = float(cb.get("taxa_descarga") or 0.0)
            st.session_state["cli_regras_descarga"] = cb.get("regras_descarga") or ""
            st.session_state["cli_status"] = cb.get("status") or "ATIVO"
            st.session_state["cli_limite_credito"] = float(cb.get("limite_credito") or 0.0)
            st.session_state["cli_limite_ilimitado"] = bool(cb.get("limite_ilimitado") if cb.get("limite_ilimitado") is not None else True)
            
            import json
            contatos = []
            c_json = cb.get("contatos_json")
            if c_json:
                try:
                    contatos = json.loads(c_json)
                except:
                    pass
            for i in range(3):
                cont = contatos[i] if i < len(contatos) else {}
                st.session_state[f"cli_contato_{i}_nome"] = cont.get("nome", "")
                st.session_state[f"cli_contato_{i}_depto"] = cont.get("depto", "")
                st.session_state[f"cli_contato_{i}_tel1"] = cont.get("tel1", "")
                st.session_state[f"cli_contato_{i}_wapp1"] = bool(cont.get("wapp1", False))
                st.session_state[f"cli_contato_{i}_tel2"] = cont.get("tel2", "")
                st.session_state[f"cli_contato_{i}_wapp2"] = bool(cont.get("wapp2", False))
                st.session_state[f"cli_contato_{i}_email"] = cont.get("email", "")

    def limpar_dados_formulario():
        keys_to_delete = [k for k in st.session_state.keys() if k.startswith("cli_") and k not in ("cli_filtro_busca", "cli_filtro_inativos", "cli_filtro_usar_periodo")]
        for k in keys_to_delete:
            del st.session_state[k]

    # 2. Query Principal de Clientes
    df_clientes_raw = fetch_all("""
        SELECT c.id, c.nome_fantasia as 'Nome Fantasia', c.grupo_lojas as 'Grupo', c.rede_clientes as 'Rede', 
               c.cidade as 'Cidade', c.uf as 'UF', f.nome as 'Representante', c.nome as 'Razão Social', 
               c.cnpj_cpf as 'CNPJ/CPF', COALESCE(fp.nome, c.prazo_pagamento) as 'Forma Pagto',
               c.status as 'Status', c.telefone as 'Telefone', c.limite_credito, c.limite_ilimitado, c.contatos_json,
               c.taxa_descarga, c.regras_descarga, c.chave_pix
        FROM clientes c
        LEFT JOIN funcionarios f ON c.representante_id = f.id
        LEFT JOIN formas_pagamento fp ON c.forma_pagamento_id = fp.id
        ORDER BY c.id DESC
    """)

    # 3. Controles e Filtros Superiores (Horizontais)
    col_f1, col_f2, col_f3 = st.columns([2.5, 1.2, 1.2])
    with col_f1:
        filtro_busca = st.text_input("🔍 Buscar por Razão Social, Nome Fantasia ou CNPJ", value="", key="cli_filtro_busca")
    with col_f2:
        filtro_inativos = st.checkbox("Exibir Clientes Inativos", value=False, key="cli_filtro_inativos")
    with col_f3:
        filtro_usar_periodo = st.checkbox("Filtrar por Período de Nasc./Fund.", value=False, key="cli_filtro_usar_periodo")

    # Filtro de Período Opcional
    dt_ini, dt_fim = None, None
    if filtro_usar_periodo:
        col_d1, col_d2 = st.columns(2)
        dt_ini = col_d1.date_input("De", value=date.today() - timedelta(days=365*10))
        dt_fim = col_d2.date_input("Até", value=date.today())

    # 4. Aplicação dos Filtros em Memória (Pandas)
    df_filtered = df_clientes_raw.copy()
    if not df_filtered.empty:
        # Filtro de Status (Inativos)
        if not filtro_inativos:
            df_filtered = df_filtered[df_filtered['Status'] == 'ATIVO']
            
        # Filtro de Busca Textual
        if filtro_busca:
            fb_upper = filtro_busca.upper()
            df_filtered = df_filtered[
                df_filtered['Razão Social'].str.upper().str.contains(fb_upper, na=False) |
                df_filtered['Nome Fantasia'].str.upper().str.contains(fb_upper, na=False) |
                df_filtered['CNPJ/CPF'].str.contains(filtro_busca, na=False)
            ]
            
        # Filtro de Período
        if filtro_usar_periodo and dt_ini and dt_fim:
            df_ids_periodo = fetch_all("SELECT id FROM clientes WHERE data_nascimento BETWEEN ? AND ?", 
                                       (dt_ini.strftime("%Y-%m-%d"), dt_fim.strftime("%Y-%m-%d")))
            if not df_ids_periodo.empty:
                df_filtered = df_filtered[df_filtered['id'].isin(df_ids_periodo['id'])]
            else:
                df_filtered = pd.DataFrame(columns=df_filtered.columns)

    # 5. Barra de Ações (Toolbar Horizontal)
    col_act1, col_act2, col_act3, col_act4, col_act5, col_act6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 2.5])
    
    show_incluir = st.session_state.get("show_incluir_cliente", False)
    edit_id = st.session_state.get("edit_cliente_id", None)
    show_importar = st.session_state.get("show_importar_csv", False)
    
    # Determinar seleção no Grid
    selected_ids = []
    
    # Renderizar a planilha/grid interativo
    page_size = 10
    total_rows = len(df_filtered)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    
    # Paginação
    with col_act6:
        col_pag1, col_pag2 = st.columns([2, 1])
        page = col_pag2.number_input("Pág.", min_value=1, max_value=total_pages, value=1, step=1)
        col_pag1.write(f"Total: **{total_rows}** clientes encontrados.")
        
    df_page = df_filtered.iloc[(page - 1) * page_size : page * page_size].copy() if not df_filtered.empty else pd.DataFrame(columns=df_filtered.columns)
    
    # Prepara dataframe de exibição com checkbox
    df_display = df_page.copy()
    if not df_display.empty:
        df_display.insert(0, "Seleção", False)
        # Selecionar apenas colunas especificadas pelo usuário
        cols_display = ["Seleção", "id", "Nome Fantasia", "Grupo", "Rede", "Cidade", "UF", "Representante", "Razão Social", "CNPJ/CPF", "Forma Pagto"]
        df_display_clean = df_display[cols_display]
        
        # Render com st.data_editor
        edited_df = st.data_editor(
            df_display_clean,
            key=f"clientes_editor_{page}",
            use_container_width=True,
            hide_index=True,
            disabled=[c for c in cols_display if c != "Seleção"]
        )
        # Extrair selecionados
        selected_rows = edited_df[edited_df["Seleção"] == True]
        selected_ids = selected_rows["id"].tolist()
    else:
        st.info("Nenhum cliente cadastrado ou correspondente aos filtros.")
        selected_rows = pd.DataFrame()
        
    can_edit = len(selected_ids) == 1

    # Configuração dos Botões da Toolbar
    with col_act1:
        if st.button("➕ Incluir Novo", use_container_width=True, type="primary" if show_incluir else "secondary"):
            limpar_dados_formulario()
            st.session_state["show_incluir_cliente"] = not show_incluir
            st.session_state["edit_cliente_id"] = None
            st.session_state["show_importar_csv"] = False
            st.rerun()
            
    with col_act2:
        if st.button("✏️ Editar", disabled=not can_edit, use_container_width=True, type="primary" if edit_id else "secondary"):
            st.session_state["show_incluir_cliente"] = False
            st.session_state["show_importar_csv"] = False
            carregar_dados_edicao(selected_ids[0])
            st.session_state["edit_cliente_id"] = selected_ids[0]
            st.rerun()
            
    with col_act3:
        # Impressão em PDF
        pdf_data = b""
        if not df_filtered.empty:
            df_print = df_filtered[df_filtered["id"].isin(selected_ids)] if selected_ids else df_page
            pdf_data = gerar_pdf_clientes(df_print)
        st.download_button(
            label="🖨️ Imprimir",
            data=pdf_data,
            file_name="relatorio_clientes.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=df_filtered.empty
        )
        
    with col_act4:
        # Exportar CSV
        csv_data = b""
        if not df_filtered.empty:
            df_export = df_filtered[df_filtered["id"].isin(selected_ids)] if selected_ids else df_filtered
            csv_data = df_export.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📤 Exportar",
            data=csv_data,
            file_name="clientes_export.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=df_filtered.empty
        )
        
    with col_act5:
        if st.button("📥 Importar", use_container_width=True, type="primary" if show_importar else "secondary"):
            st.session_state["show_importar_csv"] = not show_importar
            st.session_state["show_incluir_cliente"] = False
            st.session_state["edit_cliente_id"] = None
            st.rerun()

    # --- SEÇÃO: IMPORTAÇÃO CSV (EXIBIDA CONDICIONALMENTE) ---
    if show_importar:
        st.markdown("---")
        with st.container():
            st.markdown("#### 📥 Importação em Massa de Clientes (Planilha CSV)")
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
                        def clean_val(x):
                            if pd.isna(x): return ""
                            v = str(x).strip()
                            return "" if v.lower() == "nan" else v
                            
                        for col in df_import.columns:
                            df_import[col] = df_import[col].apply(clean_val)
                            
                        st.success("📂 Arquivo de importação carregado!")
                        st.markdown("**Prévia dos Dados (Primeiras 10 linhas):**")
                        st.dataframe(df_import.head(10), use_container_width=True)
                        
                        df_reps_db = fetch_all("SELECT id, nome FROM funcionarios")
                        existing_reps = set(df_reps_db['nome'].tolist()) if not df_reps_db.empty else set()
                        rep_id_map = dict(zip(df_reps_db['nome'], df_reps_db['id'])) if not df_reps_db.empty else {}
                        
                        df_redes_db = fetch_all("SELECT nome FROM redes_clientes")
                        existing_redes = set(df_redes_db['nome'].tolist()) if not df_redes_db.empty else set()
                        
                        df_grupos_db = fetch_all("SELECT nome FROM grupos_clientes")
                        existing_grupos = set(df_grupos_db['nome'].tolist()) if not df_grupos_db.empty else set()
                        
                        df_existing_cnpj = fetch_all("SELECT cnpj_cpf FROM clientes")
                        existing_cnpjs = set(df_existing_cnpj['cnpj_cpf'].tolist()) if not df_existing_cnpj.empty else set()
                        
                        missing_reps = set()
                        missing_redes = set()
                        missing_grupos = set()
                        duplicate_cnpjs = []
                        cnpjs_na_planilha = {}
                        
                        for idx, row in df_import.iterrows():
                            razao = row.get('Razão Social', '')
                            if not razao:
                                continue
                            cnpj = row.get('CNPJ/CPF', '')
                            rep = row.get('Representante', '')
                            rede = row.get('Rede de Clientes', '')
                            grupo = row.get('Grupo de Lojas', '')
                            
                            if cnpj:
                                if cnpj in existing_cnpjs:
                                    duplicate_cnpjs.append(f"{razao} (CNPJ: {cnpj} - já cadastrado)")
                                elif cnpj in cnpjs_na_planilha:
                                    duplicate_cnpjs.append(f"{razao} (CNPJ: {cnpj} - duplicado na planilha)")
                                else:
                                    cnpjs_na_planilha[cnpj] = 1
                                    
                            if rep and rep not in existing_reps:
                                missing_reps.add(rep)
                            if rede and rede not in existing_redes:
                                missing_redes.add(rede)
                            if grupo and grupo not in existing_grupos:
                                missing_grupos.add(grupo)
                                
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
                        else:
                            st.success("🎉 Planilha validada com sucesso! Todos os relacionamentos estão em conformidade com os cadastros prévios do ERP.")
                            limpar_banco = st.checkbox("Excluir todos os clientes existentes atualmente no sistema antes de importar", value=False, key="import_limpar_banco")
                            
                            if st.button("Confirmar Importação de Clientes", use_container_width=True, type="primary"):
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
                                        
                                        fp_id_val = None
                                        if prazo_pag:
                                            df_match = fetch_all("SELECT id FROM formas_pagamento WHERE UPPER(TRIM(nome)) = ?", (prazo_pag.strip().upper(),))
                                            if not df_match.empty:
                                                fp_id_val = int(df_match.iloc[0]['id'])
                                                
                                        query_insert = """INSERT INTO clientes 
                                                   (nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual, 
                                                    bairro, cep, cidade, uf, email, observacoes, status, rede_clientes, 
                                                    grupo_lojas, prazo_pagamento, representante_id, data_nascimento, prazo_pagamento_dias, taxa_descarga, regras_descarga, chave_pix, forma_pagamento_id, limite_credito, limite_ilimitado) 
                                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, 1)"""
                                        
                                        run_query(query_insert, (
                                            razao, telefone, endereco, nome_fantasia, cnpj, insc_estadual,
                                            bairro, cep, cidade, uf, email, observacoes, status_val, rede_val,
                                            grupo_val, prazo_pag, rep_id, None, 30, 0.0, "", chave_pix_val, fp_id_val
                                        ))
                                        imported_count += 1
                                        
                                    st.success(f"✅ Importação finalizada! {imported_count} novos clientes importados. {ignored_count} registros ignorados.")
                                    import time; time.sleep(1.5); st.rerun()
                                except Exception as ex:
                                    st.error(f"Erro ao inserir dados no banco: {ex}")

    # --- SEÇÃO: FORMULÁRIO DE INCLUSÃO OU EDIÇÃO ---
    if show_incluir or edit_id is not None:
        st.markdown("---")
        label_form = "✏️ Editar Informações do Cliente" if edit_id else "➕ Incluir Novo Cliente"
        st.markdown(f"### {label_form}")
        
        # 1. Campo de Busca de CNPJ
        col_c_cnpj, col_c_btn = st.columns([3, 1])
        cnpj_val = col_c_cnpj.text_input("CNPJ / CPF", key="cli_cnpj")
        
        if col_c_btn.button("🔍 Buscar CNPJ na Internet", use_container_width=True):
            if cnpj_val:
                with st.spinner("Consultando na Receita Federal (BrasilAPI)..."):
                    res = buscar_cnpj_api(cnpj_val)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.session_state["cli_nome"] = res.get("razao_social", "")
                        st.session_state["cli_nome_fantasia"] = res.get("nome_fantasia", "")
                        st.session_state["cli_cep"] = res.get("cep", "")
                        
                        logradouro = res.get("logradouro", "")
                        numero = res.get("numero", "")
                        complemento = res.get("complemento", "")
                        end_str = f"{logradouro}, {numero}"
                        if complemento:
                            end_str += f" - {complemento}"
                        st.session_state["cli_endereco"] = end_str
                        
                        st.session_state["cli_bairro"] = res.get("bairro", "")
                        st.session_state["cli_cidade"] = res.get("cidade", "")
                        st.session_state["cli_uf"] = res.get("uf", "")
                        st.success("Dados cadastrais pré-preenchidos! Revise e edite os campos abaixo se necessário.")
                        import time; time.sleep(1)
                        st.rerun()
            else:
                st.warning("Preencha o campo CNPJ primeiro.")

        # 2. Dados Gerais do Formulário
        c1, c2, c3 = st.columns([2, 1, 1])
        nome_val = c1.text_input("Razão Social *", key="cli_nome")
        nome_fantasia_val = c2.text_input("Nome Fantasia", key="cli_nome_fantasia")
        nascimento_val = c3.date_input("Data de Nasc/Fundação", key="cli_data_nascimento", value=None, format="DD/MM/YYYY")
        
        c4, c5, c6 = st.columns(3)
        inscricao_estadual_val = c4.text_input("Inscrição Estadual", key="cli_inscricao_estadual")
        telefone_val = c5.text_input("Telefone Geral", key="cli_telefone")
        email_val = c6.text_input("E-mail Geral", key="cli_email")
        
        c7, c8, c9, c10 = st.columns([2, 1, 1, 1])
        endereco_val = c7.text_input("Endereço", key="cli_endereco")
        bairro_val = c8.text_input("Bairro", key="cli_bairro")
        cidade_val = c9.text_input("Cidade", key="cli_cidade")
        uf_val = c10.text_input("UF", key="cli_uf")
        
        c11, c12, c13 = st.columns(3)
        cep_val = c11.text_input("CEP", key="cli_cep")
        status_val = c12.selectbox("Status do Cliente", ["ATIVO", "INATIVO"], key="cli_status")
        chave_pix_val = c13.text_input("Chave Pix", key="cli_chave_pix")

        # 3. Rede e Grupo Relacionados (Dinamismo Interno)
        df_redes_bd = fetch_all("SELECT id, nome FROM redes_clientes ORDER BY nome")
        redes_opts = ["(Nenhuma)"] + df_redes_bd['nome'].tolist() if not df_redes_bd.empty else ["(Nenhuma)"]
        
        # Obter valor de rede do session_state
        rede_atual = st.session_state.get("cli_rede", "(Nenhuma)")
        if rede_atual not in redes_opts:
            redes_opts.append(rede_atual)
        idx_rede = redes_opts.index(rede_atual)
        
        st.markdown("##### Configuração de Rede do Cliente")
        col_r1, col_r2 = st.columns(2)
        rede_selecionada = col_r1.selectbox("Rede Vinculada", redes_opts, index=idx_rede, key="cli_rede")
        
        # Filtrar grupos de acordo com a rede selecionada
        df_grupos_bd = fetch_all("SELECT g.id, g.nome, r.nome as rede_nome FROM grupos_clientes g JOIN redes_clientes r ON g.rede_id = r.id")
        grupos_opts = ["(Nenhum)"]
        if rede_selecionada != "(Nenhuma)" and not df_grupos_bd.empty:
            grupos_opts += df_grupos_bd[df_grupos_bd['rede_nome'] == rede_selecionada]['nome'].tolist()
            
        grupo_atual = st.session_state.get("cli_grupo", "(Nenhum)")
        if grupo_atual not in grupos_opts:
            grupos_opts.append(grupo_atual)
        idx_grupo = grupos_opts.index(grupo_atual)
        grupo_selecionado = col_r2.selectbox("Grupo de Lojas (Sub-rede)", grupos_opts, index=idx_grupo, key="cli_grupo")

        # 4. Crédito e Forma de Pagamento
        st.markdown("##### 💳 Limite de Crédito e Forma de Pagamento")
        col_cr1, col_cr2, col_cr3 = st.columns(3)
        with col_cr1:
            st.checkbox("Limite Ilimitado", value=True, disabled=True, key="cli_limite_ilimitado", 
                        help="Neste primeiro momento, o limite é ilimitado até o desenvolvimento da API de análise de crédito.")
        with col_cr2:
            st.number_input("Limite de Crédito (R$)", value=0.0, disabled=True, key="cli_limite_credito")
        with col_cr3:
            # Buscar formas de pagamento do banco
            df_fp_list = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
            fp_opts = {}
            if not df_fp_list.empty:
                for _, r in df_fp_list.iterrows():
                    fp_opts[r['nome']] = (r['id'], r['parcelas'])
            
            fp_keys = ["-- SELECIONE --"] + list(fp_opts.keys())
            curr_fp_id = st.session_state.get("cli_forma_pagamento_id")
            curr_index = 0
            if curr_fp_id:
                for idx, k in enumerate(fp_keys):
                    if k != "-- SELECIONE --" and fp_opts[k][0] == curr_fp_id:
                        curr_index = idx
                        break
            fp_selecionada = st.selectbox("Forma de Pagamento Padrão *", fp_keys, index=curr_index)

        # 5. Representante Responsável e Observações
        col_rp1, col_rp2 = st.columns([1, 2])
        with col_rp1:
            df_reps = fetch_all("SELECT id, nome FROM funcionarios WHERE cargo LIKE '%Representante%' OR cargo LIKE '%Vendedor%'")
            rep_dict = dict(zip(df_reps['nome'], df_reps['id'])) if not df_reps.empty else {}
            rep_keys = ["-- SELECIONE --"] + df_reps['nome'].tolist() if not df_reps.empty else ["-- SELECIONE --"]
            
            curr_rep_id = st.session_state.get("cli_representante_id")
            curr_rep_index = 0
            if curr_rep_id:
                for idx, k in enumerate(rep_keys):
                    if k != "-- SELECIONE --" and rep_dict.get(k) == curr_rep_id:
                        curr_rep_index = idx
                        break
            rep_selecionado = st.selectbox("Representante Responsável *", rep_keys, index=curr_rep_index)
            
        with col_rp2:
            observacoes_val = st.text_input("Observações Gerais do Cliente", key="cli_observacoes")

        # 6. Logística e Descarga
        st.markdown("##### 🚚 Logística e Descarga")
        col_l1, col_l2 = st.columns([1, 3])
        taxa_descarga_val = col_l1.number_input("Taxa de Descarga (R$)", min_value=0.0, step=10.0, key="cli_taxa_descarga",
                                                help="Valor cobrado para descarregar mercadoria no cliente.")
        regras_descarga_val = col_l2.text_input("Regras e Horários de Descarga (Ex: Apenas agendado, Paletizado)", key="cli_regras_descarga")

        # 7. Contatos Destacados (Mínimo 3)
        st.markdown("##### 👥 Contatos de Atendimento (Mínimo 3)")
        col_ct1, col_ct2, col_ct3 = st.columns(3)
        
        for i, col_c in enumerate([col_ct1, col_ct2, col_ct3]):
            with col_c:
                st.markdown(f"**Contato {i+1}**")
                st.text_input("Nome", key=f"cli_contato_{i}_nome")
                st.text_input("Departamento / Setor", key=f"cli_contato_{i}_depto")
                
                col_t1_w1, col_t1_w2 = st.columns([3, 1])
                col_t1_w1.text_input("Telefone 1", key=f"cli_contato_{i}_tel1")
                col_t1_w2.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                col_t1_w2.checkbox("Wapp?", key=f"cli_contato_{i}_wapp1")
                
                col_t2_w1, col_t2_w2 = st.columns([3, 1])
                col_t2_w1.text_input("Telefone 2", key=f"cli_contato_{i}_tel2")
                col_t2_w2.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                col_t2_w2.checkbox("Wapp?", key=f"cli_contato_{i}_wapp2")
                
                st.text_input("E-mail", key=f"cli_contato_{i}_email")

        # 8. Ações do Formulário (Salvar e Cancelar)
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn_salvar, col_btn_cancelar = st.columns(2)
        
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            limpar_dados_formulario()
            st.session_state["show_incluir_cliente"] = False
            st.session_state["edit_cliente_id"] = None
            st.rerun()
            
        if col_btn_salvar.button("Salvar Cadastro", use_container_width=True, type="primary"):
            if not nome_val:
                st.error("Por favor, preencha o campo Razão Social.")
            elif fp_selecionada == "-- SELECIONE --":
                st.error("Por favor, selecione a Forma de Pagamento Padrão.")
            elif rep_selecionado == "-- SELECIONE --":
                st.error("Por favor, selecione o Representante Responsável.")
            else:
                # Validar duplicados
                if edit_id:
                    chk_nome = fetch_all("SELECT id FROM clientes WHERE UPPER(TRIM(nome)) = ? AND id != ?", (nome_val.upper(), edit_id))
                else:
                    chk_nome = fetch_all("SELECT id FROM clientes WHERE UPPER(TRIM(nome)) = ?", (nome_val.upper(),))
                    
                chk_cnpj = pd.DataFrame()
                if cnpj_val:
                    if edit_id:
                        chk_cnpj = fetch_all("SELECT id FROM clientes WHERE TRIM(cnpj_cpf) = ? AND id != ?", (cnpj_val, edit_id))
                    else:
                        chk_cnpj = fetch_all("SELECT id FROM clientes WHERE TRIM(cnpj_cpf) = ?", (cnpj_val,))
                        
                if not chk_nome.empty:
                    st.error(f"⚠️ Já existe um cliente cadastrado com a Razão Social '{nome_val}'. Se forem clientes diferentes, diferencie-os (ex: '{nome_val} RJ').")
                elif not chk_cnpj.empty:
                    st.error(f"⚠️ Já existe um cliente cadastrado com o CNPJ/CPF '{cnpj_val}'.")
                else:
                    # Preparação final dos valores
                    rep_id_val = rep_dict.get(rep_selecionado)
                    fp_id_val, fp_parc_val = fp_opts[fp_selecionada]
                    
                    import re
                    first_day = 30
                    nums = re.findall(r'\d+', fp_parc_val)
                    if nums:
                        first_day = int(nums[0])
                        
                    nasc_str = nascimento_val.strftime("%Y-%m-%d") if nascimento_val else None
                    r_val = rede_selecionada if rede_selecionada != "(Nenhuma)" else ""
                    g_val = grupo_selecionado if grupo_selecionado != "(Nenhum)" else ""
                    
                    import json
                    contatos_list = []
                    for i in range(3):
                        contatos_list.append({
                            "nome": st.session_state.get(f"cli_contato_{i}_nome", ""),
                            "depto": st.session_state.get(f"cli_contato_{i}_depto", ""),
                            "tel1": st.session_state.get(f"cli_contato_{i}_tel1", ""),
                            "wapp1": bool(st.session_state.get(f"cli_contato_{i}_wapp1", False)),
                            "tel2": st.session_state.get(f"cli_contato_{i}_tel2", ""),
                            "wapp2": bool(st.session_state.get(f"cli_contato_{i}_wapp2", False)),
                            "email": st.session_state.get(f"cli_contato_{i}_email", "")
                        })
                    contatos_json_val = json.dumps(contatos_list, ensure_ascii=False)
                    
                    limit_cred = 0.0
                    limit_ilimit = 1
                    
                    if edit_id:
                        # UPDATE
                        run_query("""
                            UPDATE clientes
                            SET nome=?, nome_fantasia=?, cnpj_cpf=?, data_nascimento=?, inscricao_estadual=?,
                                telefone=?, email=?, endereco=?, bairro=?, cidade=?, uf=?, cep=?, rede_clientes=?, grupo_lojas=?,
                                status=?, chave_pix=?, prazo_pagamento=?, prazo_pagamento_dias=?, representante_id=?,
                                observacoes=?, taxa_descarga=?, regras_descarga=?, forma_pagamento_id=?,
                                limite_credito=?, limite_ilimitado=?, contatos_json=?
                            WHERE id=?
                        """, (nome_val, nome_fantasia_val, cnpj_val, nasc_str, inscricao_estadual_val,
                              telefone_val, email_val, endereco_val, bairro_val, cidade_val, uf_val, cep_val, r_val, g_val,
                              status_val, chave_pix_val, fp_selecionada, first_day, rep_id_val,
                              observacoes_val, taxa_descarga_val, regras_descarga_val, fp_id_val,
                              limit_cred, limit_ilimit, contatos_json_val, edit_id))
                        st.success("Cadastro do cliente atualizado com sucesso!")
                    else:
                        # INSERT
                        run_query("""
                            INSERT INTO clientes 
                            (nome, nome_fantasia, cnpj_cpf, data_nascimento, inscricao_estadual,
                             telefone, email, endereco, bairro, cidade, uf, cep, rede_clientes, grupo_lojas,
                             status, chave_pix, prazo_pagamento, prazo_pagamento_dias, representante_id,
                             observacoes, taxa_descarga, regras_descarga, forma_pagamento_id,
                             limite_credito, limite_ilimitado, contatos_json) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nome_val, nome_fantasia_val, cnpj_val, nasc_str, inscricao_estadual_val,
                              telefone_val, email_val, endereco_val, bairro_val, cidade_val, uf_val, cep_val, r_val, g_val,
                              status_val, chave_pix_val, fp_selecionada, first_day, rep_id_val,
                              observacoes_val, taxa_descarga_val, regras_descarga_val, fp_id_val,
                              limit_cred, limit_ilimit, contatos_json_val))
                        st.success("Cliente cadastrado com sucesso!")
                        
                    limpar_dados_formulario()
                    st.session_state["show_incluir_cliente"] = False
                    st.session_state["edit_cliente_id"] = None
                    import time; time.sleep(1.5)
                    st.rerun()

# ======= FORNECEDORES =======
with tab3:

    # ─────── Funções Auxiliares Fornecedores ───────
    def buscar_cnpj_api_forn(cnpj_val):
        import requests
        cnpj_clean = "".join(filter(str.isdigit, cnpj_val))
        if len(cnpj_clean) != 14:
            return {"error": "CNPJ inválido. Deve conter 14 dígitos."}
        try:
            r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}", timeout=8)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return {"error": "CNPJ não encontrado na Receita Federal."}
            else:
                return {"error": f"Erro na consulta (status {r.status_code})."}
        except Exception as e:
            return {"error": f"Erro de conexão com a API: {str(e)}"}

    def limpar_form_forn():
        keys_forn = [
            "forn_cnpj", "forn_nome", "forn_fantasia", "forn_ie", "forn_telefone", "forn_email",
            "forn_cep", "forn_endereco", "forn_bairro", "forn_cidade", "forn_uf",
            "forn_chave_pix", "forn_observacoes", "forn_status",
            "forn_c0_nome","forn_c0_depto","forn_c0_tel1","forn_c0_wapp1","forn_c0_tel2","forn_c0_wapp2","forn_c0_email",
            "forn_c1_nome","forn_c1_depto","forn_c1_tel1","forn_c1_wapp1","forn_c1_tel2","forn_c1_wapp2","forn_c1_email",
            "forn_c2_nome","forn_c2_depto","forn_c2_tel1","forn_c2_wapp1","forn_c2_tel2","forn_c2_wapp2","forn_c2_email",
        ]
        for k in keys_forn:
            if k in st.session_state:
                del st.session_state[k]

    # ─────── Inicialização de estados ───────
    if "show_form_forn" not in st.session_state:
        st.session_state["show_form_forn"] = False
    if "edit_forn_id" not in st.session_state:
        st.session_state["edit_forn_id"] = None

    # ─────── Carrega Dados Base ───────
    df_planos = fetch_all("SELECT id, nome FROM planos_de_contas ORDER BY nome")
    planos_options = df_planos['nome'].tolist() if not df_planos.empty else []
    planos_dict = dict(zip(df_planos['nome'], df_planos['id'])) if not df_planos.empty else {}
    planos_reverse_dict = dict(zip(df_planos['id'], df_planos['nome'])) if not df_planos.empty else {}

    df_fp_list_forn = fetch_all("SELECT id, nome FROM formas_pagamento ORDER BY id ASC")
    fp_opts_forn = {}
    if not df_fp_list_forn.empty:
        for _, _r in df_fp_list_forn.iterrows():
            fp_opts_forn[_r['nome']] = _r['id']

    # ─────── Query e Filtros ───────
    st.markdown("### Fornecedores Cadastrados")
    f_col1, f_col2, f_col3, f_col4 = st.columns([3, 2, 1, 2])
    forn_busca = f_col1.text_input("🔍 Busca por nome, CNPJ ou cidade", key="forn_busca_txt", label_visibility="collapsed", placeholder="🔍 Buscar por nome, CNPJ ou cidade...")
    forn_exibir_inativos = f_col2.checkbox("Exibir Fornecedores Inativos", key="forn_exibir_inativos", value=False)
    forn_filtro_periodo = f_col3.checkbox("Filtrar por período", key="forn_filtro_periodo", value=False)
    if forn_filtro_periodo:
        forn_data_ini = f_col4.date_input("Data inicial", key="forn_data_ini", format="DD/MM/YYYY", value=None)
        forn_data_fim = f_col4.date_input("Data final", key="forn_data_fim", format="DD/MM/YYYY", value=None)
    else:
        forn_data_ini = None
        forn_data_fim = None

    # ─── Toolbar: Ferramentas e Ações ───
    tb_a, tb_b, tb_c, tb_d, tb_e, tb_f = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5])
    if tb_a.button("➕ Incluir Novo Fornecedor", use_container_width=True):
        limpar_form_forn()
        st.session_state["show_form_forn"] = True
        st.session_state["edit_forn_id"] = None
        st.rerun()

    df_forn_raw = fetch_all("""
        SELECT f.id, f.nome as "Razão Social", f.nome_fantasia as "Nome Fantasia",
               f.cnpj_cpf as "CNPJ/CPF", f.cidade as "Cidade", f.uf as "UF",
               f.telefone as "Telefone", f.email as "E-mail",
               f.status as "Status", f.prazo_pagamento as "Prazo Padrão",
               f.chave_pix as "Chave Pix", f.plano_conta_id, f.forma_pagamento_id,
               f.observacoes, f.cep, f.endereco, f.bairro, f.inscricao_estadual,
               f.contatos_json
        FROM fornecedores f
        ORDER BY f.id DESC
    """)

    if df_forn_raw.empty:
        df_forn_raw = pd.DataFrame()

    df_forn_filtered = df_forn_raw.copy() if not df_forn_raw.empty else pd.DataFrame()

    if not df_forn_filtered.empty:
        if not forn_exibir_inativos:
            df_forn_filtered = df_forn_filtered[df_forn_filtered["Status"].str.upper() != "INATIVO"]
        if forn_busca:
            mask = (
                df_forn_filtered["Razão Social"].str.contains(forn_busca, case=False, na=False) |
                df_forn_filtered["Nome Fantasia"].str.contains(forn_busca, case=False, na=False) |
                df_forn_filtered["CNPJ/CPF"].str.contains(forn_busca, case=False, na=False) |
                df_forn_filtered["Cidade"].str.contains(forn_busca, case=False, na=False)
            )
            df_forn_filtered = df_forn_filtered[mask]

    # Botões de utilidade (export/import)
    if not df_forn_filtered.empty:
        csv_forn = df_forn_filtered[["id","Razão Social","Nome Fantasia","CNPJ/CPF","Cidade","UF","Telefone","E-mail","Status","Prazo Padrão","Chave Pix"]].to_csv(index=False, sep=';').encode('utf-8-sig')
        tb_c.download_button("📤 Exportar CSV", data=csv_forn, file_name="fornecedores.csv", mime="text/csv", use_container_width=True)

    show_import_forn = tb_d.button("📥 Importar CSV", use_container_width=True, key="forn_import_btn")

    # Paginação
    FORN_PAGE_SIZE = 10
    if "forn_page" not in st.session_state:
        st.session_state["forn_page"] = 0
    total_forn = len(df_forn_filtered) if not df_forn_filtered.empty else 0
    total_pages_forn = max(1, (total_forn + FORN_PAGE_SIZE - 1) // FORN_PAGE_SIZE)
    if st.session_state["forn_page"] >= total_pages_forn:
        st.session_state["forn_page"] = 0

    pag_a, pag_b, pag_c = st.columns([1, 3, 1])
    if pag_a.button("◀ Anterior", key="forn_prev", disabled=st.session_state["forn_page"] == 0):
        st.session_state["forn_page"] -= 1; st.rerun()
    pag_b.markdown(f"<div style='text-align:center; padding-top:6px'>Pág. {st.session_state['forn_page']+1} de {total_pages_forn} — {total_forn} fornecedor(es)</div>", unsafe_allow_html=True)
    if pag_c.button("Próximo ▶", key="forn_next", disabled=st.session_state["forn_page"] >= total_pages_forn - 1):
        st.session_state["forn_page"] += 1; st.rerun()

    # Grid
    FORN_GRID_COLS = ["Razão Social", "Nome Fantasia", "CNPJ/CPF", "Cidade", "UF", "Telefone", "E-mail", "Status", "Prazo Padrão"]
    if not df_forn_filtered.empty:
        forn_start = st.session_state["forn_page"] * FORN_PAGE_SIZE
        df_forn_page = df_forn_filtered.iloc[forn_start: forn_start + FORN_PAGE_SIZE].reset_index(drop=True)
        df_forn_page.insert(0, "✓", False)

        edited_forn = st.data_editor(
            df_forn_page[["✓"] + FORN_GRID_COLS],
            column_config={"✓": st.column_config.CheckboxColumn("✓", default=False, width="small")},
            hide_index=True,
            use_container_width=True,
            key="forn_grid_editor"
        )

        selecionados_forn = df_forn_page[edited_forn["✓"].values == True]

        if tb_b.button("✏️ Editar Selecionado", use_container_width=True, disabled=len(selecionados_forn) != 1):
            fid_edit = selecionados_forn.iloc[0]["id"] if "id" in selecionados_forn.columns else df_forn_page[edited_forn["✓"].values == True].iloc[0]["id"]
            forn_row = df_forn_raw[df_forn_raw["id"] == fid_edit].iloc[0]
            limpar_form_forn()
            st.session_state["edit_forn_id"] = int(fid_edit)
            st.session_state["show_form_forn"] = True
            st.session_state["forn_cnpj"] = forn_row.get("CNPJ/CPF", "") or ""
            st.session_state["forn_nome"] = forn_row.get("Razão Social", "") or ""
            st.session_state["forn_fantasia"] = forn_row.get("Nome Fantasia", "") or ""
            st.session_state["forn_ie"] = forn_row.get("inscricao_estadual", "") or ""
            st.session_state["forn_telefone"] = forn_row.get("Telefone", "") or ""
            st.session_state["forn_email"] = forn_row.get("E-mail", "") or ""
            st.session_state["forn_cep"] = forn_row.get("cep", "") or ""
            st.session_state["forn_endereco"] = forn_row.get("endereco", "") or ""
            st.session_state["forn_bairro"] = forn_row.get("bairro", "") or ""
            st.session_state["forn_cidade"] = forn_row.get("Cidade", "") or ""
            st.session_state["forn_uf"] = forn_row.get("UF", "") or ""
            st.session_state["forn_chave_pix"] = forn_row.get("Chave Pix", "") or ""
            st.session_state["forn_observacoes"] = forn_row.get("observacoes", "") or ""
            st.session_state["forn_status"] = forn_row.get("Status", "ATIVO") or "ATIVO"
            import json as _json
            try:
                contatos_salvos = _json.loads(forn_row.get("contatos_json") or "[]")
            except Exception:
                contatos_salvos = []
            for ci in range(3):
                c_data = contatos_salvos[ci] if ci < len(contatos_salvos) else {}
                st.session_state[f"forn_c{ci}_nome"] = c_data.get("nome", "")
                st.session_state[f"forn_c{ci}_depto"] = c_data.get("depto", "")
                st.session_state[f"forn_c{ci}_tel1"] = c_data.get("tel1", "")
                st.session_state[f"forn_c{ci}_wapp1"] = c_data.get("wapp1", False)
                st.session_state[f"forn_c{ci}_tel2"] = c_data.get("tel2", "")
                st.session_state[f"forn_c{ci}_wapp2"] = c_data.get("wapp2", False)
                st.session_state[f"forn_c{ci}_email"] = c_data.get("email", "")
            st.rerun()
    else:
        st.info("Nenhum fornecedor encontrado com os filtros aplicados.")
        selecionados_forn = pd.DataFrame()
        if not df_forn_filtered.empty or df_forn_raw.empty:
            tb_b.button("✏️ Editar Selecionado", use_container_width=True, disabled=True)

    # Importação por CSV
    if show_import_forn:
        with st.expander("📥 Importar Fornecedores via Planilha CSV", expanded=True):
            st.caption("O arquivo deve conter as colunas: nome, nome_fantasia, cnpj_cpf, telefone, email, endereco, bairro, cidade, uf, cep, status")
            csv_import_forn = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="forn_import_upload")
            if csv_import_forn:
                try:
                    df_imp = pd.read_csv(csv_import_forn, sep=';', dtype=str)
                    st.dataframe(df_imp.head(5))
                    if st.button("✅ Confirmar Importação", key="forn_confirm_import"):
                        imported = 0
                        for _, imp_row in df_imp.iterrows():
                            n = str(imp_row.get("nome", "")).strip()
                            if not n: continue
                            chk = fetch_all("SELECT id FROM fornecedores WHERE UPPER(TRIM(nome))=?", (n.upper(),))
                            if not chk.empty: continue
                            run_query("""INSERT INTO fornecedores (nome, nome_fantasia, cnpj_cpf, telefone, email, endereco, bairro, cidade, uf, cep, status)
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                      (n, str(imp_row.get("nome_fantasia","")).strip(), str(imp_row.get("cnpj_cpf","")).strip(),
                                       str(imp_row.get("telefone","")).strip(), str(imp_row.get("email","")).strip(),
                                       str(imp_row.get("endereco","")).strip(), str(imp_row.get("bairro","")).strip(),
                                       str(imp_row.get("cidade","")).strip(), str(imp_row.get("uf","")).strip(),
                                       str(imp_row.get("cep","")).strip(), str(imp_row.get("status","ATIVO")).strip()))
                            imported += 1
                        st.success(f"{imported} fornecedor(es) importados com sucesso!")
                        import time; time.sleep(1.5); st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {e}")

    # ─────── Formulário de Inclusão / Edição ───────
    if st.session_state.get("show_form_forn"):
        is_editing_forn = st.session_state.get("edit_forn_id") is not None
        forn_form_title = f"✏️ Editando Fornecedor (ID {st.session_state['edit_forn_id']})" if is_editing_forn else "➕ Novo Fornecedor"
        st.markdown(f"---\n### {forn_form_title}")

        # 1. Campo de CNPJ com busca
        fcol_cnpj, fcol_btn = st.columns([3, 1])
        forn_cnpj_val = fcol_cnpj.text_input("CNPJ / CPF *", key="forn_cnpj")

        if fcol_btn.button("🔍 Buscar CNPJ", use_container_width=True):
            if forn_cnpj_val:
                with st.spinner("Consultando Receita Federal (BrasilAPI)..."):
                    res = buscar_cnpj_api_forn(forn_cnpj_val)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.session_state["forn_nome"] = res.get("razao_social", "")
                        st.session_state["forn_fantasia"] = res.get("nome_fantasia", "")
                        st.session_state["forn_cep"] = res.get("cep", "")
                        logr = res.get("logradouro", "")
                        num = res.get("numero", "")
                        comp = res.get("complemento", "")
                        end_str = f"{logr}, {num}"
                        if comp:
                            end_str += f" - {comp}"
                        st.session_state["forn_endereco"] = end_str
                        st.session_state["forn_bairro"] = res.get("bairro", "")
                        st.session_state["forn_cidade"] = res.get("municipio", "")
                        st.session_state["forn_uf"] = res.get("uf", "")
                        st.success("Dados pré-preenchidos! Revise e edite se necessário.")
                        import time; time.sleep(1); st.rerun()
            else:
                st.warning("Preencha o campo CNPJ antes de buscar.")

        # 2. Dados Gerais
        fg1, fg2 = st.columns([2, 1])
        forn_nome_val = fg1.text_input("Razão Social *", key="forn_nome")
        forn_fantasia_val = fg2.text_input("Nome Fantasia", key="forn_fantasia")

        fg3, fg4, fg5 = st.columns(3)
        forn_ie_val = fg3.text_input("Inscrição Estadual", key="forn_ie")
        forn_tel_val = fg4.text_input("Telefone Geral", key="forn_telefone")
        forn_email_val = fg5.text_input("E-mail Geral", key="forn_email")

        fg6, fg7, fg8, fg9, fg10 = st.columns([3, 1, 2, 1, 1])
        forn_end_val = fg6.text_input("Endereço (Rua, Número, Complemento)", key="forn_endereco")
        forn_cep_val = fg7.text_input("CEP", key="forn_cep")
        forn_bairro_val = fg8.text_input("Bairro", key="forn_bairro")
        forn_cidade_val = fg9.text_input("Cidade", key="forn_cidade")
        forn_uf_val = fg10.text_input("UF", key="forn_uf", max_chars=2)

        fg11, fg12, fg13, fg14 = st.columns(4)
        forn_pix_val = fg11.text_input("Chave Pix", key="forn_chave_pix")

        _forn_fp_keys = list(fp_opts_forn.keys())
        _forn_fp_default_idx = 0
        if is_editing_forn:
            _eid_forn = st.session_state["edit_forn_id"]
            _ef_row = df_forn_raw[df_forn_raw["id"] == _eid_forn]
            if not _ef_row.empty:
                _fp_id_cur = _ef_row.iloc[0].get("forma_pagamento_id")
                if _fp_id_cur and pd.notna(_fp_id_cur):
                    _df_fp_cur = fetch_all("SELECT nome FROM formas_pagamento WHERE id=?", (int(_fp_id_cur),))
                    if not _df_fp_cur.empty:
                        _fp_nome_cur = _df_fp_cur.iloc[0]['nome']
                        if _fp_nome_cur in _forn_fp_keys:
                            _forn_fp_default_idx = _forn_fp_keys.index(_fp_nome_cur)

        forn_fp_sel = fg12.selectbox("Forma / Prazo Pagto.", _forn_fp_keys if _forn_fp_keys else ["(nenhuma)"], index=_forn_fp_default_idx, key="forn_fp_sel")
        forn_fp_id_val = fp_opts_forn.get(forn_fp_sel, None) if _forn_fp_keys else None

        _plano_default_idx = 0
        if is_editing_forn and planos_options:
            _eid_forn = st.session_state["edit_forn_id"]
            _ef_row2 = df_forn_raw[df_forn_raw["id"] == _eid_forn]
            if not _ef_row2.empty:
                _plano_id_cur = _ef_row2.iloc[0].get("plano_conta_id")
                _plano_nome_cur = planos_reverse_dict.get(_plano_id_cur, "")
                if _plano_nome_cur in planos_options:
                    _plano_default_idx = planos_options.index(_plano_nome_cur) + 1

        forn_plano_sel = fg13.selectbox("Plano de Contas", ["(Nenhum/Outro)"] + planos_options, index=_plano_default_idx, key="forn_plano_sel")
        forn_plano_id_val = planos_dict.get(forn_plano_sel, None) if forn_plano_sel != "(Nenhum/Outro)" else None

        _forn_status_opts = ["ATIVO", "INATIVO"]
        _forn_status_default = 0
        if is_editing_forn:
            _cur_status = st.session_state.get("forn_status", "ATIVO")
            if _cur_status in _forn_status_opts:
                _forn_status_default = _forn_status_opts.index(_cur_status)
        forn_status_val = fg14.selectbox("Status", _forn_status_opts, index=_forn_status_default, key="forn_status_sel")

        forn_obs_val = st.text_area("Observações", key="forn_observacoes", height=70)

        # 3. Seção de Contatos
        st.markdown("---")
        st.markdown("#### 👥 Contatos do Fornecedor")
        import json as _json_forn
        forn_contatos_coletados = []
        for ci in range(3):
            st.markdown(f"**Contato {ci+1}**")
            cc1, cc2, cc3, cc4, cc5, cc6, cc7 = st.columns([2, 1.5, 1.5, 0.6, 1.5, 0.6, 2])
            c_nome = cc1.text_input("Nome", key=f"forn_c{ci}_nome")
            c_depto = cc2.text_input("Departamento", key=f"forn_c{ci}_depto")
            c_tel1 = cc3.text_input("Telefone 1", key=f"forn_c{ci}_tel1")
            c_wapp1 = cc4.checkbox("WhatsApp", key=f"forn_c{ci}_wapp1")
            c_tel2 = cc5.text_input("Telefone 2", key=f"forn_c{ci}_tel2")
            c_wapp2 = cc6.checkbox("WhatsApp", key=f"forn_c{ci}_wapp2")
            c_email = cc7.text_input("E-mail", key=f"forn_c{ci}_email")
            forn_contatos_coletados.append({
                "nome": c_nome, "depto": c_depto,
                "tel1": c_tel1, "wapp1": c_wapp1,
                "tel2": c_tel2, "wapp2": c_wapp2,
                "email": c_email
            })

        # 4. Botões de Ação
        st.markdown("")
        fbn_salvar, fbn_cancelar, _ = st.columns([2, 2, 6])
        forn_contatos_json_val = _json_forn.dumps(forn_contatos_coletados, ensure_ascii=False)

        if fbn_salvar.button("💾 Salvar Fornecedor", use_container_width=True, type="primary"):
            if not forn_nome_val.strip():
                st.error("A Razão Social é obrigatória.")
            else:
                nome_limpo = forn_nome_val.strip().upper()
                cnpj_limpo = forn_cnpj_val.strip() if forn_cnpj_val else ""

                if is_editing_forn:
                    fid_upd = st.session_state["edit_forn_id"]
                    chk_nome_upd = fetch_all("SELECT id FROM fornecedores WHERE UPPER(TRIM(nome))=? AND id != ?", (nome_limpo, fid_upd))
                    chk_cnpj_upd = fetch_all("SELECT id FROM fornecedores WHERE TRIM(cnpj_cpf)=? AND id != ?", (cnpj_limpo, fid_upd)) if cnpj_limpo else pd.DataFrame()

                    if not chk_nome_upd.empty:
                        st.error(f"Já existe outro fornecedor com a Razão Social '{forn_nome_val.strip()}'.")
                    elif not chk_cnpj_upd.empty:
                        st.error(f"Já existe outro fornecedor com o CNPJ '{cnpj_limpo}'.")
                    else:
                        run_query("""
                            UPDATE fornecedores
                            SET nome=?, nome_fantasia=?, cnpj_cpf=?, inscricao_estadual=?,
                                telefone=?, email=?, endereco=?, bairro=?, cidade=?, uf=?, cep=?,
                                chave_pix=?, prazo_pagamento=?, plano_de_contas=?, status=?,
                                plano_conta_id=?, forma_pagamento_id=?, observacoes=?, contatos_json=?
                            WHERE id=?
                        """, (forn_nome_val, forn_fantasia_val, forn_cnpj_val, forn_ie_val,
                              forn_tel_val, forn_email_val, forn_end_val, forn_bairro_val,
                              forn_cidade_val, forn_uf_val, forn_cep_val,
                              forn_pix_val, forn_fp_sel, forn_plano_sel, forn_status_val,
                              forn_plano_id_val, forn_fp_id_val, forn_obs_val,
                              forn_contatos_json_val, fid_upd))
                        st.success("Fornecedor atualizado com sucesso!")
                        limpar_form_forn()
                        st.session_state["show_form_forn"] = False
                        st.session_state["edit_forn_id"] = None
                        import time; time.sleep(1.5); st.rerun()
                else:
                    chk_nome_new = fetch_all("SELECT id FROM fornecedores WHERE UPPER(TRIM(nome))=?", (nome_limpo,))
                    chk_cnpj_new = fetch_all("SELECT id FROM fornecedores WHERE TRIM(cnpj_cpf)=?", (cnpj_limpo,)) if cnpj_limpo else pd.DataFrame()

                    if not chk_nome_new.empty:
                        st.error(f"Já existe um fornecedor com a Razão Social '{forn_nome_val.strip()}'.")
                    elif not chk_cnpj_new.empty:
                        st.error(f"Já existe um fornecedor com o CNPJ '{cnpj_limpo}'.")
                    else:
                        run_query("""
                            INSERT INTO fornecedores
                            (nome, nome_fantasia, cnpj_cpf, inscricao_estadual,
                             telefone, email, endereco, bairro, cidade, uf, cep,
                             chave_pix, prazo_pagamento, plano_de_contas, status,
                             plano_conta_id, forma_pagamento_id, observacoes, contatos_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (forn_nome_val, forn_fantasia_val, forn_cnpj_val, forn_ie_val,
                              forn_tel_val, forn_email_val, forn_end_val, forn_bairro_val,
                              forn_cidade_val, forn_uf_val, forn_cep_val,
                              forn_pix_val, forn_fp_sel, forn_plano_sel, forn_status_val,
                              forn_plano_id_val, forn_fp_id_val, forn_obs_val,
                              forn_contatos_json_val))
                        st.success("Fornecedor cadastrado com sucesso!")
                        limpar_form_forn()
                        st.session_state["show_form_forn"] = False
                        import time; time.sleep(1.5); st.rerun()

        if fbn_cancelar.button("✖ Cancelar", use_container_width=True):
            limpar_form_forn()
            st.session_state["show_form_forn"] = False
            st.session_state["edit_forn_id"] = None
            st.rerun()


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
        df_maq_show = df_maq.copy()
        df_maq_show['Data'] = pd.to_datetime(df_maq_show['Data']).dt.strftime('%d/%m/%Y')
        export_btn(df_maq_show, 'maquinario.csv')
        st.dataframe(df_maq_show, hide_index=True, width="stretch")
        
        with st.expander("🗑️ Excluir Máquina/Ativo"):
            opts_maq_del = {f"ID {row['id']} | {row['Máquina/Ativo']} (R$ {row['Valor R$']:,.2f})": row['id'] for _, row in df_maq.iterrows()}
            m_del = st.selectbox("Selecione o Equipamento para Excluir:", ["-- SELECIONE --"] + list(opts_maq_del.keys()), key="sb_maq_delete")
            if m_del != "-- SELECIONE --":
                maq_id_del = opts_maq_del[m_del]
                if st.button("Confirmar Exclusão do Ativo", type="primary", key="btn_maq_delete"):
                    df_com = fetch_all("SELECT id FROM comodatos WHERE maquina_id = ? AND status = 'ATIVO'", (maq_id_del,))
                    if not df_com.empty:
                        st.error("⚠️ Não é permitido excluir esta máquina pois ela possui um comodato ATIVO com um cliente.")
                    else:
                        run_query("DELETE FROM maquinario WHERE id = ?", (maq_id_del,))
                        st.success("Equipamento excluído com sucesso!")
                        import time; time.sleep(1); st.rerun()

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
