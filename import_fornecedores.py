import pandas as pd
from database import get_connection

url = 'https://docs.google.com/spreadsheets/d/17I9qmnme5pcR_yE590FTold9YyBo2qc-wZ7h71dXlec/export?format=csv'
print("Fazendo download da planilha de Fornecedores...")
df = pd.read_csv(url)
df.columns = [str(c).strip() for c in df.columns]

conn = get_connection()
cursor = conn.cursor()

# Opcional: deletar todos os dados e inserir frestos. Como estamos no inicio, a migração faz sentido.
# cursor.execute("DELETE FROM fornecedores") 
# Faremos validação por CNPJ/CPF.

count = 0
for idx, row in df.iterrows():
    razao = str(row.get('Razão Social', '')).strip()
    if not razao or razao == "nan":
        continue
        
    def val(k):
        v = str(row.get(k, '')).strip()
        return "" if v == "nan" else v

    cnpj_cpf = val('CNPJ/CPF')
    
    cursor.execute("SELECT id FROM fornecedores WHERE cnpj_cpf=?", (cnpj_cpf,))
    if cursor.fetchone() and cnpj_cpf:
        print(f"Ignorando fornecedor CNPJ {cnpj_cpf}, já existe.")
        continue
    # if empty cnpj, check by reason
    elif not cnpj_cpf:
        cursor.execute("SELECT id FROM fornecedores WHERE nome=?", (razao,))
        if cursor.fetchone():
             print(f"Ignorando fornecedor Nome {razao}, já existe.")
             continue

    nome_fantasia = val('Nome Fantasia')
    insc_estadual = val('Inscrição Estadual')
    endereco = val('Endereço')
    bairro = val('Bairro')
    cep = val('CEP')
    cidade = val('Cidade')
    uf = val('UF')
    telefone = val('Telefone')
    email = val('E-mail')
    plano_contas = val('PLANO DE CONTAS')
    status = val('Status')
    
    query = """INSERT INTO fornecedores 
               (nome, telefone, cnpj_cpf, nome_fantasia, inscricao_estadual, 
                endereco, bairro, cep, cidade, uf, email, plano_de_contas, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
               
    cursor.execute(query, (
        razao, telefone, cnpj_cpf, nome_fantasia, insc_estadual,
        endereco, bairro, cep, cidade, uf, email, plano_contas, status
    ))
    count += 1

conn.commit()
conn.close()
print(f"Sucesso! {count} fornecedores importados corretamente.")
