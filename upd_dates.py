import os

def replace_in_file(path, old, new):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Replaced in {path}')

rh_path = 'C:/Users/MARCIO/Gestao_Fabrica_Alho/pages/3_RH.py'
replace_in_file(rh_path, 'admissao = col5.date_input("Data de Início", value=date.today())', 'admissao = col5.date_input("Data de Início", value=date.today(), format="DD/MM/YYYY")')
replace_in_file(rh_path, 'nascimento = col6.date_input("Data de Nascimento", value=date(1990, 1, 1))', 'nascimento = col6.date_input("Data de Nascimento", value=date(1990, 1, 1), format="DD/MM/YYYY")')
replace_in_file(rh_path, 'termino = col_t.date_input("Data de Término (Opcional)", value=None)', 'termino = col_t.date_input("Data de Término (Opcional)", value=None, format="DD/MM/YYYY")')
replace_in_file(rh_path, 'ef_termino = e_term.date_input("Data de Término (Opcional)", value=dt_term_val)', 'ef_termino = e_term.date_input("Data de Término (Opcional)", value=dt_term_val, format="DD/MM/YYYY")')
replace_in_file(rh_path, 'data_pgto = col1.date_input("Data de Pagamento", value=date.today())', 'data_pgto = col1.date_input("Data de Pagamento", value=date.today(), format="DD/MM/YYYY")')

cad_path = 'C:/Users/MARCIO/Gestao_Fabrica_Alho/pages/1_Cadastros.py'
replace_in_file(cad_path, 'nascimento = c_nasc.date_input("Data de Nasc/Fundação", value=None)', 'nascimento = c_nasc.date_input("Data de Nasc/Fundação", value=None, format="DD/MM/YYYY")')
replace_in_file(cad_path, 'data_aq_maq = col_m2.date_input("Data de Aquisição")', 'data_aq_maq = col_m2.date_input("Data de Aquisição", format="DD/MM/YYYY")')
