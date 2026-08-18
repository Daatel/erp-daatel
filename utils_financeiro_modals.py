import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import uuid
import re
from database import fetch_all, run_query, gerar_comissao_se_necessario

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

# ==============================================================================
# MODAIS DE CONTAS A PAGAR
# ==============================================================================

@st.dialog("Lançar uma Duplicata a Pagar (Despesa / Passivo)", width="large")
def dialog_lancar_pagar():
    df_forn = fetch_all("SELECT id, nome_fantasia, plano_conta_id FROM fornecedores ORDER BY nome_fantasia")
    op_forn = {"-- SELECIONE O FORNECEDOR --": None}
    forn_pc_map = {}
    if not df_forn.empty:
        for _, r in df_forn.iterrows():
            op_forn[f"{r['nome_fantasia']}"] = r['id']
            forn_pc_map[r['id']] = r['plano_conta_id']
    
    df_pc = fetch_all("SELECT id, codigo, nome FROM planos_de_contas WHERE categoria NOT IN ('RECEITA', 'RECEITA_NAO_OP') ORDER BY codigo")
    op_pc = {"-- SELECIONE O PLANO DE CONTAS --": (None, None)}
    if not df_pc.empty:
        for _, r in df_pc.iterrows():
            op_pc[f"{r['codigo']} - {r['nome']}"] = (r['id'], r['codigo'])
            
    df_cli = fetch_all("SELECT id, nome, cnpj_cpf FROM clientes ORDER BY nome")
    op_cli = {"-- SELECIONE O CLIENTE --": None}
    if not df_cli.empty:
        for _, r in df_cli.iterrows():
            op_cli[f"{r['nome']} ({r['cnpj_cpf']})"] = r['id']
            
    st.markdown("""
    <style>
    div[data-testid="stCheckbox"] { margin-bottom: -12px !important; }
    div[data-baseweb="select"]:has(input:disabled) > div { background-color: #f1f5f9 !important; border-color: #cbd5e1 !important; color: #94a3b8 !important; cursor: not-allowed !important; }
    div[data-baseweb="select"]:has(input:disabled) * { color: #94a3b8 !important; }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.get("cap_limpar_formulario", False):
        st.session_state["cap_forn_sel"] = list(op_forn.keys())[0]
        st.session_state["cap_pc_sel"] = list(op_pc.keys())[0]
        st.session_state["cap_num_doc_p"] = ""
        st.session_state["cap_desc_p"] = ""
        st.session_state["cap_val_p"] = 0.01
        st.session_state["cap_venc_p"] = date.today() + timedelta(days=30)
        st.session_state["cap_is_vinc"] = False
        st.session_state["cap_cli_sel"] = list(op_cli.keys())[0]
        st.session_state["cap_num_parcelas"] = 1
        st.session_state["cap_periodicidade"] = "Mensal (Mesmo dia do mês)"
        st.session_state["cap_dias_intervalo"] = 30
        st.session_state["cap_prev_forn"] = list(op_forn.keys())[0]
        st.session_state["cap_limpar_formulario"] = False

    if "cap_prev_forn" not in st.session_state:
        st.session_state["cap_prev_forn"] = list(op_forn.keys())[0]

    # Detect change of supplier to auto-fill Plano de Contas
    if st.session_state.get("cap_forn_sel") != st.session_state["cap_prev_forn"]:
        st.session_state["cap_prev_forn"] = st.session_state.get("cap_forn_sel")
        forn_name = st.session_state.get("cap_forn_sel")
        forn_id_val = op_forn.get(forn_name)
        if forn_id_val:
            pc_id_default = forn_pc_map.get(forn_id_val)
            if pc_id_default:
                for pc_key, (pc_val_id, _) in op_pc.items():
                    if pc_val_id == pc_id_default:
                        st.session_state["cap_pc_sel"] = pc_key
                        break

    col_m1, col_m2 = st.columns(2)
    forn_sel = col_m1.selectbox("Fornecedor", list(op_forn.keys()), key="cap_forn_sel")
    pc_sel = col_m2.selectbox("Plano de Contas (Planta de Custo)", list(op_pc.keys()), key="cap_pc_sel")
    
    col_m3, col_m4, col_mx = st.columns([1, 2, 1])
    num_doc_p = col_m3.text_input("Nº Documento (Opcional)", value=st.session_state.get("cap_num_doc_p", ""), key="cap_num_doc_p")
    desc_p = col_m4.text_input("Descrição / Fatura (Ex: Nota Fiscal nº 123)", value=st.session_state.get("cap_desc_p", ""), key="cap_desc_p")
    val_p = col_mx.number_input("Valor da Duplicata (R$)", min_value=0.01, step=50.0, key="cap_val_p")
    
    col_m5, col_m6, col_m7 = st.columns(3)
    dt_emissao_p = col_m5.date_input("Data de Emissão", date.today(), key="cap_emissao_p")
    venc_p = col_m6.date_input("Vencimento (ou da 1ª Parcela)", date.today() + timedelta(days=30), key="cap_venc_p")
    with col_m7:
        is_vinc = st.checkbox("É Cliente Vinculado (CNPJ) ?", value=False, key="cap_is_vinc")
        cli_sel = st.selectbox("Cliente Vinculado (CNPJ)", list(op_cli.keys()), disabled=not is_vinc, label_visibility="collapsed", key="cap_cli_sel")
    
    st.markdown("##### 📅 Opções de Parcelamento / Recorrência")
    col_p1, col_p2, col_p3 = st.columns([1, 1.5, 1.5])
    n_parcelas = col_p1.number_input("Nº de Parcelas", min_value=1, max_value=36, value=1, step=1, key="cap_num_parcelas")
    
    periodicidade = "Mensal (Mesmo dia do mês)"
    dias_intervalo = 30
    if n_parcelas > 1:
        periodicidade = col_p2.selectbox("Periodicidade", ["Mensal (Mesmo dia do mês)", "A cada X dias"], key="cap_periodicidade")
        if periodicidade == "A cada X dias":
            dias_intervalo = col_p3.number_input("Dias entre parcelas", min_value=1, max_value=365, value=30, step=1, key="cap_dias_intervalo")
        
        preview_data = []
        for i in range(n_parcelas):
            if periodicidade == "Mensal (Mesmo dia do mês)":
                dt_venc = add_months(venc_p, i)
            else:
                dt_venc = venc_p + timedelta(days=dias_intervalo * i)
            preview_data.append({
                "Parcela": f"{i+1}/{n_parcelas}",
                "Vencimento": dt_venc.strftime("%d/%m/%Y"),
                "Valor": f"R$ {val_p:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            })
        
        st.info(f"💰 **Total a ser lançado:** {n_parcelas} parcelas de R$ {val_p:,.2f} = **R$ {val_p * n_parcelas:,.2f}**")
        st.markdown("**Prévia das Parcelas:**")
        st.dataframe(pd.DataFrame(preview_data), hide_index=True, use_container_width=True)
    
    if st.button("Salvar Duplicata a Pagar", type="primary", use_container_width=True):
        if st.session_state.get("cap_clique_bloqueado", False):
            st.warning("Gravação já em andamento. Aguarde...")
        elif forn_sel == "-- SELECIONE O FORNECEDOR --" and not is_vinc:
            st.error("Por favor, selecione um Fornecedor ou marque a caixinha de Cliente Vinculado.")
        elif is_vinc and cli_sel == "-- SELECIONE O CLIENTE --":
            st.error("Por favor, selecione um Cliente Vinculado.")
        elif pc_sel == "-- SELECIONE O PLANO DE CONTAS --":
            st.error("Por favor, selecione um Plano de Contas.")
        elif not desc_p:
            st.error("Preencha a descrição do lançamento.")
        else:
            pc_id, pc_codigo = op_pc[pc_sel]
            forn_id = op_forn[forn_sel] if forn_sel != "-- SELECIONE O FORNECEDOR --" else None
            cli_id = op_cli[cli_sel] if is_vinc else None
            
            if pc_codigo in ('2.2.1', '2.2.2', '2.2.4') and cli_id is None:
                st.error(f"A conta selecionada ({pc_sel}) exige a vinculação obrigatória de um Cliente (CNPJ).")
            elif forn_id is None and cli_id is None:
                st.error("Por favor, selecione um Fornecedor ou um Cliente Vinculado.")
            else:
                st.session_state["cap_clique_bloqueado"] = True
                with st.spinner("Registrando duplicatas a pagar..."):
                    for i in range(n_parcelas):
                        if periodicidade == "Mensal (Mesmo dia do mês)":
                            dt_venc = add_months(venc_p, i)
                        else:
                            dt_venc = venc_p + timedelta(days=dias_intervalo * i)
                            
                        desc_final = f"{desc_p} ({i+1}/{n_parcelas})" if n_parcelas > 1 else desc_p
                        
                        run_query(
                            "INSERT INTO contas_a_pagar (fornecedor_id, plano_conta_id, cliente_id, numero_documento, descricao, valor, data_vencimento, data_emissao, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDENTE')",
                            (forn_id, pc_id, cli_id, num_doc_p, desc_final, val_p, dt_venc.strftime("%Y-%m-%d"), dt_emissao_p.strftime("%Y-%m-%d"))
                        )
                
                st.session_state["cap_clique_bloqueado"] = False
                st.session_state["cap_limpar_formulario"] = True
                
                if n_parcelas > 1:
                    st.success(f"✅ {n_parcelas} duplicatas a pagar lançadas com sucesso!")
                else:
                    st.success("✅ Duplicata a Pagar lançada com sucesso!")
                import time; time.sleep(1); st.rerun()

@st.dialog("Confirmar Liquidação (Pagamento)", width="large")
def dialog_confirmar_baixa_lote_pagar(ids_selecionados, df_all_contas, opcoes_bancos):
    st.write(f"Você selecionou **{len(ids_selecionados)}** duplicata(s) para baixar.")
    
    df_selecionadas = df_all_contas[df_all_contas['id'].isin(ids_selecionados)]
    total = df_selecionadas['Valor'].sum()
    
    st.metric("Total Selecionado", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    op_bancos = {"-- SELECIONE A CONTA BANCÁRIA --": None}
    op_bancos.update(opcoes_bancos)

    colA, colB = st.columns(2)
    d_pgto = colA.date_input("Data real do Pagamento", date.today())
    conta_saida = colB.selectbox("Sair de qual banco/conta?", list(op_bancos.keys()))
    
    # Lógica de Baixa Parcial
    valor_pago = total
    is_partial = False
    if len(ids_selecionados) == 1:
        st.markdown("---")
        is_partial = st.checkbox("Pagamento Parcial? (Baixar apenas uma parte do valor)")
        if is_partial:
            valor_pago = st.number_input("Valor Pago (R$)", min_value=0.01, max_value=float(total) - 0.01, value=float(total) * 0.5, step=10.0)
            saldo = float(total) - valor_pago
            st.info(f"ℹ️ O título original de R$ {total:,.2f} será desmembrado: R$ {valor_pago:,.2f} será liquidado e o saldo restante de R$ {saldo:,.2f} continuará pendente.")
            
    if st.button("💸 Confirmar Liquidação", type="primary", use_container_width=True):
        if conta_saida == "-- SELECIONE A CONTA BANCÁRIA --" or conta_saida not in opcoes_bancos:
            st.error("Por favor, selecione a Conta Bancária de saída para realizar a baixa.")
        else:
            conta_id = opcoes_bancos[conta_saida]
        
        for _, r in df_selecionadas.iterrows():
            c_id = int(r['id'])
            v_base = float(r['Valor'])
            
            # Obtém o credor unificado de forma resiliente
            credor = r.get('Credor', r.get('Fornecedor', ''))
            credor = str(credor) if pd.notna(credor) else ""
            
            # Obtém histórico e planta de custo de forma resiliente para evitar KeyError
            fat = r.get('Histórico', r.get('Descrição/Fatura', ''))
            plant = r.get('Planta de Custo', r.get('Categoria', 'Gasto'))
            
            # Limpa tag de bloqueio do nome
            credor = credor.replace("🔴 [BLOQUEADO FALTAM CANHOTOS] ", "")
            
            df_cap_cli = fetch_all("SELECT cliente_id FROM contas_a_pagar WHERE id=?", (c_id,))
            cap_cli_id = int(df_cap_cli.iloc[0]['cliente_id']) if not df_cap_cli.empty and pd.notna(df_cap_cli.iloc[0]['cliente_id']) else None

            val_efetivo = valor_pago if is_partial else v_base
            
            if is_partial:
                saldo = v_base - val_efetivo
                df_orig = fetch_all("SELECT * FROM contas_a_pagar WHERE id = ?", (c_id,))
                if not df_orig.empty:
                    orig = df_orig.iloc[0]
                    forn_id_orig = int(orig['fornecedor_id']) if pd.notna(orig['fornecedor_id']) else None
                    pc_id_orig = int(orig['plano_conta_id']) if pd.notna(orig['plano_conta_id']) else None
                    desc_orig = orig['descricao'] if pd.notna(orig['descricao']) else ""
                    venc_orig = orig['data_vencimento']
                    doc_orig = orig['numero_documento'] if pd.notna(orig['numero_documento']) else None
                    cli_id_orig = int(orig['cliente_id']) if pd.notna(orig['cliente_id']) else None
                    
                    # Insere o saldo restante
                    run_query("INSERT INTO contas_a_pagar (fornecedor_id, plano_conta_id, descricao, valor, data_vencimento, status, numero_documento, cliente_id) VALUES (?, ?, ?, ?, ?, 'PENDENTE', ?, ?)",
                              (forn_id_orig, pc_id_orig, f"{desc_orig} (Saldo Parcial)", saldo, venc_orig, doc_orig, cli_id_orig))

            run_query("UPDATE contas_a_pagar SET status='PAGO', data_pagamento=?, conta_bancaria_id=?, valor=? WHERE id=?", 
                      (d_pgto.strftime("%Y-%m-%d"), conta_id, val_efetivo, c_id))
            
            run_query("INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, fonte_id, conta_bancaria_id, conciliado, cliente_id) VALUES (?, 'Saída', ?, ?, ?, ?, ?, FALSE, ?)",
                      (d_pgto.strftime("%Y-%m-%d"), plant, f"PGTO Credor: {credor} - Fat: {fat}", val_efetivo, c_id, conta_id, cap_cli_id))
                      
        st.success(f"✔️ {len(df_selecionadas)} contas liquidadas e debitadas do banco {conta_saida} com sucesso!")
        import time; time.sleep(1.5); st.rerun()

@st.dialog("Renegociar com Fornecedor", width="large")
def dialog_renegociar_pagar():
    df_forn_devedores = fetch_all("""
        SELECT DISTINCT f.id, f.nome_fantasia, f.nome 
        FROM contas_a_pagar c
        JOIN fornecedores f ON c.fornecedor_id = f.id
        WHERE c.status = 'PENDENTE'
        ORDER BY f.nome_fantasia
    """)
    
    if df_forn_devedores.empty:
        st.info("Não há fornecedores com contas pendentes para renegociação.")
        return
        
    opcoes_forn_devedores = {}
    for _, r in df_forn_devedores.iterrows():
        lbl = r['nome_fantasia'] if pd.notna(r['nome_fantasia']) and r['nome_fantasia'].strip() else r['nome']
        opcoes_forn_devedores[lbl] = r['id']
        
    forn_renome = st.selectbox("Selecione o Fornecedor:", ["-- SELECIONE --"] + list(opcoes_forn_devedores.keys()), key="reneg_forn_sel")
    
    if forn_renome != "-- SELECIONE --":
        f_id_reneg = opcoes_forn_devedores[forn_renome]
        df_pend_reneg_f = fetch_all("""
            SELECT id, descricao, valor, data_vencimento, plano_conta_id, compra_id 
            FROM contas_a_pagar 
            WHERE fornecedor_id=? AND status='PENDENTE' 
            ORDER BY data_vencimento ASC
        """, (f_id_reneg,))
        
        if df_pend_reneg_f.empty:
            st.info("Este fornecedor não possui contas pendentes.")
        else:
            df_pend_reneg_f['venc_f'] = pd.to_datetime(df_pend_reneg_f['data_vencimento']).dt.strftime('%d/%m/%Y')
            opts_titulos_f = {}
            for _, r in df_pend_reneg_f.iterrows():
                lbl = f"ID #{r['id']} | {r['descricao']} | Venc: {r['venc_f']} | R$ {r['valor']:,.2f}"
                opts_titulos_f[lbl] = r
            
            selec_titulos_lbls_f = st.multiselect(
                "Selecione os boletos a consolidar:",
                options=list(opts_titulos_f.keys()),
                default=list(opts_titulos_f.keys()),
                key="reneg_titulos_forn_sel"
            )
            
            if selec_titulos_lbls_f:
                titulos_para_acordo_f = [opts_titulos_f[lbl] for lbl in selec_titulos_lbls_f]
                soma_original_f = sum(float(t['valor']) for t in titulos_para_acordo_f)
                
                st.metric("Total da Dívida Consolidada (Original)", f"R$ {soma_original_f:,.2f}")
                
                col_ref1, col_ref2 = st.columns(2)
                novo_valor_acordo_f = col_ref1.number_input("Novo Valor Acordado (R$)", min_value=0.01, value=soma_original_f, step=0.01)
                
                df_fps = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
                fps_dict = {r['nome']: r for _, r in df_fps.iterrows()}
                forma_pag_acordo_f = col_ref2.selectbox("Nova Condição de Pagamento:", list(fps_dict.keys()))
                
                rule_str_f = fps_dict[forma_pag_acordo_f]['parcelas']
                dias_list_f = [int(n) for n in re.findall(r'\d+', rule_str_f)]
                if not dias_list_f: dias_list_f = [0]
                
                N_f = len(dias_list_f)
                val_pf = round(novo_valor_acordo_f / N_f, 2)
                diff_pf = round(novo_valor_acordo_f - val_pf * N_f, 2)
                
                data_base_acordo_f = st.date_input("Data Base para Vencimento das Parcelas:", value=date.today())
                
                preview_reneg_f = []
                for i, dias in enumerate(dias_list_f):
                    v_p = val_pf + (diff_pf if i == N_f - 1 else 0.0)
                    dt_v = data_base_acordo_f + timedelta(days=dias)
                    preview_reneg_f.append({
                        "Parcela": f"{i+1}/{N_f}", "Vencimento": dt_v.strftime("%d/%m/%Y"), "Valor": f"R$ {v_p:,.2f}", "valor_num": v_p, "venc_date": dt_v
                    })
                
                st.markdown("**Prévia do Novo Parcelamento:**")
                st.dataframe(pd.DataFrame(preview_reneg_f)[["Parcela", "Vencimento", "Valor"]], hide_index=True, use_container_width=True)
                
                desc_acordo_f = st.text_input("Descrição / Motivo do Acordo (opcional):", value="Acordo de Renegociação de Contas a Pagar")
                
                if st.button("Confirmar Acordo de Renegociação", type="primary", use_container_width=True):
                    with st.spinner("Processando..."):
                        acordo_id_f = str(uuid.uuid4())[:8].upper()
                        ids_cancelar_f = [int(t['id']) for t in titulos_para_acordo_f]
                        nota_cancelamento_f = f" [RENEGOCIADO - Acordo #{acordo_id_f}]"
                        
                        for t_id in ids_cancelar_f:
                            run_query("UPDATE contas_a_pagar SET status='CANCELADO', descricao = descricao || ? WHERE id=?", (nota_cancelamento_f, t_id))
                        
                        for i, p_info in enumerate(preview_reneg_f):
                            nova_desc = f"{desc_acordo_f} (Acordo #{acordo_id_f} - Parcela {p_info['Parcela']})"
                            venc_str = p_info['venc_date'].strftime("%Y-%m-%d")
                            val_num = p_info['valor_num']
                            
                            p_c_id_default = titulos_para_acordo_f[0].get('plano_conta_id')
                            if not p_c_id_default or pd.isna(p_c_id_default):
                                df_forn_pc = fetch_all("SELECT plano_conta_id FROM fornecedores WHERE id = ?", (f_id_reneg,))
                                if not df_forn_pc.empty and pd.notna(df_forn_pc.iloc[0]['plano_conta_id']):
                                    p_c_id_default = int(df_forn_pc.iloc[0]['plano_conta_id'])
                            if not p_c_id_default or pd.isna(p_c_id_default):
                                p_c_acordo = fetch_all("SELECT id FROM planos_de_contas WHERE categoria NOT IN ('RECEITA', 'RECEITA_NAO_OP') LIMIT 1")
                                p_c_id_default = int(p_c_acordo.iloc[0]['id']) if not p_c_acordo.empty else None
                                
                            compra_id_default = titulos_para_acordo_f[0].get('compra_id')
                            
                            run_query(
                                "INSERT INTO contas_a_pagar (fornecedor_id, plano_conta_id, compra_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                (f_id_reneg, int(p_c_id_default) if pd.notna(p_c_id_default) else None, int(compra_id_default) if pd.notna(compra_id_default) else None, nova_desc, val_num, venc_str)
                            )
                            
                    st.success(f"🤝 Renegociação concluída! Acordo #{acordo_id_f} registrado.")
                    import time; time.sleep(1.5); st.rerun()

@st.dialog("Editar Duplicata a Pagar", width="large")
def dialog_editar_pagar(id_selecionado):
    dup_data = fetch_all("SELECT * FROM contas_a_pagar WHERE id=?", (id_selecionado,)).iloc[0]
    valor_original = float(dup_data['valor'])

    acao = st.radio("O que deseja fazer?", ["Alterar Vencimento/Valor", "Aplicar Juros / Desconto", "Reparcelar", "Excluir/Cancelar"], horizontal=True)

    if acao == "Alterar Vencimento/Valor":
        ed1, ed2 = st.columns(2)
        novo_venc = ed1.date_input("Novo Vencimento", value=pd.to_datetime(dup_data['data_vencimento']).date())
        novo_valor = ed2.number_input("Novo Valor (R$)", value=valor_original, min_value=0.01)
        novo_doc = st.text_input("Nº Documento", value=dup_data["numero_documento"] if dup_data["numero_documento"] else "")
        nova_desc = st.text_input("Descrição", value=dup_data['descricao'])
        if st.button("Salvar Alteração", type="primary"):
            run_query("UPDATE contas_a_pagar SET data_vencimento=?, valor=?, descricao=?, numero_documento=? WHERE id=?",
                        (novo_venc.strftime("%Y-%m-%d"), novo_valor, nova_desc, novo_doc, id_selecionado))
            st.success("Duplicata atualizada!")
            import time; time.sleep(1); st.rerun()

    elif acao == "Aplicar Juros / Desconto":
        st.markdown(f"**Valor original:** R$ {valor_original:,.2f}")
        jd1, jd2, jd3 = st.columns(3)
        juros_pct = jd1.number_input("Juros (%)", min_value=0.0, value=0.0, step=0.5)
        desconto_rs = jd2.number_input("Desconto (R$)", min_value=0.0, value=0.0, step=0.01)
        valor_juros = valor_original * (juros_pct / 100)
        valor_final = valor_original + valor_juros - desconto_rs
        jd3.metric("Valor Final", f"R$ {valor_final:,.2f}")

        if valor_final <= 0:
            st.error("O valor final não pode ser zero ou negativo.")
        else:
            novo_venc_jd = st.date_input("Novo Vencimento", value=pd.to_datetime(dup_data['data_vencimento']).date())
            obs_juros = f" [Juros {juros_pct}%: +R${valor_juros:,.2f}]" if juros_pct > 0 else ""
            obs_desc = f" [Desc: -R${desconto_rs:,.2f}]" if desconto_rs > 0 else ""
            if st.button("Aplicar Juros/Desconto", type="primary"):
                nova_descricao = dup_data['descricao'] + obs_juros + obs_desc
                run_query("UPDATE contas_a_pagar SET data_vencimento=?, valor=?, descricao=? WHERE id=?",
                            (novo_venc_jd.strftime("%Y-%m-%d"), valor_final, nova_descricao, id_selecionado))
                st.success(f"Duplicata atualizada! Novo valor: R$ {valor_final:,.2f}")
                import time; time.sleep(1); st.rerun()

    elif acao == "Reparcelar":
        st.markdown(f"**Valor original a reparcelar:** R$ {valor_original:,.2f}")
        rp1, rp2 = st.columns(2)
        n_parc = rp1.number_input("Nº de Parcelas", min_value=2, value=2, step=1)
        data_inicio = st.date_input("Data da 1ª Parcela", value=date.today())
        
        rp3, rp4 = st.columns(2)
        periodicidade_rp = rp3.selectbox("Periodicidade", ["Mensal (Mesmo dia do mês)", "A cada X dias"])
        dias_entre = 30
        if periodicidade_rp == "A cada X dias":
            dias_entre = rp4.number_input("Dias entre Parcelas", min_value=1, value=30, step=1)

        valor_parc = round(valor_original / n_parc, 2)
        diff_parc = round(valor_original - valor_parc * n_parc, 2)
        
        preview = []
        for i in range(n_parc):
            v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
            if periodicidade_rp == "Mensal (Mesmo dia do mês)":
                d = add_months(data_inicio, i)
            else:
                d = data_inicio + timedelta(days=dias_entre * i)
            preview.append({"Parcela": f"{i+1}/{n_parc}", "Vencimento": d.strftime("%d/%m/%Y"), "Valor": f"R$ {v:,.2f}"})
        st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)

        if st.button("Confirmar Reparcelamento", type="primary"):
            run_query("UPDATE contas_a_pagar SET status='CANCELADO', descricao = descricao || ' [REPARCELADO]' WHERE id=?", (id_selecionado,))
            for i in range(n_parc):
                v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                if periodicidade_rp == "Mensal (Mesmo dia do mês)":
                    d = add_months(data_inicio, i)
                else:
                    d = data_inicio + timedelta(days=dias_entre * i)
                nova_desc_rp = f"{dup_data['descricao']} (Repar. {i+1}/{n_parc})"
                p_c_id_rp = int(dup_data['plano_conta_id']) if pd.notna(dup_data['plano_conta_id']) else None
                if not p_c_id_rp:
                    if pd.notna(dup_data['fornecedor_id']):
                        df_forn_pc = fetch_all("SELECT plano_conta_id FROM fornecedores WHERE id=?", (int(dup_data['fornecedor_id']),))
                        if not df_forn_pc.empty and pd.notna(df_forn_pc.iloc[0]['plano_conta_id']):
                            p_c_id_rp = int(df_forn_pc.iloc[0]['plano_conta_id'])
                if not p_c_id_rp:
                    p_c_acordo = fetch_all("SELECT id FROM planos_de_contas WHERE categoria NOT IN ('RECEITA', 'RECEITA_NAO_OP') LIMIT 1")
                    p_c_id_rp = int(p_c_acordo.iloc[0]['id']) if not p_c_acordo.empty else None

                run_query(
                    "INSERT INTO contas_a_pagar (fornecedor_id, compra_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                    (int(dup_data['fornecedor_id']) if pd.notna(dup_data['fornecedor_id']) else None,
                     int(dup_data['compra_id']) if pd.notna(dup_data['compra_id']) else None,
                     p_c_id_rp, nova_desc_rp, v, d.strftime("%Y-%m-%d")))
            st.success(f"Reparcelamento concluído! {n_parc} novas duplicatas criadas.")
            import time; time.sleep(1); st.rerun()

    elif acao == "Excluir/Cancelar":
        st.markdown("**Tem certeza que deseja cancelar/excluir este recebível?**")
        st.markdown("Esta ação mudará o status do recebível para `'CANCELADO'`.")
        if st.button("Confirmar Cancelamento", type="primary"):
            run_query("UPDATE contas_a_pagar SET status='CANCELADO', descricao = descricao || ' [CANCELADO]' WHERE id=?", (id_selecionado,))
            st.success("Cancelado com sucesso!")
            import time; time.sleep(1); st.rerun()


# ==============================================================================
# MODAIS DE CONTAS A RECEBER
# ==============================================================================

@st.dialog("Lançar uma Duplicata a Receber", width="large")
def dialog_lancar_receber():
    df_cli = fetch_all("SELECT id, nome, plano_conta_id FROM clientes ORDER BY nome")
    op_cli = {"-- SELECIONE O CLIENTE --": "placeholder", "Genérico / Não Cadastrado": None}
    cli_pc_map = {}
    if not df_cli.empty:
        for _, r in df_cli.iterrows():
            op_cli[r['nome']] = r['id']
            cli_pc_map[r['id']] = r['plano_conta_id']
        
    df_planos = fetch_all("SELECT id, codigo, nome FROM planos_de_contas WHERE categoria IN ('RECEITA', 'RECEITA_NAO_OP') ORDER BY codigo")
    op_plan = {"-- SELECIONE O PLANO DE CONTAS --": None}
    if not df_planos.empty:
        for _, r in df_planos.iterrows():
            op_plan[f"{r['codigo']} - {r['nome']}"] = r['id']
            
    if st.session_state.get("car_limpar_formulario", False):
        st.session_state["car_cli_sel"] = list(op_cli.keys())[0]
        st.session_state["car_pc_sel"] = list(op_plan.keys())[0]
        st.session_state["car_num_doc_r"] = ""
        st.session_state["car_desc"] = ""
        st.session_state["car_val_r"] = 0.01
        st.session_state["car_venc"] = date.today() + timedelta(days=15)
        st.session_state["car_prev_cli"] = list(op_cli.keys())[0]
        st.session_state["car_limpar_formulario"] = False

    if "car_cli_sel" not in st.session_state:
        st.session_state["car_cli_sel"] = list(op_cli.keys())[0]
    if "car_pc_sel" not in st.session_state:
        st.session_state["car_pc_sel"] = list(op_plan.keys())[0]
    if "car_prev_cli" not in st.session_state:
        st.session_state["car_prev_cli"] = list(op_cli.keys())[0]

    # Detect change of client to auto-fill Plano de Contas
    if st.session_state.get("car_cli_sel") != st.session_state["car_prev_cli"]:
        st.session_state["car_prev_cli"] = st.session_state.get("car_cli_sel")
        cli_name = st.session_state.get("car_cli_sel")
        cli_id_val = op_cli.get(cli_name)
        if cli_id_val and cli_id_val != "placeholder":
            pc_id_default = cli_pc_map.get(cli_id_val)
            if pc_id_default:
                for pc_key, pc_val_id in op_plan.items():
                    if pc_val_id == pc_id_default:
                        st.session_state["car_pc_sel"] = pc_key
                        break
        
    c1, c2, c3, c3_e = st.columns(4)
    cli_nome = c1.selectbox("Cliente", list(op_cli.keys()), key="car_cli_sel")
    plan_sel = c2.selectbox("Plano de Contas", list(op_plan.keys()), key="car_pc_sel")
    dt_emissao = c3_e.date_input("Data de Emissão", value=date.today(), key="car_dt_emissao")
    venc = c3.date_input("Vencimento", value=st.session_state.get("car_venc", date.today() + timedelta(days=15)), key="car_venc")
    
    c4, c5, c6 = st.columns([1, 2, 1])
    num_doc_r = c4.text_input("Nº Documento (Opcional)", value=st.session_state.get("car_num_doc_r", ""), key="car_num_doc_r")
    desc = c5.text_input("Fatura (Referência)", value=st.session_state.get("car_desc", ""), key="car_desc")
    val_r = c6.number_input("Valor da Fatura (R$)", min_value=0.01, value=st.session_state.get("car_val_r", 0.01), key="car_val_r")
    
    if st.button("Lançar Promessa de Faturamento", type="primary", use_container_width=True):
        if cli_nome == "-- SELECIONE O CLIENTE --":
            st.error("Por favor, selecione um Cliente (ou 'Genérico / Não Cadastrado').")
        elif plan_sel == "-- SELECIONE O PLANO DE CONTAS --":
            st.error("Por favor, selecione um Plano de Contas.")
        elif not desc:
            st.error("Preencha a descrição.")
        else:
            with st.spinner("Registrando recebível..."):
                run_query("INSERT INTO contas_a_receber (cliente_id, plano_conta_id, numero_documento, descricao, valor, data_emissao, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDENTE')",
                          (op_cli[cli_nome], op_plan[plan_sel], num_doc_r, desc, val_r, dt_emissao.strftime("%Y-%m-%d"), venc.strftime("%Y-%m-%d")))
            st.session_state["car_limpar_formulario"] = True
            st.success("Boleto emitido (pendente)")
            import time; time.sleep(1); st.rerun()

@st.dialog("Fechamento Semanal de Carteira", width="large")
def dialog_fechamento_carteira():
    df_clientes_pendentes = fetch_all("""
        SELECT DISTINCT cl.id, cl.nome 
        FROM contas_a_receber c
        JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.status = 'PENDENTE'
    """)
    
    if df_clientes_pendentes.empty:
        st.info("Não há nenhum cliente com saldo devedor/faturas pendentes.")
        return
        
    opcoes_cli_pend = {r['nome']: r['id'] for _, r in df_clientes_pendentes.iterrows()}
    cli_fechamento = st.selectbox("Selecione o Cliente para Fechamento:", ["-- SELECIONE --"] + list(opcoes_cli_pend.keys()))
    
    if cli_fechamento != "-- SELECIONE --":
        c_id_fech = opcoes_cli_pend[cli_fechamento]
        df_fat_cli = fetch_all("SELECT id, descricao, valor, data_vencimento FROM contas_a_receber WHERE cliente_id=? AND status='PENDENTE' ORDER BY data_vencimento ASC", (c_id_fech,))
        
        st.markdown(f"**Títulos Pendentes: {cli_fechamento}**")
        df_fat_cli['Gerar no Relatório?'] = True
        df_fat_cli['data_vencimento_original'] = pd.to_datetime(df_fat_cli['data_vencimento']).dt.strftime('%d/%m/%Y')
        
        df_view_fech = df_fat_cli[['Gerar no Relatório?', 'id', 'descricao', 'data_vencimento_original', 'valor']]
        
        edited_fech = st.data_editor(df_view_fech, hide_index=True, width="stretch",
                                        column_config={
                                            "Gerar no Relatório?": st.column_config.CheckboxColumn("Incluir?", default=True),
                                            "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f")
                                        })
        
        selecionados_fech = edited_fech[edited_fech['Gerar no Relatório?'] == True]
        
        if not selecionados_fech.empty:
            total_fech = selecionados_fech['valor'].sum()
            
            col_fa, col_fb = st.columns([1, 1])
            dt_pgto_estimada = col_fa.date_input("Data de Vencimento/Acerto Combinada para o Extrato:", date.today())
            
            if col_fb.button("🖨️ Gerar Extrato de Fechamento (A4)", type="primary", use_container_width=True):
                from utils_carteira import gerar_html_carteira
                import streamlit.components.v1 as components
                
                faturas_list = selecionados_fech.to_dict('records')
                
                html_carteira = gerar_html_carteira(
                    cliente_nome=cli_fechamento,
                    dados_faturas=faturas_list,
                    total_faturas=total_fech,
                    data_pagamento_estimada=dt_pgto_estimada.strftime('%d/%m/%Y')
                )
                components.html(html_carteira, height=800, scrolling=True)
                st.success(f"Extrato gerado com sucesso! Total: R$ {total_fech:,.2f}")

@st.dialog("Renegociar Dívida de Cliente", width="large")
def dialog_renegociar_receber():
    df_cli_devedores = fetch_all("""
        SELECT DISTINCT cl.id, cl.nome 
        FROM contas_a_receber c
        JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.status = 'PENDENTE'
        ORDER BY cl.nome
    """)
    
    if df_cli_devedores.empty:
        st.info("Não há clientes com faturas pendentes para renegociação.")
        return
        
    opcoes_devedores = {r['nome']: r['id'] for _, r in df_cli_devedores.iterrows()}
    cli_renome = st.selectbox("Selecione o Cliente para Renegociar:", ["-- SELECIONE --"] + list(opcoes_devedores.keys()), key="reneg_cli_sel")
    
    if cli_renome != "-- SELECIONE --":
        c_id_reneg = opcoes_devedores[cli_renome]
        df_pend_reneg = fetch_all("""
            SELECT id, descricao, valor, data_vencimento, plano_conta_id 
            FROM contas_a_receber 
            WHERE cliente_id=? AND status='PENDENTE' 
            ORDER BY data_vencimento ASC
        """, (c_id_reneg,))
        
        if df_pend_reneg.empty:
            st.info("Este cliente não possui faturas pendentes.")
        else:
            df_pend_reneg['venc_f'] = pd.to_datetime(df_pend_reneg['data_vencimento']).dt.strftime('%d/%m/%Y')
            opts_titulos = {}
            for _, r in df_pend_reneg.iterrows():
                lbl = f"ID #{r['id']} | {r['descricao']} | Venc: {r['venc_f']} | R$ {r['valor']:,.2f}"
                opts_titulos[lbl] = r
            
            selec_titulos_lbls = st.multiselect(
                "Selecione as faturas a consolidar no acordo:",
                options=list(opts_titulos.keys()),
                default=list(opts_titulos.keys()),
                key="reneg_titulos_sel"
            )
            
            if selec_titulos_lbls:
                titulos_para_acordo = [opts_titulos[lbl] for lbl in selec_titulos_lbls]
                soma_original = sum(float(t['valor']) for t in titulos_para_acordo)
                
                st.metric("Total da Dívida Consolidada (Original)", f"R$ {soma_original:,.2f}")
                
                col_re1, col_re2 = st.columns(2)
                novo_valor_acordo = col_re1.number_input("Novo Valor Acordado (R$)", min_value=0.01, value=soma_original, step=0.01)
                
                df_fps = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
                fps_dict = {r['nome']: r for _, r in df_fps.iterrows()}
                forma_pag_acordo = col_re2.selectbox("Nova Condição de Pagamento:", list(fps_dict.keys()))
                
                rule_str = fps_dict[forma_pag_acordo]['parcelas']
                dias_list = [int(n) for n in re.findall(r'\d+', rule_str)]
                if not dias_list: dias_list = [0]
                
                N = len(dias_list)
                val_p = round(novo_valor_acordo / N, 2)
                diff_p = round(novo_valor_acordo - val_p * N, 2)
                
                data_base_acordo = st.date_input("Data Base para Vencimento das Parcelas:", value=date.today())
                
                preview_reneg = []
                for i, dias in enumerate(dias_list):
                    v_p = val_p + (diff_p if i == N - 1 else 0.0)
                    dt_v = data_base_acordo + timedelta(days=dias)
                    preview_reneg.append({
                        "Parcela": f"{i+1}/{N}", "Vencimento": dt_v.strftime("%d/%m/%Y"), "Valor": f"R$ {v_p:,.2f}", "valor_num": v_p, "venc_date": dt_v
                    })
                
                st.markdown("**Prévia do Novo Parcelamento:**")
                st.dataframe(pd.DataFrame(preview_reneg)[["Parcela", "Vencimento", "Valor"]], hide_index=True, use_container_width=True)
                
                desc_acordo = st.text_input("Descrição / Motivo do Acordo (opcional):", value="Acordo de Renegociação de Dívida")
                
                if st.button("Confirmar Acordo de Renegociação", type="primary", use_container_width=True):
                    with st.spinner("Processando..."):
                        acordo_id = str(uuid.uuid4())[:8].upper()
                        ids_cancelar = [int(t['id']) for t in titulos_para_acordo]
                        nota_cancelamento = f" [RENEGOCIADO - Acordo #{acordo_id}]"
                        
                        for t_id in ids_cancelar:
                            run_query("UPDATE contas_a_receber SET status='CANCELADO', descricao = descricao || ? WHERE id=?", (nota_cancelamento, t_id))
                        
                        p_c_id_default_r = titulos_para_acordo[0].get('plano_conta_id') if hasattr(titulos_para_acordo[0], 'get') else None
                        if not p_c_id_default_r or pd.isna(p_c_id_default_r):
                            p_c_rec = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
                            p_c_id_default_r = int(p_c_rec.iloc[0]['id']) if not p_c_rec.empty else None

                        for i, p_info in enumerate(preview_reneg):
                            nova_desc = f"{desc_acordo} (Acordo #{acordo_id} - Parcela {p_info['Parcela']})"
                            venc_str = p_info['venc_date'].strftime("%Y-%m-%d")
                            dt_emissao_acordo = date.today().strftime("%Y-%m-%d")
                            val_num = p_info['valor_num']
                            
                            run_query(
                                "INSERT INTO contas_a_receber (cliente_id, plano_conta_id, descricao, valor, data_emissao, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                (c_id_reneg, p_c_id_default_r, nova_desc, val_num, dt_emissao_acordo, venc_str)
                            )
                            
                    st.success(f"🤝 Renegociação concluída! Acordo #{acordo_id} registrado.")
                    import time; time.sleep(1.5); st.rerun()

def primeiro_valor_valido(row, campos, default=""):
    for campo in campos:
        valor = row.get(campo)
        if pd.notna(valor):
            valor_str = str(valor).strip()
            if valor_str and valor_str != "None":
                return valor_str
    return default

@st.dialog("Confirmar Recebimento", width="large")
def dialog_confirmar_baixa_lote_receber(ids_selecionados, df_receber, opcoes_bancos):
    st.write(f"Você selecionou **{len(ids_selecionados)}** título(s) para recebimento.")
    
    df_selecionadas = df_receber[df_receber['id'].isin(ids_selecionados)]
    total = df_selecionadas['Valor'].sum()
    
    st.metric("Total Selecionado", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    rA, rB = st.columns(2)
    dt_rec = rA.date_input("Data que o dinheiro caiu", date.today())
    banco_destino = rB.selectbox("PAGO EM QUAL BANCO?", list(opcoes_bancos.keys()))
    
    # Lógica de Baixa Parcial
    valor_pago = total
    is_partial = False
    if len(ids_selecionados) == 1:
        st.markdown("---")
        is_partial = st.checkbox("Recebimento Parcial? (Baixar apenas uma parte do valor)")
        if is_partial:
            valor_pago = st.number_input("Valor Recebido (R$)", min_value=0.01, max_value=float(total) - 0.01, value=float(total) * 0.5, step=10.0)
            saldo = float(total) - valor_pago
            st.info(f"ℹ️ O título original de R$ {total:,.2f} será desmembrado: R$ {valor_pago:,.2f} será recebido e o saldo restante de R$ {saldo:,.2f} continuará pendente.")
            
    if st.button("💸 Confirmar Recebimento", type="primary", use_container_width=True):
        if not banco_destino or banco_destino not in opcoes_bancos:
            st.error("Por favor, selecione uma Conta Bancária de Destino válida.")
        else:
            bCid = opcoes_bancos[banco_destino]
            
            for _, r in df_selecionadas.iterrows():
                rr_id = int(r['id'])
                v_base = float(r['Valor'])
                cli = primeiro_valor_valido(r, ['Cliente', 'Cliente_Fantasia', 'Cliente_Razao'], 'Diversos')
                fat = primeiro_valor_valido(r, ['N. Doc', 'Histórico'], '')
                
                val_efetivo = valor_pago if is_partial else v_base
                
                if is_partial:
                    saldo = v_base - val_efetivo
                    df_orig = fetch_all("SELECT * FROM contas_a_receber WHERE id = ?", (rr_id,))
                    if not df_orig.empty:
                        orig = df_orig.iloc[0]
                        c_id_orig = int(orig['cliente_id']) if pd.notna(orig['cliente_id']) else None
                        v_id_orig = int(orig['venda_id']) if pd.notna(orig['venda_id']) else None
                        pc_id_orig = int(orig['plano_conta_id']) if pd.notna(orig['plano_conta_id']) else None
                        desc_orig = orig['descricao'] if pd.notna(orig['descricao']) else ""
                        venc_orig = orig['data_vencimento']
                        dt_emissao_orig = orig['data_emissao'] if 'data_emissao' in orig and pd.notna(orig['data_emissao']) else date.today().strftime("%Y-%m-%d")
                        doc_orig = orig['numero_documento'] if pd.notna(orig['numero_documento']) else None
                        
                        # Insere o saldo restante
                        run_query("INSERT INTO contas_a_receber (cliente_id, venda_id, plano_conta_id, descricao, valor, data_emissao, data_vencimento, status, numero_documento) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDENTE', ?)",
                                  (c_id_orig, v_id_orig, pc_id_orig, f"{desc_orig} (Saldo Parcial)", saldo, dt_emissao_orig, venc_orig, doc_orig))
                
                # Atualiza o original com val_efetivo
                run_query("UPDATE contas_a_receber SET status='RECEBIDO', data_recebimento=?, conta_bancaria_id=?, valor=? WHERE id=?",
                          (dt_rec.strftime("%Y-%m-%d"), bCid, val_efetivo, rr_id))
                
                df_v = fetch_all("SELECT venda_id FROM contas_a_receber WHERE id = ?", (rr_id,))
                if not df_v.empty and pd.notna(df_v.iloc[0]['venda_id']):
                    vid = int(df_v.iloc[0]['venda_id'])
                    gerar_comissao_se_necessario(vid, 'LIQUIDAÇÃO', cli)
                    
                desc_final = f"REC. Cliente {cli}: {fat}"
                run_query("INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, fonte_id, conta_bancaria_id, conciliado) VALUES (?, 'Entrada', 'Receita Com Vendas', ?, ?, ?, ?, FALSE)",
                          (dt_rec.strftime("%Y-%m-%d"), desc_final, val_efetivo, rr_id, bCid))
                          
            st.success(f"✔️ {len(df_selecionadas)} recebimentos injetados no Fluxo do banco {banco_destino}!")
            import time; time.sleep(1.5); st.rerun()

@st.dialog("Editar Duplicata a Receber", width="large")
def dialog_editar_receber(id_selecionado):
    rec_data = fetch_all("SELECT * FROM contas_a_receber WHERE id=?", (id_selecionado,)).iloc[0]
    valor_original = float(rec_data['valor'])
    venda_id = rec_data['venda_id']

    if pd.notna(venda_id):
        st.warning(f"**Atenção:** Este recebível está vinculado à **Venda #{int(venda_id)}**.")

    acao_rec = st.radio("O que deseja fazer?", ["Alterar Vencimento/Valor", "Aplicar Juros / Desconto", "Reparcelar", "Excluir/Cancelar"], horizontal=True)

    if acao_rec == "Alterar Vencimento/Valor":
        ed1, ed2 = st.columns(2)
        novo_venc = ed1.date_input("Novo Vencimento", value=pd.to_datetime(rec_data['data_vencimento']).date())
        
        if pd.notna(venda_id):
            st.info("ℹ️ Para títulos de vendas, a alteração de valor é bloqueada. Edite o valor pago diretamente na tabela de Baixa.")
            novo_valor = st.number_input("Valor Original (R$)", value=valor_original, disabled=True)
        else:
            novo_valor = ed2.number_input("Novo Valor (R$)", value=valor_original, min_value=0.01)
            
        novo_doc = st.text_input("Nº Documento", value=rec_data["numero_documento"] if rec_data["numero_documento"] else "")
        nova_desc = st.text_input("Descrição", value=rec_data['descricao'])
        if st.button("Salvar Alteração", type="primary"):
            run_query("UPDATE contas_a_receber SET data_vencimento=?, valor=?, descricao=?, numero_documento=? WHERE id=?",
                      (novo_venc.strftime("%Y-%m-%d"), novo_valor, nova_desc, novo_doc, id_selecionado))
            st.success("Recebível atualizado!")
            import time; time.sleep(1); st.rerun()

    elif acao_rec == "Aplicar Juros / Desconto":
        if pd.notna(venda_id):
            st.warning("Esta duplicata está vinculada a uma Venda. Digite o valor final pago diretamente na tabela de recebimento.")
        else:
            st.markdown(f"**Valor original:** R$ {valor_original:,.2f}")
            jd1, jd2, jd3 = st.columns(3)
            juros_pct = jd1.number_input("Juros (%)", min_value=0.0, value=0.0, step=0.5)
            desconto_rs = jd2.number_input("Desconto (R$)", min_value=0.0, value=0.0, step=0.01)
            valor_juros = valor_original * (juros_pct / 100)
            valor_final = valor_original + valor_juros - desconto_rs
            jd3.metric("Valor Final", f"R$ {valor_final:,.2f}")

            if valor_final <= 0:
                st.error("O valor final não pode ser zero ou negativo.")
            else:
                novo_venc_jd = st.date_input("Novo Vencimento", value=pd.to_datetime(rec_data['data_vencimento']).date())
                obs_juros = f" [Juros {juros_pct}%: +R${valor_juros:,.2f}]" if juros_pct > 0 else ""
                obs_desc = f" [Desc: -R${desconto_rs:,.2f}]" if desconto_rs > 0 else ""
                if st.button("Aplicar Juros/Desconto", type="primary"):
                    nova_descricao = rec_data['descricao'] + obs_juros + obs_desc
                    run_query("UPDATE contas_a_receber SET data_vencimento=?, valor=?, descricao=? WHERE id=?",
                              (novo_venc_jd.strftime("%Y-%m-%d"), valor_final, nova_descricao, id_selecionado))
                    st.success(f"Atualizado! Novo valor: R$ {valor_final:,.2f}")
                    import time; time.sleep(1); st.rerun()

    elif acao_rec == "Reparcelar":
        st.markdown(f"**Valor original a reparcelar:** R$ {valor_original:,.2f}")
        rp1, rp2 = st.columns(2)
        n_parc = rp1.number_input("Nº de Parcelas", min_value=2, value=2, step=1)
        dias_entre = rp2.number_input("Dias entre Parcelas", min_value=1, value=30, step=1)
        data_inicio = st.date_input("Data da 1ª Parcela", value=date.today())

        valor_parc = round(valor_original / n_parc, 2)
        diff_parc = round(valor_original - valor_parc * n_parc, 2)
        preview = []
        for i in range(n_parc):
            v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
            d = data_inicio + timedelta(days=dias_entre * i)
            preview.append({"Parcela": f"{i+1}/{n_parc}", "Vencimento": d.strftime("%d/%m/%Y"), "Valor": f"R$ {v:,.2f}"})
        st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)

        if st.button("Confirmar Reparcelamento", type="primary"):
            run_query("UPDATE contas_a_receber SET status='CANCELADO', descricao = descricao || ' [REPARCELADO]' WHERE id=?", (id_selecionado,))
            for i in range(n_parc):
                v = valor_parc + (diff_parc if i == n_parc - 1 else 0)
                d = data_inicio + timedelta(days=dias_entre * i)
                nova_desc_rp = f"{rec_data['descricao']} (Repar. {i+1}/{n_parc})"
                
                p_c_id_rp_r = int(rec_data['plano_conta_id']) if pd.notna(rec_data['plano_conta_id']) else None
                if not p_c_id_rp_r:
                    p_c_rec = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
                    p_c_id_rp_r = int(p_c_rec.iloc[0]['id']) if not p_c_rec.empty else None
                
                run_query(
                    "INSERT INTO contas_a_receber (cliente_id, venda_id, plano_conta_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                    (int(rec_data['cliente_id']) if pd.notna(rec_data['cliente_id']) else None,
                     int(rec_data['venda_id']) if pd.notna(rec_data['venda_id']) else None,
                     p_c_id_rp_r, nova_desc_rp, v, d.strftime("%Y-%m-%d")))
            st.success(f"Reparcelamento concluído! {n_parc} novos recebíveis criados.")
            import time; time.sleep(1); st.rerun()

    elif acao_rec == "Excluir/Cancelar":
        if pd.notna(venda_id):
            st.error("Para excluir recebíveis de vendas, desfaça o faturamento do pedido na tela de Faturamento.")
        else:
            st.markdown("**Tem certeza que deseja cancelar/excluir este recebível?**")
            if st.button("Confirmar Cancelamento/Exclusão", type="primary"):
                run_query("UPDATE contas_a_receber SET status='CANCELADO', descricao = descricao || ' [CANCELADO]' WHERE id=?", (id_selecionado,))
                st.success("Cancelado com sucesso!")
                import time; time.sleep(1); st.rerun()
