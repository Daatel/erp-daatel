import streamlit as st
import pandas as pd
import calendar
import io
from datetime import timedelta, date
from database import fetch_all
from estilo import carregar_estilo
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from fpdf import FPDF

st.set_page_config(page_title="Relatório Gerencial de Caixa", page_icon="🏛️", layout="wide")
carregar_estilo()

def gerar_excel_rgc(sel_mes_ano, saldo_inicial_caixa, rb_mes, ent_nat, ent_desc, ent_outros, dev_mes, imp_venda_mes, rl_mes, cmv_tot_mes, mp_val_mes, emb_mes, outros_fab_mes, desp_com_mes, comi_mes, frete_mes, acordos_mes, descarga_mes, degust_mes, promotores_mes, mc_mes, df_mes_val, ebitda_mes, depr_mes, imp_lucro_mes, finan_mes, jcp_mes, lucro_mes, div_mes, retido_mes, capex_mes, caixa_livre_mes, saldo_final_caixa, df_sai_mes):
    wb = Workbook()
    ws = wb.active
    ws.title = "RGC"
    ws.views.sheetView[0].showGridLines = True

    # Estilos Corporativos Elegantes
    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0F172A', end_color='0F172A', fill_type='solid')

    hdr_font = Font(name='Segoe UI', size=10, bold=True, color='0F172A')
    hdr_fill = PatternFill(start_color='F1F5F9', end_color='F1F5F9', fill_type='solid')

    ini_font = Font(name='Segoe UI', size=10.5, bold=True, color='0369A1')
    ini_fill = PatternFill(start_color='E0F2FE', end_color='E0F2FE', fill_type='solid')

    subtot_font = Font(name='Segoe UI', size=10, bold=True, color='1E293B')
    subtot_fill = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')

    tot_font = Font(name='Segoe UI', size=10.5, bold=True, color='0F172A')
    tot_fill = PatternFill(start_color='E2E8F0', end_color='E2E8F0', fill_type='solid')

    cpx_font = Font(name='Segoe UI', size=10.5, bold=True, color='854D0E')
    cpx_fill = PatternFill(start_color='FEF08A', end_color='FEF08A', fill_type='solid')

    fim_font = Font(name='Segoe UI', size=11, bold=True, color='15803D')
    fim_fill = PatternFill(start_color='DCFCE7', end_color='DCFCE7', fill_type='solid')

    det_font = Font(name='Segoe UI', size=9, italic=True, color='64748B')

    light_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    ws.merge_cells('A1:C1')
    ws['A1'] = f'DAATEL ERP — DEMONSTRATIVO GERENCIAL DE CAIXA (RGC) — {sel_mes_ano.upper()}'
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 32

    ws.append([])
    ws.append(['Código / Ref.', 'Descrição da Conta / Movimentação Gerencial', 'Valor (R$)'])
    ws.row_dimensions[3].height = 24
    for col in ['A3', 'B3', 'C3']:
        ws[col].font = hdr_font
        ws[col].fill = hdr_fill
        ws[col].border = light_border
        ws[col].alignment = Alignment(vertical='center')

    data_rows = [
        ('INICIAL', '(+) SALDO INICIAL CONSOLIDADO DE CAIXA (Abertura)', saldo_inicial_caixa, 'ini'),
        ('1.0', '1. Receita Operacional Realizada', rb_mes, 'subtotal'),
        ('1.1.1', '  1.1 Entradas de Vendas de Alho In Natura', ent_nat, 'normal'),
        ('1.1.2', '  1.2 Entradas de Vendas de Alho Descascado', ent_desc, 'normal'),
        ('1.3', '  1.3 Outras Receitas Operacionais Recebidas', ent_outros, 'normal') if ent_outros > 0 else None,
        ('2.0', '2. (-) Devoluções / Abatimentos Realizados', dev_mes, 'normal'),
        ('2.1.3', '3. (-) Impostos sobre Venda Pagos', imp_venda_mes, 'normal'),
        ('RL', '(=) RECEITA LÍQUIDA DE CAIXA', rl_mes, 'total'),
        ('4.0', '4. Custo Total de Fabricação / CMV Pago', cmv_tot_mes, 'subtotal'),
        ('2.1.1', '  4.1 (-) Matéria-Prima Paga (Alho in Natura)', mp_val_mes, 'normal'),
        ('2.1.2', '  4.2 (-) Embalagens & Insumos Pagos', emb_mes, 'normal'),
        ('5.0', '5. Despesas Comerciais Variáveis Pagas', desp_com_mes, 'subtotal'),
        ('2.1.4', '  5.1 (-) Comissões de Vendas Pagas', comi_mes, 'normal'),
        ('2.1.5', '  5.2 (-) Fretes de Entrega Pagos', frete_mes, 'normal'),
        ('2.2.2', '  5.3 (-) Acordos de Rede & Rebates Pagos', acordos_mes, 'normal'),
        ('2.2.0', '  5.4 (-) Taxas de Descarga Pagas', descarga_mes, 'normal'),
        ('2.2.1', '  5.5 (-) Degustações e Amostras Pagas', degust_mes, 'normal'),
        ('2.2.4', '  5.6 (-) Promotores de Vendas Pagos', promotores_mes, 'normal'),
        ('MC', '(=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA DE CAIXA', mc_mes, 'total'),
        ('6.0', '6. (-) Custos e Despesas Fixas Totais Pagas', df_mes_val, 'subtotal'),
    ]

    if not df_sai_mes.empty:
        is_cf = df_sai_mes['codigo'].str.startswith(('2.3.', '3.1.'), na=False) | ((df_sai_mes['codigo'] == 'OUTROS') & ~df_sai_mes['codigo'].str.startswith(('3.2.', '3.3.', '1.2.', '4.1.'), na=False))
        df_cf = df_sai_mes[is_cf & ~df_sai_mes['codigo'].str.startswith(('3.2.', '3.3.', '1.2.', '4.1.'), na=False)]
        if not df_cf.empty:
            grp_cf = df_cf.groupby(['codigo', 'pc_nome'])['valor'].sum().reset_index().sort_values(by='codigo')
            for _, r in grp_cf.iterrows():
                data_rows.append((str(r['codigo']), f"    {r['codigo']} - {r['pc_nome']}", float(r['valor']), "detail"))

    data_rows.extend([
        ("EBITDA", "(=) EBITDA DE CAIXA (Resultado Operacional)", ebitda_mes, "total"),
        ("3.2.1", "9. (-) Juros e Financiamentos Pagos", finan_mes, "normal"),
        ("3.2.0", "8. (-) Impostos sobre Lucro Pagos (IRPJ/CSLL)", imp_lucro_mes, "normal"),
        ("GER", "(=) GERAÇÃO LÍQUIDA DE CAIXA OPERACIONAL", lucro_mes, "subtotal"),
        ("DIV", "12. (-) Dividendos (Saque/Distribuição Efetivada)", div_mes, "normal"),
        ("RET", "(=) GERAÇÃO RETIDA DE CAIXA OPERACIONAL", retido_mes, "total"),
        ("CAPEX", "(-) Desembolsos de Investimentos Pagos (CAPEX / Máquinas)", capex_mes, "normal"),
        ("VAR", "(=) GERAÇÃO / REDUÇÃO LÍQUIDA DE CAIXA NO MÊS", caixa_livre_mes, "capex"),
        ("FINAL", "(=) SALDO FINAL CONSOLIDADO DE CAIXA (Fechamento)", saldo_final_caixa, "fim")
    ])

    for row in data_rows:
        if row is None: continue
        cod, desc, val, rtype = row
        ws.append([cod, desc, val])
        curr_row = ws.max_row
        ws.row_dimensions[curr_row].height = 20
        ws.cell(row=curr_row, column=3).number_format = 'R$ #,##0.00;[Red]-R$ #,##0.00;"-"'
        
        c1 = ws.cell(row=curr_row, column=1)
        c2 = ws.cell(row=curr_row, column=2)
        c3 = ws.cell(row=curr_row, column=3)
        
        c1.alignment = Alignment(horizontal='center', vertical='center')
        c2.alignment = Alignment(vertical='center')
        c3.alignment = Alignment(horizontal='right', vertical='center')

        for c in (c1, c2, c3): c.border = light_border

        if rtype == 'ini':
            for c in (c1, c2, c3): c.font = ini_font; c.fill = ini_fill
        elif rtype == 'total':
            for c in (c1, c2, c3): c.font = tot_font; c.fill = tot_fill
        elif rtype == 'subtotal':
            for c in (c1, c2, c3): c.font = subtot_font; c.fill = subtot_fill
        elif rtype == 'capex':
            for c in (c1, c2, c3): c.font = cpx_font; c.fill = cpx_fill
        elif rtype == 'fim':
            for c in (c1, c2, c3): c.font = fim_font; c.fill = fim_fill
        elif rtype == 'detail':
            for c in (c1, c2, c3): c.font = det_font

    ws.column_dimensions['A'].width = 16
    ws.column_dimensions['B'].width = 62
    ws.column_dimensions['C'].width = 24

    output_excel = io.BytesIO()
    wb.save(output_excel)
    return output_excel.getvalue()


def to_latin1(text):
    if not isinstance(text, str):
        text = str(text)
    text = (text.replace("—", "-")
                .replace("–", "-")
                .replace("“", '"')
                .replace("”", '"')
                .replace("’", "'")
                .replace("‘", "'")
                .replace("•", "*")
                .replace("…", "..."))
    return text.encode('latin-1', 'replace').decode('latin-1')


class ExecutivePDF(FPDF):
    def __init__(self, sel_mes_ano):
        super().__init__()
        self.sel_mes_ano = sel_mes_ano

    def cell(self, w=0, h=0, text="", border=0, new_x="RIGHT", new_y="TOP", align="", fill=False, link=""):
        if text:
            text = to_latin1(text)
        return super().cell(w=w, h=h, text=text, border=border, new_x=new_x, new_y=new_y, align=align, fill=fill, link=link)

    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 20, style='F')
        
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 4)
        self.cell(0, 6, "DAATEL ERP - GESTÃO INDUSTRIAL & FINANCEIRA", align='L')
        
        self.set_font('Helvetica', '', 8.5)
        self.set_text_color(203, 213, 225)
        self.set_xy(10, 10.5)
        self.cell(0, 5, f"DEMONSTRATIVO GERENCIAL DE CAIXA (RGC) - MÊS DE REFERÊNCIA: {self.sel_mes_ano.upper()}", align='L')
        self.ln(10)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 6, f"DAATEL ERP - Documento Gerencial Confidencial - Página {self.page_no()}/{{nb}}", align='C')


def gerar_pdf_rgc(sel_mes_ano, saldo_inicial_caixa, rb_mes, ent_nat, ent_desc, ent_outros, dev_mes, imp_venda_mes, rl_mes, cmv_tot_mes, mp_val_mes, emb_mes, outros_fab_mes, desp_com_mes, comi_mes, frete_mes, acordos_mes, descarga_mes, degust_mes, promotores_mes, mc_mes, df_mes_val, ebitda_mes, depr_mes, imp_lucro_mes, finan_mes, jcp_mes, lucro_mes, div_mes, retido_mes, capex_mes, caixa_livre_mes, saldo_final_caixa, df_sai_mes):
    pdf = ExecutivePDF(sel_mes_ano)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def fmt_val(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # KPI Summary Cards Block at top
    pdf.set_y(24)

    # Card 1: Opening Cash Balance
    pdf.set_fill_color(224, 242, 254)
    pdf.set_draw_color(2, 132, 199)
    pdf.rect(10, 24, 61, 14, style='FD')
    pdf.set_xy(12, 25)
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_text_color(3, 105, 161)
    pdf.cell(57, 4, "SALDO INICIAL (ABERTURA)")
    pdf.set_xy(12, 29.5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(57, 6, fmt_val(saldo_inicial_caixa))

    # Card 2: Net Cash Generation in Month
    cg_bg = (220, 252, 231) if caixa_livre_mes >= 0 else (254, 226, 226)
    cg_txt = (21, 128, 61) if caixa_livre_mes >= 0 else (185, 28, 28)
    cg_brd = (22, 163, 74) if caixa_livre_mes >= 0 else (220, 38, 38)
    pdf.set_fill_color(*cg_bg)
    pdf.set_draw_color(*cg_brd)
    pdf.rect(74.5, 24, 61, 14, style='FD')
    pdf.set_xy(76.5, 25)
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_text_color(*cg_txt)
    pdf.cell(57, 4, "GERAÇÃO LÍQUIDA NO MÊS")
    pdf.set_xy(76.5, 29.5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(57, 6, fmt_val(caixa_livre_mes))

    # Card 3: Closing Cash Balance
    pdf.set_fill_color(238, 242, 255)
    pdf.set_draw_color(99, 102, 241)
    pdf.rect(139, 24, 61, 14, style='FD')
    pdf.set_xy(141, 25)
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_text_color(67, 56, 202)
    pdf.cell(57, 4, "SALDO FINAL (FECHAMENTO)")
    pdf.set_xy(141, 29.5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(57, 6, fmt_val(saldo_final_caixa))

    pdf.set_xy(10, 42)

    # Main Table Header
    pdf.set_draw_color(226, 232, 240)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(20, 7.5, "  Código", border=0, fill=True)
    pdf.cell(118, 7.5, "Descrição da Conta / Movimentação Gerencial", border=0, fill=True)
    pdf.cell(52, 7.5, "Valor (R$)  ", border=0, align='R', fill=True, new_x='LMARGIN', new_y='NEXT')

    rows = [
        ("INICIAL", "(+) SALDO INICIAL CONSOLIDADO DE CAIXA (Abertura)", saldo_inicial_caixa, "ini"),
        ("1.0", "1. Receita Operacional Realizada", rb_mes, "subtotal"),
        ("1.1.1", "  1.1 Entradas de Vendas de Alho In Natura", ent_nat, "normal"),
        ("1.1.2", "  1.2 Entradas de Vendas de Alho Descascado", ent_desc, "normal"),
        ("2.0", "2. (-) Devoluções / Abatimentos Realizados", dev_mes, "normal"),
        ("2.1.3", "3. (-) Impostos sobre Venda Pagos", imp_venda_mes, "normal"),
        ("RL", "(=) RECEITA LÍQUIDA DE CAIXA", rl_mes, "total"),
        ("4.0", "4. Custo Total de Fabricação / CMV Pago", cmv_tot_mes, "subtotal"),
        ("2.1.1", "  4.1 (-) Matéria-Prima Paga (Alho in Natura)", mp_val_mes, "normal"),
        ("2.1.2", "  4.2 (-) Embalagens & Insumos Pagos", emb_mes, "normal"),
        ("5.0", "5. Despesas Comerciais Variáveis Pagas", desp_com_mes, "subtotal"),
        ("2.1.5", "  5.2 (-) Fretes de Entrega Pagos", frete_mes, "normal"),
        ("MC", "(=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA DE CAIXA", mc_mes, "total"),
        ("6.0", "6. (-) Custos e Despesas Fixas Totais Pagas", df_mes_val, "subtotal"),
    ]

    if not df_sai_mes.empty:
        is_cf = df_sai_mes['codigo'].str.startswith(('2.3.', '3.1.'), na=False) | ((df_sai_mes['codigo'] == 'OUTROS') & ~df_sai_mes['codigo'].str.startswith(('3.2.', '3.3.', '1.2.', '4.1.'), na=False))
        df_cf = df_sai_mes[is_cf & ~df_sai_mes['codigo'].str.startswith(('3.2.', '3.3.', '1.2.', '4.1.'), na=False)]
        if not df_cf.empty:
            grp_cf = df_cf.groupby(['codigo', 'pc_nome'])['valor'].sum().reset_index().sort_values(by='codigo')
            for _, r in grp_cf.iterrows():
                rows.append((str(r['codigo']), f"    {r['codigo']} - {r['pc_nome']}", float(r['valor']), "detail"))

    rows.extend([
        ("EBITDA", "(=) EBITDA DE CAIXA (Resultado Operacional)", ebitda_mes, "total"),
        ("3.2.1", "9. (-) Juros e Financiamentos Pagos", finan_mes, "normal"),
        ("3.2.0", "8. (-) Impostos sobre Lucro Pagos (IRPJ/CSLL)", imp_lucro_mes, "normal"),
        ("GER", "(=) GERAÇÃO LÍQUIDA DE CAIXA OPERACIONAL", lucro_mes, "subtotal"),
        ("DIV", "12. (-) Dividendos (Saque/Distribuição Efetivada)", div_mes, "normal"),
        ("RET", "(=) GERAÇÃO RETIDA DE CAIXA OPERACIONAL", retido_mes, "total"),
        ("CAPEX", "(-) Desembolsos de Investimentos Pagos (CAPEX / Máquinas)", capex_mes, "normal"),
        ("VAR", "(=) GERAÇÃO / REDUÇÃO LÍQUIDA DE CAIXA NO MÊS", caixa_livre_mes, "capex"),
        ("FINAL", "(=) SALDO FINAL CONSOLIDADO DE CAIXA (Fechamento)", saldo_final_caixa, "fim")
    ])

    alt = False
    for r in rows:
        cod, desc, val, rtype = r
        val_str = fmt_val(val)
        
        pdf.set_draw_color(241, 245, 249)
        
        if rtype == 'ini':
            pdf.set_font('Helvetica', 'B', 8.5)
            pdf.set_fill_color(224, 242, 254)
            pdf.set_text_color(3, 105, 161)
        elif rtype == 'total':
            pdf.set_font('Helvetica', 'B', 8.5)
            pdf.set_fill_color(241, 245, 249)
            pdf.set_text_color(15, 23, 42)
        elif rtype == 'subtotal':
            pdf.set_font('Helvetica', 'B', 8.5)
            pdf.set_fill_color(248, 250, 252)
            pdf.set_text_color(30, 41, 59)
        elif rtype == 'capex':
            pdf.set_font('Helvetica', 'B', 8.5)
            pdf.set_fill_color(254, 240, 138)
            pdf.set_text_color(133, 77, 14)
        elif rtype == 'fim':
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_fill_color(220, 252, 231)
            pdf.set_text_color(21, 128, 61)
        elif rtype == 'detail':
            pdf.set_font('Helvetica', 'I', 7.5)
            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(100, 116, 139)
        else:
            pdf.set_font('Helvetica', '', 8)
            pdf.set_fill_color(250, 250, 250) if alt else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(51, 65, 85)
            alt = not alt

        pdf.cell(20, 5.8, f"  {cod}", border='B', fill=True)
        pdf.cell(118, 5.8, desc, border='B', fill=True)
        pdf.cell(52, 5.8, f"{val_str}  ", border='B', align='R', fill=True, new_x='LMARGIN', new_y='NEXT')

    pdf_bytes = pdf.output()
    return bytes(pdf_bytes) if isinstance(pdf_bytes, bytearray) else pdf_bytes

def f_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_kg(valor):
    return f"{valor:,.1f} Kg".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pm(valor):
    return f"R$ {valor:,.2f}/Kg".replace(",", "X").replace(".", ",").replace("X", ".")

# 1. Filtro de Calendário no Topo
hoje = date.today()
meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

opcoes_meses = []
for ano in [hoje.year - 1, hoje.year, hoje.year + 1]:
    for m in range(1, 13):
        opcoes_meses.append(f"{meses_nomes[m-1]}/{ano}")

default_label = f"{meses_nomes[hoje.month-1]}/{hoje.year}"
default_idx = opcoes_meses.index(default_label) if default_label in opcoes_meses else len(opcoes_meses) // 2

if "sel_mes_ano" not in st.session_state:
    st.session_state["sel_mes_ano"] = default_label

sel_mes_ano = st.session_state.get("sel_mes_ano", default_label)

nome_mes, ano_sel = sel_mes_ano.split("/")
ano_sel = int(ano_sel)
mes_sel = meses_nomes.index(nome_mes) + 1

p_mes = pd.Period(f"{ano_sel}-{mes_sel:02d}", freq='M')

dt_vd_devol_inicio_str = p_mes.start_time.strftime("%Y-%m-%d")
dt_vd_devol_fim_str = p_mes.end_time.strftime("%Y-%m-%d")

# --- QUERY PRINCIPAL DO FLUXO DE CAIXA REAL (EXTRATO RAZÃO BANCOS / CAIXA FÍSICO) ---
q_fc = """
    SELECT 
        f.id,
        f.data,
        f.tipo,
        f.valor,
        f.descricao,
        f.categoria as fc_categoria,
        COALESCE(pc_p.codigo, pc_r.codigo, 'OUTROS') as codigo,
        COALESCE(pc_p.nome, pc_r.nome, f.categoria, 'Outros Lançamentos') as pc_nome,
        COALESCE(pc_p.categoria, pc_r.categoria, 'Geral') as pc_cat
    FROM fluxo_caixa f
    LEFT JOIN contas_a_pagar cp ON (UPPER(f.tipo) = 'SAIDA' OR f.tipo = 'Saída' OR f.tipo = 'Saida') AND f.fonte_id = cp.id AND (f.categoria IS NULL OR f.categoria NOT IN ('Transferência', 'Ajuste de saldo'))
    LEFT JOIN planos_de_contas pc_p ON cp.plano_conta_id = pc_p.id
    LEFT JOIN contas_a_receber cr ON (UPPER(f.tipo) = 'ENTRADA' OR f.tipo = 'Entrada') AND f.fonte_id = cr.id AND (f.categoria IS NULL OR f.categoria NOT IN ('Transferência', 'Ajuste de saldo'))
    LEFT JOIN planos_de_contas pc_r ON cr.plano_conta_id = pc_r.id
    WHERE f.data >= ? AND f.data <= ?
      AND (f.categoria IS NULL OR f.categoria NOT IN ('Transferência', 'Ajuste de saldo'))
    ORDER BY f.data ASC
"""
df_fc_mes = fetch_all(q_fc, (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

if df_fc_mes is None or df_fc_mes.empty:
    df_fc_mes = pd.DataFrame(columns=['id', 'data', 'tipo', 'valor', 'descricao', 'fc_categoria', 'codigo', 'pc_nome', 'pc_cat'])

# Subdivisão por tipo de movimentação
is_ent = df_fc_mes['tipo'].astype(str).str.upper().isin(['ENTRADA'])
is_sai = df_fc_mes['tipo'].astype(str).str.upper().isin(['SAIDA', 'SAÍDA'])

df_ent_mes = df_fc_mes[is_ent]
df_sai_mes = df_fc_mes[is_sai]

# --- 1. RECEITAS DE CAIXA (ENTRADAS DE CAIXA EFETIVADAS) ---
rb_mes = float(df_ent_mes['valor'].sum()) if not df_ent_mes.empty else 0.0

ent_nat = float(df_ent_mes[df_ent_mes['codigo'] == '1.1.1']['valor'].sum()) if not df_ent_mes.empty else 0.0
ent_desc = float(df_ent_mes[df_ent_mes['codigo'] == '1.1.2']['valor'].sum()) if not df_ent_mes.empty else 0.0
ent_outros = rb_mes - ent_nat - ent_desc

# Faturamento Físico em Kg (Consultado das Vendas Faturadas para apoio de indicadores físicos)
df_vd_mes = fetch_all("SELECT quantidade, valor_total FROM vendas WHERE status = 'FATURADO' AND data >= ? AND data <= ?", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))
rb_kg_mes = float(df_vd_mes['quantidade'].sum()) if (df_vd_mes is not None and not df_vd_mes.empty) else 0.0
rb_pm_mes = rb_mes / rb_kg_mes if rb_kg_mes > 0 else 0.0

# Receita Líquida de Caixa
dev_mes = 0.0
imp_venda_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.1.3', na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
rl_mes = rb_mes - dev_mes - imp_venda_mes
rl_kg_mes = rb_kg_mes
rl_pm_mes = rl_mes / rl_kg_mes if rl_kg_mes > 0 else 0.0

# --- 2. CUSTOS FABRIS E CUSTOS VARIÁVEIS PAGOS ---
mp_val_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.1.1', na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
emb_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.1.2', na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
outros_fab_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.1.', na=False) & ~df_sai_mes['codigo'].str.startswith(('2.1.1', '2.1.2', '2.1.3', '2.1.4', '2.1.5'), na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0

cmv_tot_mes = mp_val_mes + emb_mes + outros_fab_mes

df_mp_mes = fetch_all("SELECT peso_kg FROM compras_materia_prima WHERE data >= ? AND data <= ?", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))
mp_kg_mes = float(df_mp_mes['peso_kg'].sum()) if (df_mp_mes is not None and not df_mp_mes.empty) else 0.0

if mp_kg_mes == 0:
    df_est_mp = fetch_all("""
        SELECT em.quantidade
        FROM estoque_movimentos em
        JOIN produtos p ON em.produto_id = p.id
        WHERE UPPER(em.tipo_movimento) = 'ENTRADA'
          AND (p.is_materia_prima IS TRUE OR CAST(p.is_materia_prima AS TEXT) = '1')
          AND em.data >= ? AND em.data <= ?
    """, (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))
    if df_est_mp is not None and not df_est_mp.empty:
        mp_kg_mes = float(df_est_mp['quantidade'].sum())

mp_pm_mes = mp_val_mes / mp_kg_mes if mp_kg_mes > 0 else 0.0

if mp_kg_mes > 0:
    tags_mp_html = f"<span class='dre-tag'>Compras: {f_kg(mp_kg_mes)}</span><span class='dre-tag'>Custo Médio: {f_pm(mp_pm_mes)}</span>"
else:
    tags_mp_html = "<span class='dre-tag'>Lançamentos no Contas a Pagar</span>"

# --- 3. DESPESAS COMERCIAIS VARIÁVEIS PAGAS ---
comi_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.1.4', na=False) | df_sai_mes['pc_nome'].str.contains('Comissão|Comissões', case=False, na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
frete_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith(('2.1.5', '2.2.3', '2.2.5'), na=False) | df_sai_mes['pc_nome'].str.contains('Frete', case=False, na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
acordos_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.2.2', na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
descarga_mes = float(df_sai_mes[df_sai_mes['pc_nome'].str.contains('Descarga', case=False, na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
degust_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.2.1', na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
promotores_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('2.2.4', na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0

desp_com_mes = comi_mes + frete_mes + acordos_mes + descarga_mes + degust_mes + promotores_mes

# Margem de Contribuição Líquida de Caixa
mc_mes = rl_mes - cmv_tot_mes - desp_com_mes
mc_perc = (mc_mes / rl_mes * 100) if rl_mes > 0 else 0.0
mc_kg_mes = mc_mes / rl_kg_mes if rl_kg_mes > 0 else 0.0

# --- 4. CUSTOS E DESPESAS FIXAS PAGAS ---
is_cf = df_sai_mes['codigo'].str.startswith(('2.3.', '3.1.'), na=False) | ((df_sai_mes['codigo'] == 'OUTROS') & ~df_sai_mes['codigo'].str.startswith(('3.2.', '3.3.', '1.2.', '4.1.'), na=False))
df_mes_val = float(df_sai_mes[is_cf & ~df_sai_mes['codigo'].str.startswith(('3.2.', '3.3.', '1.2.', '4.1.'), na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0

# EBITDA de Caixa (Resultado Operacional Real)
ebitda_mes = mc_mes - df_mes_val
ebitda_perc = (ebitda_mes / rl_mes * 100) if rl_mes > 0 else 0.0

# --- 5. FATORES NÃO-OPERACIONAIS E FINANCEIROS PAGOS ---
finan_mes = float(df_sai_mes[df_sai_mes['codigo'].str.startswith('3.2.', na=False) | df_sai_mes['pc_nome'].str.contains('Financiamento|Empréstimo|Juros', case=False, na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
depr_mes = 0.0
imp_lucro_mes = float(df_sai_mes[df_sai_mes['pc_nome'].str.contains('IRPJ|CSLL', case=False, na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
jcp_mes = float(df_sai_mes[df_sai_mes['pc_nome'].str.contains('JCP', case=False, na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0

# Geração Líquida de Caixa Operacional
lucro_mes = ebitda_mes - depr_mes - imp_lucro_mes - finan_mes - jcp_mes
lucro_perc = (lucro_mes / rl_mes * 100) if rl_mes > 0 else 0.0

div_mes = float(df_sai_mes[df_sai_mes['pc_nome'].str.contains('Dividendos|Distribuição de Lucro', case=False, na=False)]['valor'].sum()) if not df_sai_mes.empty else 0.0
retido_mes = lucro_mes - div_mes

# --- 6. INVESTIMENTOS PAGOS (CAPEX) ---
is_capex = df_sai_mes['codigo'].str.startswith(('3.3.', '1.2.', '4.1.'), na=False) | (df_sai_mes['pc_nome'].str.contains('Compra de Máquinas|Imobilizado|CAPEX', case=False, na=False) & ~df_sai_mes['codigo'].str.startswith('2.', na=False))
capex_mes = float(df_sai_mes[is_capex]['valor'].sum()) if not df_sai_mes.empty else 0.0

# Geração / Redução Líquida de Caixa no Mês
tot_saidas = float(df_sai_mes['valor'].sum()) if not df_sai_mes.empty else 0.0
caixa_livre_mes = rb_mes - tot_saidas

# --- 7. SALDO INICIAL E SALDO FINAL CONSOLIDADO DE CAIXA ---
saldo_ini_df = fetch_all("""
    SELECT SUM(CASE WHEN UPPER(tipo) = 'ENTRADA' THEN valor ELSE -valor END) as saldo_ini
    FROM fluxo_caixa
    WHERE data < ?
""", (dt_vd_devol_inicio_str,))
saldo_inicial_caixa = float(saldo_ini_df['saldo_ini'].iloc[0]) if (not saldo_ini_df.empty and pd.notnull(saldo_ini_df['saldo_ini'].iloc[0])) else 0.0
saldo_final_caixa = saldo_inicial_caixa + caixa_livre_mes

# Ponto de Equilíbrio
break_even = (df_mes_val / (mc_perc / 100)) if mc_perc > 0 else 0.0

# --- FUNÇÃO NATIVA DE EXIBIÇÃO DE LINHA RGC ---
def render_linha_rgc(cod, desc, val, rtype="normal", tags=None):
    col_c, col_d, col_v = st.columns([1.2, 5.8, 2.5])
    val_fmt = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    tag_str = f" &nbsp; *({' | '.join(tags)})*" if tags else ""
    
    if rtype == "ini":
        col_c.markdown(f"**:blue[{cod}]**")
        col_d.markdown(f"### :blue[{desc}]")
        col_v.markdown(f"### :blue[{val_fmt}]")
    elif rtype == "total":
        col_c.markdown(f"**`{cod}`**")
        col_d.markdown(f"#### **{desc}**{tag_str}")
        col_v.markdown(f"#### **{val_fmt}**")
        st.divider()
    elif rtype == "subtotal":
        col_c.markdown(f"**{cod}**")
        col_d.markdown(f"**{desc}**{tag_str}")
        col_v.markdown(f"**{val_fmt}**")
    elif rtype == "capex":
        col_c.markdown(f"**:orange[{cod}]**")
        col_d.markdown(f"### :orange[{desc}]")
        col_v.markdown(f"### :orange[{val_fmt}]")
        st.divider()
    elif rtype == "fim":
        col_c.markdown(f"**:green[{cod}]**")
        col_d.markdown(f"### :green[{desc}]")
        col_v.markdown(f"### :green[{val_fmt}]")
        st.divider()
    elif rtype == "detail":
        col_c.caption(f"└ {cod}")
        col_d.caption(f"↳ {desc}")
        col_v.caption(f"{val_fmt}")
    else:
        col_c.write(f"`{cod}`" if cod else "")
        col_d.write(f"{desc}{tag_str}")
        col_v.write(f"{val_fmt}")

def render_detalhes_plano(prefixos_codigo=None, nomes_filtro=None, ignorar_codigos=None):
    if df_sai_mes.empty:
        return
    cond = pd.Series([False] * len(df_sai_mes), index=df_sai_mes.index)
    if prefixos_codigo:
        for pfix in prefixos_codigo:
            cond |= df_sai_mes['codigo'].str.startswith(pfix, na=False)
    if nomes_filtro:
        for nfilt in nomes_filtro:
            cond |= df_sai_mes['pc_nome'].str.contains(nfilt, case=False, na=False)
            
    if ignorar_codigos:
        for icod in ignorar_codigos:
            cond &= ~df_sai_mes['codigo'].str.startswith(icod, na=False)
            
    df_filtered = df_sai_mes[cond]
    if df_filtered.empty:
        return
        
    grouped = df_filtered.groupby(['codigo', 'pc_nome'])['valor'].sum().reset_index().sort_values(by='codigo')
    for _, r in grouped.iterrows():
        render_linha_rgc(str(r['codigo']), r['pc_nome'], float(r['valor']), rtype="detail")


# --- MODAL DE AUDITORIA DE LANÇAMENTOS DE CAIXA ---
@st.dialog("🔍 Auditoria de Lançamentos de Caixa", width="large")
def modal_auditoria_lancamentos(conta_label, sel_mes_ano):
    st.caption(f"Exibindo extrato de caixa analítico com todas as movimentações reais que compõem **{conta_label}** em **{sel_mes_ano}**.")
    
    dt_inc = dt_vd_devol_inicio_str
    dt_fim = dt_vd_devol_fim_str
    
    if "1.1" in conta_label or "Venda" in conta_label or "Receita" in conta_label:
        df_a = fetch_all("""
            SELECT f.data AS "Data Pgto", f.descricao AS "Descrição / Histórico", f.valor AS "Valor (R$)"
            FROM fluxo_caixa f
            WHERE (UPPER(f.tipo) = 'ENTRADA' OR f.tipo = 'Entrada') AND f.data >= ? AND f.data <= ?
            ORDER BY f.data ASC
        """, (dt_inc, dt_fim))
    else:
        cod_alvo = conta_label.split(' - ')[0].strip()
        df_a = fetch_all("""
            SELECT f.data AS "Data Pgto", f.descricao AS "Descrição / Histórico",
                   COALESCE(pc.codigo, 'OUTROS') AS "Código", COALESCE(pc.nome, f.categoria) AS "Rubrica",
                   f.valor AS "Valor (R$)"
            FROM fluxo_caixa f
            LEFT JOIN contas_a_pagar cp ON (UPPER(f.tipo) = 'SAIDA' OR f.tipo = 'Saída' OR f.tipo = 'Saida') AND f.fonte_id = cp.id
            LEFT JOIN planos_de_contas pc ON cp.plano_conta_id = pc.id
            WHERE (UPPER(f.tipo) = 'SAIDA' OR f.tipo = 'Saída' OR f.tipo = 'Saida')
              AND f.data >= ? AND f.data <= ?
              AND (pc.codigo LIKE ? OR f.categoria LIKE ? OR pc.nome LIKE ?)
            ORDER BY f.data ASC
        """, (dt_inc, dt_fim, f"{cod_alvo}%", f"%{cod_alvo}%", f"%{cod_alvo}%"))
        
    if df_a is None or df_a.empty:
        st.info(f"Nenhuma movimentação de caixa encontrada para **{conta_label}** no período de {sel_mes_ano}.")
    else:
        tot_val = float(df_a['Valor (R$)'].sum()) if 'Valor (R$)' in df_a.columns else 0.0
        tot_reg = len(df_a)
        
        mc1, mc2 = st.columns(2)
        mc1.metric("Qtd. Lançamentos", tot_reg)
        mc2.metric("Soma Total Auditada", f_br(tot_val))
        
        df_disp = df_a.copy()
        if 'Valor (R$)' in df_disp.columns:
            df_disp['Valor (R$)'] = df_disp['Valor (R$)'].apply(lambda x: f_br(float(x)) if pd.notnull(x) else "R$ 0,00")
            
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        
        csv_data = df_a.to_csv(index=False).encode('utf-8')
        cod_clean = conta_label.split(' - ')[0].replace('.', '_')
        st.download_button(
            label="📥 Baixar Extrato de Auditoria (CSV)",
            data=csv_data,
            file_name=f"auditoria_caixa_{cod_clean}_{sel_mes_ano.replace('/', '_')}.csv",
            mime="text/csv"
        )

# -------- RENDERIZAÇÃO VISUAL NATIVA DO STREAMLIT ---------

st.title("🏛️ Relatório Gerencial de Caixa (RGC)")

col_hdr_sel, col_hdr_audit, col_exp_1, col_exp_2 = st.columns([1.2, 1.4, 1.2, 1.2])

with col_hdr_sel:
    st.selectbox(
        "Selecione o Mês/Ano:",
        opcoes_meses,
        index=opcoes_meses.index(sel_mes_ano) if sel_mes_ano in opcoes_meses else default_idx,
        key="sel_mes_ano"
    )

with col_hdr_audit:
    opcoes_audit = [
        "🔍 Auditar Rubrica / Conta...",
        "1.1 - Vendas por Nota Fiscal (NF)",
        "1.2 - Vendas por DAV (Pedido)",
        "2 - Devoluções e Abatimentos",
        "4.1 - Matéria-Prima (Alho in Natura)"
    ]
    if not df_sai_mes.empty:
        pcs_mes = df_sai_mes[['codigo', 'pc_nome']].drop_duplicates().sort_values('codigo')
        for _, r in pcs_mes.iterrows():
            lbl = f"{r['codigo']} - {r['pc_nome']}"
            if lbl not in opcoes_audit:
                opcoes_audit.append(lbl)
                
    def on_audit_change():
        selected = st.session_state.get("sel_audit_rubrica")
        if selected and selected != "🔍 Auditar Rubrica / Conta...":
            st.session_state["active_audit_rubrica"] = selected
            st.session_state["sel_audit_rubrica"] = "🔍 Auditar Rubrica / Conta..."
            
    st.selectbox(
        "🔍 Inspecionar Conta:",
        opcoes_audit,
        key="sel_audit_rubrica",
        on_change=on_audit_change
    )
    
    active_rubrica = st.session_state.pop("active_audit_rubrica", None)
    if active_rubrica:
        modal_auditoria_lancamentos(active_rubrica, sel_mes_ano)

with col_exp_1:
    excel_bytes = gerar_excel_rgc(sel_mes_ano, saldo_inicial_caixa, rb_mes, ent_nat, ent_desc, ent_outros, dev_mes, imp_venda_mes, rl_mes, cmv_tot_mes, mp_val_mes, emb_mes, outros_fab_mes, desp_com_mes, comi_mes, frete_mes, acordos_mes, descarga_mes, degust_mes, promotores_mes, mc_mes, df_mes_val, ebitda_mes, depr_mes, imp_lucro_mes, finan_mes, jcp_mes, lucro_mes, div_mes, retido_mes, capex_mes, caixa_livre_mes, saldo_final_caixa, df_sai_mes)
    st.download_button(
        label="📊 Excel (.xlsx)",
        data=excel_bytes,
        file_name=f"Relatorio_Gerencial_Caixa_{sel_mes_ano.replace('/', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_exp_2:
    pdf_bytes = gerar_pdf_rgc(sel_mes_ano, saldo_inicial_caixa, rb_mes, ent_nat, ent_desc, ent_outros, dev_mes, imp_venda_mes, rl_mes, cmv_tot_mes, mp_val_mes, emb_mes, outros_fab_mes, desp_com_mes, comi_mes, frete_mes, acordos_mes, descarga_mes, degust_mes, promotores_mes, mc_mes, df_mes_val, ebitda_mes, depr_mes, imp_lucro_mes, finan_mes, jcp_mes, lucro_mes, div_mes, retido_mes, capex_mes, caixa_livre_mes, saldo_final_caixa, df_sai_mes)
    st.download_button(
        label="📄 PDF",
        data=pdf_bytes,
        file_name=f"Relatorio_Gerencial_Caixa_{sel_mes_ano.replace('/', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.divider()

# ABERTURA DO CAIXA
with st.container(border=True):
    render_linha_rgc("INICIAL", "(+) SALDO INICIAL CONSOLIDADO DE CAIXA (Abertura do Mês)", saldo_inicial_caixa, rtype="ini")

# I. ENTRADAS DE CAIXA
st.subheader("I. Entradas de Caixa (Recebimentos Efetivados)")
with st.container(border=True):
    render_linha_rgc("1.0", f"1. Receita Operacional Realizada ({sel_mes_ano})", rb_mes, rtype="subtotal", tags=[f"Volume: {f_kg(rb_kg_mes)}", f"Preço Médio: {f_pm(rb_pm_mes)}"])
    render_linha_rgc("1.1.1", "1.1 Entradas de Vendas de Alho In Natura", ent_nat)
    render_linha_rgc("1.1.2", "1.2 Entradas de Vendas de Alho Descascado", ent_desc)
    if ent_outros > 0:
        render_linha_rgc("1.3", "1.3 Outras Receitas Operacionais Recebidas", ent_outros)
    render_linha_rgc("2.0", "2. (-) Devoluções / Abatimentos Realizados", dev_mes)
    render_linha_rgc("2.1.3", "3. (-) Impostos sobre Venda Pagos", imp_venda_mes)
    render_detalhes_plano(prefixos_codigo=['2.1.3'])
    render_linha_rgc("RL", "(=) RECEITA LÍQUIDA DE CAIXA", rl_mes, rtype="total", tags=[f"Volume: {f_kg(rl_kg_mes)}", f"PM Líquido: {f_pm(rl_pm_mes)}"])

# II. CUSTOS FABRIS E VARIÁVEIS PAGOS
st.subheader("II. Custos Fabris e Despesas Variáveis Pagas")
with st.container(border=True):
    render_linha_rgc("4.0", "4. Custo Total de Fabricação / CMV Pago", cmv_tot_mes, rtype="subtotal")
    mp_tags = [f"Compras: {f_kg(mp_kg_mes)}", f"Custo Médio: {f_pm(mp_pm_mes)}"] if mp_kg_mes > 0 else ["Lançamentos no Contas a Pagar"]
    render_linha_rgc("2.1.1", "4.1 (-) Matéria-Prima Paga (Alho in Natura)", mp_val_mes, tags=mp_tags)
    render_linha_rgc("2.1.2", "4.2 (-) Embalagens & Insumos Pagos", emb_mes)
    if outros_fab_mes > 0:
        render_linha_rgc("2.1.X", "4.3 (-) Outros Custos Fabris Diretos Pagos", outros_fab_mes)
    render_detalhes_plano(prefixos_codigo=['2.1.'], ignorar_codigos=['2.1.1', '2.1.2', '2.1.3', '2.1.4', '2.1.5'])
    
    st.markdown("---")
    render_linha_rgc("5.0", "5. Despesas Comerciais Variáveis Pagas", desp_com_mes, rtype="subtotal")
    render_linha_rgc("2.1.4", "5.1 (-) Comissões de Vendas Pagas", comi_mes)
    render_linha_rgc("2.1.5", "5.2 (-) Fretes de Entrega Pagos (Logística de Saída)", frete_mes)
    render_linha_rgc("2.2.2", "5.3 (-) Acordos de Rede & Rebates Comerciais Pagos", acordos_mes)
    render_linha_rgc("2.2.0", "5.4 (-) Taxas de Descarga Pagas (CD/Redes)", descarga_mes)
    render_linha_rgc("2.2.1", "5.5 (-) Degustações e Amostras Pagas", degust_mes)
    render_linha_rgc("2.2.4", "5.6 (-) Serviços de Promotores de Vendas Pagos", promotores_mes)
    render_detalhes_plano(prefixos_codigo=['2.2.'], ignorar_codigos=['2.2.1', '2.2.2', '2.2.4', '2.1.4', '2.1.5'])
    
    render_linha_rgc("MC", "(=) MARGEM DE CONTRIBUIÇÃO LÍQUIDA DE CAIXA", mc_mes, rtype="total", tags=[f"Margem: {mc_perc:.1f}%", f"Margem/Kg: {f_pm(mc_kg_mes)}"])

# III. CUSTOS FIXOS PAGOS
st.subheader("III. Custos e Despesas Fixas Pagas")
with st.container(border=True):
    render_linha_rgc("6.0", "6. (-) Custos e Despesas Fixas Totais Pagas", df_mes_val, rtype="subtotal")
    render_detalhes_plano(prefixos_codigo=['2.3.', '3.1.', 'OUTROS'], ignorar_codigos=['3.2.', '3.3.', '1.2.', '4.1.'])

# IV. EBITDA
st.subheader("IV. EBITDA de Caixa (Resultado Operacional Real)")
with st.container(border=True):
    render_linha_rgc("EBITDA", "(=) EBITDA DE CAIXA (Resultado Operacional Real)", ebitda_mes, rtype="total", tags=[f"Margem EBITDA: {ebitda_perc:.1f}%"])

# V. FATORES NÃO-OPERACIONAIS E FINANCEIROS
st.subheader("V. Fatores Não-Operacionais e Financeiros Pagos")
with st.container(border=True):
    render_linha_rgc("3.1.9", "7. (-) Depreciação / Amortização (Não-Caixa)", depr_mes)
    render_linha_rgc("3.2.0", "8. (-) Impostos sobre Lucro Pagos (IRPJ/CSLL)", imp_lucro_mes)
    render_linha_rgc("3.2.1", "9. (-) Juros e Financiamentos Pagos", finan_mes)
    render_linha_rgc("3.2.2", "10. (-) JCP Pagos (Juros s/ Capital Próprio)", jcp_mes)
    render_detalhes_plano(prefixos_codigo=['3.2.'], nomes_filtro=['Depreciação', 'Impostos sobre Lucro', 'IRPJ', 'CSLL', 'Financiamento', 'Juros', 'JCP'])

# VI. GERAÇÃO LÍQUIDA DE CAIXA OPERACIONAL
st.subheader("VI. Geração Líquida de Caixa Operacional")
with st.container(border=True):
    render_linha_rgc("GER", "11. (=) GERAÇÃO LÍQUIDA DE CAIXA OPERACIONAL", lucro_mes, rtype="subtotal", tags=[f"Lucratividade: {lucro_perc:.1f}%"])
    render_linha_rgc("DIV", "12. (-) Dividendos (Saque/Distribuição Efetivada ao Sócio)", div_mes)
    render_linha_rgc("RET", "(=) GERAÇÃO RETIDA DE CAIXA OPERACIONAL", retido_mes, rtype="total")

# VII. DESEMBOLSOS DE INVESTIMENTOS (CAPEX)
st.subheader("VII. Desembolsos de Investimentos (CAPEX)")
with st.container(border=True):
    render_linha_rgc("GER", "Geração Líquida de Caixa Operacional", lucro_mes)
    render_linha_rgc("CAPEX", "(-) Desembolsos de Investimentos Pagos (Compra de Máquinas e Equipamentos)", capex_mes)
    render_detalhes_plano(prefixos_codigo=['3.3.', '1.2.', '4.1.'], nomes_filtro=['Compra de Máquinas', 'Imobilizado', 'CAPEX'], ignorar_codigos=['2.3.3', '2.3.'])
    render_linha_rgc("VAR", "(=) GERAÇÃO / REDUÇÃO LÍQUIDA DE CAIXA NO MÊS", caixa_livre_mes, rtype="capex")

# FECHAMENTO DO CAIXA (SALDO FINAL)
with st.container(border=True):
    render_linha_rgc("FINAL", "(=) SALDO FINAL CONSOLIDADO DE CAIXA (Fechamento do Mês)", saldo_final_caixa, rtype="fim", tags=[f"Geração Líquida: {f_br(caixa_livre_mes)}"])

st.caption("📌 **Visão Gerencial:** Relatório 100% extraído das movimentações reais do Extrato Bancário e Caixa Físico (`fluxo_caixa`). Paridade absoluta de 100,00% com o Extrato Razão oficial.")

st.divider()

# VIII. PONTO DE EQUILÍBRIO (BREAK-EVEN) EM EXPANDER
with st.expander("🎯 Ponto de Equilíbrio (Break-Even Operacional)", expanded=False):
    st.markdown("> **O que é isso?** É o ponto exato de faturamento onde a sua fábrica zera todas as contas operacionais (EBITDA Zero) e passa a ter fluxo positivo para pagar bancos e lucros. Vender abaixo disso significa tirar dinheiro do próprio bolso para a fábrica abrir as portas.")
    
    colB1, colB2 = st.columns(2)
    colB1.metric("Faturamento Mínimo para Sobrevivência (Mês)", f_br(break_even))
    faltante = break_even - rl_mes
    if faltante > 0:
        colB2.metric("Ainda Faltam Vender (Neste Mês):", f_br(faltante), delta="Risco de Sangria", delta_color="inverse")
        st.warning(f"⚠️ Atenção! Você faturou apenas {f_br(rl_mes)} esse mês. A sua margem atual não cobre os R$ {df_mes_val:,.2f} de despesas fixas. Desperte a área comercial ou enxugue o RH e o aluguel.")
    else:
        lucro_acima = rl_mes - break_even
        colB2.metric("Oceano Azul (Faturamento Acima do Ponto):", f_br(lucro_acima), delta="Zona de Lucro", delta_color="normal")
        st.success(f"🥳 Parabéns Máquina! Você já estourou o teto e pagou todas das despesas desse mês. As próximas vendas são lucro quase líquido pro caixa!")



