import pandas as pd
from datetime import datetime, timedelta
from database import fetch_all

def f_b(val):
    if pd.isna(val): return "0,00"
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def buscar_dados_venda(venda_id):
    # Primeiro busca a venda base para saber o numero_documento
    df_base = fetch_all("SELECT numero_documento, pedido_grupo FROM vendas WHERE id = ?", (venda_id,))
    if df_base.empty: return None
    
    num_doc = df_base.iloc[0]['numero_documento']
    ped_grp = df_base.iloc[0]['pedido_grupo']
    
    # Se tiver pedido_grupo, busca todos os itens desse grupo
    if ped_grp:
        query_where = "v.pedido_grupo = ?"
        param = ped_grp
    elif num_doc:
        query_where = "v.numero_documento = ?"
        param = num_doc
    else:
        query_where = "v.id = ?"
        param = venda_id

    df_venda = fetch_all(f"""
        SELECT v.id, v.data, v.quantidade, v.valor_unitario, v.valor_total, 
               v.custo_frete_rateado, v.numero_documento, v.tipo_documento, v.pedido_grupo,
               c.nome as cliente_nome, c.cnpj_cpf as cliente_cnpj, c.uf as uf, c.status,
               p.nome as produto_nome, p.id as p_id,
               f.nome as vendedor_nome
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN produtos p ON v.produto_id = p.id
        LEFT JOIN funcionarios f ON v.vendedor_id = f.id
        WHERE {query_where}
    """, (param,))
    
    if df_venda.empty:
        return None
        
    row = df_venda.iloc[0] # Pega dados do cabeçalho do primeiro item
    
    # Conversão de data/hora
    dt_obj = pd.to_datetime(row['data'], errors='coerce')
    data_str = dt_obj.strftime('%d/%m/%Y') if pd.notna(dt_obj) else ""
    hora_str = dt_obj.strftime('%H:%M:%S') if pd.notna(dt_obj) else "00:00:00"
    validade_str = (dt_obj + timedelta(days=30)).strftime('%d/%m/%Y') if pd.notna(dt_obj) else ""
    
    produtos = []
    total_qtd = 0.0
    subtotal = 0.0
    frete_total = 0.0
    
    for _, item in df_venda.iterrows():
        produtos.append({
            'cod': str(item['p_id']).zfill(3), 
            'cod_barras': str(item['p_id']), 
            'desc': item['produto_nome'], 
            'qtd': f_b(item['quantidade']), 
            'med': 'KG', 
            'unit': f_b(item['valor_unitario']), 
            'desc_valor': '0,00', 
            'total': f_b(item['valor_total'])
        })
        total_qtd += float(item['quantidade'] or 0)
        subtotal += float(item['valor_total'] or 0)
        frete_total += float(item['custo_frete_rateado'] or 0)
    
    venda_info = {
        'tipo_documento': row['tipo_documento'] or "",
        'dav_numero': str(row['numero_documento'] or "").zfill(10),
        'vendedor': row['vendedor_nome'] or "VENDEDOR PADRÃO",
        'data': data_str,
        'hora': hora_str,
        'validade': validade_str,
        'cliente_nome': f"{row['id']} - {row['cliente_nome']}",
        'cliente_fantasia': row['cliente_nome'],
        'solicitante': "COMPRADOR",
        'cliente_endereco': "ENDEREÇO DO CLIENTE, S/N",
        'cliente_cep': "00000-000",
        'comercial': "", 'fax': "", 'residencial': "", 'email': "",
        'cliente_cnpj': row['cliente_cnpj'] or "00.000.000/0000-00",
        'cliente_ie': "ISENTO",
        'cliente_bairro': "CENTRO",
        'cliente_cidade_uf': f"CIDADE / {row['uf']}",
        'celular': "",
        'produtos': produtos,
        'total_qtd': f_b(total_qtd),
        'subtotal': f_b(subtotal),
        'desconto_total': '0,00',
        'frete': f_b(frete_total),
        'total': f_b(subtotal)
    }
    return venda_info
def gerar_html_dav(info):
    linhas_prod = ""
    for p in info['produtos']:
        linhas_prod += f'''
        <tr>
            <td class="no-border">{p['cod']}</td>
            <td class="no-border center">{p['cod_barras']}</td>
            <td class="no-border">{p['desc']}</td>
            <td class="no-border right">{p['qtd']}</td>
            <td class="no-border center">{p['med']}</td>
            <td class="no-border right">{p['unit']}</td>
            <td class="no-border right">{p['desc_valor']}</td>
            <td class="no-border right">{p['total']}</td>
        </tr>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Arial', sans-serif; font-size: 11px; margin: 0; padding: 0; background: #555; }}
        .page {{ width: 21cm; min-height: 29.7cm; padding: 1cm; margin: 20px auto; background: white; box-sizing: border-box; box-shadow: 0 0 5px rgba(0,0,0,0.5); }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 5px; }}
        th, td {{ border: 1px solid #000; padding: 3px 5px; text-align: left; vertical-align: top; }}
        .center {{ text-align: center; }}
        .right {{ text-align: right; }}
        .bold {{ font-weight: bold; }}
        .header-title {{ font-size: 14px; text-align: center; font-weight: bold; }}
        .header-sub {{ font-size: 11px; text-align: center; font-weight: bold; margin-bottom: 5px; }}
        .no-border {{ border: none !important; }}
        .bt {{ border-top: 1px solid #000 !important; }}
        .bb {{ border-bottom: 1px solid #000 !important; }}
        .bl {{ border-left: 1px solid #000 !important; }}
        .br {{ border-right: 1px solid #000 !important; }}
        @media print {{
            body {{ margin: 0; padding: 0; background: white; }}
            .page {{ width: 100%; padding: 0; margin: 0; border: none; box-shadow: none; min-height: auto; page-break-after: avoid;}}
            #print-btn {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div style="text-align:center;">
        <button id="print-btn" onclick="window.print()" style="padding:10px 20px;font-size:16px;margin:20px;cursor:pointer;background:#292d77;color:white;border:none;border-radius:5px;box-shadow:0 2px 4px rgba(0,0,0,0.2);">🖨️ Imprimir DAV no Formato A4</button>
    </div>
    <div class="page">
        <!-- CABEÇALHO 1 -->
        <table>
            <tr>
                <td class="center no-border bb">
                    <div class="header-title">DOCUMENTO AUXILIAR DE VENDA - PEDIDO DE VENDA</div>
                    <div class="header-sub">NÃO É DOCUMENTO FISCAL - NÃO É VÁLIDO COMO RECIBO E COMO<br>GARANTIA DE MERCADORIA - NÃO COMPROVA PAGAMENTO</div>
                </td>
            </tr>
        </table>
        
        <!-- CABEÇALHO EMPRESA -->
        <table>
            <tr>
                <td class="no-border bl br" colspan="2">
                    <span class="bold">EMPORIO DO ALHO RJ LTDA - EMPORIO DO ALHO</span><span style="float:right">Página 1/1</span><br>
                    CNPJ: 61.088.045/0001-54 - Insc. Estadual: 15550880<br>
                    Alameda PRESIDENTE WILSON - QUADRA 4 LT 29, S/N - JARDIM ... Duque de Caxias - RJ
                </td>
                <td class="no-border br" style="vertical-align:bottom">Fone: (32) 98856 1305</td>
            </tr>
        </table>
        
        <!-- DADOS DAV -->
        <table class="bt bb bl br">
            <tr>
                <td class="no-border bl" style="width:50%">
                    <span class="bold">N. do Documento Fiscal:</span> 000000<br>
                    <span class="bold">Vendedor:</span> {info['vendedor']}<br>
                    <span class="bold">Validade:</span> {info['validade']}
                </td>
                <td class="no-border br right" style="width:50%">
                    <span class="bold">DAV:</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span class="bold">{info['dav_numero']}</span><br><br>
                    <span class="bold">Data:</span> {info['data']} &nbsp;&nbsp; <span class="bold">Hora:</span> {info['hora']}
                </td>
            </tr>
        </table>
        
        <!-- IDENTIFICAÇÃO DO SOLICITANTE -->
        <table>
            <tr><td class="bold no-border bl br bb" colspan="2">Identificação do Solicitante</td></tr>
            <tr>
                <td class="no-border bl" style="width:65%">
                    <span class="bold">Cliente:</span> {info['cliente_nome']}<br>
                    <span class="bold">Fantasia:</span> {info['cliente_fantasia']}<br>
                    <span class="bold">Solicitante:</span> {info['solicitante']}<br>
                    <span class="bold">Endereço:</span> {info['cliente_endereco']}<br>
                    <span class="bold">CEP:</span> {info['cliente_cep']}<br>
                    <span class="bold">Comercial:</span> {info['comercial']} &nbsp;&nbsp;&nbsp; <span class="bold">Fax:</span> {info['fax']}<br>
                    <span class="bold">Residencial:</span> {info['residencial']} &nbsp;&nbsp;&nbsp; <span class="bold">E-mail:</span> {info['email']}
                </td>
                <td class="no-border br" style="width:35%">
                    <span class="bold">CPF/CNPJ:</span> {info['cliente_cnpj']}<br>
                    <span class="bold">RG/IE:</span> {info['cliente_ie']}<br>
                    <span class="bold">IM:</span> <br>
                    <span class="bold">Bairro:</span> {info['cliente_bairro']}<br>
                    <span class="bold">Cidade/UF:</span> {info['cliente_cidade_uf']}<br>
                    <span class="bold">Celular/0800:</span> {info['celular']}
                </td>
            </tr>
        </table>
        
        <!-- PRODUTOS -->
        <table class="bt bb bl br">
            <tr>
                <td class="bold no-border bl br bb" colspan="8">Relação de Produtos/Serviços</td>
            </tr>
            <tr class="bb">
                <th class="no-border left">Código</th>
                <th class="no-border center">Cód. Barras</th>
                <th class="no-border left">Descrição</th>
                <th class="no-border right">Qtd</th>
                <th class="no-border center">Med</th>
                <th class="no-border right">Unitário</th>
                <th class="no-border right">Desconto</th>
                <th class="no-border right">Total</th>
            </tr>
            {linhas_prod}
        </table>
        
        <!-- TOTAIS E OBSERVACOES -->
        <table>
            <tr>
                <td class="no-border bl bt bb" style="width:65%">
                    <span class="bold">Transportadora:</span><br>
                    <span class="bold">Quantidade:</span> 0,00 &nbsp;&nbsp;&nbsp; <span class="bold">Peso Bruto:</span> 0,0000 &nbsp;&nbsp;&nbsp; <span class="bold">Peso Líquido:</span> 0,0000<br>
                    <span class="bold">Qtd Total de Itens:</span> {info['total_qtd']}<br><br>
                    <span class="bold">Pagamento:</span> Nenhum<br><br>
                    <span class="bold">Observações:</span>
                </td>
                <td class="no-border br bt bb" style="width:35%">
                    <table>
                        <tr><td class="no-border bold">SubTotal:</td><td class="no-border right bold">{info['subtotal']}</td></tr>
                        <tr><td class="no-border bold">Desconto:</td><td class="no-border right bold">{info['desconto_total']}</td></tr>
                        <tr><td class="no-border bold">Frete:</td><td class="no-border right bold">{info['frete']}</td></tr>
                        <tr><td class="no-border bold">Total:</td><td class="no-border right bold">{info['total']}</td></tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- ASSINATURAS -->
        <div style="margin-top: 80px; text-align: center;">
            <table class="no-border">
                <tr>
                    <td class="no-border center" style="width:30%"><div class="bt" style="margin: 0 auto; width:80%; padding-top:5px;">Data</div></td>
                    <td class="no-border center" style="width:70%"><div class="bt" style="margin: 0 auto; width:80%; padding-top:5px;">Assinatura do Solicitante</div></td>
                </tr>
            </table>
        </div>
        
    </div>
</body>
</html>'''
    return html
