import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from database import fetch_all, run_query, get_connection, db_connection, release_connection
from estilo import carregar_estilo

st.set_page_config(page_title="Compras e Entradas", page_icon="🛒", layout="wide")
carregar_estilo()

def format_brl(val):
    if val is None: return "R$ 0,00"
    try:
        return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

st.title("🛒 Registro de Notas Fiscais de Entrada")
st.markdown("Lance NFs com múltiplos itens, cálculo fiscal (Lucro Presumido) e entrada automática no estoque.")

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if 'itens_nf' not in st.session_state:
    st.session_state.itens_nf = []
if 'parcelas_temp' not in st.session_state:
    st.session_state.parcelas_temp = []
if 'compras_clique_bloqueado' not in st.session_state:
    st.session_state.compras_clique_bloqueado = False

# ─── PRÉ-REQUISITOS ───────────────────────────────────────────────────────────
df_fornecedores = fetch_all(
    "SELECT id, nome_fantasia, nome, plano_de_contas, prazo_pagamento, plano_conta_id, forma_pagamento_id FROM fornecedores WHERE status='ATIVO' ORDER BY nome_fantasia")
df_produtos = fetch_all(
    "SELECT id, nome, unidade_medida, is_materia_prima, custo_unidade, unidades_por_fardo FROM produtos ORDER BY nome")
df_fp = fetch_all("SELECT id, nome, parcelas FROM formas_pagamento ORDER BY id ASC")
fp_options_compras = df_fp['nome'].tolist() if not df_fp.empty else []
fp_dict_compras = dict(zip(df_fp['nome'], df_fp['id'])) if not df_fp.empty else {}
fp_reverse_dict_compras = dict(zip(df_fp['id'], df_fp['nome'])) if not df_fp.empty else {}
fp_rules_compras = dict(zip(df_fp['nome'], df_fp['parcelas'])) if not df_fp.empty else {}

if df_fornecedores.empty:
    st.error("⚠️ Nenhum fornecedor ativo. Cadastre em **Cadastros → Fornecedores**.")
    st.stop()

if df_produtos.empty:
    st.error("⚠️ Nenhum produto cadastrado. Cadastre em **Cadastros → Produtos**.")
    st.stop()

# Dicts auxiliares
forn_dict = {}
for _, row in df_fornecedores.iterrows():
    label = str(row['nome_fantasia'] or row['nome'] or "").strip()
    if label:
        forn_dict[label] = row

if not forn_dict:
    st.error("⚠️ Fornecedores sem Nome Fantasia. Atualize no Cadastro.")
    st.stop()

prod_dict = {row['nome']: row for _, row in df_produtos.iterrows()}

DESTINOS = {
    "🌾 Matéria-Prima / Produção": "PRODUCAO",
    "📦 Produto para Revenda": "REVENDA",
    "🧹 Consumo Interno (escritório, limpeza, etc.)": "CONSUMO_INTERNO",
}

def parse_prazo(rule_str):
    import re
    dias_list = [int(n) for n in re.findall(r'\d+', str(rule_str))]
    if not dias_list:
        return [0]
    return dias_list

import xml.etree.ElementTree as ET

# ═══════════════════════════════════════════════════════════════════════════════
# LEITURA PASSIVA (XML NF-e)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("### ⚡ Entrada Passiva de Dados")
xml_file = st.file_uploader("Arraste o XML da Nota Fiscal (NF-e) aqui para preencher tudo sozinho", type=["xml"])

xml_nNF = ""
xml_forn_name = None
xml_itens = []

if xml_file is not None:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        # Namespace strip hack
        for elem in root.iter():
            if '}' in elem.tag: elem.tag = elem.tag.split('}', 1)[1]
            
        ide = root.find('.//ide')
        if ide is not None:
            nNF_elem = ide.find('nNF')
            if nNF_elem is not None: xml_nNF = nNF_elem.text
            
        emit = root.find('.//emit')
        if emit is not None:
            xNome_elem = emit.find('xNome')
            if xNome_elem is not None:
                xml_forn_name = xNome_elem.text.upper()
                
        dets = root.findall('.//det')
        for det in dets:
            prod = det.find('prod')
            if prod is not None:
                xProd = prod.find('xProd').text if prod.find('xProd') is not None else "Produto Desconhecido"
                qCom = float(prod.find('qCom').text) if prod.find('qCom') is not None else 1.0
                vUnCom = float(prod.find('vUnCom').text) if prod.find('vUnCom') is not None else 0.0
                xml_itens.append({"nome": xProd, "qtd": qCom, "preco": vUnCom})
                
        st.success(f"XML lido com sucesso! Nota Fiscal: {xml_nNF} | Fornecedor do XML: {xml_forn_name}")
        if xml_itens:
            st.info(f"O XML possui {len(xml_itens)} item(ns). Como as descrições podem ser diferentes do seu cadastro, adicione-os manualmente na Seção 2 usando os valores lidos.")
            st.dataframe(pd.DataFrame(xml_itens), hide_index=True)
            
    except Exception as e:
        st.error(f"Erro ao ler XML: {e}")

st.markdown("---")
# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — CABEÇALHO DA NF
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 1️⃣ Cabeçalho da Nota Fiscal")

hc1, hc2 = st.columns([1, 2])
data_compra = hc1.date_input("Data de Emissão", datetime.today().date(), format="DD/MM/YYYY")
fornecedor_sel = hc2.selectbox("Fornecedor (cadastrado)", list(forn_dict.keys()))

hc3, hc4, hc5 = st.columns(3)
tipo_doc = hc3.selectbox("Tipo de Documento", ["NF", "REC", "BOLETO", "OUTRO"])
numero_doc = hc4.text_input("Número do Documento", value=xml_nNF)
obs = hc5.text_input("Observações")

frn_data = forn_dict[fornecedor_sel]

# Determinar a condição padrão do fornecedor
d_fp_id = frn_data.get('forma_pagamento_id') if 'forma_pagamento_id' in frn_data else None
d_fp_nome = ""
if d_fp_id is not None and pd.notna(d_fp_id):
    d_fp_nome = fp_reverse_dict_compras.get(int(d_fp_id), "")

if not d_fp_nome:
    d_fp_nome = frn_data.get('prazo_pagamento', '')

idx_fp = fp_options_compras.index(d_fp_nome) if d_fp_nome in fp_options_compras else 0

# Exibir o selectbox para selecionar a condição de pagamento desta compra
hc_fp = st.selectbox("Condição de Pagamento para esta Compra", fp_options_compras, index=idx_fp)
fp_id_compra = fp_dict_compras.get(hc_fp, None)

prazo_str = hc_fp
rule_str = fp_rules_compras.get(hc_fp, "0")

numero_doc_final = numero_doc.strip() if numero_doc.strip() else f"AUT-{datetime.now().strftime('%m%d%H%M')}"

if not numero_doc.strip():
    st.caption(f"⚠️ Nº não informado. Será gerado automaticamente: `{numero_doc_final}`")

st.info(f"📋 Fornecedor **{fornecedor_sel}** · Condição de Pagamento: **{hc_fp}**")

# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — ITENS DA NF
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 2️⃣ Itens da Nota Fiscal")

st.markdown("##### ➕ Adicionar Item à NF")

ai1, ai2 = st.columns([3, 2])
destino_label = ai2.selectbox("Destino deste Item", list(DESTINOS.keys()))
destino_val = DESTINOS[destino_label]

if destino_val == "CONSUMO_INTERNO":
    item_nome = ai1.text_input("Nome do Item (Ex: Material de Limpeza, Papelaria)")
    item_id = None
    unidade_default = "un"
    fator_conv = 1
else:
    # Filtrar produtos por destino
    if destino_val == "PRODUCAO":
        prod_filtrado = {k: v for k, v in prod_dict.items() if v.get('is_materia_prima', 0) == 1}
        label_prod = "Produto (apenas Matéria-Prima)"
    else:
        prod_filtrado = {k: v for k, v in prod_dict.items() if v.get('is_materia_prima', 0) == 0}
        label_prod = "Produto (apenas Acabado / Revenda)"

    if not prod_filtrado:
        st.warning("⚠️ Nenhum produto cadastrado para este destino. Mostrando todos.")
        prod_filtrado = prod_dict
        label_prod = "Produto (todos)"

    prod_sel = ai1.selectbox(label_prod, list(prod_filtrado.keys()))
    item_nome = prod_sel
    prod_row = prod_filtrado[prod_sel]
    item_id = int(prod_row['id'])
    unidade_default = str(prod_row['unidade_medida'] or "un")
    _fardo_raw = prod_row['unidades_por_fardo']
    fator_conv = int(_fardo_raw) if (_fardo_raw is not None and not pd.isna(_fardo_raw) and _fardo_raw > 0) else 1

col_q, col_u, col_p = st.columns([2, 1, 2])
quantidade = col_q.number_input("Quantidade", min_value=0.0, step=1.0, format="%.3f", value=0.0)
unidade_compra = col_u.text_input("Unidade", value=unidade_default)
preco_bruto_unit = col_p.number_input(
    "Preço Unitário Bruto (R$) — conforme NF",
    min_value=0.0, step=0.01, format="%.4f", value=0.0
)

# Cálculo do estoque real
qtd_estoque = quantidade * fator_conv
if destino_val != "CONSUMO_INTERNO" and fator_conv > 1 and quantidade > 0:
    st.info(f"📦 **Conversão de Estoque:** {quantidade} {unidade_compra} será registrado como **{qtd_estoque:,.2f}** unidades no estoque.")

icms_total_item = 0.0
ipi_total_item = 0.0

if destino_val != "CONSUMO_INTERNO":
    st.markdown("*Impostos recuperáveis — Lucro Presumido (reduzem custo de estoque):*")
    fi1, fi2, fi3 = st.columns(3)
    icms_total_item = fi1.number_input(
        "ICMS Total R$ (deste item)",
        min_value=0.0, step=0.01, format="%.2f",
        help="ICMS destacado na NF para este item. É crédito fiscal — reduz o custo do estoque."
    )
    ipi_total_item = fi2.number_input(
        "IPI Total R$ (deste item)",
        min_value=0.0, step=0.01, format="%.2f",
        help="IPI destacado. Em geral zero para alho in natura e alimentos."
    )
    total_bruto_item_calc = preco_bruto_unit * quantidade
    custo_liq_unit = (total_bruto_item_calc - icms_total_item - ipi_total_item) / quantidade if quantidade > 0 else preco_bruto_unit
    fi3.metric("Custo Líq. Unitário Calculado", f"R$ {custo_liq_unit:.4f}")
else:
    custo_liq_unit = preco_bruto_unit
    st.info("💡 Consumo Interno: sem crédito fiscal. Custo = preço bruto integral.")

total_liquido_item = custo_liq_unit * quantidade

if st.button("➕ Adicionar Item", use_container_width=True):
    if quantidade > 0 and preco_bruto_unit > 0 and item_nome:
        st.session_state.itens_nf.append({
            'produto_id': item_id,
            'produto_nome': item_nome,
            'unidade': unidade_compra,
            'destino_label': destino_label,
            'destino': destino_val,
            'quantidade': float(quantidade),
            'quantidade_estoque': float(qtd_estoque),
            'preco_bruto_unit': float(preco_bruto_unit),
            'icms_valor': float(icms_total_item),
            'ipi_valor': float(ipi_total_item),
            'custo_liq_unit': float(custo_liq_unit),
            'total_liquido_item': float(total_liquido_item),
        })
        st.session_state.parcelas_temp = []  # reset parcelas ao mudar itens
        st.rerun()
    else:
        st.error("⚠️ Preencha o nome do item, quantidade e preço antes de adicionar.")

# ─── Grade de Itens Adicionados ───────────────────────────────────────────────
if st.session_state.itens_nf:
    st.markdown("##### 📋 Itens na NF")

    rows = []
    for it in st.session_state.itens_nf:
        rows.append({
            'Produto': it['produto_nome'],
            'Destino': it['destino_label'],
            'Qtd': f"{it['quantidade']:.3f} {it['unidade']}",
            'Estoque': f"{it.get('quantidade_estoque', it['quantidade']):,.0f} un",
            'Bruto Unit.': format_brl(it['preco_bruto_unit']),
            'Total Líq.': format_brl(it['total_liquido_item']),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    rc1, rc2 = st.columns([4, 1])
    opcoes_remover = {
        f"Item {i+1}: {it['produto_nome']} ({it['quantidade']:.2f} {it['unidade']})": i
        for i, it in enumerate(st.session_state.itens_nf)
    }
    item_del_sel = rc1.selectbox("Selecionar item para remover:", list(opcoes_remover.keys()), key="sel_remover")
    if rc2.button("🗑️ Remover", use_container_width=True):
        del st.session_state.itens_nf[opcoes_remover[item_del_sel]]
        st.session_state.parcelas_temp = []
        st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 3 — TOTALIZADOR
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## 3️⃣ Totalizador da NF")

    total_bruto_nf = sum(it['preco_bruto_unit'] * it['quantidade'] for it in st.session_state.itens_nf)
    total_icms_nf = sum(it['icms_valor'] for it in st.session_state.itens_nf)
    total_ipi_nf = sum(it['ipi_valor'] for it in st.session_state.itens_nf)
    total_creditos_nf = total_icms_nf + total_ipi_nf
    total_custo_estoque = sum(it['total_liquido_item'] for it in st.session_state.itens_nf)
    n_itens_estoque = len([it for it in st.session_state.itens_nf if it['destino'] != 'CONSUMO_INTERNO'])

    tc1, tc2, tc3, tc4 = st.columns(4)
    tc1.metric("💳 Total Bruto NF (A Pagar)", format_brl(total_bruto_nf))
    tc2.metric("🏛️ (-) Créditos Fiscais", format_brl(total_creditos_nf))
    tc3.metric("📦 Custo Real p/ Estoque", format_brl(total_custo_estoque))
    tc4.metric("📥 Itens que Entram no Estoque", n_itens_estoque)

    # ═══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 4 — PARCELAMENTO
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## 4️⃣ Duplicatas (Contas a Pagar)")
    st.info(f"Parcelas calculadas sobre o **valor bruto {format_brl(total_bruto_nf)}** — o que a fábrica deve ao fornecedor.")

    col_auto, col_man, col_clr = st.columns([2, 4, 1])

    with col_auto:
        if st.button(f"🪄 Gerar pelo Prazo ({prazo_str})", type="primary", use_container_width=True):
            dias_list = parse_prazo(rule_str)
            qtd_p = len(dias_list)
            valor_p = round(total_bruto_nf / qtd_p, 2)
            diff_p = round(total_bruto_nf - valor_p * qtd_p, 2)
            novas = []
            for i, dias in enumerate(dias_list):
                v = valor_p + (diff_p if i == qtd_p - 1 else 0)
                d = data_compra + timedelta(days=dias)
                novas.append({"ID Parcela": f"{numero_doc_final}/{i+1}", "Vencimento": d, "Valor (R$)": float(v)})
            st.session_state.parcelas_temp = novas

    with col_man:
        with st.expander("⚙️ Parcelamento Customizado"):
            cm1, cm2 = st.columns(2)
            n_p = cm1.number_input("Qtd Parcelas", min_value=1, value=2, key="np_man")
            d_int = cm2.number_input("Dias entre Parcelas", min_value=0, value=30, key="dint_man")
            if st.button("Gerar Frações Manuais"):
                valor_p = round(total_bruto_nf / n_p, 2)
                diff_p = round(total_bruto_nf - valor_p * n_p, 2)
                novas = []
                for i in range(n_p):
                    v = valor_p + (diff_p if i == n_p - 1 else 0)
                    d = data_compra + timedelta(days=d_int * (i + 1))
                    novas.append({"ID Parcela": f"{numero_doc_final}/{i+1}", "Vencimento": d, "Valor (R$)": float(v)})
                st.session_state.parcelas_temp = novas

    with col_clr:
        if st.session_state.parcelas_temp:
            if st.button("🔄 Limpar", use_container_width=True):
                st.session_state.parcelas_temp = []
                st.rerun()

    if not st.session_state.parcelas_temp:
        # Auto-gerar pelo prazo do fornecedor
        dias_list = parse_prazo(rule_str)
        qtd_p = len(dias_list)
        valor_p = round(total_bruto_nf / qtd_p, 2)
        diff_p = round(total_bruto_nf - valor_p * qtd_p, 2)
        novas = []
        for i, dias in enumerate(dias_list):
            v = valor_p + (diff_p if i == qtd_p - 1 else 0)
            d = data_compra + timedelta(days=dias)
            novas.append({"ID Parcela": f"{numero_doc_final}/{i+1}", "Vencimento": d, "Valor (R$)": float(v)})
        st.session_state.parcelas_temp = novas
        st.info(f"✅ Duplicatas geradas automaticamente pelo prazo do fornecedor (**{prazo_str}**). Edite abaixo se necessário.")

    if not st.session_state.parcelas_temp:
        st.write("Pressione o botão azul para gerar as duplicatas.")
    else:
        st.caption("Você pode editar valores e datas. A soma deve fechar com o valor bruto da NF.")

        df_editor = pd.DataFrame(st.session_state.parcelas_temp)
        config_ed = {
            "Valor (R$)": st.column_config.NumberColumn("Valor na Duplicata (R$)", format="R$ %.2f", min_value=0.01),
            "Vencimento": st.column_config.DateColumn("Vencimento do Boleto/DOC"),
            "ID Parcela": st.column_config.TextColumn("Nº da Fração", disabled=True),
        }
        edited_df = st.data_editor(df_editor, num_rows="dynamic", column_config=config_ed, use_container_width=True, key="editor_parcelas")
        st.session_state.parcelas_temp = edited_df.to_dict('records')

        soma_parcelas = round(sum(float(p.get('Valor (R$)', 0)) for p in st.session_state.parcelas_temp), 2)
        diff_val = round(total_bruto_nf - soma_parcelas, 2)
        pode_salvar = abs(diff_val) == 0.0

        if pode_salvar:
            st.success(f"✅ Soma exata: {format_brl(soma_parcelas)} — Nota fechada!")
        else:
            st.error(f"⚠️ Soma das parcelas: {format_brl(soma_parcelas)} | Faltam: {format_brl(diff_val)}")

        # ═══════════════════════════════════════════════════════════════════════
        # SEÇÃO 5 — CONFIRMAÇÃO E GRAVAÇÃO
        # ═══════════════════════════════════════════════════════════════════════
        if pode_salvar:
            st.markdown("---")
            st.markdown("## 5️⃣ Confirmar e Registrar")

            confirm = st.checkbox(
                "Confirmo que os dados da NF, itens e duplicatas estão corretos e autorizo o registro no sistema."
            )

            if st.button("✔️ Registrar NF no Sistema", type="primary", use_container_width=True):
                if st.session_state.get("compras_clique_bloqueado", False):
                    st.warning("⚠️ Gravação já em andamento. Aguarde...")
                elif not confirm:
                    st.error("Marque a caixa de confirmação antes de registrar.")
                else:
                    st.session_state["compras_clique_bloqueado"] = True
                    try:
                        with st.spinner("Registrando Notas Fiscais, Estoque e Contas a Pagar..."):
                            with db_connection() as conn:
                                cursor = conn.cursor()

                            fid = int(frn_data['id'])
                            plano_id = int(frn_data['plano_conta_id']) if 'plano_conta_id' in frn_data and pd.notnull(frn_data['plano_conta_id']) else None
                            if not plano_id and frn_data['plano_de_contas']:
                                cursor.execute("SELECT id FROM planos_de_contas WHERE nome=?", (frn_data['plano_de_contas'],))
                                res = cursor.fetchone()
                                if res:
                                    plano_id = res[0]

                            # 1. Cabeçalho da Compra (Nota Mãe)
                            destinos_resumo = ", ".join(set(it['destino'] for it in st.session_state.itens_nf))
                            cursor.execute("""
                                INSERT INTO compras
                                    (fornecedor_id, data_compra, tipo_insumo, valor_total, tipo_doc, numero_doc, observacoes, forma_pagamento_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (fid, data_compra.strftime("%Y-%m-%d"), destinos_resumo,
                                  total_bruto_nf, tipo_doc, numero_doc_final, obs, fp_id_compra))
                            compra_id = cursor.lastrowid

                            # 2. Itens da NF
                            for it in st.session_state.itens_nf:
                                cursor.execute("""
                                    INSERT INTO compras_itens
                                        (compra_id, produto_id, produto_nome, destino, unidade, quantidade, quantidade_estoque,
                                         preco_unitario_bruto, icms_valor, ipi_valor,
                                         custo_unitario_liquido, total_liquido_item)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (compra_id, it['produto_id'], it['produto_nome'], it['destino'],
                                      it['unidade'], it['quantidade'], it.get('quantidade_estoque', it['quantidade']),
                                      it['preco_bruto_unit'], it['icms_valor'], it['ipi_valor'],
                                      it['custo_liq_unit'], it['total_liquido_item']))

                                # 3. Entrada no Estoque (MP e Revenda)
                                if it['destino'] in ('PRODUCAO', 'REVENDA'):
                                    qtd_stock = it.get('quantidade_estoque', it['quantidade'])
                                    cursor.execute("""
                                        INSERT INTO estoque_movimentos
                                            (data, produto_id, tipo_movimento, quantidade, origem)
                                        VALUES (?, ?, 'Entrada', ?, ?)
                                    """, (data_compra.strftime("%Y-%m-%d"), it['produto_id'],
                                          qtd_stock,
                                          f"Compra NF {tipo_doc} {numero_doc_final} (ID #{compra_id})"))

                                    # 4. Atualiza custo unitário do produto (último preço real estocado)
                                    custo_medio_unidade = it['total_liquido_item'] / it['quantidade_estoque'] if it['quantidade_estoque'] > 0 else it['custo_liq_unit']
                                    cursor.execute(
                                        "UPDATE produtos SET custo_unidade=? WHERE id=?",
                                        (custo_medio_unidade, it['produto_id'])
                                    )

                            # 5. Duplicatas (Contas a Pagar)
                            for parc in st.session_state.parcelas_temp:
                                p_val = float(parc['Valor (R$)'])
                                p_venc = parc['Vencimento']
                                p_num = parc['ID Parcela']
                                d_str = p_venc.strftime("%Y-%m-%d") if hasattr(p_venc, 'strftime') else str(p_venc)
                                desc = f"{tipo_doc} {p_num} | {fornecedor_sel}"
                                cursor.execute("""
                                    INSERT INTO contas_a_pagar
                                        (compra_id, fornecedor_id, plano_conta_id, descricao, valor, data_vencimento, status)
                                    VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')
                                """, (compra_id, fid, plano_id, desc, p_val, d_str))

                            conn.commit()

                        # Limpa sessão
                        st.session_state.itens_nf = []
                        st.session_state.parcelas_temp = []
                        st.session_state["compras_clique_bloqueado"] = False

                        st.success(
                            f"✅ NF {numero_doc_final} registrada com sucesso! "
                            f"Compra #{compra_id} | {n_itens_estoque} item(s) entraram no estoque | "
                            f"{len(edited_df)} duplicata(s) geradas no Financeiro."
                        )
                        import time; time.sleep(2); st.rerun()

                    except Exception as e:
                        st.session_state["compras_clique_bloqueado"] = False
                        st.error(f"Erro ao registrar a NF: {e}")
                        import traceback
                        st.code(traceback.format_exc())

else:
    st.info("👆 Adicione pelo menos um item à NF para continuar.")

# ═══════════════════════════════════════════════════════════════════════════════
# HISTÓRICO DE COMPRAS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📦 Histórico de Notas Fiscais de Entrada")

# Inicializar datas no session state se não existirem
if 'compras_dt_inicio' not in st.session_state:
    st.session_state['compras_dt_inicio'] = date.today() - timedelta(days=30)
if 'compras_dt_fim' not in st.session_state:
    st.session_state['compras_dt_fim'] = date.today()

st.markdown("##### 📅 Filtro por Período de Emissão")
col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1, 1.3, 1.3, 2, 2])

col_f1.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
if col_f1.button("📅 Hoje", use_container_width=True, key="btn_compras_hoje"):
    st.session_state['compras_dt_inicio'] = date.today()
    st.session_state['compras_dt_fim'] = date.today()
    st.rerun()
    
col_f2.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
if col_f2.button("📅 Últimos 7 Dias", use_container_width=True, key="btn_compras_7d"):
    st.session_state['compras_dt_inicio'] = date.today() - timedelta(days=7)
    st.session_state['compras_dt_fim'] = date.today()
    st.rerun()
    
col_f3.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
if col_f3.button("📅 Últimos 30 Dias", use_container_width=True, key="btn_compras_30d"):
    st.session_state['compras_dt_inicio'] = date.today() - timedelta(days=30)
    st.session_state['compras_dt_fim'] = date.today()
    st.rerun()
    
dt_inicio = col_f4.date_input("Data de Início", value=st.session_state['compras_dt_inicio'], key="compras_dt_inicio_input")
dt_fim = col_f5.date_input("Data de Fim", value=st.session_state['compras_dt_fim'], key="compras_dt_fim_input")

# Sincronizar de volta
st.session_state['compras_dt_inicio'] = dt_inicio
st.session_state['compras_dt_fim'] = dt_fim

df_compras = fetch_all("""
    SELECT c.id, c.data_compra as 'Data', f.nome_fantasia as 'Fornecedor',
           c.numero_doc as 'Nº Doc', c.tipo_doc as 'Tipo',
           c.valor_total as 'Total Bruto (R$)', c.observacoes as 'Obs'
    FROM compras c
    JOIN fornecedores f ON c.fornecedor_id = f.id
    WHERE c.data_compra BETWEEN ? AND ?
    ORDER BY c.id DESC
""", (dt_inicio.strftime("%Y-%m-%d"), dt_fim.strftime("%Y-%m-%d")))

if not df_compras.empty:
    df_view = df_compras.copy()
    df_view['Data'] = pd.to_datetime(df_view['Data']).dt.strftime('%d/%m/%Y')
    df_view['Total Bruto (R$)'] = df_view['Total Bruto (R$)'].apply(format_brl)
    # Adiciona resumo das duplicatas
    df_view['Duplicatas'] = ''
    for idx, row in df_view.iterrows():
        parcelas = fetch_all("SELECT data_vencimento, valor, status FROM contas_a_pagar WHERE compra_id=? ORDER BY data_vencimento", (row['id'],))
        if not parcelas.empty:
            resumo = " | ".join([f"{pd.to_datetime(p['data_vencimento']).strftime('%d/%m/%Y')} {format_brl(p['valor'])} ({p['status']})" for _, p in parcelas.iterrows()])
            df_view.at[idx, 'Duplicatas'] = resumo
    st.dataframe(df_view, hide_index=True, use_container_width=True)

    with st.expander("🔍 Ver Itens de uma NF"):
        opts_nf = {
            f"NF #{r['id']} | {r['Nº Doc']} — {r['Fornecedor']} ({pd.to_datetime(df_compras[df_compras['id']==r['id']]['Data'].values[0]).strftime('%d/%m/%Y') if pd.to_datetime(df_compras[df_compras['id']==r['id']]['Data'].values[0]) else ''})": r['id']
            for _, r in df_compras.iterrows()
        }
        nf_sel = st.selectbox("Selecione a NF:", list(opts_nf.keys()))
        if nf_sel:
            nf_id = opts_nf[nf_sel]
            df_itens_hist = fetch_all("""
                SELECT ci.produto_nome as 'Produto', ci.destino as 'Destino',
                       ci.quantidade as 'Qtd Comprada', ci.unidade as 'Unidade',
                       ci.quantidade_estoque as 'Qtd Estoque',
                       ci.preco_unitario_bruto as 'Bruto Unit R$',
                       ci.custo_unitario_liquido as 'Custo Líq. R$',
                       ci.total_liquido_item as 'Total Líq. R$'
                FROM compras_itens ci
                WHERE ci.compra_id = ?
            """, (nf_id,))
            if not df_itens_hist.empty:
                for col in ['Bruto Unit R$', 'Custo Líq. R$', 'Total Líq. R$']:
                    df_itens_hist[col] = df_itens_hist[col].apply(format_brl)
                st.dataframe(df_itens_hist, hide_index=True, use_container_width=True)
            else:
                st.info("NF sem itens detalhados (registro legado).")

    with st.expander("✏️ Editar Cabeçalho da NF (Nota Mãe)"):
        st.info("⚠️ Para alterar valores ou datas de **boletos já lançados**, acesse o módulo **Financeiro → Contas a Pagar**.")
        opts_edit = {
            f"#{r['id']} | {r['Nº Doc']} | {r['Fornecedor']}": r['id']
            for _, r in df_compras.iterrows()
        }
        c_sel = st.selectbox("Selecione a NF para editar:", list(opts_edit.keys()), key="edit_nf_sel")
        if c_sel:
            cid = opts_edit[c_sel]
            cb = fetch_all("SELECT * FROM compras WHERE id=?", (cid,)).iloc[0]
            with st.form("edit_compra"):
                ed1, ed2, ed3 = st.columns(3)
                ev_data = pd.to_datetime(cb['data_compra']).date() if pd.notnull(cb['data_compra']) else datetime.today().date()
                edta = ed1.date_input("Data Compra", value=ev_data)
                tipos = ["NF", "REC", "BOLETO", "OUTRO"]
                etdoc = ed2.selectbox("Tipo Doc", tipos,
                                      index=tipos.index(cb['tipo_doc']) if cb.get('tipo_doc') in tipos else 0)
                endoc = ed3.text_input("Número Documento", cb['numero_doc'] if cb.get('numero_doc') else "")
                eobs = st.text_input("Observações", cb['observacoes'] if cb.get('observacoes') else "")

                if st.form_submit_button("Salvar Cabeçalho"):
                    run_query("UPDATE compras SET data_compra=?, tipo_doc=?, numero_doc=?, observacoes=? WHERE id=?",
                              (edta.strftime("%Y-%m-%d"), etdoc, endoc, eobs, cid))
                    st.success("Cabeçalho atualizado!")
                    import time; time.sleep(1); st.rerun()
    with st.expander("❌ Cancelar / Estornar NF"):
        st.warning("⚠️ **ATENÇÃO:** O cancelamento estorna duplicatas e entradas de estoque desta NF.")
        opts_cancel = {
            f"#{r['id']} | {r['Nº Doc']} | {r['Fornecedor']}": r['id']
            for _, r in df_compras.iterrows()
        }
        nf_cancel_sel = st.selectbox("Selecione a NF para cancelar:", list(opts_cancel.keys()), key="cancel_nf_sel")
        if nf_cancel_sel:
            cid_cancel = opts_cancel[nf_cancel_sel]
            col_confirm, col_btn = st.columns([3, 1])
            confirm_cancel = col_confirm.checkbox("Confirmo o cancelamento total desta NF e seus lançamentos.", key="chk_cancel")
            if col_btn.button("🚫 Cancelar NF", type="primary", use_container_width=True):
                if not confirm_cancel:
                    st.error("Marque a caixa de confirmação.")
                else:
                    try:
                        with db_connection() as conn:
                            cursor = conn.cursor()

                            # 1. Estornar movimentos de estoque (registrar saída de estorno)
                            itens_nf_cancel = cursor.execute(
                                "SELECT produto_id, quantidade_estoque, quantidade, destino FROM compras_itens WHERE compra_id=?",
                                (cid_cancel,)).fetchall()
                            for prod_id, qtd_est, qtd_orig, dest in itens_nf_cancel:
                                if dest in ('PRODUCAO', 'REVENDA') and prod_id is not None:
                                    qtd_reversa = qtd_est if qtd_est else qtd_orig
                                    cursor.execute(
                                        "INSERT INTO estoque_movimentos (data, produto_id, tipo_movimento, quantidade, origem) VALUES (date('now'), ?, 'Saída', ?, ?)",
                                        (prod_id, qtd_reversa, f"ESTORNO - Cancelamento NF #{cid_cancel}"))

                            # 2. Cancelar duplicatas no financeiro
                            cursor.execute(
                                "UPDATE contas_a_pagar SET status='CANCELADO' WHERE compra_id=?",
                                (cid_cancel,))

                            # 3. Marcar NF como cancelada
                            cursor.execute(
                                "UPDATE compras SET observacoes = COALESCE(observacoes,'') || ' [❌ CANCELADA]' WHERE id=?",
                                (cid_cancel,))

                            conn.commit()

                        st.success(f"NF #{cid_cancel} cancelada! Estoque estornado e duplicatas canceladas.")
                        import time; time.sleep(2); st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cancelar: {e}")
                        import traceback
                        st.code(traceback.format_exc())

else:
    st.info("Nenhuma nota fiscal registrada ainda.")
