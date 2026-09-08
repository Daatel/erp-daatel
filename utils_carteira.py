from datetime import date
import pandas as pd

def gerar_html_carteira(cliente_nome, dados_faturas, total_faturas, data_pagamento_estimada):
    """
    Gera o HTML para impressão do Relatório de Fechamento de Carteira (Fiado).
    dados_faturas deve ser uma lista de dicts contendo: 'id', 'venda_id', 'descricao', 'valor', 'data_vencimento'
    """
    
    # Montando as linhas da tabela de faturas
    linhas_html = ""
    for idx, fat in enumerate(dados_faturas):
        bg_color = "#ffffff" if idx % 2 == 0 else "#f9f9f9"
        linhas_html += f"""
        <tr style="background-color: {bg_color}; text-align: center;">
            <td style="padding: 10px; border: 1px solid #ddd;">{fat.get('id', '')}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{fat.get('descricao', '')}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{fat.get('data_vencimento_original', '')}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">R$ {float(fat.get('valor', 0)):,.2f}</td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
            body {{
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: white;
                color: #111827;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #111827;
                padding-bottom: 20px;
                margin-bottom: 20px;
            }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }}
            .header p {{ margin: 5px 0 0 0; font-size: 14px; color: #4B5563; }}
            
            .info-block {{
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #F9FAFB;
            }}
            .info-block h2 {{
                margin: 0 0 10px 0; font-size: 18px; color: #111827; border-bottom: 1px solid #E5E7EB; padding-bottom: 5px;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
                font-size: 15px;
            }}
            .info-row span.label {{ font-weight: 600; color: #374151; }}
            .info-row span.value {{ font-weight: 400; color: #111827; }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            th {{
                background-color: #111827;
                color: white;
                padding: 12px 10px;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.5px;
                border: 1px solid #111827;
            }}
            
            .total-box {{
                float: right;
                border: 3px solid #111827;
                padding: 15px 25px;
                border-radius: 8px;
                text-align: right;
                background-color: #F3F4F6;
                width: 300px;
            }}
            .total-box .total-label {{ font-size: 16px; font-weight: 600; color: #4B5563; margin-bottom: 5px; }}
            .total-box .total-value {{ font-size: 26px; font-weight: 800; color: #111827; }}
            
            .footer-notes {{
                clear: both;
                margin-top: 50px;
                text-align: center;
                font-size: 12px;
                color: #6B7280;
                border-top: 1px solid #E5E7EB;
                padding-top: 20px;
            }}
            
            .print-btn {{
                display: block;
                width: 100%;
                padding: 15px;
                background-color: #2563EB;
                color: white;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                margin-bottom: 20px;
                cursor: pointer;
                border: none;
            }}
            
            @media print {{
                .print-btn {{ display: none !important; }}
                body {{ padding: 0; margin: 0; }}
            }}
        </style>
    </head>
    <body>
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir Extrato de Fechamento (A4)</button>
        
        <div class="header">
            <h1>EMPÓRIO DO ALHO</h1>
            <p>RELATÓRIO DE FECHAMENTO DE CARTEIRA (CONSOLIDADO)</p>
        </div>
        
        <div class="info-block">
            <h2>Dados do Acerto</h2>
            <div class="info-row">
                <span class="label">Cliente / Razão Social:</span>
                <span class="value">{cliente_nome}</span>
            </div>
            <div class="info-row">
                <span class="label">Data de Emissão do Relatório:</span>
                <span class="value">{date.today().strftime('%d/%m/%Y')}</span>
            </div>
            <div class="info-row">
                <span class="label">Data de Acerto/Vencimento Previsto:</span>
                <span class="value" style="color: #DC2626; font-weight: bold;">{data_pagamento_estimada}</span>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Ref. Financeira</th>
                    <th>Descrição do Faturamento (DAV/NF)</th>
                    <th>Data Faturamento</th>
                    <th>Valor (R$)</th>
                </tr>
            </thead>
            <tbody>
                {linhas_html}
            </tbody>
        </table>
        
        <div class="total-box">
            <div class="total-label">VALOR TOTAL DO ACERTO:</div>
            <div class="total-value">R$ {float(total_faturas):,.2f}</div>
        </div>
        
        <div class="footer-notes">
            <p>Este documento é um agrupamento analítico de faturas pendentes emitidas anteriormente. O pagamento deste montante quitará todos os títulos listados acima.</p>
            <p>Empório do Alho - Relatório de Governança Financeira Gerado por IA</p>
        </div>
    </body>
    </html>
    """
    return html
