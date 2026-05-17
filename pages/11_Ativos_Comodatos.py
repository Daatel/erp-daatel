import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import fetch_all, run_query
from estilo import carregar_estilo
from fpdf import FPDF
import io

def gerar_pdf_comodato(empresa_info, cli_info, maq_info, data_ini, meses, data_venc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    
    # Título
    pdf.cell(0, 10, "MINUTA DE CONTRATO DE COMODATO DE EQUIPAMENTO - USO EXCLUSIVO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Partes
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "PARTES:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"COMODANTE: {empresa_info['razao_social']} - CNPJ: {empresa_info['cnpj']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"ENDEREÇO COMODANTE: {empresa_info['endereco_completo']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.cell(0, 6, f"COMODATÁRIO: {cli_info['razao_social']} - A/C {cli_info['nome']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"CNPJ/CPF: {cli_info['cnpj']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"ENDEREÇO DE INSTALAÇÃO: {cli_info['endereco_completo']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Cláusulas
    texto_clausulas = f"""1. OBJETO E IDENTIFICAÇÃO DO BEM
O COMODANTE cede ao COMODATÁRIO, a título de empréstimo gratuito (comodato), o seguinte equipamento:
- MARCA/MODELO: {maq_info['nome']}
- NÚMERO DE SÉRIE: {maq_info['numero_serie'] if maq_info['numero_serie'] else 'N/A'} (Patrimônio: {maq_info['patrimônio']})
- ESTADO: Equipamento revisado, adesivado com a identidade visual "{empresa_info['nome_fantasia']}".

2. DA EXCLUSIVIDADE ABSOLUTA (CLÁUSULA DE BARREIRA)
O COMODATÁRIO obriga-se a utilizar o equipamento identificado na Cláusula 1 EXCLUSIVAMENTE para o armazenamento, exposição e comercialização de produtos da marca {empresa_info['nome_fantasia']}.
2.1. É expressamente proibida a guarda de produtos de terceiros, concorrentes ou de qualquer outra natureza (bebidas, gelo, outros alimentos) no interior do equipamento.
2.2. A presença de um único item não autorizado no interior do freezer configurará quebra contratual imediata.

3. DA MANUTENÇÃO DA MARCA E ADESIVAGEM
O COMODATÁRIO compromete-se a manter a integridade visual do equipamento.
3.1. Proíbe-se a colagem de cartazes, preços ou qualquer material que obstrua a logomarca "{empresa_info['nome_fantasia']}".
3.2. O equipamento deve ser mantido em local visível ao consumidor final, com a face adesivada voltada para o fluxo de clientes.

4. DA FISCALIZAÇÃO E VIGÊNCIA
4. DA FISCALIZAÇÃO E VIGÊNCIA
O contrato terá vigência de {meses} meses, iniciando em {data_ini.strftime('%d/%m/%Y')} e vencendo em {data_venc.strftime('%d/%m/%Y')}. O COMODANTE ({empresa_info['nome_fantasia']}), por meio de seus representantes, terá livre acesso ao estabelecimento em horário comercial, sem necessidade de aviso prévio, para vistoriar o cumprimento das cláusulas de exclusividade e conservação.

5. CUSTOS OPERACIONAIS E SINISTROS
5.1. As despesas de energia elétrica para o funcionamento do equipamento correm por conta exclusiva do COMODATÁRIO.
5.2. Em caso de furto, roubo ou danos por mau uso, o COMODATÁRIO deverá indenizar o COMODANTE pelo valor integral do equipamento (R$ {maq_info['valor_aquisicao']:,.2f}).

6. RESCISÃO E RETIRADA
6.1. O descumprimento da Cláusula de Exclusividade (Cláusula 2) autoriza o COMODANTE a rescindir o contrato imediatamente e retirar o bem em até 24 horas.
6.2. Em caso de rescisão por desinteresse comercial, a parte interessada deverá notificar a outra com 07 dias de antecedência.

7. FORO
Fica eleito o foro da sede do COMODANTE para dirimir quaisquer dúvidas."""

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, texto_clausulas)
    pdf.ln(15)
    
    # Assinaturas
    pdf.cell(0, 6, f"Data de Emissão: {data_ini.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.ln(10)
    
    c_width = pdf.epw / 2
    y_before = pdf.get_y()
    
    # Assinatura 1
    pdf.set_xy(pdf.l_margin, y_before)
    pdf.cell(c_width - 10, 5, "_" * 40, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(c_width - 10, 5, "COMODANTE", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(c_width - 10, 5, f"({empresa_info['razao_social']})", new_x="LMARGIN", new_y="NEXT", align="C")
    
    # Assinatura 2
    pdf.set_xy(pdf.l_margin + c_width, y_before)
    pdf.cell(c_width - 10, 5, "_" * 40, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(c_width - 10, 5, "COMODATÁRIO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(c_width - 10, 5, f"({cli_info['razao_social'][:30]})", new_x="LMARGIN", new_y="NEXT", align="C")
    
    return pdf.output(dest="S")

st.set_page_config(page_title="Gestão de Comodatos", page_icon="❄️", layout="wide")
carregar_estilo()

st.title("❄️ Ativos e Comodatos")
st.markdown("Controle de equipamentos cedidos a clientes, contratos automáticos e análise de ROI/Volume de Vendas.")

# Abas
tab1, tab2, tab3 = st.tabs(["🚀 Ativar Novo Comodato", "📋 Painel de Equipamentos Cedidos", "🧊 Cadastro de Freezers/Ativos"])

# ==========================================
# TAB 3: CADASTRO DE EQUIPAMENTOS
# ==========================================
with tab3:
    st.subheader("Cadastrar/Editar Equipamentos (Maquinário)")
    with st.form("form_equipamento", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        nome_eq = c1.text_input("Nome/Modelo do Equipamento (Ex: Freezer Metalfrio 400L)")
        patrimonio = c2.text_input("Nº do Patrimônio (Plaqueta)")
        num_serie = c3.text_input("Número de Série")
        
        c4, c5, c6 = st.columns(3)
        valor_aq = c4.number_input("Valor de Aquisição (R$)", min_value=0.0)
        vida_util = c5.number_input("Vida Útil Estimada (Anos)", min_value=0.0, value=10.0)
        data_aq = c6.date_input("Data de Aquisição")
        
        if st.form_submit_button("Salvar Equipamento"):
            dep_mensal = (valor_aq / vida_util) / 12 if vida_util > 0 else 0
            query = """
            INSERT INTO maquinario (nome, patrimônio, numero_serie, valor_aquisicao, vida_util_anos, valor_depreciacao_mensal, data_aquisicao, localizacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Fábrica')
            """
            run_query(query, (nome_eq, patrimonio, num_serie, valor_aq, vida_util, dep_mensal, data_aq))
            st.success("Equipamento cadastrado com sucesso! Já disponível para comodato.")
            import time; time.sleep(1); st.rerun()

# ==========================================
# TAB 1: ATIVAR NOVO COMODATO
# ==========================================
with tab1:
    st.subheader("Vincular Equipamento a Cliente")
    
    # Pega apenas equipamentos que estão na fábrica
    df_maq_disp = fetch_all("SELECT id, nome, patrimônio FROM maquinario WHERE localizacao = 'Fábrica' AND status = 'ATIVO'")
    df_clientes = fetch_all("SELECT id, nome as razao_social, cnpj_cpf as cnpj, endereco || ' - ' || cidade || '/' || uf as endereco_completo, nome FROM clientes WHERE status = 'ATIVO' ORDER BY nome")
    
    if df_maq_disp.empty:
        st.warning("⚠️ Não há freezers/equipamentos disponíveis na Fábrica. Cadastre na aba ao lado ou encerre um comodato atual.")
    elif df_clientes.empty:
        st.warning("⚠️ Nenhum cliente cadastrado.")
    else:
        with st.form("form_comodato"):
            c_cli, c_maq = st.columns(2)
            
            cli_dict = {f"{r['nome']} - CNPJ: {r['cnpj']}": r['id'] for _, r in df_clientes.iterrows()}
            maq_dict = {f"[{r['patrimônio']}] {r['nome']}": r['id'] for _, r in df_maq_disp.iterrows()}
            
            sel_cli = c_cli.selectbox("Cliente Destino", list(cli_dict.keys()))
            sel_maq = c_maq.selectbox("Equipamento (Freezer)", list(maq_dict.keys()))
            
            d1, d2 = st.columns(2)
            data_ini = d1.date_input("Data de Envio do Freezer", value=date.today())
            meses = d2.number_input("Duração do Contrato (Meses)", min_value=1, value=12, max_value=60)
            
            if st.form_submit_button("Ativar Comodato & Gerar Contrato", use_container_width=True):
                cli_id = cli_dict[sel_cli]
                maq_id = maq_dict[sel_maq]
                data_venc = data_ini + timedelta(days=30*meses)
                
                # 1. Cria comodato
                run_query("INSERT INTO comodatos (maquina_id, cliente_id, data_inicio, data_vencimento) VALUES (?, ?, ?, ?)",
                          (maq_id, cli_id, data_ini, data_venc))
                # 2. Atualiza localizacao da maquina
                run_query("UPDATE maquinario SET localizacao = 'Cliente' WHERE id = ?", (maq_id,))
                
                st.success(f"✅ Equipamento transferido em sistema. Contrato ativo até {data_venc.strftime('%d/%m/%Y')}!")
                
                # Simulação do texto do contrato para o usuário
                # Coleta dados para o PDF
                df_emp = fetch_all("SELECT * FROM empresa_config LIMIT 1")
                empresa_info = df_emp.iloc[0] if not df_emp.empty else pd.Series({"razao_social": "Sua Empresa LTDA", "cnpj": "00.000.000/0000-00", "endereco_completo": "Endereço não cadastrado", "nome_fantasia": "Sua Empresa"})
                
                cli_info = df_clientes[df_clientes['id'] == cli_id].iloc[0]
                maq_info = df_maq_disp[df_maq_disp['id'] == maq_id].iloc[0]
                
                pdf_bytes = gerar_pdf_comodato(empresa_info, cli_info, maq_info, data_ini, meses, data_venc)
                
                st.download_button(
                    label="📄 Baixar Contrato em PDF (Pronto para Impressão)",
                    data=pdf_bytes,
                    file_name=f"Comodato_{cli_info['cnpj']}_{maq_info['patrimônio']}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
                st.info("Imprima este contrato em 2 vias para entregar ao motorista.")

# ==========================================
# TAB 2: PAINEL DE EQUIPAMENTOS (ROI / VOLUME)
# ==========================================
with tab2:
    st.subheader("Farol de Rentabilidade de Freezers")
    st.markdown("Cruzamento da localização física do freezer com o volume total que o cliente faturou desde que recebeu o equipamento.")
    
    query_painel = """
    SELECT c.id as com_id, m.nome as Equipamento, m.patrimônio as Patrimonio, cl.nome as Cliente, cl.id as cid,
           c.data_inicio, c.data_vencimento
    FROM comodatos c
    JOIN maquinario m ON c.maquina_id = m.id
    JOIN clientes cl ON c.cliente_id = cl.id
    WHERE c.status = 'ATIVO'
    """
    df_comodatos = fetch_all(query_painel)
    
    if df_comodatos.empty:
        st.info("Nenhum equipamento em comodato ativo.")
    else:
        painel_data = []
        for _, row in df_comodatos.iterrows():
            cid = row['cid']
            d_ini = pd.to_datetime(row['data_inicio'])
            
            # Busca todas as vendas (faturadas) DESDE que o comodato iniciou
            df_vendas = fetch_all("SELECT valor_total, quantidade FROM vendas WHERE cliente_id = ? AND data >= ? AND status = 'FATURADO'", (cid, d_ini.strftime('%Y-%m-%d')))
            
            vol_kg = df_vendas['quantidade'].sum() if not df_vendas.empty else 0
            faturamento = df_vendas['valor_total'].sum() if not df_vendas.empty else 0
            
            dias_com = (pd.to_datetime('today') - d_ini).days
            dias_com = 1 if dias_com == 0 else dias_com
            media_dia = faturamento / dias_com
            
            # Regra de negócio fictícia: Mínimo de R$ 50/dia (R$ 1500/mês) para o freezer valer a pena
            status_roi = "🟢 LUCRO" if media_dia > 50 else "🔴 DEFICIT"
            if vol_kg == 0:
                status_roi = "🔴 ZERO VENDAS"
                
            painel_data.append({
                "Equipamento": f"[{row['Patrimonio']}] {row['Equipamento']}",
                "Cliente": row['Cliente'],
                "Início": d_ini.strftime('%d/%m/%Y'),
                "Dias de Uso": dias_com,
                "Volume (Un/Kg)": vol_kg,
                "Faturado (R$)": f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "Status de Giro": status_roi,
                "Ação": "Manter" if "LUCRO" in status_roi else "Notificar/Recolher"
            })
            
        st.dataframe(pd.DataFrame(painel_data), hide_index=True, use_container_width=True)
