import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta
from database import (
    run_query, fetch_all, gerar_comissao_se_necessario,
    db_transaction, run_query_tx, fetch_all_tx,
    consumir_estoque_fifo_tx, gerar_comissao_se_necessario_tx,
    get_clientes_ativos_cached, get_produtos_cached
)
from estilo import carregar_estilo

st.set_page_config(page_title="Faturamento & Expedição", layout="wide")
carregar_estilo()

# Modais de Impressão imediata de DAV
@st.dialog("Imprimir Documento Auxiliar de Venda (DAV)")
def modal_perguntar_impressao(vendas_ids):
    st.write("O faturamento foi concluído com sucesso!")
    st.write("Deseja abrir a tela de impressão do(s) DAV(s) agora?")
    
    col1, col2 = st.columns(2)
    if col1.button("Sim, Imprimir", type="primary", use_container_width=True):
        st.session_state['disparar_impressao_davs'] = vendas_ids
        if 'pedidos_dav_faturados' in st.session_state:
            del st.session_state['pedidos_dav_faturados']
        st.rerun()
    if col2.button("Não", use_container_width=True):
        if 'pedidos_dav_faturados' in st.session_state:
            del st.session_state['pedidos_dav_faturados']
        st.rerun()

@st.dialog("Imprimir DAV", width="large")
def modal_impressao_dav(vendas_ids):
    import streamlit.components.v1 as components
    from utils_dav import buscar_dados_venda, gerar_html_dav
    
    st.write("Abrindo painel de visualização e fila de impressão...")
    for vid in vendas_ids:
        venda_info = buscar_dados_venda(vid)
        if venda_info:
            html_dav = gerar_html_dav(venda_info)
            # Injeta window.print() automática no HTML do DAV
            html_dav = html_dav.replace("</body>", "<script>window.print();</script></body>")
            components.html(html_dav, height=800, scrolling=True)
            
    if st.button("Fechar", type="primary", use_container_width=True):
        if 'disparar_impressao_davs' in st.session_state:
            del st.session_state['disparar_impressao_davs']
        st.rerun()

@st.dialog("Faturamento Parcial / Fracionar Pedido")
def dialog_fracionar_pedido(pedido_id):
    # Busca detalhes da venda
    df_vd = fetch_all("""
        SELECT v.id, v.quantidade, v.valor_unitario, p.nome as produto_nome
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.id = ?
    """, (pedido_id,))
    if df_vd.empty:
        st.error("Pedido não encontrado.")
        return
    row = df_vd.iloc[0]
    qtd_total = float(row['quantidade'])
    v_uni = float(row['valor_unitario'])
    prod = row['produto_nome']
    
    st.write(f"Você está fracionando o item **{prod}** do pedido.")
    st.write(f"Quantidade total cadastrada: **{qtd_total:,.2f}**")
    
    qtd_part = st.number_input("Quantidade a Faturar Agora", min_value=0.01, max_value=qtd_total - 0.01, value=qtd_total * 0.5, step=1.0)
    qtd_resto = qtd_total - qtd_part
    valor_total_part = qtd_part * v_uni
    valor_total_resto = qtd_resto * v_uni
    
    st.info(f"💡 **Resultado do Fracionamento:**\n"
            f"* **Lote 1 (Faturar Agora):** {qtd_part:,.2f} UN (Total: R$ {valor_total_part:,.2f})\n"
            f"* **Lote 2 (Novo Pedido Pendente):** {qtd_resto:,.2f} UN (Total: R$ {valor_total_resto:,.2f})")
            
    if st.button("Confirmar Fracionamento", type="primary", use_container_width=True):
        df_orig = fetch_all("SELECT * FROM vendas WHERE id = ?", (pedido_id,))
        if not df_orig.empty:
            orig = df_orig.iloc[0]
            
            comissao_orig = float(orig['comissao_valor']) if pd.notna(orig['comissao_valor']) else 0.0
            comissao_part = round(comissao_orig * (qtd_part / qtd_total), 2)
            comissao_resto = round(comissao_orig - comissao_part, 2)
            
            custo_acordos_orig = float(orig['custo_acordos_rede']) if pd.notna(orig['custo_acordos_rede']) else 0.0
            custo_acordos_part = round(custo_acordos_orig * (qtd_part / qtd_total), 2)
            custo_acordos_resto = round(custo_acordos_orig - custo_acordos_part, 2)
            
            # Atualiza o original para a quantidade parcial
            run_query("""
                UPDATE vendas 
                SET quantidade = ?, valor_total = ?, comissao_valor = ?, custo_acordos_rede = ?
                WHERE id = ?
            """, (qtd_part, valor_total_part, comissao_part, custo_acordos_part, pedido_id))
            
            # Insere o saldo restante como novo pedido pendente
            run_query("""
                INSERT INTO vendas (
                    data, cliente_id, vendedor_id, produto_id, quantidade, valor_unitario, valor_total, 
                    comissao_valor, custo_acordos_rede, is_bonificacao, status, forma_pagamento_id, 
                    flag_op_casada, filial_atacadao, pedido_atacadao_numero, pedido_grupo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                orig['data'],
                int(orig['cliente_id']) if pd.notna(orig['cliente_id']) else None,
                int(orig['vendedor_id']) if pd.notna(orig['vendedor_id']) else None,
                int(orig['produto_id']) if pd.notna(orig['produto_id']) else None,
                qtd_resto,
                v_uni,
                valor_total_resto,
                comissao_resto,
                custo_acordos_resto,
                orig['is_bonificacao'],
                orig['status'],
                int(orig['forma_pagamento_id']) if pd.notna(orig['forma_pagamento_id']) else None,
                orig['flag_op_casada'],
                orig['filial_atacadao'] if pd.notna(orig['filial_atacadao']) else '',
                orig['pedido_atacadao_numero'] if pd.notna(orig['pedido_atacadao_numero']) else '',
                orig['pedido_grupo'] if pd.notna(orig['pedido_grupo']) else None
            ))
            
            st.success("Pedido fracionado com sucesso!")
            import time; time.sleep(1.5); st.rerun()

# Disparadores de Modais baseados em Session State
if st.session_state.get('pedidos_dav_faturados'):
    modal_perguntar_impressao(st.session_state['pedidos_dav_faturados'])
elif st.session_state.get('disparar_impressao_davs'):
    modal_impressao_dav(st.session_state['disparar_impressao_davs'])
elif st.session_state.get('split_dialog_pid'):
    pid_to_split = st.session_state.pop('split_dialog_pid')
    dialog_fracionar_pedido(pid_to_split)

st.markdown("""
<style>
/* Remove padding do topo da página do Streamlit para subir tudo de forma limpa e sem cortar o texto */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}
</style>
<h1 style='font-size: 2.2rem; font-weight: 700; margin-top: -15px; margin-bottom: 20px; color: #1e293b;'>
Faturamento e Expedição
</h1>
""", unsafe_allow_html=True)
st.markdown("Central de liberação de carga. Fature os pedidos aprovados na Venda, bata o estoque e gere arquivos de integração fiscal.")

def format_brl(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

df_clientes = get_clientes_ativos_cached()
df_produtos = get_produtos_cached()

tab1, tab2, tab3, tab4 = st.tabs([
    "Fila de Faturamento (Em Lote)", 
    "Gerador Fiscal (SEFAZ/Emissor)", 
    "Estornar NF / DAV",
    "Logística Reversa (Devoluções)"
])

# ======= 1. FILA DE FATURAMENTO =======
with tab1:
    st.subheader("Fila de Pedidos Aprovados")
    st.markdown("Selecione os pedidos que deseja faturar agora. **Atenção ao farol de estoque:** O sistema permite faturar no vermelho, mas o saldo do Produto Acabado ficará negativo.")

    # Busca saldos de estoque atuais por produto
    df_saldos = fetch_all('''
        SELECT produto_id, SUM(CASE WHEN tipo_movimento = 'Entrada' THEN quantidade ELSE -quantidade END) as saldo_atual 
        FROM estoque_movimentos GROUP BY produto_id
    ''')
    dict_saldos = {}
    if not df_saldos.empty:
        dict_saldos = dict(zip(df_saldos['produto_id'], df_saldos['saldo_atual']))

    # Busca formas de pagamento
    df_fp = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
    fp_dict = dict(zip(df_fp['id'], df_fp['nome'])) if not df_fp.empty else {}
    fp_names = df_fp['nome'].tolist() if not df_fp.empty else []
    fp_rule_dict = dict(zip(df_fp['nome'], df_fp['parcelas'])) if not df_fp.empty else {}

    # Busca fila de pedidos abertos
    df_fila = fetch_all('''
        SELECT v.id as pedido_id, v.data as data_pedido, c.nome as cliente, c.uf as uf_cliente, c.cnpj_cpf as cnpj_cliente,
               p.nome as produto, p.id as p_id, v.quantidade, v.valor_total, v.custo_acordos_rede,
               v.forma_pagamento_id, fp.nome as forma_pagamento, fp.parcelas as rule_str,
               v.pedido_grupo, v.cliente_id
        FROM vendas v 
        JOIN clientes c ON v.cliente_id=c.id
        JOIN produtos p ON v.produto_id=p.id
        LEFT JOIN formas_pagamento fp ON v.forma_pagamento_id=fp.id
        WHERE v.status = 'APROVADO'
        ORDER BY v.pedido_grupo ASC, v.id ASC
    ''')

    if df_fila.empty:
        st.info("Nenhum pedido aguardando faturamento na fila. Todos os pedidos aprovados já foram faturados.")
    else:
        # Limita para renderizar no máximo 25 pedidos por motivos de performance
        max_exibir = 25
        total_pendentes = len(df_fila)
        df_exibir_fila = df_fila.head(max_exibir)
        
        if total_pendentes > max_exibir:
            st.warning(f"Mostrando apenas os primeiros {max_exibir} de {total_pendentes} pedidos pendentes para otimização de performance.")
            
        pedidos_selecionados_lista = []
        
        st.markdown("### Fila de Pedidos para Faturamento")
        st.markdown("*Selecione os pedidos para faturar. Ajuste o lote e validade se necessário. Os vencimentos de cada duplicata são calculados automaticamente conforme a forma de pagamento cadastrada no pedido.*")
        
        # Cabeçalho da Tabela
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8, col_h9, col_h10 = st.columns([0.4, 0.6, 2.0, 1.4, 1.0, 1.0, 0.7, 0.7, 1.8, 0.4], vertical_alignment="center")
        col_h1.markdown("**Faturar?**")
        col_h2.markdown("**Pedido**")
        col_h3.markdown("**Cliente**")
        col_h4.markdown("**CNPJ**")
        col_h5.markdown("**Total**")
        col_h6.markdown("**Estoque**")
        col_h7.markdown("**Lote**")
        col_h8.markdown("**Val.**")
        col_h9.markdown("**Vencimentos**")
        col_h10.markdown("**Part.**")
        st.markdown("<div style='margin-top: -10px; margin-bottom: 10px; border-top: 1px solid #ccc;'></div>", unsafe_allow_html=True)
        
        import re
        
        # Montar nomenclatura visual do pedido_grupo (ex: 57.1, 57.2)
        grupo_contadores = {}
        pedido_labels = {}
        for _, r in df_exibir_fila.iterrows():
            grp = r['pedido_grupo']
            pid = int(r['pedido_id'])
            if grp and pd.notna(grp):
                if grp not in grupo_contadores:
                    grupo_contadores[grp] = 0
                grupo_contadores[grp] += 1
                pedido_labels[pid] = f"{grp}.{grupo_contadores[grp]}"
            else:
                pedido_labels[pid] = f"#{pid}"
        
        for idx, row in df_exibir_fila.iterrows():
            pid = int(row['pedido_id'])
            p_id = int(row['p_id'])
            cliente_nome = row['cliente']
            cnpj_val = row['cnpj_cliente'] if pd.notna(row['cnpj_cliente']) else ""
            prod_nome = row['produto']
            qtd_pedida = float(row['quantidade'])
            valor_total_pedido = float(row['valor_total'])
            
            # 1. Obter saldo de estoque e farol (sem números de saldo)
            saldo_est = dict_saldos.get(p_id, 0.0)
            if saldo_est >= qtd_pedida:
                farol = "🟢 Saldo Ok"
            elif saldo_est > 0:
                farol = "🟡 Parcial"
            else:
                farol = "🔴 Sem Saldo"
                
            # 2. Obter forma de pagamento cadastrada no pedido
            cur_fp_nome = row['forma_pagamento'] if pd.notna(row['forma_pagamento']) else "A vista"
            rule_str = row['rule_str'] if pd.notna(row['rule_str']) else "0"
            
            # Lote e Validade padrões
            default_lote = date.today().strftime('FAB %d/%m')
            default_validade = (date.today() + timedelta(days=90)).strftime('%d/%m/%Y')
            
            # Renderizar linha da tabela usando st.columns (10 colunas)
            col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([0.4, 0.6, 2.0, 1.4, 1.0, 1.0, 0.7, 0.7, 1.8, 0.4], vertical_alignment="center")
            
            faturar_check = col1.checkbox("Faturar", value=False, key=f"sel_{pid}", label_visibility="collapsed")
            label_pedido = pedido_labels.get(pid, f"#{pid}")
            col2.markdown(f"**{label_pedido}**")
            col3.markdown(cliente_nome)
            col4.markdown(cnpj_val)
            col5.markdown(format_brl(valor_total_pedido))
            col6.markdown(farol)
            
            lote_val = col7.text_input("Lote", value=default_lote, key=f"lote_{pid}", label_visibility="collapsed")
            val_val = col8.text_input("Val.", value=default_validade, key=f"val_{pid}", label_visibility="collapsed")
            
            # Calcular parcelas detalhadas/vencimentos em formato horizontal compactado
            dias_list = [int(n) for n in re.findall(r'\d+', str(rule_str))]
            if not dias_list:
                dias_list = [0]
            
            N = len(dias_list)
            val_p = round(valor_total_pedido / N, 2)
            val_p_str = f"{val_p:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            dates_venc_list = []
            for dias in dias_list:
                dt_v = date.today() + timedelta(days=dias)
                # Formatar dia/mes sem zeros à esquerda e ano com 2 dígitos
                dt_v_str = f"{dt_v.day}/{dt_v.month}/{dt_v.strftime('%y')}"
                dates_venc_list.append(dt_v_str)
                
            dates_str = ", ".join(dates_venc_list)
            venc_str_horizontal = f"{N} x {val_p_str} ({dates_str})"
            
            col9.markdown(f"<div style='font-size: 14px; font-weight: bold; color: #292d77; white-space: nowrap;'>{venc_str_horizontal}</div>", unsafe_allow_html=True)
            
            # Botão de Fracionamento de Pedidos (Faturamento Parcial)
            if col10.button("✂️", key=f"split_btn_{pid}", help="Fracionar Pedido (Faturamento Parcial)"):
                st.session_state['split_dialog_pid'] = pid
                st.rerun()
            
            st.markdown("<div style='margin-top: 5px; margin-bottom: 5px; border-top: 1px dashed #eee;'></div>", unsafe_allow_html=True)
            
            if faturar_check:
                ped_grp = row['pedido_grupo'] if pd.notna(row.get('pedido_grupo')) else None
                pedidos_selecionados_lista.append({
                    "pedido_id": pid,
                    "pedido_grupo": ped_grp,
                    "cliente": cliente_nome,
                    "cliente_id": int(row['cliente_id']),
                    "produto": prod_nome,
                    "p_id": p_id,
                    "quantidade": qtd_pedida,
                    "valor_total": valor_total_pedido,
                    "Forma de Pagamento": cur_fp_nome,
                    "Lote Impresso (NF/DAV)": lote_val,
                    "Validade (NF/DAV)": val_val
                })
                
        if pedidos_selecionados_lista:
            pedidos_selecionados = pd.DataFrame(pedidos_selecionados_lista)
        else:
            pedidos_selecionados = pd.DataFrame()
        
        if not pedidos_selecionados.empty:
            st.markdown("---")
            st.subheader("Ação em Lote")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            tipo_doc = col_f1.selectbox("Tipo de Documento", ["Nota Fiscal (NF)", "DAV (Documento Auxiliar de Venda)"])
            
            # Aviso contextual por tipo de documento
            if "DAV" in tipo_doc:
                col_f1.success("✅ **DAV:** Número gerado automaticamente. Embarque liberado imediatamente após o faturamento.")
            else:
                col_f1.warning(
                    "⏳ **Nota Fiscal:** O embarque na Logística ficará **retido** até o número "
                    "oficial da SEFAZ ser registrado na aba *Gerador Fiscal*. "
                    "Se precisar embarcar imediatamente, use a DAV."
                )
            
            sobrescrever = col_f2.checkbox("Sobrescrever Vencimento do Cliente?")
            venc_boleto_override = col_f2.date_input("Vencimento Forçado", value=date.today() + timedelta(days=30)) if sobrescrever else None
            
            # Lógica de geração de parcelas para a prévia - AGRUPADA por pedido_grupo
            import re
            insts = []
            
            # Agrupar os pedidos selecionados por pedido_grupo (ou por pedido_id individual se sem grupo)
            grupos_faturamento = {}
            for _, row in pedidos_selecionados.iterrows():
                pid = int(row['pedido_id'])
                grp = row.get('pedido_grupo')
                chave_grupo = str(grp) if grp and pd.notna(grp) else f"solo_{pid}"
                if chave_grupo not in grupos_faturamento:
                    grupos_faturamento[chave_grupo] = {
                        "ids": [],
                        "cliente": row['cliente'],
                        "fp_nome": row['Forma de Pagamento'],
                        "total": 0.0
                    }
                grupos_faturamento[chave_grupo]["ids"].append(pid)
                grupos_faturamento[chave_grupo]["total"] += float(df_fila[df_fila['pedido_id'] == pid].iloc[0]['valor_total'])
            
            for chave_grupo, ginfo in grupos_faturamento.items():
                v_total_grupo = ginfo["total"]
                fp_nome = ginfo["fp_nome"]
                label_grupo = chave_grupo if not chave_grupo.startswith("solo_") else f"#{ginfo['ids'][0]}"
                
                if sobrescrever:
                    insts.append({
                        "Grupo": chave_grupo,
                        "Pedido/Grupo": label_grupo,
                        "Cliente": ginfo["cliente"],
                        "Parcela": "1/1",
                        "Vencimento": venc_boleto_override,
                        "Valor (R$)": float(v_total_grupo),
                        "Valor Original": float(v_total_grupo)
                    })
                else:
                    rule_str = fp_rule_dict.get(fp_nome, "30")
                    dias_list = [int(n) for n in re.findall(r'\d+', rule_str)]
                    if not dias_list:
                        dias_list = [0]
                    
                    N = len(dias_list)
                    val_p = round(v_total_grupo / N, 2)
                    diff_p = round(v_total_grupo - val_p * N, 2)
                    
                    for i, dias in enumerate(dias_list):
                        v_p = val_p + (diff_p if i == N - 1 else 0.0)
                        dt_v = date.today() + timedelta(days=dias)
                        insts.append({
                            "Grupo": chave_grupo,
                            "Pedido/Grupo": label_grupo,
                            "Cliente": ginfo["cliente"],
                            "Parcela": f"{i+1}/{N}",
                            "Vencimento": dt_v,
                            "Valor (R$)": float(v_p),
                            "Valor Original": float(v_total_grupo)
                        })
            
            # Cria uma chave única que inclui o ID, a Forma de Pagamento e o Valor Total de cada pedido selecionado
            sel_ids_fps_vals = sorted([(int(row['pedido_id']), row['Forma de Pagamento'], float(row['valor_total'])) for _, row in pedidos_selecionados.iterrows()], key=lambda x: x[0])
            sobrescreveu_flag = f"{sobrescrever}_{venc_boleto_override}"
            session_key_ids = f"last_sel_{sel_ids_fps_vals}_{sobrescreveu_flag}"
            if st.session_state.get('last_selected_combo') != session_key_ids:
                st.session_state['parcelas_faturamento'] = insts
                st.session_state['last_selected_combo'] = session_key_ids
            
            st.markdown("#### 💳 Revisar/Customizar Parcelas do Contas a Receber")
            st.caption("Altere os valores ou datas de vencimento de cada parcela se necessário. A soma das parcelas de cada pedido deve ser igual ao seu total original.")
            
            df_insts = pd.DataFrame(st.session_state['parcelas_faturamento'])
            if not df_insts.empty:
                df_insts['Vencimento'] = pd.to_datetime(df_insts['Vencimento']).dt.date
                
            edited_insts_df = st.data_editor(
                df_insts,
                hide_index=True,
                column_config={
                    "Grupo": st.column_config.TextColumn("Grupo", disabled=True),
                    "Pedido/Grupo": st.column_config.TextColumn("Pedido/Grupo", disabled=True),
                    "Cliente": st.column_config.TextColumn("Cliente", disabled=True),
                    "Parcela": st.column_config.TextColumn("Parcela", disabled=True),
                    "Vencimento": st.column_config.DateColumn("Vencimento", required=True),
                    "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.01, required=True),
                    "Valor Original": st.column_config.NumberColumn("Valor Original", disabled=True, format="R$ %.2f")
                },
                use_container_width=True,
                key="editor_insts_fat"
            )
            st.session_state['parcelas_faturamento'] = edited_insts_df.to_dict('records')
            
            validacao_somas = True
            for grp_key in df_insts['Grupo'].unique():
                df_p = edited_insts_df[edited_insts_df['Grupo'] == grp_key]
                orig_val = float(df_p.iloc[0]['Valor Original'])
                soma_val = round(df_p['Valor (R$)'].sum(), 2)
                label = df_p.iloc[0]['Pedido/Grupo']
                if abs(orig_val - soma_val) > 0.01:
                    validacao_somas = False
                    st.error(f"**Erro no Grupo {label}:** A soma das parcelas (R$ {soma_val:,.2f}) nao e igual ao total original (R$ {orig_val:,.2f}). Diferenca: R$ {round(orig_val - soma_val, 2):,.2f}")

            def simular_emissao_sefaz_with_retry(venda_id, cliente_nome, valor, max_retries=3):
                import random
                import time
                status_placeholder = st.empty()
                status_placeholder.info(f"📡 Transmitindo NF-e da Venda #{venda_id} ({cliente_nome}) para a SEFAZ... Valor: R$ {valor:,.2f}")
                time.sleep(0.5)
                base_backoff = 1.0  # segundos
                for attempt in range(1, max_retries + 1):
                    try:
                        if random.random() < 0.20:
                            raise Exception("Erro HTTP 503: SEFAZ fora do ar temporariamente.")
                        status_placeholder.success(f"✅ NF da Venda #{venda_id} ({cliente_nome}) autorizada na SEFAZ (Tentativa {attempt})!")
                        time.sleep(0.5)
                        status_placeholder.empty()
                        return True
                    except Exception as e:
                        if attempt == max_retries:
                            status_placeholder.error(f"🛑 Falha final: SEFAZ inalcançável após {max_retries} tentativas. Revertendo alterações.")
                            raise e
                        sleep_time = (base_backoff * (2 ** (attempt - 1))) + random.uniform(0.1, 0.5)
                        status_placeholder.warning(f"⚠️ Tentativa {attempt} falhou ({str(e)}). Retentando em {sleep_time:.2f}s...")
                        time.sleep(sleep_time)

            if col_f3.button("Processar Faturamento Selecionado", type="primary", use_container_width=True, disabled=not validacao_somas):
                p_c = fetch_all("SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
                pc_id = int(p_c.iloc[0]['id']) if not p_c.empty else None
                
                sucesso = False
                qtd_processada = 0
                
                try:
                    # Envolve tudo em uma transacao atomica
                    with db_transaction() as conn:
                        cursor = conn.cursor()
                        
                        from database import _get_modo_estoque
                        is_pg = "DATABASE_URL" in st.secrets
                        modo = _get_modo_estoque(cursor, is_pg)
                        alertas_custo_ausente = []
                        
                        # === FASE 1: AGRUPAR por pedido_grupo para NF/DAV/Financeiro ===
                        grupos_proc = {}
                        for _, row in pedidos_selecionados.iterrows():
                            pid = int(row['pedido_id'])
                            grp = row.get('pedido_grupo')
                            chave = str(grp) if grp and pd.notna(grp) else f"solo_{pid}"
                            if chave not in grupos_proc:
                                grupos_proc[chave] = []
                            grupos_proc[chave].append(row)
                        
                        dav_numeros_grupo = {}
                        bling_ids_grupo = {}
                        
                        for chave_grupo, rows_grupo in grupos_proc.items():
                            first_row = rows_grupo[0]
                            primeiro_pid = int(first_row['pedido_id'])
                            cli_id_grupo = int(first_row['cliente_id'])
                            lote_impresso = first_row.get('Lote Impresso (NF/DAV)', '')
                            validade_impressa = first_row.get('Validade (NF/DAV)', '')
                            
                            # --- DAV: Gerar 1 unico numero para todo o grupo ---
                            if "DAV" in tipo_doc:
                                df_dav_max = fetch_all_tx(cursor, "SELECT MAX(CAST(numero_documento AS INTEGER)) as max_dav FROM vendas WHERE tipo_documento LIKE '%DAV%'")
                                max_dav = df_dav_max.iloc[0]['max_dav'] if not df_dav_max.empty and pd.notna(df_dav_max.iloc[0]['max_dav']) else 0
                                novo_dav = int(max_dav) + 1
                                dav_numeros_grupo[chave_grupo] = f"{novo_dav:010d}"
                            
                            # --- NF (Bling): Enviar 1 unica NF consolidada ---
                            if "Nota Fiscal" in tipo_doc:
                                from utils_bling import enviar_faturamento_ao_bling
                                
                                itens_bling = []
                                for r in rows_grupo:
                                    itens_bling.append({
                                        'produto_id': int(r['p_id']),
                                        'quantidade': float(r['quantidade']),
                                        'valor_unitario': float(r['valor_total']) / float(r['quantidade']) if float(r['quantidade']) > 0 else 0
                                    })
                                
                                vd_first = fetch_all_tx(cursor, "SELECT flag_op_casada, filial_atacadao, pedido_atacadao_numero FROM vendas WHERE id=?", (primeiro_pid,))
                                obs_extras_grupo = ""
                                if not vd_first.empty:
                                    vf = vd_first.iloc[0]
                                    if bool(vf.get('flag_op_casada')):
                                        obs_extras_grupo = f"Operacao Casada - Filial: {vf.get('filial_atacadao','')} - Pedido Interno: {vf.get('pedido_atacadao_numero','')}"
                                
                                insts_grupo = [p for p in st.session_state['parcelas_faturamento'] if p.get('Grupo') == chave_grupo]
                                
                                bling_id = enviar_faturamento_ao_bling(
                                    venda_id_ref=f"Grupo-{chave_grupo}",
                                    cliente_id=cli_id_grupo,
                                    itens_list=itens_bling,
                                    lote=lote_impresso,
                                    validade=validade_impressa,
                                    parcelas=insts_grupo,
                                    obs_extras=obs_extras_grupo
                                )
                                bling_ids_grupo[chave_grupo] = bling_id
                            
                            # --- FINANCEIRO: Gerar duplicatas consolidadas por grupo ---
                            insts_grupo = [p for p in st.session_state['parcelas_faturamento'] if p.get('Grupo') == chave_grupo]
                            
                            fp_sel_nome = first_row['Forma de Pagamento']
                            df_fp_sel = fetch_all_tx(cursor, "SELECT id FROM formas_pagamento WHERE nome=?", (fp_sel_nome,))
                            fp_id_val = int(df_fp_sel.iloc[0]['id']) if not df_fp_sel.empty else None
                            
                            prods_desc = ", ".join([r['produto'] for r in rows_grupo])
                            cli_nome_grupo = first_row['cliente']
                            
                            for p in insts_grupo:
                                val_i = float(p['Valor (R$)'])
                                venc_i = p['Vencimento']
                                venc_str = venc_i.strftime("%Y-%m-%d") if hasattr(venc_i, 'strftime') else str(venc_i)
                                desc_i = f"{tipo_doc} ({p['Parcela']}) - Grupo {chave_grupo} ({cli_nome_grupo} - {prods_desc})"
                                
                                run_query_tx(cursor, "INSERT INTO contas_a_receber (venda_id, cliente_id, plano_conta_id, numero_documento, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                          (primeiro_pid, cli_id_grupo, pc_id, tipo_doc, desc_i, val_i, venc_str, 'PENDENTE'))
                        
                        # === FASE 2: PROCESSAR CADA ITEM INDIVIDUALMENTE ===
                        for _, row in pedidos_selecionados.iterrows():
                            pid = int(row['pedido_id'])
                            grp = row.get('pedido_grupo')
                            chave = str(grp) if grp and pd.notna(grp) else f"solo_{pid}"
                            
                            vd_df = fetch_all_tx(cursor, '''
                                SELECT v.id as pedido_id, v.data as data_pedido, c.nome as cliente, c.uf as uf_cliente, 
                                       p.nome as produto, p.id as p_id, v.quantidade, v.valor_total, v.custo_acordos_rede,
                                       v.cliente_id, v.flag_op_casada, v.filial_atacadao, v.pedido_atacadao_numero
                                FROM vendas v 
                                JOIN clientes c ON v.cliente_id=c.id
                                JOIN produtos p ON v.produto_id=p.id
                                WHERE v.id = ?
                            ''', (pid,))
                            
                            if vd_df.empty:
                                continue
                            
                            vd = vd_df.iloc[0]
                            prod_nome = vd['produto']
                            prod_id = int(vd['p_id'])
                            qtd = float(vd['quantidade'])
                            cli_id = int(vd['cliente_id'])
                            cli_nome = vd['cliente']
                            
                            lote_impresso = row.get('Lote Impresso (NF/DAV)', '')
                            validade_impressa = row.get('Validade (NF/DAV)', '')
                            
                            fp_sel_nome = row['Forma de Pagamento']
                            df_fp_sel = fetch_all_tx(cursor, "SELECT id FROM formas_pagamento WHERE nome=?", (fp_sel_nome,))
                            fp_id_val = int(df_fp_sel.iloc[0]['id']) if not df_fp_sel.empty else None
                            run_query_tx(cursor, "UPDATE vendas SET forma_pagamento_id=? WHERE id=?", (fp_id_val, pid))
                            
                            # 1. Status + Numeracao DO GRUPO
                            if "DAV" in tipo_doc:
                                dav_str = dav_numeros_grupo.get(chave, "0000000000")
                                run_query_tx(cursor, "UPDATE vendas SET status='FATURADO', tipo_documento=?, numero_documento=?, lote_impresso=?, validade_impressa=? WHERE id=?", (tipo_doc, dav_str, lote_impresso, validade_impressa, pid))
                            else:
                                bling_id = bling_ids_grupo.get(chave)
                                doc_num = f"Bling #{bling_id}" if bling_id else ""
                                run_query_tx(cursor, "UPDATE vendas SET status='FATURADO', tipo_documento=?, numero_documento=?, lote_impresso=?, validade_impressa=? WHERE id=?", (tipo_doc, doc_num, lote_impresso, validade_impressa, pid))
                            
                            # 2. Baixa de Estoque via FIFO
                            custo_cmv_real, is_estimado, cmv_metodo, custo_ausente = consumir_estoque_fifo_tx(
                                cursor=cursor,
                                produto_id=prod_id,
                                quantidade=qtd,
                                data_mov=date.today().strftime("%Y-%m-%d"),
                                origem=f'Expedicao {tipo_doc}',
                                doc_ref=f"Venda Lote #{pid}",
                                modo_estoque=modo
                            )
                            
                            run_query_tx(cursor, "UPDATE vendas SET custo_cmv_real = ?, cmv_metodo = ? WHERE id = ?", (custo_cmv_real, cmv_metodo, pid))
                            
                            if custo_ausente:
                                alertas_custo_ausente.append(prod_nome)
                            
                            # 3. Acordos de Rede
                            custo_acordos = float(vd['custo_acordos_rede']) if pd.notnull(vd['custo_acordos_rede']) else 0.0
                            if custo_acordos > 0:
                                venc_acordo = date.today() + timedelta(days=30)
                                cli_rede_df = fetch_all_tx(cursor, "SELECT rede_clientes FROM clientes WHERE id=?", (cli_id,))
                                rede_str = cli_rede_df.iloc[0]['rede_clientes'] if not cli_rede_df.empty and cli_rede_df.iloc[0]['rede_clientes'] else "Rede Desconhecida"
                                desc_acordo = f"Repasse Acordo Comercial: REDE {str(rede_str).upper()} - Venda #{pid}"
                                
                                p_c_acordo = fetch_all_tx(cursor, "SELECT id FROM planos_de_contas WHERE codigo = '2.2.2' OR nome LIKE '%Acordo%' OR nome LIKE '%Comiss%' LIMIT 1")
                                pc_acord_id = int(p_c_acordo.iloc[0]['id']) if not p_c_acordo.empty else None
                                
                                run_query_tx(cursor, "INSERT INTO contas_a_pagar (plano_conta_id, cliente_id, numero_documento, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                          (pc_acord_id, cli_id, "Acordo/Rede", desc_acordo, custo_acordos, venc_acordo.strftime("%Y-%m-%d")))
                            
                            # 4. Taxa de Descarga
                            cli_taxa_df = fetch_all_tx(cursor, "SELECT taxa_descarga, regras_descarga, nome FROM clientes WHERE id=?", (cli_id,))
                            if not cli_taxa_df.empty:
                                taxa_desc = float(cli_taxa_df.iloc[0]['taxa_descarga'] or 0.0)
                                if taxa_desc > 0:
                                    regra_str = cli_taxa_df.iloc[0]['regras_descarga'] or "Sem regras especificas"
                                    desc_taxa = f"Taxa de Descarga CD - {cli_nome} - Venda #{pid} | Regra: {regra_str}"
                                    
                                    p_c_descarga = fetch_all_tx(cursor, "SELECT id FROM planos_de_contas WHERE codigo = '2.1.5' OR nome LIKE '%Frete%' OR nome LIKE '%Descarga%' LIMIT 1")
                                    pc_desc_id = int(p_c_descarga.iloc[0]['id']) if not p_c_descarga.empty else None
                                    
                                    run_query_tx(cursor, "INSERT INTO contas_a_pagar (plano_conta_id, cliente_id, numero_documento, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')",
                                              (pc_desc_id, cli_id, "Taxa Descarga", desc_taxa, taxa_desc, date.today().strftime("%Y-%m-%d")))
                                    run_query_tx(cursor, "UPDATE vendas SET custo_descarga=? WHERE id=?", (taxa_desc, pid))
                                     
                            # 5. Comissao
                            gerar_comissao_se_necessario_tx(cursor, pid, 'FATURAMENTO', cli_nome)
                        
                        qtd_processada = len(pedidos_selecionados)
                    
                    sucesso = True
                except Exception as e:
                    st.error(f"🛑 Erro ao processar faturamento (Operação cancelada/revertida): {str(e)}")
                
                if sucesso:
                    st.success(f"✅ {qtd_processada} Pedido(s) Faturados com Sucesso! Estoque e Financeiro atualizados de forma consistente.")
                    if "DAV" in tipo_doc:
                        # Passar apenas 1 ID por grupo para evitar DAVs duplicados
                        ids_para_dav = []
                        grupos_ja_adicionados = set()
                        for _, row in pedidos_selecionados.iterrows():
                            grp = row.get('pedido_grupo')
                            chave = str(grp) if grp and pd.notna(grp) else f"solo_{int(row['pedido_id'])}"
                            if chave not in grupos_ja_adicionados:
                                grupos_ja_adicionados.add(chave)
                                ids_para_dav.append(int(row['pedido_id']))
                        st.session_state['pedidos_dav_faturados'] = ids_para_dav
                    
                    if alertas_custo_ausente:
                        produtos_unicos = ", ".join(sorted(set(alertas_custo_ausente)))
                        st.warning(f"⚠️ Produto(s) sem custo cadastrado (CMV registrado como zero): {produtos_unicos}. Cadastre o custo em Produtos.")
                        time.sleep(4)
                    else:
                        time.sleep(2)
                    st.rerun()
                
    st.markdown("---")
    with st.expander("🖨️ Reimpressão e Visualização de Documentos (DAV)"):
        st.markdown("Busque pela venda digitando o ID do Pedido ou Número da NF/DAV. Se o campo de busca estiver vazio, serão exibidas as 10 faturas mais recentes.")
        busca_reimp = st.text_input("Buscar Pedido ou NF/DAV (ID ou Número)", key="busca_reimpressao_doc").strip()
        
        # Constrói query dinâmica com base na busca
        if busca_reimp:
            q_reimp = '''
                SELECT v.id, c.nome, v.tipo_documento, v.numero_documento, v.data 
                FROM vendas v 
                JOIN clientes c ON v.cliente_id=c.id 
                WHERE v.status='FATURADO' 
                  AND (v.id = ? OR v.numero_documento LIKE ?)
                ORDER BY v.id DESC 
                LIMIT 50
            '''
            search_id = int(busca_reimp) if busca_reimp.isdigit() else -1
            search_doc = f"%{busca_reimp}%"
            df_fat = fetch_all(q_reimp, (search_id, search_doc))
        else:
            df_fat = fetch_all('''
                SELECT v.id, c.nome, v.tipo_documento, v.numero_documento, v.data 
                FROM vendas v 
                JOIN clientes c ON v.cliente_id=c.id 
                WHERE v.status='FATURADO' 
                ORDER BY v.id DESC 
                LIMIT 10
            ''')
            
        if not df_fat.empty:
            opcoes_fat = {}
            for _, r in df_fat.iterrows():
                num_doc = r['numero_documento']
                doc_desc = f" - Nº {num_doc}" if num_doc and str(num_doc).strip() else ""
                label = f"Venda #{r['id']} - {r['nome']} ({r['tipo_documento']}{doc_desc})"
                opcoes_fat[label] = r['id']
            v_sel = st.selectbox("Selecione o pedido faturado para visualizar/imprimir:", ["-- SELECIONE --"] + list(opcoes_fat.keys()), key="sb_reimpressao_venda")
            if v_sel != "-- SELECIONE --":
                vid = opcoes_fat[v_sel]
                
                # 1. Visualização do Documento (DAV ou NF) primeiro (recarregando modulo para evitar caches de import)
                import streamlit.components.v1 as components
                import sys
                import importlib
                import utils_dav
                importlib.reload(utils_dav)
                from utils_dav import buscar_dados_venda, gerar_html_dav
                
                venda_info = buscar_dados_venda(vid)
                if venda_info and "DAV" in venda_info['tipo_documento']:
                    html_dav = gerar_html_dav(venda_info)
                    components.html(html_dav, height=800, scrolling=True)
                elif venda_info:
                    # Painel de dados para NF (sem XML, mas com todas as informações do registro)
                    st.markdown("#### 🧾 Dados da Nota Fiscal Registrada")
                    df_nf_detail = fetch_all("""
                        SELECT v.id, v.data, v.numero_documento, v.tipo_documento,
                               v.valor_total, v.quantidade, v.lote_impresso, v.validade_impressa,
                               c.nome as cliente, c.cnpj_cpf, c.cidade, c.uf,
                               p.nome as produto, f.nome as vendedor
                        FROM vendas v
                        JOIN clientes c ON v.cliente_id = c.id
                        JOIN produtos p ON v.produto_id = p.id
                        LEFT JOIN funcionarios f ON v.vendedor_id = f.id
                        WHERE v.id = ?
                    """, (vid,))
                    if not df_nf_detail.empty:
                        nf = df_nf_detail.iloc[0]
                        num_nf = nf['numero_documento'] or "(Aguardando número SEFAZ)"
                        data_fat = pd.to_datetime(nf['data']).strftime('%d/%m/%Y') if pd.notna(nf['data']) else "-"
                        
                        info_col1, info_col2, info_col3 = st.columns(3)
                        info_col1.metric("Nº do Documento", num_nf)
                        info_col1.metric("Data de Faturamento", data_fat)
                        info_col1.metric("Tipo", nf['tipo_documento'])
                        
                        info_col2.metric("Cliente", nf['cliente'])
                        info_col2.metric("CNPJ/CPF", nf['cnpj_cpf'] or "(não informado)")
                        info_col2.metric("Cidade/UF", f"{nf['cidade'] or '-'} / {nf['uf'] or '-'}")
                        
                        info_col3.metric("Produto", nf['produto'])
                        info_col3.metric("Quantidade", f"{nf['quantidade']:,.2f}")
                        info_col3.metric("Valor Total", format_brl(nf['valor_total']))
                        
                        st.markdown("---")
                        det_col1, det_col2 = st.columns(2)
                        det_col1.info(f"📦 **Lote Impresso:** {nf['lote_impresso'] or '(não informado)'}")
                        det_col2.info(f"📅 **Validade Impressa:** {nf['validade_impressa'] or '(não informada)'}")
                        
                        if not num_nf or num_nf == "(Aguardando número SEFAZ)":
                            st.warning(
                                "⏳ Esta NF ainda não possui número SEFAZ registrado. "
                                "Registre o número na aba **Gerador Fiscal (SEFAZ/Emissor)** para liberar o embarque."
                            )
                        else:
                            st.success(f"✅ NF autorizada. Para reimprimir o DANFE, utilize seu Emissor SEFAZ com o número **{num_nf}**.")
        else:
            st.info("Nenhuma venda faturada encontrada.")

# ======= 2. EXPORTADOR SEFAZ =======
with tab2:
    st.subheader("📥 Exportador Fiscal (Geração de Arquivo SEFAZ)")
    st.markdown("Exporte as vendas faturadas no mês para um arquivo TXT/CSV padronizado para importação no Emissor SEFAZ de Terceiros.")
    
    hoje = date.today()
    mes_fiscal = st.selectbox("Mês de Competência do Arquivo", [hoje.strftime('%Y-%m'), (hoje - timedelta(days=30)).strftime('%Y-%m')])
    
    uf_fabrica = st.selectbox("UF Origem (Fábrica)", ["SP", "MG", "RJ", "PR", "SC", "RS", "GO", "DF", "BA", "PE", "CE"])
    
    if st.button("🔄 Consultar Faturamentos e Gerar Arquivo"):
        # Pega as vendas FATURADAS do mês
        q_sefaz = '''
            SELECT v.id as NUM_PEDIDO, c.nome as CLIENTE, c.cnpj_cpf as CNPJ, c.uf as UF_DESTINO,
                   p.nome as PRODUTO, v.quantidade as QTD, v.valor_unitario as V_UNIT, v.valor_total as V_TOTAL,
                   v.lote_impresso as LOTE_NF, v.validade_impressa as VAL_NF,
                   v.data as DATA_FATURAMENTO, v.tipo_documento as DOC_ORIGEM
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.status = 'FATURADO' 
              AND v.tipo_documento = 'Nota Fiscal (NF)'
              AND strftime('%Y-%m', v.data) = ?
        '''
        df_export = fetch_all(q_sefaz, (mes_fiscal,))
        
        if df_export.empty:
            st.warning("Nenhum faturamento encontrado neste mês de competência.")
        else:
            # Enriquecendo com CFOP Dinâmico e NCM fixo para MVP
            df_export['NCM'] = "0703.20.90"
            df_export['CFOP'] = df_export['UF_DESTINO'].apply(lambda uf: "5101" if uf == uf_fabrica else "6101")
            
            st.success(f"Pronto! {len(df_export)} registros fiscais compilados.")
            st.dataframe(df_export, hide_index=True)
            
            # Geração do Arquivo Físico para Download
            csv_bytes = df_export.to_csv(index=False, sep=";").encode('utf-8-sig')
            
            st.download_button(
                label="📥 Baixar Arquivo de Integração (CSV SEFAZ)",
                data=csv_bytes,
                file_name=f"export_sefaz_{mes_fiscal}.csv",
                mime="text/csv",
                type="primary"
            )

    # ======= CONEXÃO / SINCRONIZAÇÃO AUTOMÁTICA BLING =======
    st.markdown("---")
    st.subheader("🔄 Sincronização de Retorno Automática com o Bling")
    st.markdown("Consulte automaticamente o Bling para obter os números oficiais das Notas Fiscais autorizadas pela SEFAZ.")
    
    # Busca vendas faturadas com Bling ID mas sem número oficial de nota
    df_sync_pendentes = fetch_all('''
        SELECT id, numero_documento
        FROM vendas
        WHERE status = 'FATURADO'
          AND tipo_documento = 'Nota Fiscal (NF)'
          AND numero_documento LIKE 'Bling #%'
    ''')
    
    if df_sync_pendentes.empty:
        st.info("ℹ️ Não há Notas Fiscais pendentes de sincronização automática com o Bling.")
    else:
        st.warning(f"🔔 Existem {len(df_sync_pendentes)} Notas Fiscais faturadas aguardando retorno do Bling.")
        if st.button("🔄 Sincronizar Notas Fiscais com o Bling", type="primary", use_container_width=True):
            from utils_bling import sincronizar_nfe_do_bling
            success_sync = 0
            fail_sync = 0
            
            progress_bar = st.progress(0)
            status_txt = st.empty()
            
            for idx, r in df_sync_pendentes.iterrows():
                v_id = int(r['id'])
                doc_doc = str(r['numero_documento'])
                bling_id = doc_doc.replace("Bling #", "").strip()
                
                status_txt.markdown(f"Consultando Bling para a Venda #{v_id} (Bling ID: {bling_id})...")
                
                try:
                    num_nfe = sincronizar_nfe_do_bling(bling_id)
                    if num_nfe:
                        run_query("UPDATE vendas SET numero_documento = ? WHERE id = ?", (num_nfe, v_id))
                        success_sync += 1
                    else:
                        fail_sync += 1
                except Exception as ex:
                    st.error(f"Erro na Venda #{v_id} (Bling ID: {bling_id}): {ex}")
                    fail_sync += 1
                
                progress_bar.progress((idx + 1) / len(df_sync_pendentes))
                
            status_txt.empty()
            progress_bar.empty()
            
            if success_sync > 0:
                st.success(f"✅ {success_sync} Notas Fiscais foram sincronizadas e atualizadas com sucesso!")
            if fail_sync > 0:
                st.info(f"ℹ️ {fail_sync} Notas Fiscais ainda estão em processamento ou sem número gerado no Bling.")
                
            import time; time.sleep(1.5); st.rerun()

    st.markdown("---")
    st.subheader("✍️ Atualizar Números de Notas Fiscais Autorizadas (Retorno SEFAZ)")
    st.markdown("Digite os números oficiais das notas geradas no SEFAZ para atualizar o ERP e liberar o embarque seguro na Logística.")
    
    # Busca vendas faturadas como 'Nota Fiscal (NF)' sem número de documento
    df_nfs_pendentes = fetch_all('''
        SELECT v.id as 'Venda ID', v.data as 'Data', c.nome as 'Cliente', p.nome as 'Produto', 
               v.quantidade as 'Qtd', v.valor_total as 'Valor Total', v.numero_documento as 'Número da NF-e'
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.status = 'FATURADO'
          AND v.tipo_documento = 'Nota Fiscal (NF)'
          AND (v.numero_documento IS NULL OR v.numero_documento = '')
        ORDER BY v.id ASC
    ''')
    
    if df_nfs_pendentes.empty:
        st.success("🎉 Nenhuma Nota Fiscal faturada pendente de número oficial!")
    else:
        df_nfs_pendentes['Data'] = pd.to_datetime(df_nfs_pendentes['Data']).dt.strftime('%d/%m/%Y')
        df_nfs_pendentes['Valor Total'] = df_nfs_pendentes['Valor Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Garante que Número da NF-e seja string
        df_nfs_pendentes['Número da NF-e'] = df_nfs_pendentes['Número da NF-e'].fillna("").astype(str)
        
        st.info("💡 **Dica:** Digite as numerações diretamente na coluna **'Número da NF-e'** abaixo e clique no botão para salvar tudo de uma vez.")
        
        edited_nfs = st.data_editor(
            df_nfs_pendentes,
            hide_index=True,
            width="stretch",
            column_config={
                "Número da NF-e": st.column_config.TextColumn("📝 Número da NF-e (Digitar)", help="Insira o número oficial da nota emitida pelo SEFAZ"),
            },
            disabled=["Venda ID", "Data", "Cliente", "Produto", "Qtd", "Valor Total"]
        )
        
        if st.button("💾 Salvar Números de NF-e", type="primary", use_container_width=True):
            saved_count = 0
            for idx, row in edited_nfs.iterrows():
                v_id = int(row['Venda ID'])
                nfe_num = str(row['Número da NF-e']).strip()
                if nfe_num != "":
                    run_query("UPDATE vendas SET numero_documento = ? WHERE id = ?", (nfe_num, v_id))
                    saved_count += 1
            
            if saved_count > 0:
                st.success(f"✅ {saved_count} Notas Fiscais atualizadas com sucesso! Embarque liberado na Logística.")
                import time; time.sleep(1.5); st.rerun()
            else:
                st.warning("Nenhum número de nota foi inserido.")

# ======= 3. ESTORNAR NF / DAV =======
with tab3:
    st.subheader("🔄 Estornar / Cancelar Faturamento (NF / DAV)")
    st.markdown("Use esta tela para desfazer o faturamento de um pedido. Isso reverterá o estoque, cancelará os lançamentos financeiros e retornará o pedido para a fila de faturamento.")
    
    df_fat_est = fetch_all("SELECT v.id, c.nome, v.tipo_documento, v.numero_documento, v.data FROM vendas v JOIN clientes c ON v.cliente_id=c.id WHERE v.status='FATURADO' ORDER BY v.id DESC LIMIT 50")
    if not df_fat_est.empty:
        opcoes_est = {}
        for _, r in df_fat_est.iterrows():
            num_doc = r['numero_documento']
            doc_desc = f" - Nº {num_doc}" if num_doc and str(num_doc).strip() else ""
            label = f"Venda #{r['id']} - {r['nome']} ({r['tipo_documento']}{doc_desc})"
            opcoes_est[label] = r['id']
            
        v_sel_est = st.selectbox("Selecione o pedido faturado para Estornar/Cancelar:", ["-- SELECIONE --"] + list(opcoes_est.keys()), key="sb_estorno_venda")
        
        if v_sel_est != "-- SELECIONE --":
            vid_est = opcoes_est[v_sel_est]
            
            df_venda_manifesto = fetch_all("SELECT manifesto_id FROM vendas WHERE id = ?", (vid_est,))
            manifesto_id = df_venda_manifesto.iloc[0]['manifesto_id'] if not df_venda_manifesto.empty else None
            
            if manifesto_id is not None:
                st.error(f"🛑 **Estorno Bloqueado:** Este pedido já está vinculado ao **Manifesto de Logística #{manifesto_id}**! Remova o pedido do caminhão no módulo de Logística antes de tentar estornar o faturamento.")
            else:
                st.warning("⚠️ **Atenção:** Desfazer o faturamento é uma ação irreversível. Certifique-se de que a NF foi devidamente cancelada na SEFAZ (se aplicável).")
                
                if st.button("🔄 Confirmar e Executar Estorno de Faturamento", type="primary", use_container_width=True, key=f"btn_run_estorno_{vid_est}"):
                    # 1. Buscar movimentações originais de saída para reverter
                    df_movs = fetch_all('''
                        SELECT produto_id, quantidade, lote_origem_id 
                        FROM estoque_movimentos 
                        WHERE documento_referencia = ? AND tipo_movimento = 'Saída'
                    ''', (f"Venda Lote #{vid_est}",))
                    
                    # 2. Inserir entradas reversoras
                    for _, mov in df_movs.iterrows():
                        p_id = int(mov['produto_id'])
                        qtd = float(mov['quantidade'])
                        lote_origem = int(mov['lote_origem_id']) if pd.notnull(mov['lote_origem_id']) else None
                        
                        run_query(
                            """INSERT INTO estoque_movimentos 
                               (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id) 
                               VALUES (?, ?, 'Entrada', ?, ?, ?, ?)""",
                            (date.today().strftime("%Y-%m-%d"), p_id, qtd, 'Estorno de Faturamento', f"Estorno Venda Lote #{vid_est}", lote_origem)
                        )
                        
                    # 3. Deletar Contas a Receber associada
                    run_query("DELETE FROM contas_a_receber WHERE venda_id = ?", (vid_est,))
                    
                    # 4. Deletar Contas a Pagar associadas (descarga e acordos de rede)
                    desc_descarga = f"%Venda #{vid_est}%"
                    run_query("DELETE FROM contas_a_pagar WHERE descricao LIKE ? AND status = 'PENDENTE'", (desc_descarga,))
                    
                    # 5. Resetar registro da venda de volta para APROVADO (Pendente)
                    run_query('''
                        UPDATE vendas 
                        SET status = 'APROVADO', 
                            tipo_documento = NULL, 
                            numero_documento = NULL, 
                            custo_cmv_real = 0.0, 
                            custo_descarga = 0.0, 
                            lote_impresso = NULL, 
                            validade_impressa = NULL
                        WHERE id = ?
                    ''', (vid_est,))
                    
                    st.success("✅ **Faturamento Estornado com Sucesso!**")
                    st.info("""
                    **Ações Realizadas pelo Sistema:**
                    1. 📦 **As mercadorias foram devolvidas ao estoque** (os lotes originais foram reestabelecidos).
                    2. 💳 **O título gerado no Contas a Receber foi apagado** e também as contas a pagar de comissão e taxa de descarga associadas a esta venda.
                    3. 📝 **O pedido retornou ao status "APROVADO"** (na fila de pendentes) para que possa ser alterado, faturado novamente ou cancelado de vez comercialmente.
                    """)
                    
                    import time; time.sleep(5); st.rerun()
    else:
        st.info("Nenhuma venda faturada encontrada para estorno.")

# ======= 4. LOGISTICA REVERSA =======
with tab4:
    st.subheader("Processamento de Devoluções e Revalidação")
    st.markdown("Mercadoria que chegou podre no destino ou venceu na gôndola. Isso abaterá o imposto lá no DRE (como Logística Reversa).")
    
    with st.form("form_devol", clear_on_submit=True):
        d1, d2 = st.columns(2)
        dt_dev = d1.date_input("Data do Ocorrido")
        
        if df_clientes.empty or df_produtos.empty:
            st.warning("Cadastros incompletos.")
        else:
            c_opts_dev = {f"{r['nome']}": r['id'] for _, r in df_clientes.iterrows()}
            cli_options = ["-- SELECIONE O CLIENTE --"] + list(c_opts_dev.keys())
            cli_dev = d2.selectbox("Rede/Cliente Reclamante", cli_options)
            
            d3, d4, d5 = st.columns([2, 1, 1])
            p_opts_dev = {f"{r['nome']}": r for _, r in df_produtos.iterrows()}
            prod_options = ["-- SELECIONE O PRODUTO --"] + list(p_opts_dev.keys())
            prod_dev = d3.selectbox("Pacote/Produto Avariado", prod_options)
            qtd_dev = d4.number_input("Carga Negada (Un/Kg)", min_value=0.1, step=1.0)
            
            if prod_dev != "-- SELECIONE O PRODUTO --":
                p_base = float(p_opts_dev[prod_dev]['preco_venda_base'])
                val_sug = float(qtd_dev * p_base)
            else:
                val_sug = 0.0
            valor_abatido = d5.number_input("Sangria Financeira R$ (Amargar no DRE)", value=val_sug, min_value=0.0)
            
            d6, d7 = st.columns([1, 2])
            motivo = d6.selectbox("Fator", ["Alho Esponjoso / Mofo", "Vencimento na Gôndola (S/ Giro)", "Amassado pelo Carga", "Quebra Direta"])
            obs_dev = d7.text_input("Nota Restritiva")
            
            if st.form_submit_button("Protocolar Sangria (Estornar Dinheiro da Fábrica)"):
                if cli_dev == "-- SELECIONE O CLIENTE --":
                    st.error("Por favor, selecione a Rede/Cliente Reclamante.")
                elif prod_dev == "-- SELECIONE O PRODUTO --":
                    st.error("Por favor, selecione o Pacote/Produto Avariado.")
                else:
                    c_id = c_opts_dev[cli_dev]
                    p_id = p_opts_dev[prod_dev]['id']
                    
                    # --- LÓGICA FINANCEIRA (DRE) ---
                    run_query("INSERT INTO devolucoes (data, cliente_id, produto_id, quantidade, motivo, valor_financeiro_abatido, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (dt_dev, c_id, p_id, qtd_dev, motivo, valor_abatido, obs_dev))
                              
                    run_query("INSERT INTO fluxo_caixa (data, tipo, categoria, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                              (dt_dev, "Saída", "Logística Reversa (Devoluções)", valor_abatido, f"Estorno: {cli_dev} ({qtd_dev}x {prod_dev}) - {motivo}"))
                              
                    # --- LÓGICA DE ESTOQUE FÍSICO (Retorno com Custo Zero) ---
                    # 1. Busca Saldo Atual
                    df_saldo = fetch_all("SELECT SUM(CASE WHEN tipo_movimento = 'Entrada' THEN quantidade ELSE -quantidade END) as saldo FROM estoque_movimentos WHERE produto_id = ?", (p_id,))
                    saldo_atual = float(df_saldo.iloc[0]['saldo']) if not df_saldo.empty and pd.notna(df_saldo.iloc[0]['saldo']) else 0.0
                    if saldo_atual < 0: saldo_atual = 0.0 # Previne anomalias matemáticas
                    
                    # 2. Busca Custo Atual
                    df_custo = fetch_all("SELECT custo_unidade FROM produtos WHERE id = ?", (p_id,))
                    custo_atual = float(df_custo.iloc[0]['custo_unidade']) if not df_custo.empty and pd.notna(df_custo.iloc[0]['custo_unidade']) else 0.0
                    
                    # 3. Calcula o Custo Médio Ponderado (O lote devolvido entra valendo R$ 0,00)
                    novo_saldo = saldo_atual + qtd_dev
                    novo_custo_medio = (saldo_atual * custo_atual + qtd_dev * 0.0) / novo_saldo if novo_saldo > 0 else custo_atual
                    
                    # 4. Atualiza o cadastro do produto com o custo barateado
                    run_query("UPDATE produtos SET custo_unidade = ? WHERE id = ?", (novo_custo_medio, p_id))
                    
                    # 5. Dá a Entrada Física no Galpão
                    run_query("INSERT INTO estoque_movimentos (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia) VALUES (?, ?, ?, ?, ?, ?)",
                              (dt_dev, p_id, 'Entrada', qtd_dev, 'Devolução de Cliente', f"Motivo: {motivo} (Cliente: {cli_dev})"))
    
                    st.error(f"Devolução Homologada! Mercadoria retornou ao estoque com custo R$0,00. Custo médio do produto caiu para R$ {novo_custo_medio:.2f}. Impacto DRE: R$ -{valor_abatido:,.2f}")
                    st.cache_data.clear()
                    import time; time.sleep(4); st.rerun()
            
    st.markdown("---")
    df_dev = fetch_all('''
       SELECT d.id as Req, d.data as Data, c.nome as Conta, p.nome as Carga, d.quantidade as Qtd, d.motivo as Causa, d.valor_financeiro_abatido as 'Estorno Financeiro'
       FROM devolucoes d JOIN clientes c ON d.cliente_id=c.id JOIN produtos p ON d.produto_id=p.id ORDER BY d.id DESC LIMIT 50
    ''')
    if not df_dev.empty:
        df_dev['Data'] = pd.to_datetime(df_dev['Data'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_dev['Estorno Financeiro'] = df_dev['Estorno Financeiro'].apply(format_brl)
        st.dataframe(df_dev, hide_index=True, width="stretch")
