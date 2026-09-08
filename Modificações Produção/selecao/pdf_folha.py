# components/selecao/pdf_folha.py
# Geração do PDF da Folha Diária de Seleção
# Retorna bytes para uso com st.download_button

import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

# --------------------------------------------------------------------------
# Paleta (mesma do design)
# --------------------------------------------------------------------------
GRAY_DARK  = colors.HexColor("#2C2C2A")
GRAY_MID   = colors.HexColor("#888780")
GRAY_LIGHT = colors.HexColor("#D3D1C7")
GRAY_BG    = colors.HexColor("#F1EFE8")
WHITE      = colors.white

# --------------------------------------------------------------------------
# Estilos
# --------------------------------------------------------------------------
s_title   = ParagraphStyle("title",  fontName="Helvetica-Bold", fontSize=14, textColor=GRAY_DARK)
s_sub     = ParagraphStyle("sub",    fontName="Helvetica",      fontSize=9,  textColor=GRAY_MID)
s_meta_r  = ParagraphStyle("metar",  fontName="Helvetica",      fontSize=9,  textColor=GRAY_DARK, alignment=TA_RIGHT)
s_section = ParagraphStyle("sec",    fontName="Helvetica-Bold", fontSize=7,  textColor=GRAY_MID,  spaceAfter=3)
s_rodape  = ParagraphStyle("rod",    fontName="Helvetica",      fontSize=7,  textColor=GRAY_MID)
s_rodape_r= ParagraphStyle("rodr",   fontName="Helvetica",      fontSize=7,  textColor=GRAY_MID,  alignment=TA_RIGHT)
s_obs     = ParagraphStyle("obs",    fontName="Helvetica",      fontSize=7,  textColor=GRAY_MID,  alignment=TA_RIGHT)
s_th      = ParagraphStyle("th",     fontName="Helvetica-Bold", fontSize=7,  textColor=GRAY_MID)
s_td      = ParagraphStyle("td",     fontName="Helvetica",      fontSize=9,  textColor=GRAY_DARK)
s_td_c    = ParagraphStyle("tdc",    fontName="Helvetica",      fontSize=9,  textColor=GRAY_MID, alignment=TA_CENTER)
s_tot     = ParagraphStyle("tot",    fontName="Helvetica-Bold", fontSize=9,  textColor=GRAY_DARK, alignment=TA_RIGHT)
s_tot2    = ParagraphStyle("tot2",   fontName="Helvetica-Bold", fontSize=9,  textColor=GRAY_MID, alignment=TA_CENTER)
s_ass     = ParagraphStyle("ass",    fontName="Helvetica",      fontSize=8,  textColor=GRAY_MID)


def gerar_pdf_folha(data_ref: date, presentes: list) -> bytes:
    """
    Gera a folha diária de seleção em PDF.

    Args:
        data_ref: Data do dia
        presentes: Lista de dicts com keys: nome, meta_kg_dia

    Returns:
        bytes do PDF gerado
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
            Paragraph(f"Data: {data_str}<br/>Responsável: ______________________", s_meta_r),
        ]
    ], colWidths=[W * 0.6, W * 0.4])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header)
    story.append(Paragraph("Folha diária de seleção", s_sub))
    story.append(HRFlowable(width=W, thickness=1.5, color=GRAY_DARK, spaceAfter=6))

    # -- Resumo do dia --
    n_presentes  = len(presentes)
    cap_total    = sum(p["meta_kg_dia"] for p in presentes)

    resumo = Table([
        ["Presentes hoje", "Capacidade do dia", "Meta da casa"],
        [f"{n_presentes} selecionadoras", f"{cap_total:,.0f} kg", "500 kg"],
    ], colWidths=[W / 3] * 3)
    resumo.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), GRAY_BG),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, 0), 7),
        ("TEXTCOLOR",     (0, 0), (-1, 0), GRAY_MID),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 13),
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
    story.append(Paragraph("PESAGEM INDIVIDUAL", s_section))

    COL_P = [W*0.05, W*0.30, W*0.10, W*0.18, W*0.18, W*0.19]
    linha_peso = lambda: "________________________"

    header_row = [
        Paragraph("#",          s_th),
        Paragraph("Nome",       s_th),
        Paragraph("Meta (kg)",  s_th),
        Paragraph("Pesagem 1",  s_th),
        Paragraph("Pesagem 2",  s_th),
        Paragraph("Total (kg)", s_th),
    ]

    rows = [header_row]
    meta_total = 0
    for i, p in enumerate(presentes, start=1):
        meta_total += p["meta_kg_dia"]
        rows.append([
            Paragraph(str(i), s_td_c),
            Paragraph(p["nome"], s_td),
            Paragraph(f"{p['meta_kg_dia']:.0f}", s_td_c),
            "", "", ""
        ])
    rows.append([
        "",
        Paragraph("Total", s_tot),
        Paragraph(f"{meta_total:,.0f}", s_tot2),
        "", "", ""
    ])

    tab_p = Table(
        rows,
        colWidths=COL_P,
        rowHeights=[None] + [14*mm] * len(presentes) + [None],
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
    story.append(Paragraph("DESCARTE X 2A LINHA — LOTE DO DIA", s_section))
    story.append(Paragraph("Preencher ao final do turno", s_obs))

    COL_D = [W*0.20, W*0.46, W*0.17, W*0.17]
    s_bold = ParagraphStyle("b", fontName="Helvetica-Bold", fontSize=9, textColor=GRAY_DARK)
    s_dd   = ParagraphStyle("dd", fontName="Helvetica", fontSize=8, textColor=GRAY_MID)

    desc_rows = [
        [Paragraph("Classificacao", s_th), Paragraph("Descricao", s_th),
         Paragraph("Peso (kg)", s_th), Paragraph("% do lote", s_th)],
        [Paragraph("Alho Nobre", s_bold),
         Paragraph("Dentes integros — sacos para consumo", s_dd), "", ""],
        [Paragraph("2a Linha", s_bold),
         Paragraph("Bombona — venda para industria de temperos", s_dd), "", ""],
        [Paragraph("Descarte", s_bold),
         Paragraph("Lixo — material improprio para consumo", s_dd), "", ""],
        ["", Paragraph("Total do lote", s_tot), "", Paragraph("100%", s_td_c)],
    ]

    tab_d = Table(desc_rows, colWidths=COL_D, rowHeights=[None, 13*mm, 13*mm, 13*mm, None])
    tab_d.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0),  (-1, 0),  GRAY_BG),
        ("BACKGROUND",    (0, -1), (-1, -1), GRAY_BG),
        ("GRID",          (0, 0),  (-1, -1), 0.5, GRAY_LIGHT),
        ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0),  (-1, 0),  4),
        ("BOTTOMPADDING", (0, 0),  (-1, 0),  4),
        ("TOPPADDING",    (0, 1),  (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1),  (-1, -1), 3),
        ("LINEBELOW",     (2, 1),  (3, -2),  0.8, GRAY_DARK),
        ("LINEBELOW",     (2, -1), (2, -1),  0.8, GRAY_DARK),
    ]))
    story.append(tab_d)
    story.append(Spacer(1, 10))

    # -- Assinaturas --
    ass = Table([
        [Paragraph("Responsavel pelo turno", s_ass), "",
         Paragraph("Conferido por", s_ass)],
        ["", "", ""],
    ], colWidths=[W*0.42, W*0.16, W*0.42], rowHeights=[None, 12*mm])
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
        Paragraph("ERP do Alho — gerado automaticamente", s_rodape),
        Paragraph(f"Folha do dia {data_ref.strftime('%d/%m/%Y')} / Pagina 1", s_rodape_r),
    ]], colWidths=[W*0.6, W*0.4])
    rodape.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(rodape)

    doc.build(story)
    buf.seek(0)
    return buf.read()
