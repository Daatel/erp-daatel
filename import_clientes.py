import pandas as pd
from database import get_connection

url = 'https://docs.google.com/spreadsheets/d/1RSZOeXyvya4lQoixdeq1UWj_LicsUmWdW2IlwJfK6eA/export?format=csv'
print("Fazendo download da planilha de clientes...")
df = pd.read_csv(url)
df.columns = [str(c).strip() for c in df.columns]

conn = get_connection()
cursor = conn.cursor()

cursor.execute("DELETE FROM clientes")

# 1. Register representatives safely
reps = df['Representante'].dropna().unique()
for rep in reps:
    r_name = str(rep).strip()
    if r_name and r_name != "nan":
        cursor.execute("SELECT id FROM funcionarios WHERE nome=?", (r_name,))
        if not cursor.fetchone():
            print(f"Cadastrando Representante Autônomo: {r_name}")
            cursor.execute("""
                INSERT INTO funcionarios (nome, cargo, salario_base, regime_contratacao) 
                VALUES (?, ?, ?, ?)
            """, (r_name, 'Representante Comercial', 0.0, 'PJ/Autônomo'))
conn.commit()

# 2. Extract map of Reps to ID
cursor.execute("SELECT id, nome FROM funcionarios")
rep_map = {row[1]: row[0] for row in cursor.fetchall()}

count = 0
for idx, row in df.iterrows():
    razao = str(row.get('Razão Social', '')).strip()
    if not razao or razao == "nan":
        continue
        
    def val(k):
        v = str(row.get(k, '')).strip()
        return "" if v == "nan" else v

    nome_fantasia = val('Nome Fantasia')
    cnpj_cpf = val('CNPJ/CPF')
    
    cursor.execute("SELECT id FROM clientes WHERE cnpj_cpf=?", (cnpj_cpf,))
    if cursor.fetchone():
        print(f"Ignorando cliente CNPJ {cnpj_cpf}, já existe.")
        continue
        
    insc_estadual = val('Inscrição Estadual')
    endereco = val('Endereço')
    bairro = val('Bairro')
    cep = val('CEP')
    cidade = val('Cidade')
    uf = val('UF')
    telefone = val('Telefone')
    email = val('E-mail')
    observacoes = val('Observações')
    status = val('Status')
    rede_clientes = val('Rede de Clientes')
    grupo_lojas = val('Grupo de Lojas')
    prazo_pagamento = val('PRAZO DE PAGAMENTO')
    
    rep_nome = val('Representante')
    rep_id = rep_map.get(rep_nome, None)
    
    query = """INSERT INTO clientes 
               (nome, telefone, endereco, nome_fantasia, cnpj_cpf, inscricao_estadual, 
                bairro, cep, cidade, uf, email, observacoes, status, rede_clientes, 
                grupo_lojas, prazo_pagamento, representante_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
               
    cursor.execute(query, (
        razao, telefone, endereco, nome_fantasia, cnpj_cpf, insc_estadual,
        bairro, cep, cidade, uf, email, observacoes, status, rede_clientes,
        grupo_lojas, prazo_pagamento, rep_id
    ))
    count += 1

conn.commit()
conn.close()
print(f"Sucesso! {count} clientes importados corretamente.")
