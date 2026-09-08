import pandas as pd
from database import get_connection

url = 'https://docs.google.com/spreadsheets/d/15Cg521JkqXM4ZTLjDyF3uG3JOGPdMKfHslp3y-gZ5M0/export?format=csv'
print("Fazendo download da planilha...")
df = pd.read_csv(url)

# Clean and normalize columns
df.columns = [c.strip() for c in df.columns]

def parse_moeda(val):
    if pd.isna(val):
        return 0.0
    v = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(v)
    except:
        return 0.0

conn = get_connection()
cursor = conn.cursor()

cursor.execute("DELETE FROM produtos")

count = 0
for idx, row in df.iterrows():
    nome = str(row['PRODUTOS']).strip()
    if pd.isna(row['PRODUTOS']) or nome == "nan" or nome == "":
        continue
        
    marca = str(row.get('MARCA', '')).strip()
    if marca == "nan": marca = ""
    
    peso_volume = str(row.get('KG/ GR', '')).strip()
    if peso_volume == "nan": peso_volume = ""
    
    referencia = str(row.get('REF', '')).strip()
    if referencia == "nan": referencia = ""
    
    ean = str(row.get('EAN', '')).strip()
    if ean == "nan": ean = ""
    if ean.endswith(".0"): ean = ean[:-2] # clean float to string
    
    unidades_por_fardo_str = str(row.get('UNIDADE / FARDO', '1')).strip()
    try:
        unidades_por_fardo = int(float(unidades_por_fardo_str))
    except:
        unidades_por_fardo = 1
        
    tipo_embalagem = str(row.get('CAIXA/ SACO', '')).strip()
    if tipo_embalagem == "nan": tipo_embalagem = ""
    
    custo_und_key = next((k for k in df.columns if 'CUSTO' in k and 'UND' in k), 'CUSTO UND')
    custo_und = parse_moeda(row.get(custo_und_key, '0'))
    
    custo_fardo_key = next((k for k in df.columns if 'CUSTO' in k and 'FARDO' in k), 'CUSTO FARDO')
    custo_fardo = parse_moeda(row.get(custo_fardo_key, '0'))
    
    unidade_medida = f"{peso_volume} - {tipo_embalagem}"
    base_price = 0.0
    is_mp = 0
    
    cursor.execute("""
    INSERT INTO produtos (nome, unidade_medida, preco_venda_base, is_materia_prima, 
                          marca, peso_volume, referencia, ean, unidades_por_fardo, 
                          tipo_embalagem, custo_unidade, custo_fardo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, unidade_medida, base_price, is_mp, marca, peso_volume, referencia, ean, 
          unidades_por_fardo, tipo_embalagem, custo_und, custo_fardo))
    count += 1

conn.commit()
conn.close()
print(f"Sucesso! {count} produtos importados corretamente.")
