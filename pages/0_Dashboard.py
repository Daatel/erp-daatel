import streamlit as st
import pandas as pd
from pathlib import Path
from database import fetch_all

st.set_page_config(
    page_title="Gestão Fábrica de Alho - Dashboard",
    page_icon="🧄",
    layout="wide"
)

from estilo import carregar_estilo
carregar_estilo()

st.title("Dashboard Executivo")

st.markdown(f"Bem-vindo, **{st.session_state.get('logged_user', 'Usuário')}**. Abaixo está o resumo da operação.")

# KPIs resumidos
st.subheader("Resumo Geral")

col1, col2, col3, col4 = st.columns(4)

try:
    # Busca fluxo de caixa geral
    df_caixa = fetch_all("SELECT tipo, valor FROM fluxo_caixa")
    if not df_caixa.empty:
        entradas = df_caixa[df_caixa['tipo'] == 'Entrada']['valor'].sum()
        saidas = df_caixa[df_caixa['tipo'] == 'Saída']['valor'].sum()
        saldo = entradas - saidas
    else:
        entradas = 0
        saidas = 0
        saldo = 0

    col1.metric("Saldo em Caixa", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Total Entradas", f"R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Total Saídas", f"R$ {saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Total Funcionários Ativos
    df_func = fetch_all("SELECT COUNT(id) as total FROM funcionarios")
    total_func = df_func.iloc[0]['total'] if not df_func.empty else 0
    col4.metric("Funcionários Cadastrados", total_func)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

st.divider()

# ======= RASTREADOR VISUAL DE PEDIDOS (LIFECYCLE PIPELINE) =======
st.subheader("🔍 Rastreador Visual de Linha do Tempo do Pedido")
st.markdown("Busque e rastreie o andamento do ciclo de vida de qualquer venda registrada no ERP em tempo real.")

df_vendas_todas = fetch_all('''
    SELECT v.id, c.nome as cliente_nome
    FROM vendas v
    JOIN clientes c ON v.cliente_id = c.id
    ORDER BY v.id DESC LIMIT 100
''')

if df_vendas_todas.empty:
    st.info("Nenhum pedido cadastrado no sistema para ser rastreado.")
else:
    venda_opcoes = {f"Pedido #{r['id']} - {r['cliente_nome']}": r['id'] for _, r in df_vendas_todas.iterrows()}
    pedido_sel = st.selectbox("Selecione um pedido recente para rastrear:", ["-- SELECIONE --"] + list(venda_opcoes.keys()))
    
    def exibir_stepper(etapa_atual):
        etapas = [
            {"nome": "Captação", "icon": "📝", "desc": "Pedido Comercial"},
            {"nome": "Faturamento", "icon": "📦", "desc": "Estoque & Financeiro"},
            {"nome": "Expedição", "icon": "🚛", "desc": "Carga Despachada"},
            {"nome": "Entregue", "icon": "🏁", "desc": "Canhoto Confirmado"}
        ]
        
        html = '<div style="display: flex; justify-content: space-between; align-items: center; padding: 25px 10px; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;">'
        for i, et in enumerate(etapas):
            num = i + 1
            is_completed = num <= etapa_atual
            is_active = num == etapa_atual
            
            if is_active:
                bg_color = "#292d77"
                text_color = "#ffffff"
                border_style = "border: 2px solid #292d77; box-shadow: 0 0 10px rgba(41, 45, 119, 0.4);"
                label_color = "#292d77"
            elif is_completed:
                bg_color = "#01743d"
                text_color = "#ffffff"
                border_style = "border: 2px solid #01743d;"
                label_color = "#01743d"
            else:
                bg_color = "#f1f3f5"
                text_color = "#adb5bd"
                border_style = "border: 2px dashed #dee2e6;"
                label_color = "#6c757d"
                
            html += f'''
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; text-align: center;">
                <div style="width: 50px; height: 50px; border-radius: 50%; background: {bg_color}; color: {text_color}; display: flex; justify-content: center; align-items: center; font-size: 20px; {border_style} font-weight: bold; transition: all 0.3s ease;">
                    {et['icon']}
                </div>
                <div style="margin-top: 10px; font-weight: bold; color: {label_color}; font-size: 13px;">{et['nome']}</div>
                <div style="font-size: 11px; color: #868e96; margin-top: 2px; padding: 0 5px;">{et['desc']}</div>
            </div>
            '''
            
            if i < 3:
                line_color = "#01743d" if (num < etapa_atual) else "#dee2e6"
                line_style = "solid" if (num < etapa_atual) else "dashed"
                html += f'''
                <div style="flex: 1.5; height: 4px; background: {line_color}; border-top: 1px {line_style} {line_color}; margin-top: -30px; transition: all 0.3s ease;"></div>
                '''
                
        html += '</div>'
        return html

    if pedido_sel != "-- SELECIONE --":
        vid = venda_opcoes[pedido_sel]
        
        # Puxa informações detalhadas do pedido
        df_det = fetch_all('''
            SELECT v.id, v.data, v.status, v.tipo_documento, v.numero_documento,
                   v.valor_total, v.comprovante_url,
                   c.nome as cliente, c.cidade, c.uf,
                   vn.nome as vendedor,
                   p.nome as produto, v.quantidade,
                   v.manifesto_id,
                   m.motorista_nome, m.placa_veiculo, m.status as manifesto_status, m.data_saida
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.id
            JOIN funcionarios vn ON v.vendedor_id = vn.id
            JOIN produtos p ON v.produto_id = p.id
            LEFT JOIN manifestos_carga m ON v.manifesto_id = m.id
            WHERE v.id = ?
        ''', (vid,))
        
        if not df_det.empty:
            row = df_det.iloc[0]
            
            comprovante = row['comprovante_url']
            has_comprovante = comprovante and str(comprovante).strip() != ""
            manifesto_status = row['manifesto_status']
            is_delivered = has_comprovante or (manifesto_status == 'CONCLUÍDO (CANHOTOS OK)')
            
            if is_delivered:
                etapa = 4
            elif row['manifesto_id'] is not None:
                etapa = 3
            elif row['status'] == 'FATURADO':
                etapa = 2
            else:
                etapa = 1
                
            # Renderiza stepper visual
            st.markdown(exibir_stepper(etapa), unsafe_allow_html=True)
            
            # Detalhes em cards estruturados
            st.markdown("#### 📋 Histórico do Ciclo de Vida do Pedido")
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.markdown(f"""
                <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;border:1px solid #dee2e6;min-height:220px;'>
                    <h5 style='color:#292d77;margin-top:0;'>🛒 Detalhes Comerciais</h5>
                    <b>Pedido ID:</b> #{row['id']}<br>
                    <b>Cliente:</b> {row['cliente']} ({row['cidade']} - {row['uf']})<br>
                    <b>Produto Comercial:</b> {row['produto']} (x {row['quantidade']:.0f} UN)<br>
                    <b>Vendedor:</b> {row['vendedor']}<br>
                    <b>Data de Captação:</b> {pd.to_datetime(row['data']).strftime('%d/%m/%Y')}<br><br>
                    <span style='font-size:16px;font-weight:bold;color:#01743d;'>Total: R$ {row['valor_total']:,.2f}</span>
                </div>
                """, unsafe_allow_html=True)
                
            with col_t2:
                # Construção dos detalhes das etapas
                etapa_detalhes = []
                
                # Etapa 1: Captação
                etapa_detalhes.append(f"🟢 **[Etapa 1] Captação:** Pedido registrado e aprovado comercialmente em {pd.to_datetime(row['data']).strftime('%d/%m/%Y')} pelo vendedor {row['vendedor']}.")
                
                # Etapa 2: Faturamento
                if etapa >= 2:
                    tipo = row['tipo_documento'] or "Nota Fiscal (NF)"
                    num = row['numero_documento']
                    if "DAV" in tipo:
                        doc_label = f"DAV #{str(num).zfill(10)}" if num else f"DAV #{row['id']}"
                    else:
                        doc_label = f"NF-e #{num}" if (num and str(num).strip() != "") else "NF-e (Pendente de número SEFAZ)"
                    etapa_detalhes.append(f"🟢 **[Etapa 2] Faturamento:** Baixado do estoque físico e faturado como **{doc_label}**.")
                else:
                    etapa_detalhes.append("⏳ **[Etapa 2] Faturamento:** Pendente na Fila de Faturamento. Aguardando baixa física do estoque.")
                    
                # Etapa 3: Roteirização
                if etapa >= 3:
                    dt_s = pd.to_datetime(row['data_saida']).strftime('%d/%m/%Y') if row['data_saida'] else "Em trânsito"
                    etapa_detalhes.append(f"🟢 **[Etapa 3] Expedição:** Despachado no manifesto **#{row['manifesto_id']}** em {dt_s}. Motorista: **{row['motorista_nome']}** | Placa: **{row['placa_veiculo']}**.")
                else:
                    etapa_detalhes.append("⏳ **[Etapa 3] Expedição:** Aguardando roteirização no galpão.")
                    
                # Etapa 4: Entrega
                if etapa >= 4:
                    etapa_detalhes.append("🟢 **[Etapa 4] Entrega:** Carga entregue e canhoto físico assinado/confirmado pelo motorista no galpão.")
                else:
                    etapa_detalhes.append("⏳ **[Etapa 4] Entrega:** Aguardando encerramento da viagem e upload do comprovante.")
                    
                detalhes_str = "<br><br>".join(etapa_detalhes)
                st.markdown(f"""
                <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;border:1px solid #dee2e6;font-size:12.5px;min-height:220px;line-height:1.4;'>
                    <h5 style='color:#01743d;margin-top:0;'>⚙️ Rastreabilidade de Etapas</h5>
                    {detalhes_str}
                </div>
                """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.info("Utilize as opções no menu à esquerda para navegar pelas outras seções do ERP.")
