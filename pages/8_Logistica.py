import streamlit as st
import pandas as pd
from datetime import date
from database import run_query, fetch_all
from estilo import carregar_estilo

st.set_page_config(page_title="Roteirização Logística", page_icon="🚛", layout="wide")
carregar_estilo()

st.title("🚛 Gestão de Frota e Manifestos de Carga")
st.markdown("Crie rotas, embarque faturamentos e rateie o custo do frete nas notas de venda para obter a margem real (CMV Líquido).")

def format_brl(val):
    if pd.isna(val) or val is None: return "R$ 0,00"
    return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

tab1, tab2 = st.tabs(["🛣️ Criar Novo Manifesto (Embarque)", "🗂️ Histórico de Viagens"])

with tab1:
    st.subheader("Montagem do Centro de Custo da Rota")
    
    # Busca vendas sem embarque no momento (Sem vinculo a viagem e estritamente faturadas)
    df_orfãs = fetch_all('''
       SELECT v.id, v.data, c.nome as Cliente, c.taxa_descarga, c.regras_descarga, p.nome as Carga, v.valor_total,
              v.tipo_documento, v.numero_documento
       FROM vendas v 
       JOIN clientes c ON v.cliente_id=c.id 
       JOIN produtos p ON v.produto_id=p.id 
       WHERE v.manifesto_id IS NULL AND v.status = 'FATURADO'
       ORDER BY v.data DESC
    ''')
    
    with st.form("form_manifesto"):
        col1, col2, col3 = st.columns(3)
        dt_saida = col1.date_input("Data Oficial de Despacho", value=date.today())
        tipo_frota = col2.selectbox("Natureza do Veículo", ["Frota Própria", "Frete Terceirizado"])
        
        # Opcional puxar os funcionarios que são motoristas, aqui fica livre como text
        motorista = col3.text_input("Nome do Motorista")
        
        col4, col5 = st.columns(2)
        placa = col4.text_input("Placa do Caminhão / Van")
        custo_frete = col5.number_input("Custo Total Acordado da Viagem (Frete R$)", min_value=0.0, step=100.0)
        
        st.markdown("##### Acerto Secundário (Apenas para Transportadoras Terceiras)")
        df_fornec = fetch_all("SELECT id, nome FROM fornecedores WHERE status='ATIVO'")
        f_opts = {r['nome']: r['id'] for _, r in df_fornec.iterrows()} if not df_fornec.empty else {}
        
        f1, f2 = st.columns(2)
        fornecedor_selecionado = f1.selectbox("PJ da Transportadora (Para gerar Boleto no Financeiro)", ["-- INTERNO / NÃO GERAR PAGAR --"] + list(f_opts.keys()))
        venc_frete = f2.date_input("Vencimento do Acerto deste Frete")
        
        st.markdown("---")
        st.markdown("### Seleção de Carga no Pátio (Notas sem Rota)")
        
        notas_selecionadas = []
        options_map = {}
        if df_orfãs.empty:
            st.info("📦 Não existem faturamentos aguardando embarque. Todas as notas despachadas já estão em caminhões.")
        else:
            options = []
            for _, row in df_orfãs.iterrows():
                dt_f = pd.to_datetime(row['data']).strftime('%d/%m')
                tipo = row['tipo_documento'] or "Nota Fiscal (NF)"
                num = row['numero_documento']
                
                if "DAV" in tipo:
                    doc_label = f"DAV #{str(num).zfill(10)}" if num else f"DAV #{row['id']}"
                else:
                    doc_label = f"NF-e #{num}" if (num and str(num).strip() != "") else "⚠️ [NF PENDENTE DE NÚMERO]"
                
                label = f"Venda #{row['id']} ({doc_label}) | {dt_f} - {row['Cliente']} ({row['Carga']}) -> {format_brl(row['valor_total'])}"
                options.append(label)
                options_map[label] = row
                
            notas_selecionadas = st.multiselect("Marque quais Faturamentos irão neste caminhão:", options)
        
        # Alerta de Taxas e Regras de Descarga dos clientes selecionados
        if notas_selecionadas:
            ids_sel = []
            for ns in notas_selecionadas:
                if ns in options_map:
                    ids_sel.append(int(options_map[ns]['id']))
            df_alertas = df_orfãs[df_orfãs['id'].isin(ids_sel)]
            
            # Filtra somente clientes com taxa ou regra preenchida
            df_com_taxa = df_alertas[(df_alertas['taxa_descarga'].fillna(0) > 0) | (df_alertas['regras_descarga'].notna() & (df_alertas['regras_descarga'] != ''))]
            if not df_com_taxa.empty:
                st.markdown("---")
                st.markdown("### ⚠️ Alertas Logísticos da Carga")
                for _, alerta_row in df_com_taxa.iterrows():
                    taxa_val = float(alerta_row['taxa_descarga'] or 0.0)
                    regra_val = alerta_row['regras_descarga'] or "Sem regra cadastrada"
                    taxa_fmt = format_brl(taxa_val) if taxa_val > 0 else "Sem taxa"
                    st.warning(f"🚨 **{alerta_row['Cliente']}** (NF #{alerta_row['id']}) — Taxa de Descarga: **{taxa_fmt}** | Regra: _{regra_val}_")
            
        st.info("⚙️ **Como funciona o Rateio Sagrado:** O sistema somará o valor comercial em Reais de tudo que subir no caminhão. Se a Nota do Supermercado A for 80% do valor do caminhão, ela sofrerá a dedução de 80% do Custo do Frete que você preencheu lá em cima para seu DRE não ser mentiroso.")
        
        if st.form_submit_button("Liberar Caminhão (Gerar Manifesto)", type="primary"):
            id_lista = []
            nfs_sem_numero = []
            for ns in notas_selecionadas:
                if ns in options_map:
                    row = options_map[ns]
                    v_id = int(row['id'])
                    id_lista.append(v_id)
                    tipo = row['tipo_documento'] or "Nota Fiscal (NF)"
                    num = row['numero_documento']
                    if "Nota Fiscal" in tipo and (not num or str(num).strip() == ""):
                        nfs_sem_numero.append(f"Venda #{v_id} ({row['Cliente']})")
            
            if not notas_selecionadas:
                st.error("Selecione no mínimo 1 faturamento para viajar!")
            elif nfs_sem_numero:
                st.error(f"🛑 **Erro de Expedição:** O caminhão não pode ser liberado! As seguintes Notas Fiscais estão pendentes do número oficial do SEFAZ: {', '.join(nfs_sem_numero)}. Favor registrar as numerações no módulo de Faturamento primeiro.")
            elif custo_frete == 0.0:
                st.warning("Tem certeza que este frete será grátis (0 R$)? O custo para calcular a margem precisa ser real.")
            else:
                # Se passou
                # Vamos puxar os valores brutos exatos do Banco
                s_orfas = df_orfãs[df_orfãs['id'].isin(id_lista)]
                total_da_carga = s_orfas['valor_total'].sum()
                
                if total_da_carga <= 0:
                    st.error("Existe um erro nos Faturamentos (Valor Zero). Eles não podem ser embarcados com rateio financeiro de frete.")
                else:
                    # 1. Cria o Manifesto Pai
                    run_query('''
                      INSERT INTO manifestos_carga (data_saida, placa_veiculo, motorista_nome, tipo_frete, valor_total_frete) 
                      VALUES (?, ?, ?, ?, ?)
                    ''', (dt_saida, placa, motorista, tipo_frota, custo_frete))
                    
                    man_id = fetch_all("SELECT MAX(id) as lg FROM manifestos_carga").iloc[0]['lg']
                    
                    # 2. Rateio Dinâmico Proporcional:
                    # Pedaço a pagar = (Valor Faturado da Nota / Valor Faturado Total de todo o Caminhão) * Frete Total do Caminhão
                    for _, vp in s_orfas.iterrows():
                        v_fat = float(vp['valor_total'])
                        percentual_peso_na_carga = v_fat / total_da_carga
                        frete_absorvido = percentual_peso_na_carga * custo_frete
                        
                        run_query("UPDATE vendas SET manifesto_id=?, custo_frete_rateado=? WHERE id=?", (man_id, frete_absorvido, vp['id']))
                        
                    # 3. Lançamento automático no Contas a Pagar
                    if tipo_frota == "Frete Terceirizado" and fornecedor_selecionado != "-- INTERNO / NÃO GERAR PAGAR --" and custo_frete > 0:
                        f_id = f_opts[fornecedor_selecionado]
                        p_c = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Frete%' OR categoria LIKE '%Logística%' OR categoria LIKE '%Transporte%' LIMIT 1")
                        pc_id = p_c.iloc[0]['id'] if not p_c.empty else None
                        
                        desc_pagar = f"Acerto Rota/Manifesto #{man_id} - Placa: {placa}"
                        run_query("INSERT INTO contas_a_pagar (fornecedor_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?)",
                                  (f_id, pc_id, desc_pagar, custo_frete, venc_frete, 'PENDENTE'))
                        st.info(f"💸 Conta a Pagar gerada para a Transportadora {fornecedor_selecionado} com vencimento em {venc_frete.strftime('%d/%m/%Y')}.")
                        
                    st.success(f"🚚 Manifesto #{man_id} finalizado e lacrado com Sucesso!")
                    st.write(f"💼 Valor da Carga Embarcada: {format_brl(total_da_carga)}")
                    st.write(f"⛓️ Custo de R$ {custo_frete:,.2f} diluído perfeitamente entre {len(id_lista)} pedidos na contabilidade.")
                    import time; time.sleep(4); st.rerun()

with tab2:
    st.subheader("📥 Fechamento de Rota — Canhotos e Recibos de Descarga")
    st.markdown("Anexe os documentos de cada entrega. O Financeiro só consegue dar a **baixa** nas taxas de descarga após os comprovantes estarem aqui.")
    
    df_transit = fetch_all("SELECT id, motorista_nome FROM manifestos_carga WHERE status='EM TRÂNSITO' ORDER BY id ASC")
    if not df_transit.empty:
        opts_transit = {f"Manifesto #{r['id']} - {r['motorista_nome']}": r['id'] for _, r in df_transit.iterrows()}
        c_man, c_btn = st.columns([3,1])
        man_baixa = c_man.selectbox("Selecione a Rota para fechar:", ["-- SELECIONE --"] + list(opts_transit.keys()))
        
        if man_baixa != "-- SELECIONE --":
            man_id = opts_transit[man_baixa]
            
            # Busca vendas da rota com dados do cliente (taxa de descarga)
            df_v_man = fetch_all("""
                SELECT v.id, c.nome as 'Cliente', c.taxa_descarga, p.nome as 'Produto', v.comprovante_url 
                FROM vendas v 
                JOIN clientes c ON v.cliente_id=c.id 
                JOIN produtos p ON v.produto_id=p.id 
                WHERE v.manifesto_id=?
            """, (man_id,))
            
            if not df_v_man.empty:
                st.markdown(f"#### 📎 Entregas na Rota #{man_id}")
                
                import os
                upload_dir = r"uploads\canhotos"
                os.makedirs(upload_dir, exist_ok=True)
                
                todos_completos = True  # flag para liberar fechamento
                
                for _, r in df_v_man.iterrows():
                    venda_id = r['id']
                    cliente = r['Cliente']
                    taxa_desc = float(r['taxa_descarga'] or 0.0)
                    url_canhoto = r['comprovante_url']
                    
                    with st.container():
                        st.markdown(f"**NF #{venda_id} — {cliente}**")
                        c_left, c_right = st.columns(2)
                        
                        # --- COLUNA 1: CANHOTO DE ENTREGA ---
                        with c_left:
                            st.markdown("📄 **Canhoto Assinado (Confirmação de Entrega)**")
                            if pd.notna(url_canhoto) and url_canhoto != "":
                                st.success(f"✔️ Canhoto anexado: `{url_canhoto}`")
                            else:
                                todos_completos = False
                                f_can = st.file_uploader(
                                    f"Anexar Canhoto (Venda #{venda_id})",
                                    type=['png', 'jpg', 'jpeg', 'pdf'],
                                    key=f"can_{venda_id}"
                                )
                                if f_can is not None:
                                    ext = f_can.name.split('.')[-1]
                                    fname = f"Canhoto_Manifesto{man_id}_Venda{venda_id}.{ext}"
                                    fpath = os.path.join(upload_dir, fname)
                                    with open(fpath, "wb") as f:
                                        f.write(f_can.getbuffer())
                                    run_query("UPDATE vendas SET comprovante_url=? WHERE id=?", (fpath, venda_id))
                                    st.rerun()
                        
                        # --- COLUNA 2: RECIBO DE DESCARGA (se houver taxa) ---
                        with c_right:
                            if taxa_desc > 0:
                                st.markdown(f"🧾 **Recibo de Descarga** *(Taxa: {format_brl(taxa_desc)})*")
                                # Busca a conta_a_pagar de descarga desta venda
                                df_cap = fetch_all(
                                    "SELECT id, status, comprovante_url FROM contas_a_pagar WHERE descricao LIKE ? AND status != 'PAGO'",
                                    (f"%Venda #{venda_id}%",)
                                )
                                if not df_cap.empty:
                                    cap_id = int(df_cap.iloc[0]['id'])
                                    cap_status = df_cap.iloc[0]['status']
                                    cap_url = df_cap.iloc[0]['comprovante_url']
                                    
                                    if pd.notna(cap_url) and cap_url != "":
                                        st.success(f"✔️ Recibo anexado — aguardando baixa do Financeiro")
                                    else:
                                        todos_completos = False
                                        f_rec = st.file_uploader(
                                            f"Anexar Recibo de Descarga (Venda #{venda_id})",
                                            type=['png', 'jpg', 'jpeg', 'pdf'],
                                            key=f"rec_{venda_id}"
                                        )
                                        if f_rec is not None:
                                            ext = f_rec.name.split('.')[-1]
                                            fname = f"Recibo_Descarga_Venda{venda_id}.{ext}"
                                            fpath = os.path.join(upload_dir, fname)
                                            with open(fpath, "wb") as f:
                                                f.write(f_rec.getbuffer())
                                            # Salva comprovante e muda status p/ AGUARDANDO BAIXA
                                            run_query(
                                                "UPDATE contas_a_pagar SET comprovante_url=?, status='AGUARDANDO BAIXA' WHERE id=?",
                                                (fpath, cap_id)
                                            )
                                            st.rerun()
                                else:
                                    st.info("Conta a pagar de descarga não encontrada ou já liquidada.")
                            else:
                                st.markdown("✅ *Sem taxa de descarga para este cliente.*")
                        
                        st.markdown("---")
                
                if todos_completos:
                    st.info("✅ Todos os documentos desta rota estão anexados! O Financeiro já pode processar as taxas.")
                    if c_btn.button("✅ Fechar Rota", type="primary", use_container_width=True):
                        run_query("UPDATE manifestos_carga SET status='CONCLUÍDO (CANHOTOS OK)' WHERE id=?", (man_id,))
                        st.success("Rota encerrada! Financeiro liberado para dar baixa nas taxas de descarga.")
                        import time; time.sleep(2); st.rerun()
                else:
                    c_btn.button("⚠️ Docs Pendentes", disabled=True, use_container_width=True)
            else:
                st.warning("Este manifesto foi despachado vazio ou houve um erro.")
    else:
        st.info("Todos os manifestos já foram fechados.")
        
    st.markdown("---")
    st.subheader("Bordero de Manifestos e Histórico Operacional")
    
    df_man = fetch_all('''
       SELECT m.id as '# Doc', m.data_saida as 'Data Oficial', m.motorista_nome as 'Condutor', m.placa_veiculo as 'Placa', m.tipo_frete as 'Identidade', m.status as 'Status Operacional', m.valor_total_frete as 'Custeio Consolidado R$'
       FROM manifestos_carga m
       ORDER BY m.id DESC LIMIT 30
    ''')
    
    if not df_man.empty:
        df_man['Data Oficial'] = pd.to_datetime(df_man['Data Oficial']).dt.strftime('%d/%m/%Y')
        df_man['Custeio Consolidado R$'] = df_man['Custeio Consolidado R$'].apply(format_brl)
        st.dataframe(df_man, hide_index=True, width="stretch")
        
        st.markdown("### 🖨️ Imprimir Carta de Frete (Manifesto Exato)")
        m_opts = {f"Manifesto #{r['# Doc']} - {r['Condutor']} ({r['Data Oficial']})": r['# Doc'] for _, r in df_man.iterrows()}
        man_view = st.selectbox("Apontar Rota para conferir itens da Carga:", ["-- SELECIONE --"] + list(m_opts.keys()))
        
        if man_view != "-- SELECIONE --":
            m_id = m_opts[man_view]
            
            # Buscar Vendas dessa viagem com taxa e regra de descarga
            df_m_ven = fetch_all("""
                SELECT v.id as 'NF', c.nome as 'K-Account', c.cidade as 'Cidade', c.endereco as 'Logradouro', 
                       p.nome as 'Pallet/Pacote', v.quantidade as 'Vol.', v.valor_total as 'Valor Transacionado', 
                       v.custo_frete_rateado as 'Custo Tributado',
                       c.taxa_descarga as 'Taxa Descarga (R$)', c.regras_descarga as 'Regras de Descarga'
                FROM vendas v 
                JOIN clientes c ON v.cliente_id=c.id 
                JOIN produtos p ON v.produto_id=p.id 
                WHERE v.manifesto_id=?""", (m_id,))
            
            st.markdown(f"#### 📦 ROMANEIO DE CARGA - DOC Nº {m_id}")
            if not df_m_ven.empty:
                df_m_v_format = df_m_ven.copy()
                df_m_v_format['Valor Transacionado'] = df_m_v_format['Valor Transacionado'].apply(format_brl)
                df_m_v_format['Custo Tributado'] = df_m_v_format['Custo Tributado'].apply(format_brl)
                st.dataframe(df_m_v_format, hide_index=True, width="stretch")
            else:
                st.warning("Esta viagem partiu vazia de faturamentos vinculados.")
    else:
        st.info("Nenhuma rota concluída nos livros históricos ainda.")
