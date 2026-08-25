"""
Módulo de Validação e Busca Fuzzy de Entidades (Clientes, Fornecedores, Produtos e Plano de Contas)
para o Conector de Voz do ERP DAATEL.
"""

import pandas as pd
from typing import Optional, Dict, Any, Tuple
from difflib import SequenceMatcher

try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


import unicodedata


def _remover_acentos(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).strip().lower()


def _calcular_similaridade(str1: str, str2: str) -> float:
    """Calcula a similaridade de 0 a 100 entre duas strings."""
    if not str1 or not str2:
        return 0.0
    str1_clean = _remover_acentos(str1)
    str2_clean = _remover_acentos(str2)
    
    if RAPIDFUZZ_AVAILABLE:
        return float(fuzz.WRatio(str1_clean, str2_clean))
    else:
        ratio_total = SequenceMatcher(None, str1_clean, str2_clean).ratio() * 100.0
        if str1_clean in str2_clean or str2_clean in str1_clean:
            return max(ratio_total, 85.0)
        # Token set match básico
        words1 = set(str1_clean.split())
        words2 = set(str2_clean.split())
        if words1 and words2 and (words1.issubset(words2) or words2.issubset(words1)):
            return max(ratio_total, 80.0)
        return ratio_total


def buscar_cliente_fuzzy(nome_falado: str, df_clientes: pd.DataFrame, threshold: float = 65.0) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Busca o cliente mais próximo no DataFrame de clientes ativos.
    Retorna: (dict_cliente, score_similaridade)
    """
    if not nome_falado or df_clientes.empty:
        return None, 0.0

    melhor_cliente = None
    melhor_score = 0.0

    for _, row in df_clientes.iterrows():
        nome_db = str(row.get('nome') or row.get('razao_social') or '')
        score = _calcular_similaridade(nome_falado, nome_db)
        if score > melhor_score:
            melhor_score = score
            melhor_cliente = row.to_dict()

    if melhor_score >= threshold:
        return melhor_cliente, melhor_score
    return None, melhor_score


def buscar_fornecedor_fuzzy(nome_falado: str, df_fornecedores: pd.DataFrame, threshold: float = 65.0) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Busca o fornecedor mais próximo no DataFrame de fornecedores ativos.
    Retorna: (dict_fornecedor, score_similaridade)
    """
    if not nome_falado or df_fornecedores.empty:
        return None, 0.0

    melhor_fornecedor = None
    melhor_score = 0.0

    for _, row in df_fornecedores.iterrows():
        nome_db = str(row.get('nome') or row.get('razao_social') or row.get('nome_fantasia') or '')
        score = _calcular_similaridade(nome_falado, nome_db)
        if score > melhor_score:
            melhor_score = score
            melhor_fornecedor = row.to_dict()

    if melhor_score >= threshold:
        return melhor_fornecedor, melhor_score
    return None, melhor_score


def buscar_produto_fuzzy(nome_falado: str, df_produtos: pd.DataFrame, threshold: float = 60.0) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Busca o produto mais próximo no DataFrame de produtos ativos.
    Retorna: (dict_produto, score_similaridade)
    """
    if not nome_falado or df_produtos.empty:
        return None, 0.0

    melhor_produto = None
    melhor_score = 0.0

    for _, row in df_produtos.iterrows():
        nome_db = str(row.get('nome') or row.get('descricao') or '')
        score = _calcular_similaridade(nome_falado, nome_db)
        if score > melhor_score:
            melhor_score = score
            melhor_produto = row.to_dict()

    if melhor_score >= threshold:
        return melhor_produto, melhor_score
    return None, melhor_score


def buscar_plano_contas_fuzzy(categoria_falada: str, df_planos: pd.DataFrame, threshold: float = 60.0) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Busca a categoria/plano de contas mais próximo no DataFrame de planos de contas.
    Retorna: (dict_plano_conta, score_similaridade)
    """
    if not categoria_falada or df_planos.empty:
        return None, 0.0

    melhor_plano = None
    melhor_score = 0.0

    for _, row in df_planos.iterrows():
        categoria_db = str(row.get('categoria') or row.get('descricao') or row.get('codigo') or '')
        score = _calcular_similaridade(categoria_falada, categoria_db)
        if score > melhor_score:
            melhor_score = score
            melhor_plano = row.to_dict()

    if melhor_score >= threshold:
        return melhor_plano, melhor_score
    return None, melhor_score
