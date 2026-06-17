import sys
from unittest.mock import MagicMock
import pandas as pd
import importlib
import sqlite3

# 1. Mock Streamlit
mock_st = MagicMock()
mock_st.cache_resource = lambda x: x
mock_st.cache_data = lambda x: x
mock_st.secrets = {}
mock_st.selectbox.return_value = "Maio/2026"
mock_st.tabs.return_value = (MagicMock(), MagicMock())
def mock_columns(spec):
    n = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(n)]
mock_st.columns.side_effect = mock_columns
sys.modules['streamlit'] = mock_st

# 2. Database connection to SQLite
conn = sqlite3.connect("erp_fabrica.db")
cursor = conn.cursor()

# Clean up any leftover test data
cursor.execute("DELETE FROM vendas WHERE id >= 900")
cursor.execute("DELETE FROM contas_a_pagar WHERE id >= 900")
conn.commit()

# Find account IDs
cursor.execute("SELECT id FROM planos_de_contas WHERE codigo = '2.3.1' LIMIT 1")
fixed_pc_row = cursor.fetchone()
pc_fixed_id = fixed_pc_row[0] if fixed_pc_row else 19  # Default to 19

cursor.execute("SELECT id FROM planos_de_contas WHERE codigo = '2.1.3' LIMIT 1")
non_fixed_pc_row = cursor.fetchone()
pc_non_fixed_id = non_fixed_pc_row[0] if non_fixed_pc_row else 12  # Default to 12

print(f"Using pc_fixed_id={pc_fixed_id}, pc_non_fixed_id={pc_non_fixed_id}")

try:
    # Insert test Vendas
    # ID 900: May sale (Receita Bruta = 1000, Commission = 50)
    cursor.execute("""
        INSERT INTO vendas (id, data, valor_total, comissao_valor, status, cliente_id, vendedor_id, quantidade)
        VALUES (900, '2026-05-15', 1000.0, 50.0, 'FATURADO', 1, 1, 10.0)
    """)
    # ID 901: June sale (Receita Bruta = 2000, Commission = 100)
    cursor.execute("""
        INSERT INTO vendas (id, data, valor_total, comissao_valor, status, cliente_id, vendedor_id, quantidade)
        VALUES (901, '2026-06-15', 2000.0, 100.0, 'FATURADO', 1, 1, 20.0)
    """)
    
    # Insert test Contas a Pagar
    # ID 900: Fixed expense due in June 2026 (maps to May 2026 reference month)
    cursor.execute("""
        INSERT INTO contas_a_pagar (id, data_vencimento, valor, plano_conta_id, descricao)
        VALUES (900, '2026-06-10', 300.0, ?, 'Test Fixed June')
    """, (pc_fixed_id,))
    
    # ID 901: Non-fixed expense due in May 2026 (maps to May 2026 reference month)
    cursor.execute("""
        INSERT INTO contas_a_pagar (id, data_vencimento, valor, plano_conta_id, descricao)
        VALUES (901, '2026-05-20', 150.0, ?, 'Test Non-Fixed May')
    """, (pc_non_fixed_id,))
    
    # ID 902: Non-fixed expense due in June 2026 (maps to June 2026 reference month)
    cursor.execute("""
        INSERT INTO contas_a_pagar (id, data_vencimento, valor, plano_conta_id, descricao)
        VALUES (902, '2026-06-20', 250.0, ?, 'Test Non-Fixed June')
    """, (pc_non_fixed_id,))
    
    conn.commit()
    print("Temporary test records inserted successfully.")
    
    # Helper to run DRE
    def run_dre_for(month_str):
        mock_st.selectbox.return_value = month_str
        if 'pages.10_DRE' in sys.modules:
            del sys.modules['pages.10_DRE']
        dre = importlib.import_module("pages.10_DRE")
        return dre

    # Run tests for May 2026
    print("\n=== RUNNING DRE FOR MAY 2026 ===")
    dre_may = run_dre_for("Maio/2026")
    print(f"Receita Bruta: {dre_may.rb_mes} (Expected: 10225.0)")
    print(f"Comissões: {dre_may.comi_mes} (Expected: 50.0)")
    print(f"Despesas Fixas: {dre_may.df_mes_val} (Expected: 300.0)")
    print(f"Impostos s/ Venda: {dre_may.imp_venda_mes} (Expected: 150.0)")
    
    assert abs(dre_may.rb_mes - 10225.0) < 1e-3, f"Incorrect Receita Bruta: {dre_may.rb_mes}"
    assert abs(dre_may.comi_mes - 50.0) < 1e-3, f"Incorrect Comissões: {dre_may.comi_mes}"
    assert abs(dre_may.df_mes_val - 300.0) < 1e-3, f"Incorrect Despesas Fixas: {dre_may.df_mes_val}"
    assert abs(dre_may.imp_venda_mes - 150.0) < 1e-3, f"Incorrect Impostos s/ Venda: {dre_may.imp_venda_mes}"
    print("May 2026 assertions PASSED!")

    # Run tests for June 2026
    print("\n=== RUNNING DRE FOR JUNE 2026 ===")
    dre_june = run_dre_for("Junho/2026")
    print(f"Receita Bruta: {dre_june.rb_mes} (Expected: 2000.0)")
    print(f"Comissões: {dre_june.comi_mes} (Expected: 100.0)")
    print(f"Despesas Fixas: {dre_june.df_mes_val} (Expected: 0.0)")
    print(f"Impostos s/ Venda: {dre_june.imp_venda_mes} (Expected: 250.0)")
    
    assert abs(dre_june.rb_mes - 2000.0) < 1e-3, f"Incorrect Receita Bruta: {dre_june.rb_mes}"
    assert abs(dre_june.comi_mes - 100.0) < 1e-3, f"Incorrect Comissões: {dre_june.comi_mes}"
    assert abs(dre_june.df_mes_val - 0.0) < 1e-3, f"Incorrect Despesas Fixas: {dre_june.df_mes_val}"
    assert abs(dre_june.imp_venda_mes - 250.0) < 1e-3, f"Incorrect Impostos s/ Venda: {dre_june.imp_venda_mes}"
    print("June 2026 assertions PASSED!")
    
    print("\nALL DRE UNIT TESTS PASSED!")

finally:
    # Cleanup database
    print("\nCleaning up temporary test records...")
    cursor.execute("DELETE FROM vendas WHERE id >= 900")
    cursor.execute("DELETE FROM contas_a_pagar WHERE id >= 900")
    conn.commit()
    conn.close()
    print("Cleanup done.")
