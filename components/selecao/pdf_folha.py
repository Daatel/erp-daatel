# components/selecao/pdf_folha.py
# Gerador da Folha Diária de Seleção (PDF) — Empório do Alho

import io
from datetime import date
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    SimpleDocTemplate = None

# Cores Corporativas alinhadas ao ERP
GREEN_PRIMARY = HexColor("#01743d") if REPORTLAB_AVAILABLE else None
GRAY_DARK     = HexColor("#1e293b") if REPORTLAB_AVAILABLE else None
GRAY_MID      = HexColor("#64748b") if REPORTLAB_AVAILABLE else None
GRAY_BG       = HexColor("#f8fafc") if REPORTLAB_AVAILABLE else None
GRAY_LIGHT    = HexColor("#e2e8f0") if REPORTLAB_AVAILABLE else None

if REPORTLAB_AVAILABLE:
    styles = getSampleStyleSheet()
    s_title   = ParagraphStyle("title",  fontName="Helvetica-Bold", fontSize=15, textColor=GREEN_PRIMARY, spaceAfter=2)
    s_sub     = ParagraphStyle("sub",    fontName="Helvetica",      fontSize=9,  textColor=GRAY_MID)
    s_meta_r  = ParagraphStyle("metar",  fontName="Helvetica",      fontSize=9,  textColor=GRAY_DARK, alignment=TA_RIGHT)
    s_section = ParagraphStyle("sec",    fontName="Helvetica-Bold", fontSize=8,  textColor=GRAY_DARK, spaceAfter=3)
    s_rodape  = ParagraphStyle("rod",    fontName="Helvetica",      fontSize=7,  textColor=GRAY_MID)
    s_rodape_r= ParagraphStyle("rodr",   fontName="Helvetica",      fontSize=7,  textColor=GRAY_MID,  alignment=TA_RIGHT)
    s_obs     = ParagraphStyle("obs",    fontName="Helvetica",      fontSize=7,  textColor=GRAY_MID,  alignment=TA_RIGHT)
    s_th      = ParagraphStyle("th",     fontName="Helvetica-Bold", fontSize=8,  textColor=GRAY_DARK)
    s_td      = ParagraphStyle("td",     fontName="Helvetica",      fontSize=9,  textColor=GRAY_DARK)
    s_td_c    = ParagraphStyle("tdc",    fontName="Helvetica",      fontSize=9,  textColor=GRAY_MID, alignment=TA_CENTER)
    s_tot     = ParagraphStyle("tot",    fontName="Helvetica-Bold", fontSize=9,  textColor=GRAY_DARK, alignment=TA_RIGHT)
    s_tot2    = ParagraphStyle("tot2",   fontName="Helvetica-Bold", fontSize=9,  textColor=GRAY_MID, alignment=TA_CENTER)
    s_ass     = ParagraphStyle("ass",    fontName="Helvetica",      fontSize=8,  textColor=GRAY_MID)


def obter_primeiro_nome(nome_completo: str) -> str:
    """Extrai estritamente o primeiro nome por compliance e privacidade trabalhista."""
    if not nome_completo:
        return ""
    partes = nome_completo.strip().split()
    return partes[0] if partes else ""

def gerar_pdf_folha(data_ref: date, presentes: list, meta_casa_kg: float = 500.0) -> bytes:
    """
    Gera a folha diária de seleção em PDF.
    - Exibe apenas o primeiro nome das selecionadoras.
    - Exibe a meta da casa parametrizada dinamicamente.
    """
    buf = io.BytesIO()
    W = A4[0] - 30 * mm

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=12*mm,  bottomMargin=12*mm,
    )

    story = []

    # -- Cabeçalho --
    data_str = data_ref.strftime("%d / %m / %Y")
    header = Table([
        [
            Paragraph("Empório do Alho — Fábrica", s_title),
            Paragraph(f"Data: <b>{data_str}</b><br/>Responsável: ______________________", s_meta_r),
        ]
    ], colWidths=[W * 0.6, W * 0.4])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header)
    story.append(Paragraph("Folha Diária de Seleção de Alho (Chão de Fábrica)", s_sub))
    story.append(HRFlowable(width=W, thickness=1.5, color=GREEN_PRIMARY, spaceAfter=6))

    # -- Resumo do dia --
    n_presentes = len(presentes)
    cap_total   = sum(p.get("meta_kg_dia", 70.0) for p in presentes)

    resumo = Table([
        ["Presentes Hoje", "Capacidade do Dia", "Meta Mínima da Casa"],
        [f"{n_presentes} selecionadoras", f"{cap_total:,.0f} kg", f"{meta_casa_kg:,.0f} kg"],
    ], colWidths=[W / 3] * 3)
    resumo.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), GRAY_BG),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, 0), 7),
        ("TEXTCOLOR",     (0, 0), (-1, 0), GRAY_MID),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 12),
        ("TEXTCOLOR",     (0, 1), (-1, 1), GRAY_DARK),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRAY_LIGHT),
    ]))
    story.append(resumo)
    story.append(Spacer(1, 8))

    # -- Tabela de pesagem --
    story.append(Paragraph("PESAGEM INDIVIDUAL DAS SELECIONADORAS", s_section))

    COL_P = [W*0.06, W*0.34, W*0.14, W*0.15, W*0.15, W*0.16]

    header_row = [
        Paragraph("#",          s_th),
        Paragraph("Nome (Primeiro Nome)", s_th),
        Paragraph("Meta (kg)",  s_th),
        Paragraph("Pesagem 1",  s_th),
        Paragraph("Pesagem 2",  s_th),
        Paragraph("Total (kg)", s_th),
    ]

    rows = [header_row]
    meta_total = 0
    for i, p in enumerate(presentes, start=1):
        meta_p = float(p.get("meta_kg_dia", 70.0))
        meta_total += meta_p
        p_nome = obter_primeiro_nome(p.get("nome", ""))
        rows.append([
            Paragraph(str(i), s_td_c),
            Paragraph(p_nome, s_td),
            Paragraph(f"{meta_p:.0f} kg", s_td_c),
            "", "", ""
        ])
    rows.append([
        "",
        Paragraph("Total da Capacidade", s_tot),
        Paragraph(f"{meta_total:,.0f} kg", s_tot2),
        "", "", ""
    ])

    tab_p = Table(
        rows,
        colWidths=COL_P,
        rowHeights=[None] + [12*mm] * len(presentes) + [None],
    )
    tab_p.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0),  (-1, 0),  GRAY_BG),
        ("BACKGROUND",    (0, -1), (-1, -1), GRAY_BG),
        ("GRID",          (0, 0),  (-1, -1), 0.5, GRAY_LIGHT),
        ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0),  (-1, -1), "CENTER"),
        ("ALIGN",         (1, 0),  (1, -1),  "LEFT"),
        ("TOPPADDING",    (0, 0),  (-1, 0),  4),
        ("BOTTOMPADDING", (0, 0),  (-1, 0),  4),
        ("LINEBELOW",     (3, 1),  (5, -2),  0.8, GRAY_DARK),
        ("LINEBELOW",     (5, -1), (5, -1),  0.8, GRAY_DARK),
    ]))
    story.append(tab_p)
    story.append(Spacer(1, 8))

    # -- Tabela descarte x 2ª linha --
    story.append(Paragraph("BALANÇO DE RENDIMENTO & RESÍDUOS DO LOTE DIÁRIO", s_section))

    COL_D = [W*0.22, W*0.44, W*0.17, W*0.17]
    s_bold = ParagraphStyle("b", fontName="Helvetica-Bold", fontSize=9, textColor=GRAY_DARK)
    s_dd   = ParagraphStyle("dd", fontName="Helvetica", fontSize=8, textColor=GRAY_MID)

    desc_rows = [
        [Paragraph("Classificação", s_th), Paragraph("Descrição / Destino", s_th),
         Paragraph("Peso (kg)", s_th), Paragraph("% do Lote", s_th)],
        [Paragraph("Alho Nobre", s_bold),
         Paragraph("Dentes íntegros — Sacos de Alho Descascado", s_dd), "", ""],
        [Paragraph("2ª Linha (Bombona)", s_bold),
         Paragraph("Manchados/pequenos — Venda/Uso para Temperos", s_dd), "", ""],
        [Paragraph("Descarte (Lixo)", s_bold),
         Paragraph("Material deteriorado — Perda Efetiva", s_dd), "", ""],
        ["", Paragraph("Total do Lote", s_tot), "", Paragraph("100%", s_td_c)],
    ]

    tab_d = Table(desc_rows, colWidths=COL_D, rowHeights=[None, 11*mm, 11*mm, 11*mm, None])
    tab_d.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0),  (-1, 0),  GRAY_BG),
        ("BACKGROUND",    (0, -1), (-1, -1), GRAY_BG),
        ("GRID",          (0, 0),  (-1, -1), 0.5, GRAY_LIGHT),
        ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0),  (-1, 0),  4),
        ("BOTTOMPADDING", (0, 0),  (-1, 0),  4),
        ("LINEBELOW",     (2, 1),  (3, -2),  0.8, GRAY_DARK),
        ("LINEBELOW",     (2, -1), (2, -1),  0.8, GRAY_DARK),
    ]))
    story.append(tab_d)
    story.append(Spacer(1, 10))

    # -- Assinaturas --
    ass = Table([
        [Paragraph("Responsável pelo Turno", s_ass), "",
         Paragraph("Conferido por", s_ass)],
        ["", "", ""],
    ], colWidths=[W*0.42, W*0.16, W*0.42], rowHeights=[None, 10*mm])
    ass.setStyle(TableStyle([
        ("LINEBELOW", (0, 1), (0, 1), 0.8, GRAY_DARK),
        ("LINEBELOW", (2, 1), (2, 1), 0.8, GRAY_DARK),
        ("VALIGN",    (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(ass)
    story.append(Spacer(1, 6))

    # -- Rodapé --
    story.append(HRFlowable(width=W, thickness=0.5, color=GRAY_LIGHT, spaceBefore=4, spaceAfter=4))
    rodape = Table([[
        Paragraph("Powered by DAATEL • Sistema ERP Fábrica de Alho", s_rodape),
        Paragraph(f"Folha do Dia {data_ref.strftime('%d/%m/%Y')} | Pág 1", s_rodape_r),
    ]], colWidths=[W*0.6, W*0.4])
    rodape.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(rodape)

    doc.build(story)
    buf.seek(0)
    return buf.read()
