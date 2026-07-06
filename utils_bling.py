import os
import json
import base64
import requests

CREDENTIALS_PATH = os.path.join("c:\\Users\\MARCIO\\Gestao_Fabrica_Alho", "bling_credentials.json")

def load_bling_credentials():
    """Carrega as credenciais do Bling salvas localmente."""
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError("Arquivo de credenciais 'bling_credentials.json' nao encontrado. Realize a autorizacao primeiro.")
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_bling_credentials(creds):
    """Salva as credenciais do Bling localmente."""
    with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=4, ensure_ascii=False)

def refresh_bling_token():
    """Renova o access_token usando o refresh_token."""
    creds = load_bling_credentials()
    client_id = creds.get("client_id")
    client_secret = creds.get("client_secret")
    refresh_token_val = creds.get("refresh_token")
    
    if not client_id or not client_secret or not refresh_token_val:
        raise ValueError("Credenciais incompletas no arquivo bling_credentials.json.")

    credentials_encoded = f"{client_id}:{client_secret}".encode("utf-8")
    auth_header = base64.b64encode(credentials_encoded).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_val
    }
    
    response = requests.post("https://api.bling.com.br/Api/v3/oauth/token", data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        creds["access_token"] = token_data.get("access_token")
        creds["refresh_token"] = token_data.get("refresh_token")
        creds["expires_in"] = token_data.get("expires_in")
        save_bling_credentials(creds)
        return creds["access_token"]
    else:
        raise Exception(f"Erro ao renovar token no Bling (Status {response.status_code}): {response.text}")

def bling_api_request(method, endpoint, json_data=None):
    """Executa uma requisicao para a API do Bling com renovacao automatica de token (OAuth 2.0)."""
    creds = load_bling_credentials()
    url = f"https://api.bling.com.br/Api/v3/{endpoint.lstrip('/')}"
    
    headers = {
        "Authorization": f"Bearer {creds['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 1. Tenta a requisicao principal
    if method.upper() == "POST":
        response = requests.post(url, json=json_data, headers=headers)
    else:
        response = requests.get(url, headers=headers)
        
    # 2. Se receber 401 (Nao Autorizado/Token Expirado), tenta renovar o token e repetir a chamada
    if response.status_code == 401:
        try:
            print("Token expirado detectado. Tentando renovar...")
            new_token = refresh_bling_token()
            headers["Authorization"] = f"Bearer {new_token}"
            
            if method.upper() == "POST":
                response = requests.post(url, json=json_data, headers=headers)
            else:
                response = requests.get(url, headers=headers)
        except Exception as e:
            raise Exception(f"Falha de autenticacao e renovacao de token no Bling: {e}")
            
    return response

def format_cnpj_cpf(doc):
    """Remove pontuacao do CNPJ/CPF."""
    if not doc:
        return ""
    return "".join(ch for ch in str(doc) if ch.isdigit())

def enviar_faturamento_ao_bling(venda_id_ref, cliente_id, itens_list, lote, validade, parcelas, obs_extras=""):
    """Envia o pedido de faturamento para o Bling v3 como Pedido de Venda."""
    from database import fetch_all
    
    # Busca dados completos do cliente no DB
    df_cli = fetch_all("SELECT nome, cnpj_cpf, uf FROM clientes WHERE id = ?", (cliente_id,))
    if df_cli.empty:
        raise ValueError(f"Cliente ID {cliente_id} nao encontrado no banco de dados.")
    cli_data = df_cli.iloc[0]
    
    # Prepara o documento do cliente
    doc_limpo = format_cnpj_cpf(cli_data['cnpj_cpf'])
    tipo_pessoa = "J" if len(doc_limpo) == 14 else "F"
    
    # Formata as parcelas (installments)
    bling_parcelas = []
    for idx, p in enumerate(parcelas):
        venc_val = p.get('Vencimento')
        venc_str = venc_val.strftime("%Y-%m-%d") if hasattr(venc_val, 'strftime') else str(venc_val)
        bling_parcelas.append({
            "data": venc_str,
            "valor": round(float(p.get('Valor (R$)', 0.0)), 2)
        })
        
    bling_itens = []
    for item in itens_list:
        produto_id = item['produto_id']
        df_prod = fetch_all("SELECT nome, preco_venda_base, unidade_medida FROM produtos WHERE id = ?", (produto_id,))
        if df_prod.empty:
            raise ValueError(f"Produto ID {produto_id} nao encontrado no banco de dados.")
        prod_data = df_prod.iloc[0]
        
        unidade = str(prod_data['unidade_medida']).strip().upper()[:4]
        if not unidade or unidade == "NONE":
            unidade = "UN"
            
        bling_itens.append({
            "codigo": f"PROD-{produto_id}",
            "descricao": str(prod_data['nome'])[:120],
            "quantidade": float(item['quantidade']),
            "valor": float(item['valor_unitario']),
            "unidade": unidade
        })
        
    # Monta a estrutura do pedido de venda
    # Usaremos venda_id_ref (que pode ser o ID do grupo) apenas para a observação e controle interno, o Bling vai gerar o ID dele.
    
    payload = {
        "contato": {
            "nome": str(cli_data['nome'])[:120],
            "numeroDocumento": doc_limpo,
            "tipoPessoa": tipo_pessoa
        },
        "itens": bling_itens,
        "parcelas": bling_parcelas,
        "observacoes": (f"Lote: {lote} | Validade: {validade} | Ref: {venda_id_ref}" + (f" | {obs_extras}" if obs_extras else ""))
    }
    
    # Envia para a API do Bling v3
    response = bling_api_request("POST", "/pedidos/vendas", json_data=payload)
    
    if response.status_code in (200, 201):
        resp_data = response.json()
        bling_pedido_id = resp_data.get("data", {}).get("id")
        if bling_pedido_id:
            return bling_pedido_id
        else:
            raise Exception(f"Pedido enviado mas ID nao retornado pelo Bling: {response.text}")
    else:
        raise Exception(f"Erro ao cadastrar pedido no Bling (Status {response.status_code}): {response.text}")

def sincronizar_nfe_do_bling(bling_pedido_id):
    """Consulta o status do pedido no Bling e retorna o numero da NF-e caso emitida."""
    response = bling_api_request("GET", f"/pedidos/vendas/{bling_pedido_id}")
    
    if response.status_code == 200:
        resp_data = response.json()
        pedido_data = resp_data.get("data", {})
        
        # Verifica se o campo 'notaFiscal' esta preenchido e possui o numero
        nf_data = pedido_data.get("notaFiscal")
        if nf_data and nf_data.get("numero"):
            return str(nf_data["numero"]).strip()
        return None
    else:
        raise Exception(f"Erro ao consultar pedido no Bling (Status {response.status_code}): {response.text}")
