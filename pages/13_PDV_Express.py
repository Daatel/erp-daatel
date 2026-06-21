import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import run_query, fetch_all, gerar_comissao_se_necessario
from estilo import carregar_estilo

st.set_page_config(page_title="PDV Express", page_icon="⚡", layout="wide")
carregar_estilo()

st.title("⚡ PDV Express (Venda Balcão)")
st.markdown("Venda Rápida de Balcão JIT (Just in Time) com baixa física automática via FIFO e quitação instantânea do financeiro no caixa.")

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Carregar dados básicos
df_clientes = fetch_all("SELECT id, nome, rede_clientes, prazo_pagamento, representante_id, forma_pagamento_id FROM clientes WHERE status='ATIVO'")
df_vendedores = fetch_all("SELECT id, nome, gatilho_comissao FROM funcionarios WHERE cargo LIKE '%Vendedor%' OR cargo LIKE '%Representante%'")
df_produtos = fetch_all("SELECT id, nome, preco_venda_base FROM produtos WHERE is_materia_prima = FALSE")
df_bancos_pdv = fetch_all("SELECT id, nome FROM contas_bancarias WHERE status='ATIVO'")
df_fp_all = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento")
fp_rules_dict = dict(zip(df_fp_all['id'], df_fp_all['parcelas'])) if not df_fp_all.empty else {}
fp_names_dict = dict(zip(df_fp_all['id'], df_fp_all['nome'])) if not df_fp_all.empty else {}
fp_options_pdv = df_fp_all['nome'].tolist() if not df_fp_all.empty else []
fp_ids_pdv = dict(zip(df_fp_all['nome'], df_fp_all['id'])) if not df_fp_all.empty else {}
fp_rules_pdv = dict(zip(df_fp_all['nome'], df_fp_all['parcelas'])) if not df_fp_all.empty else {}

if df_clientes.empty or df_produtos.empty or df_vendedores.empty:
    st.warning("Cadastre Clientes, Vendedores e Produtos primeiro!")
elif df_bancos_pdv.empty:
    st.warning("Cadastre pelo menos uma Conta Bancária ativa em **Financeiro** para receber as vendas rápidas de balcão!")
else:
    # Puxa saldos atuais de estoque para exibir no balcão
    df_mov_saldos = fetch_all("""
        SELECT produto_id, 
               SUM(CASE WHEN tipo_movimento = 'Entrada' THEN quantidade ELSE -quantidade END) as saldo 
        FROM estoque_movimentos 
        GROUP BY produto_id
    """)
    dict_saldos_pdv = {int(r['produto_id']): float(r['saldo']) for _, r in df_mov_saldos.iterrows()}
    
    with st.form("form_pdv_balcao", clear_on_submit=True):
        col_p1, col_p2, col_p3 = st.columns(3)
        
        c_opts_pdv = {f"{r['nome']}": r for _, r in df_clientes.iterrows()}
        
        default_cli_idx = 0
        for idx, name in enumerate(c_opts_pdv.keys()):
            if name.upper().strip() == "CONSUMIDOR":
                default_cli_idx = idx
                break
                
        pdv_cli_sel = col_p1.selectbox("Cliente Comprador", list(c_opts_pdv.keys()), index=default_cli_idx, key="pdv_cli")
        
        v_opts_pdv = {f"{r['nome']}": r for _, r in df_vendedores.iterrows()}
        
        # Auto-selecionar representante vinculado
        cli_obj = c_opts_pdv[pdv_cli_sel]
        

                    
        rep_id = cli_obj['representante_id']
        default_idx = 0
        if pd.notna(rep_id):
            for idx, (_, r) in enumerate(df_vendedores.iterrows()):
                if int(r['id']) == int(rep_id):
                    default_idx = idx
                    break
        pdv_ven_sel = col_p2.selectbox("Vendedor / Representante", list(v_opts_pdv.keys()), index=default_idx, key="pdv_ven")
        
        p_opts_pdv = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
        pdv_prod_sel = col_p3.selectbox("Produto Final", list(p_opts_pdv.keys()), key="pdv_prod")
        
        col_p4, col_p5, col_p6 = st.columns([1, 1.2, 1.2])
        pdv_qtd = col_p4.number_input("Quantidade (Volumes/Kg)", min_value=1.0, step=1.0, key="pdv_qtd")
        
        # Determinar índice inicial da forma de pagamento do cliente selecionado
        cli_fp_id = cli_obj.get('forma_pagamento_id')
        cli_fp_nome = ""
        if pd.notna(cli_fp_id):
            cli_fp_nome = fp_names_dict.get(int(cli_fp_id), "")
        if not cli_fp_nome:
            cli_fp_nome = cli_obj.get('prazo_pagamento', '')
            
        default_fp_idx = fp_options_pdv.index(cli_fp_nome) if cli_fp_nome in fp_options_pdv else 0
        
        # Se o cliente for CONSUMIDOR, a forma de pagamento é forçada para 'A vista'
        is_consumidor = (pdv_cli_sel.upper().strip() == "CONSUMIDOR")
        
        if is_consumidor:
            avista_name = "A vista"
            for name in fp_options_pdv:
                if name.upper().strip() == "A VISTA":
                    avista_name = name
                    break
            pdv_fp_sel = col_p6.selectbox("Condição de Pagamento", [avista_name], disabled=True, key="pdv_fp")
        else:
            pdv_fp_sel = col_p6.selectbox("Condição de Pagamento", fp_options_pdv, index=default_fp_idx, key="pdv_fp")
            
        rule_str = fp_rules_pdv.get(pdv_fp_sel, "0")
        import re
        dias_list = [int(n) for n in re.findall(r'\d+', str(rule_str))]
        is_a_vista_pdv = (not dias_list or all(d == 0 for d in dias_list))
        fp_nome_cli = pdv_fp_sel

        # Preço dinâmico de balcão
        prod_id_pdv = int(p_opts_pdv[pdv_prod_sel]['id'])
        saldo_est_pdv = dict_saldos_pdv.get(prod_id_pdv, 0.0)
        p_base_pdv = float(p_opts_pdv[pdv_prod_sel]['preco_venda_base'])
        
        # Buscar se tem tabela individual para o cliente ou rede
        origem_pdv = "Preço Base de Balcão"
        tb_cli = fetch_all("SELECT preco FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='CLIENTE' AND entidade_nome=? AND status='ATIVO'", (prod_id_pdv, cli_obj['nome']))
        if not tb_cli.empty:
            p_base_pdv = float(tb_cli.iloc[0]['preco'])
            origem_pdv = "Tabela Acordo Cliente"
        else:
            rede_c_pdv = cli_obj['rede_clientes']
            if rede_c_pdv:
                tb_red = fetch_all("SELECT preco FROM tabelas_preco WHERE produto_id=? AND tipo_entidade='REDE' AND entidade_nome=? AND status='ATIVO'", (prod_id_pdv, rede_c_pdv))
                if not tb_red.empty:
                    p_base_pdv = float(tb_red.iloc[0]['preco'])
                    origem_pdv = "Tabela Acordo Rede"
                    
        pdv_preco = col_p5.number_input("Preço Unitário (R$)", min_value=0.0, value=p_base_pdv, step=0.1, key="pdv_preco")
        st.caption(f"💡 Origem do Preço: **{origem_pdv}** | Saldo em Estoque: **{saldo_est_pdv:.1f} unidades**")
        
        col_p7, col_p8, col_p9 = st.columns(3)
        pdv_doc = col_p7.selectbox("Documento de Venda", ["DAV (Documento Auxiliar de Venda)", "Nota Fiscal (NF)"], key="pdv_doc")
        
        b_opts_pdv = {f"{r['nome']}": r['id'] for _, r in df_bancos_pdv.iterrows()}
        if is_a_vista_pdv:
            pdv_banco_sel = col_p8.selectbox("Recebido em Qual Conta/Caixa?", list(b_opts_pdv.keys()), key="pdv_banco")
        else:
            col_p8.text_input("Conta/Caixa", value="Contas a Receber (Prazo)", disabled=True, key="pdv_banco_disabled")
            pdv_banco_sel = None
        
        pdv_lote = col_p9.text_input("📝 Lote Impresso", value=date.today().strftime('FAB %d/%m'), key="pdv_lote")
        pdv_val = col_p9.text_input("📅 Validade", value=(date.today() + timedelta(days=90)).strftime('%d/%m/%Y'), key="pdv_val")
        
        # KPI de Total
        v_total_pdv = pdv_qtd * pdv_preco
        st.markdown(f"""
        <div style='background-color:#f0f2f6;padding:12px;border-radius:10px;text-align:center;'>
            <span style='font-size:14px;color:#555;'>TOTAL A PAGAR NO BALCÃO</span><br>
            <span style='font-size:24px;font-weight:bold;color:#2e7d32;'>{format_brl(v_total_pdv)}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not is_a_vista_pdv:
            st.info("ℹ️ **Faturamento a Prazo:** A venda gerará duplicatas pendentes no Contas a Receber. A baixa financeira será feita posteriormente.")
        
        if st.form_submit_button("⚡ Efetivar Venda & Baixar Estoque/Financeiro JIT", use_container_width=True):
            cli_pdv = c_opts_pdv[pdv_cli_sel]
            ven_pdv = v_opts_pdv[pdv_ven_sel]
            
            # Bloquear CONSUMIDOR a prazo
            if not is_a_vista_pdv and cli_pdv['nome'].upper().strip() == "CONSUMIDOR":
                st.error("❌ Não é permitido realizar venda a prazo para o cliente CONSUMIDOR genérico. Por favor, selecione um cliente cadastrado.")
                st.stop()
                
            bCid = b_opts_pdv[pdv_banco_sel] if is_a_vista_pdv else None
            
            # 1. Gerar número de documento
            numero_doc_pdv = ""
            if "DAV" in pdv_doc:
                df_dav_max = fetch_all("SELECT MAX(CAST(numero_documento AS INTEGER)) as max_dav FROM vendas WHERE tipo_documento LIKE '%DAV%'")
                max_dav = df_dav_max.iloc[0]['max_dav'] if not df_dav_max.empty and pd.notna(df_dav_max.iloc[0]['max_dav']) else 0
                novo_dav = int(max_dav) + 1
                numero_doc_pdv = f"{novo_dav:010d}"
            else:
                # Gera número provisório ou pendente
                numero_doc_pdv = "BALCAO-" + date.today().strftime('%H%M%S')
            
            # Lançar com forma_pagamento_id
            fp_id_to_save = fp_ids_pdv.get(pdv_fp_sel, None)

            # 2. Grava a Venda diretamente como FATURADO
            run_query('''
                INSERT INTO vendas (data, cliente_id, vendedor_id, produto_id, quantidade, valor_unitario, valor_total, comissao_valor, status, tipo_documento, numero_documento, lote_impresso, validade_impressa, forma_pagamento_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 'FATURADO', ?, ?, ?, ?, ?)
            ''', (date.today().strftime("%Y-%m-%d"), cli_pdv['id'], ven_pdv['id'], prod_id_pdv, pdv_qtd, pdv_preco, v_total_pdv, pdv_doc, numero_doc_pdv, pdv_lote, pdv_val, fp_id_to_save))
            
            df_nova_v = fetch_all("SELECT MAX(id) as lg FROM vendas")
            nova_venda_id = int(df_nova_v.iloc[0]['lg'])
            
            # 3. Baixa de Estoque via FIFO
            from database import consumir_estoque_fifo
            custo_cmv_real, is_estimado = consumir_estoque_fifo(
                produto_id=prod_id_pdv,
                quantidade=pdv_qtd,
                data_mov=date.today().strftime("%Y-%m-%d"),
                origem=f'Venda Balcão Express ({pdv_doc})',
                doc_ref=f"Venda Balcão #{nova_venda_id}"
            )
            run_query("UPDATE vendas SET custo_cmv_real = ? WHERE id = ?", (custo_cmv_real, nova_venda_id))
            
            # Buscar plano de contas padrão para receita
            df_pc_rec = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
            pc_id_val = int(df_pc_rec.iloc[0]['id']) if not df_pc_rec.empty else None

            # 4. Grava Financeiro
            if is_a_vista_pdv:
                run_query('''
                    INSERT INTO contas_a_receber (cliente_id, plano_conta_id, descricao, valor, data_vencimento, status, data_recebimento, conta_bancaria_id, venda_id)
                    VALUES (?, ?, ?, ?, ?, 'RECEBIDO', ?, ?, ?)
                ''', (cli_pdv['id'], pc_id_val, f"{pdv_doc} #{numero_doc_pdv}", v_total_pdv, date.today().strftime("%Y-%m-%d"), date.today().strftime("%Y-%m-%d"), bCid, nova_venda_id))
                
                # 5. Lança no fluxo de caixa bancário imediatamente
                desc_receita = f"REC. Balcão Cliente {cli_pdv['nome']}: {pdv_doc} #{numero_doc_pdv}"
                run_query('''
                    INSERT INTO fluxo_caixa (data, tipo, categoria, descricao, valor, fonte_id, conta_bancaria_id, conciliado, cliente_id) 
                    VALUES (?, 'Entrada', 'Receita Com Vendas', ?, ?, ?, ?, TRUE, ?)
                ''', (date.today().strftime("%Y-%m-%d"), desc_receita, v_total_pdv, nova_venda_id, bCid, cli_pdv['id']))
                
                # 6. Dispara o cálculo e gravação de comissão
                gerar_comissao_se_necessario(nova_venda_id, 'FATURAMENTO', cli_pdv['nome'])
                gerar_comissao_se_necessario(nova_venda_id, 'LIQUIDAÇÃO', cli_pdv['nome'])
                
                st.success(f"Venda Balcão #{nova_venda_id} concluída com sucesso. Documento emitido: {pdv_doc} #{numero_doc_pdv}. Estoque JIT baixado e {format_brl(v_total_pdv)} creditado na conta '{pdv_banco_sel}'.")
            else:
                # Gerar parcelas do Contas a Receber
                dias_list = [int(n) for n in re.findall(r'\d+', str(rule_str))]
                if not dias_list:
                    dias_list = [0]
                
                N = len(dias_list)
                val_p = round(v_total_pdv / N, 2)
                diff_p = round(v_total_pdv - val_p * N, 2)
                
                for i, dias in enumerate(dias_list):
                    v_p = val_p + (diff_p if i == N - 1 else 0.0)
                    dt_v = date.today() + timedelta(days=dias)
                    desc_p = f"{pdv_doc} #{numero_doc_pdv} (Parc. {i+1}/{N})"
                    
                    run_query('''
                        INSERT INTO contas_a_receber (cliente_id, plano_conta_id, descricao, valor, data_vencimento, status, venda_id)
                        VALUES (?, ?, ?, ?, ?, 'PENDENTE', ?)
                    ''', (cli_pdv['id'], pc_id_val, desc_p, v_p, dt_v.strftime("%Y-%m-%d"), nova_venda_id))
                
                # Dispara cálculo de comissão apenas para faturamento
                gerar_comissao_se_necessario(nova_venda_id, 'FATURAMENTO', cli_pdv['nome'])
                
                st.success(f"Venda Balcão #{nova_venda_id} faturada a prazo. Documento emitido: {pdv_doc} #{numero_doc_pdv}. Estoque JIT baixado e duplicatas ({N} parcela(s)) lançadas em carteira para o cliente.")
                
            import time; time.sleep(2.0); st.rerun()
