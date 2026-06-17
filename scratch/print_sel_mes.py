import sys
from unittest.mock import MagicMock
import importlib

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

dre = importlib.import_module("pages.10_DRE")
print("=== DRE df_vd ===")
print(dre.df_vd[['data', 'sale_month', 'valor_total']])
print("=== DRE df_vd_mes ===")
print(dre.df_vd_mes[['data', 'sale_month', 'valor_total']])
print("rb_mes:", dre.rb_mes)
