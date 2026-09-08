"""
Serviço de Geração de DAV em PDF para o Conector por Voz ERP DAATEL.
Utiliza ReportLab para gerar o documento PDF do DAV pronto para envio no Telegram.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("VoicePDFService")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def gerar_pdf_dav(venda_info: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Gera o arquivo PDF do Documento Auxiliar de Venda (DAV) com os dados da venda.
    Retorna o caminho absoluto do arquivo PDF gerado.
    """
    num_doc = venda_info.get("numero_documento", f"DAV-{int(datetime.now().timestamp())}")
    if not output_path:
        os.makedirs("scratch", exist_ok=True)
        output_path = os.path.join("scratch", f"DAV_{num_doc}.pdf")

    if not REPORTLAB_AVAILABLE:
        # Fallback de emergência caso reportlab não esteja no ambiente
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"=== DAATEL EMPÓRIO DO ALHO - DAV #{num_doc} ===\n")
            f.write(f"Cliente: {venda_info.get('cliente_nome')}\n")
            f.write(f"Data: {venda_info.get('data', datetime.now().strftime('%Y-%m-%d'))}\n")
            f.write(f"Valor Total: R$ {venda_info.get('valor_total', 0.0):,.2f}\n")
            f.write("==================================================\n")
        return os.path.abspath(output_path)

    # Geração profissional do PDF com ReportLab
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#004d26'), # Verde DAATEL
        alignment=1 # Centralizado
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#333333'),
        alignment=1
    )

    normal_bold = ParagraphStyle(
        'NormalBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12
    )

    elements = []

    # Cabeçalho da Empresa
    elements.append(Paragraph("DAATEL - EMPÓRIO DO ALHO", title_style))
    elements.append(Paragraph("DOCUMENTO AUXILIAR DE VENDA - DAV", subtitle_style))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#004d26'), spaceAfter=10))

    # Dados do Cabeçalho do DAV
    data_emissao = venda_info.get("data", datetime.now().strftime("%d/%m/%Y"))
    cli_nome = venda_info.get("cliente_nome", "CONSUMIDOR")
    cond_pagto = venda_info.get("condicao_pagamento", "À VISTA")

    header_data = [
        [Paragraph(f"<b>Nº Documento:</b> {num_doc}", normal_style), Paragraph(f"<b>Data Emissão:</b> {data_emissao}", normal_style)],
        [Paragraph(f"<b>Cliente:</b> {cli_nome}", normal_style), Paragraph(f"<b>Condição Pagto:</b> {cond_pagto}", normal_style)],
        [Paragraph(f"<b>Tipo Emissão:</b> Venda Balcão Express (Voz)", normal_style), Paragraph(f"<b>Status:</b> FATURADO", normal_style)]
    ]

    t_header = Table(header_data, colWidths=[9 * cm, 9 * cm])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f7f6')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 0.5 * cm))

    # Tabela de Itens
    elements.append(Paragraph("<b>ITENS DO PEDIDO / VENDA</b>", normal_bold))
    elements.append(Spacer(1, 0.2 * cm))

    items_table_data = [
        [Paragraph("<b>Item / Produto</b>", normal_bold), 
         Paragraph("<b>Qtd</b>", normal_bold), 
         Paragraph("<b>Preço Un. (R$)</b>", normal_bold), 
         Paragraph("<b>Total (R$)</b>", normal_bold)]
    ]

    itens = venda_info.get("itens", [])
    if not itens:
        items_table_data.append([
            Paragraph("Venda Balcão Diversos", normal_style),
            Paragraph("1.0", normal_style),
            Paragraph(f"R$ {venda_info.get('valor_total', 0.0):,.2f}", normal_style),
            Paragraph(f"R$ {venda_info.get('valor_total', 0.0):,.2f}", normal_style)
        ])
    else:
        for it in itens:
            items_table_data.append([
                Paragraph(str(it.get("produto_nome", "Produto")), normal_style),
                Paragraph(f"{it.get('quantidade', 1.0):,.1f}", normal_style),
                Paragraph(f"R$ {it.get('preco_unitario', 0.0):,.2f}", normal_style),
                Paragraph(f"R$ {it.get('valor_item', 0.0):,.2f}", normal_style)
            ])

    t_items = Table(items_table_data, colWidths=[9 * cm, 2.5 * cm, 3.5 * cm, 3 * cm])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6eee9')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 0.5 * cm))

    # Totalizador
    valor_total = venda_info.get("valor_total", 0.0)
    total_data = [
        [Paragraph("<b>VALOR TOTAL DO DAV:</b>", ParagraphStyle('RightBold', parent=normal_bold, alignment=2)),
         Paragraph(f"<b>R$ {valor_total:,.2f}</b>", ParagraphStyle('RightTotal', parent=title_style, fontSize=12, alignment=2))]
    ]
    t_total = Table(total_data, colWidths=[12 * cm, 6 * cm])
    t_total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e6eee9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#004d26')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_total)
    elements.append(Spacer(1, 1 * cm))

    # Rodapé
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=6))
    elements.append(Paragraph("<i>Powered by Daatel | Wisdom into Technology</i>", ParagraphStyle('Footer', parent=subtitle_style, fontSize=8, textColor=colors.gray)))

    doc.build(elements)
    return os.path.abspath(output_path)
