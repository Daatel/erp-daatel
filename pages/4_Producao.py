import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import run_query, fetch_all, db_transaction, run_query_tx, fetch_all_tx, get_produtos_cached
from estilo import carregar_estilo

st.set_page_config(page_title="Produção e Custeio", page_icon="🏭", layout="wide")
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
<h1>Centro de Comando de Produção</h1>
""", unsafe_allow_html=True)


# Inicializa o controle dinâmico (Botão Mágico + Insumos)
if 'num_insumos' not in st.session_state:
    st.session_state['num_insumos'] = 3

df_produtos = get_produtos_cached()
if df_produtos.empty:
    st.warning("Cadastre produtos primeiro na aba de Cadastros.")
    st.stop()

df_mp = df_produtos[df_produtos['is_materia_prima'] == 1]
df_pf = df_produtos[df_produtos['is_materia_prima'] == 0]

if df_mp.empty or df_pf.empty:
    st.error("Sem Insumos ou Produtos Finais cadastrados. Você precisa de ambos para produzir.")
    st.stop()

# Dicts para facilitar o acesso (nome -> dict_com_dados)
mp_dict = {row['nome']: row for _, row in df_mp.iterrows()}
pf_dict = {row['nome']: row for _, row in df_pf.iterrows()}

opcoes_insumo = ["(Nenhum Insumo)"] + list(mp_dict.keys())

tab1, tab2 = st.tabs(["🏭 Apontamento de Novo Lote", "📜 Histórico de Produção"])

# =========================================================
# TAB 1: APONTAMENTO E CUSTEIO
# =========================================================
with tab1:
    with st.form("form_producao", clear_on_submit=True):
        st.subheader("⏱️ 1. Setup de Lote e Temporalidade")
        st.markdown("A duração da máquina ligada definirá o rateio de custo de Overhead (Energia, Salários, etc).")
        
        col1, col2, col3, col_val = st.columns(4)
        data_prod = col1.date_input("Data Oficial da Produção", value=date.today())
        hr_ini = col2.time_input("Que Horas a Linha Começou?", value=datetime.strptime("08:00", "%H:%M").time())
        hr_fim = col3.time_input("Que Horas a Linha Parou?", value=datetime.strptime("17:00", "%H:%M").time())
        data_validade = col_val.date_input("Data de Validade (Lote)", value=date.today() + timedelta(days=90))
        
        # O Custo Fixo Mensal é internalizado para o encarregado não ver cifras. (Cálculo em background)
        custo_fixo_mensal = 20000.0
        
        st.markdown("---")
        st.subheader("🎁 2. O Que Vamos Produzir?")
        col5, col6 = st.columns(2)
        pf_options = ["-- SELECIONE O PRODUTO --"] + list(pf_dict.keys())
        produto_gerado = col5.selectbox("Produto Final Embalado e Pronto", pf_options)
        pf_gerado_qtd = col6.number_input("Volume a Produzir (unidades do produto)", min_value=0.0, step=1.0, format="%.3f")
        
        perdas_kg = st.number_input("Perda Física Declarada da Esteira (Ex: Cascas, Sujeira - em Kg)", min_value=0.0, step=0.1)
        observacoes = st.text_area("Diário de Bordo (Ocorrências do Lote)")

        submitted = st.form_submit_button("🏁 Cravar Lote e Calcular Custos", type="primary", use_container_width=True)

    # ── Ficha Técnica: sugere ingredientes FORA do form (reage ao selectbox) ──
    st.markdown("---")
    st.subheader("🧪 3. A Receita (Ingredientes consumidos)")

    pf_id_prod = int(pf_dict[produto_gerado]['id']) if (produto_gerado and produto_gerado != "-- SELECIONE O PRODUTO --") else None

    # Carrega ficha técnica do produto selecionado
    df_ficha_prod = fetch_all(
        "SELECT id, rendimento_percentual FROM fichas_tecnicas WHERE produto_id=?",
        (pf_id_prod,)
    ) if pf_id_prod else pd.DataFrame()

    if not df_ficha_prod.empty:
        ficha_prod_id   = int(df_ficha_prod.iloc[0]['id'])
        rend_prod       = float(df_ficha_prod.iloc[0]['rendimento_percentual'])
        df_itens_prod   = fetch_all("""
            SELECT p.id as insumo_id, p.nome as insumo_nome,
                   p.unidade_medida as unidade, p.custo_unidade,
                   fti.quantidade_por_unidade, fti.tipo
            FROM fichas_tecnicas_itens fti
            JOIN produtos p ON fti.insumo_id = p.id
            WHERE fti.ficha_id = ?
            ORDER BY fti.tipo DESC, p.nome
        """, (ficha_prod_id,))

        if not df_itens_prod.empty and pf_gerado_qtd > 0:
            st.info(
                f"📋 Ficha Técnica carregada para **{produto_gerado}** "
                f"(Rendimento: {rend_prod:.1f}%). "
                f"Quantidades sugeridas para **{pf_gerado_qtd:.0f} unidades**:"
            )
            for _, it_prod in df_itens_prod.iterrows():
                qtd_sug = it_prod['quantidade_por_unidade'] * pf_gerado_qtd
                emoji   = "🌾" if it_prod['tipo'] == "MP" else "📦"
                st.markdown(
                    f"  {emoji} **{it_prod['insumo_nome']}**: "
                    f"`{qtd_sug:.3f} {it_prod['unidade']}`  "
                    f"*(ficha: {it_prod['quantidade_por_unidade']:.4f} por unidade)*"
                )
        elif pf_gerado_qtd == 0:
            st.info("Informe o volume a produzir acima para ver as quantidades sugeridas.")
        else:
            st.info("Ficha técnica encontrada. Informe o volume para ver as sugestões.")
    else:
        st.warning(
            f"⚠️ **{produto_gerado}** ainda não tem Ficha Técnica cadastrada. "
            "Acesse **Cadastros → 🧪 Fichas Técnicas** para criar."
        )

    st.markdown("##### Informe os insumos realmente consumidos:")
    st.markdown("Preencha o que foi puxado e o que sobrou intacto (o sistema calcula o consumo líquido).")

    insumos_selecionados = []
    qtds_selecionadas = []

    opcoes_insumo = ["(Nenhum Insumo)"] + list(mp_dict.keys())

    for i in range(st.session_state['num_insumos']):
        ci1, ci2, ci3 = st.columns([2, 1, 1])
        ins = ci1.selectbox(f"📦 Slot Insumo {i+1}", opcoes_insumo, key=f"insumo_{i}")
        qtd_puxada = ci2.number_input(f"Qtd Puxada {i+1}", min_value=0.0, step=1.0, format="%.3f", key=f"qtd_puxada_{i}")
        sobra = ci3.number_input(f"Sobra Intacta (Retorno) {i+1}", min_value=0.0, step=1.0, format="%.3f", key=f"sobra_{i}")
        
        insumos_selecionados.append(ins)
        qtds_selecionadas.append((qtd_puxada, sobra))

    # Botão Dinâmico (Fora do form)
    if st.button("➕ Adicionar mais um Ingrediente na Receita"):
        st.session_state['num_insumos'] += 1
        st.rerun()
        
    if submitted:
        insumos_usados = []
        for item, (qt_puxada, sobra) in zip(insumos_selecionados, qtds_selecionadas):
            qt_consumida = qt_puxada - sobra
            if item != "(Nenhum Insumo)" and qt_puxada > 0:
                if qt_consumida < 0:
                    st.error(f"🛑 Erro: A sobra do insumo {item} não pode ser maior que a quantidade puxada.")
                    st.stop()
                insumos_usados.append((item, qt_puxada, sobra, qt_consumida))
                
        if produto_gerado == "-- SELECIONE O PRODUTO --":
            st.error("🛑 Erro: Por favor, selecione o Produto Final Embalado e Pronto.")
        elif not insumos_usados:
            st.error("🛑 Erro: A máquina precisa consumir pelo menos 1 Insumo/Matéria-Prima.")
        elif pf_gerado_qtd <= 0:
            st.error("🛑 Erro: O Volume Útil Gerado de produto pronto deve ser maior que zero.")
        else:
            pf_id = int(pf_dict[produto_gerado]['id'])
            
            # --- CÁLCULO DE CUSTOS (A Magia Financeira) ---
            
            # 1. Custo das Matérias-Primas (Aqui a perda já é absorvida, pois paga-se por tudo que entrou na máquina)
            custo_total_mp = 0.0
            for item_nome, qt_p, sob, qt_c in insumos_usados:
                c_unit = float(mp_dict[item_nome]['custo_unidade'] or 0.0)
                custo_total_mp += (qt_c * c_unit)
                
            # 2. Custo do Overhead (Tempo de Máquina)
            dt_ini = datetime.combine(data_prod, hr_ini)
            dt_fim = datetime.combine(data_prod, hr_fim)
            duracao_horas = (dt_fim - dt_ini).total_seconds() / 3600.0
            if duracao_horas < 0:
                duracao_horas += 24.0 # Virou o dia
                
            custo_diario = custo_fixo_mensal / 21.0
            custo_hora = custo_diario / 8.0
            overhead_lote = custo_hora * duracao_horas
            
            # 3. Custo Unitário Final do Produto Produzido
            custo_total_lote = custo_total_mp + overhead_lote
            custo_unit_pf = custo_total_lote / pf_gerado_qtd
            
            str_hr_ini = hr_ini.strftime("%H:%M")
            str_hr_fim = hr_fim.strftime("%H:%M")
            peso_princiapl = insumos_usados[0][3] if insumos_usados else 0.0
            
            # --- GRAVAÇÃO NO BANCO (Transacional) ---
            try:
                with db_transaction() as conn:
                    cursor = conn.cursor()
                    
                    # A) Grava Lote no Cabeçalho (producao_diaria)
                    obs_sobra = " | ".join([f"Puxado: {q_p}kg, Sobrou: {s}kg de {item}" for item, q_p, s, q_c in insumos_usados if s > 0])
                    obs_final = observacoes
                    if obs_sobra:
                        obs_final = f"{observacoes}\n[Auditoria de Sobras]: {obs_sobra}".strip()
                        
                    run_query_tx(
                        cursor,
                        """INSERT INTO producao_diaria
                           (data, hora_inicio, hora_fim, materia_prima_kg, produto_id, produto_final_kg, perdas_kg, observacoes, custo_total_lote, custo_unitario_lote, data_validade)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (data_prod.strftime("%Y-%m-%d"), str_hr_ini, str_hr_fim, peso_princiapl, pf_id, pf_gerado_qtd, perdas_kg, obs_final, custo_total_lote, custo_unit_pf, data_validade.strftime("%Y-%m-%d"))
                    )
                    
                    lote_id_df = fetch_all_tx(cursor, "SELECT id FROM producao_diaria ORDER BY id DESC LIMIT 1")
                    lote_id = lote_id_df.iloc[0]['id']
                    ref_doc = f"Lote OP #{lote_id}"
                    
                    # B) Baixa nas Matérias-Primas (estoque_movimentos e producao_insumos)
                    for item_nome, qt_p, sob, qt_c in insumos_usados:
                        item_id = int(mp_dict[item_nome]['id'])
                        
                        # Na receita, fica gravado o consumo real para a DRE
                        run_query_tx(cursor, "INSERT INTO producao_insumos (producao_id, produto_id, quantidade) VALUES (?, ?, ?)", 
                                  (lote_id, item_id, qt_c))
                                  
                        # 1. Registra a saída total requisitada do estoque
                        run_query_tx(cursor, """INSERT INTO estoque_movimentos 
                                     (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia) 
                                     VALUES (?, ?, 'Saída', ?, ?, ?)""",
                                  (data_prod.strftime("%Y-%m-%d"), item_id, qt_p, "Produção_Requisição", ref_doc))
                                  
                        # 2. Devolve a sobra não utilizada para o estoque
                        if sob > 0:
                            run_query_tx(cursor, """INSERT INTO estoque_movimentos 
                                         (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia) 
                                         VALUES (?, ?, 'Entrada', ?, ?, ?)""",
                                      (data_prod.strftime("%Y-%m-%d"), item_id, sob, "Produção_Devolução_Sobra", ref_doc))
                                  
                    # C) Entrada do Produto Acabado no Estoque
                    run_query_tx(cursor, """INSERT INTO estoque_movimentos 
                                 (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id) 
                                 VALUES (?, ?, 'Entrada', ?, ?, ?, ?)""",
                               (data_prod.strftime("%Y-%m-%d"), pf_id, pf_gerado_qtd, "Produção_Entrada", ref_doc, int(lote_id)))
                              
                    # D) ATUALIZA O CUSTO DO PRODUTO (Estoque Financeiro)
                    run_query_tx(cursor, "UPDATE produtos SET custo_unidade = ? WHERE id = ?", (custo_unit_pf, pf_id))
                    
                    # --- FEEDBACK VISUAL ---
                    st.success(f"✔️ Lote Físico #{lote_id} gravado e Estoques atualizados!")
            except Exception as e:
                st.error(f"🛑 Erro ao salvar o lote de produção (Operação cancelada): {str(e)}")          
            
            st.markdown("### 📊 Raio-X de Produção deste Lote")
            rx1, rx2 = st.columns(2)
            rx1.metric("Duração da Linha", f"{duracao_horas:.2f} hrs")
            rx2.metric("Volume Gerado", f"{pf_gerado_qtd:.2f}")
            
            st.session_state['num_insumos'] = 3
            # import time; time.sleep(5); st.rerun()

# =========================================================
# TAB 2: HISTÓRICO DE PRODUÇÃO
# =========================================================
with tab2:
    st.subheader("Visualizador de Histórico de Lotes e Custos")
    
    query_prod = '''
        SELECT 
            pd.id as "OP (Lote)",
            pd.data as "Data Fabricação",
            pd.data_validade as "Validade",
            pd.hora_inicio || ' às ' || pd.hora_fim as "Turno (Duração)",
            COALESCE((SELECT string_agg(p_ins.nome || ' (' || pi.quantidade || ')', ', ') 
             FROM producao_insumos pi
             JOIN produtos p_ins ON pi.produto_id = p_ins.id
             WHERE pi.producao_id = pd.id), 'Sem detalhe MP') as "Matéria-Prima Consumida",
            pf.nome || ' (' || pd.produto_final_kg || ')' as "Produto Acabado (Qtd)",
            pd.perdas_kg as "Perda Kg",
            pd.custo_total_lote as "Custo Total (R$)",
            pd.custo_unitario_lote as "Custo Unitário Apurado (R$)",
            pd.observacoes as "Diário de Ocorrências"
        FROM producao_diaria pd
        JOIN produtos pf ON pd.produto_id = pf.id
        ORDER BY pd.data DESC, pd.id DESC LIMIT 300
    '''
    df_historico = fetch_all(query_prod)
    if df_historico.empty:
        st.info("Nenhum lote documentado no sistema ainda.")
    else:
        df_historico['Data Fabricação'] = pd.to_datetime(df_historico['Data Fabricação']).dt.strftime('%d/%m/%Y')
        df_historico['Validade'] = pd.to_datetime(df_historico['Validade'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_historico['Validade'] = df_historico['Validade'].fillna('-')
        
        def format_brl(val):
            if pd.isna(val) or val is None:
                return ""
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        df_historico['Custo Total (R$)'] = df_historico['Custo Total (R$)'].apply(format_brl)
        df_historico['Custo Unitário Apurado (R$)'] = df_historico['Custo Unitário Apurado (R$)'].apply(format_brl)
        
        st.dataframe(df_historico, width="stretch", hide_index=True)
