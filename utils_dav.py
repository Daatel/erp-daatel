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
               v.custo_frete_rateado, v.numero_documento, v.tipo_documento, v.pedido_grupo, v.observacoes,
               c.id as cliente_id, c.nome as cliente_nome, c.nome_fantasia as cliente_fantasia, 
               c.cnpj_cpf as cliente_cnpj, c.inscricao_estadual as cliente_ie, c.endereco as cliente_endereco, 
               c.bairro as cliente_bairro, c.cidade as cliente_cidade, c.uf as cliente_uf, 
               c.cep as cliente_cep, c.telefone as cliente_telefone, c.email as cliente_email, c.status,
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
    
    # Busca dados da Empresa Emitente
    df_emp = fetch_all("SELECT * FROM empresa_config LIMIT 1")
    emp_razao = "EMPORIO DO ALHO RJ LTDA - EMPORIO DO ALHO"
    emp_cnpj = "61.088.045/0001-54"
    emp_ie = "15550880"
    emp_endereco = "Alameda PRESIDENTE WILSON - QUADRA 4 LT 29, S/N - JARDIM ... Duque de Caxias - RJ"
    emp_fone = "(32) 98856 1305"
    if not df_emp.empty:
        r_emp = df_emp.iloc[0]
        if pd.notna(r_emp.get('razao_social')) and str(r_emp.get('razao_social')).strip():
            emp_razao = f"{r_emp.get('razao_social')} - {r_emp.get('nome_fantasia') or r_emp.get('razao_social')}"
        if pd.notna(r_emp.get('cnpj')) and str(r_emp.get('cnpj')).strip():
            emp_cnpj = str(r_emp.get('cnpj'))
        if pd.notna(r_emp.get('inscricao_estadual')) and str(r_emp.get('inscricao_estadual')).strip():
            emp_ie = str(r_emp.get('inscricao_estadual'))
        if pd.notna(r_emp.get('endereco_completo')) and str(r_emp.get('endereco_completo')).strip():
            emp_endereco = str(r_emp.get('endereco_completo'))
        if pd.notna(r_emp.get('telefone')) and str(r_emp.get('telefone')).strip():
            emp_fone = str(r_emp.get('telefone'))

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
    
    def _limpar_campo(val):
        if val is None or pd.isna(val):
            return ""
        v = str(val).strip(" ,")
        if v.lower() in ("none", "nan", "null", "0", ""):
            return ""
        return v

    def _montar_endereco(end_raw, bairro_raw, cidade_raw, uf_raw, cep_raw):
        end = _limpar_campo(end_raw)
        bairro = _limpar_campo(bairro_raw)
        cidade = _limpar_campo(cidade_raw)
        uf = _limpar_campo(uf_raw)
        cep = _limpar_campo(cep_raw)

        partes = []
        if end:
            partes.append(end)
        if bairro:
            partes.append(f"Bairro: {bairro}")
        if cidade or uf:
            cid_uf = f"{cidade} / {uf}".strip(" /")
            if cid_uf:
                partes.append(cid_uf)
        if cep:
            partes.append(f"CEP: {cep}")

        if partes:
            return " - ".join(partes)

        return "ENDEREÇO NÃO CADASTRADO (Atualizar no Cadastro do Cliente)"


    cli_id_val = row.get('cliente_id') if pd.notna(row.get('cliente_id')) else row.get('id')
    cli_nome_base = row['cliente_nome'] or ""
    cli_fantasia = row.get('cliente_fantasia') if pd.notna(row.get('cliente_fantasia')) else cli_nome_base
    cli_bairro = _limpar_campo(row.get('cliente_bairro'))
    cli_cidade = _limpar_campo(row.get('cliente_cidade'))
    cli_uf = _limpar_campo(row.get('cliente_uf') or (row.get('uf') if pd.notna(row.get('uf')) else ""))
    cli_cid_uf = f"{cli_cidade} / {cli_uf}".strip(" /") if (cli_cidade or cli_uf) else ""
    cli_cep = _limpar_campo(row.get('cliente_cep'))
    cli_end = _montar_endereco(row.get('cliente_endereco'), cli_bairro, cli_cidade, cli_uf, cli_cep)
    cli_ie = _limpar_campo(row.get('cliente_ie')) or "ISENTO"
    cli_tel = _limpar_campo(row.get('cliente_telefone'))
    cli_email = _limpar_campo(row.get('cliente_email'))

    venda_info = {
        'tipo_documento': row['tipo_documento'] or "",
        'dav_numero': str(row['numero_documento'] or "").zfill(10),
        'vendedor': row['vendedor_nome'] or "VENDEDOR PADRÃO",
        'data': data_str,
        'hora': hora_str,
        'validade': validade_str,
        'cliente_nome': f"{cli_id_val} - {cli_nome_base}",
        'cliente_fantasia': cli_fantasia,
        'solicitante': "COMPRADOR",
        'cliente_endereco': cli_end,
        'cliente_cep': cli_cep,
        'comercial': cli_tel, 'fax': "", 'residencial': "", 'email': cli_email,
        'cliente_cnpj': row['cliente_cnpj'] or "00.000.000/0000-00",
        'cliente_ie': cli_ie,
        'cliente_bairro': cli_bairro,
        'cliente_cidade_uf': cli_cid_uf,
        'celular': cli_tel,
        'emp_razao': emp_razao,
        'emp_cnpj': emp_cnpj,
        'emp_ie': emp_ie,
        'emp_endereco': emp_endereco,
        'emp_fone': emp_fone,
        'produtos': produtos,
        'total_qtd': f_b(total_qtd),
        'subtotal': f_b(subtotal),
        'desconto_total': '0,00',
        'frete': f_b(frete_total),
        'total': f_b(subtotal),
        'observacoes': row['observacoes'] or ""
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
                    <span class="bold">{info.get('emp_razao', 'EMPORIO DO ALHO RJ LTDA - EMPORIO DO ALHO')}</span><span style="float:right">Página 1/1</span><br>
                    CNPJ: {info.get('emp_cnpj', '61.088.045/0001-54')} - Insc. Estadual: {info.get('emp_ie', '15550880')}<br>
                    {info.get('emp_endereco', 'Alameda PRESIDENTE WILSON - QUADRA 4 LT 29, S/N - JARDIM ... Duque de Caxias - RJ')}
                </td>
                <td class="no-border br" style="vertical-align:bottom">Fone: {info.get('emp_fone', '(32) 98856 1305')}</td>
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
                    <span class="bold">Observações:</span> {info['observacoes']}
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
