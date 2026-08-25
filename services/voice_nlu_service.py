"""
Serviço NLU (Natural Language Understanding) para interpretação de comandos de voz do ERP DAATEL.
Utiliza Pydantic e Google Gemini API com resposta estruturada e expurgo remoto de mídia (LGPD).
"""

import os
import json
import logging
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger("VoiceNLUService")


class VoiceOrderItemSchema(BaseModel):
    produto_nome_falado: str = Field(description="Nome do produto exatamente como falado pelo usuário")
    quantidade: float = Field(description="Quantidade numérica solicitada")
    unidade_medida: Optional[str] = Field(None, description="Unidade mencionada: kg, saco, caixa, pct, etc.")
    preco_unitario_informado: Optional[float] = Field(None, description="Preço unitário em R$ se mencionado")


class VoiceCommandSchema(BaseModel):
    tipo_operacao: Literal["PDV_EXPRESS", "PEDIDO_VENDA", "CONTA_PAGAR", "CONTA_RECEBER", "DESCONHECIDO"] = Field(
        description="Tipo de operação identificada no áudio"
    )
    confiabilidade_interpretacao: float = Field(
        default=0.9, description="Nota de 0.0 a 1.0 indicando a certeza da interpretação"
    )
    nome_parceiro: Optional[str] = Field(
        None, description="Nome do cliente ou fornecedor (Se omitido em PDV_EXPRESS, inferir 'CONSUMIDOR')"
    )
    valor_total: Optional[float] = Field(
        None, description="Valor monetário total em Reais (R$)"
    )
    data_vencimento: Optional[str] = Field(
        None, description="Data YYYY-MM-DD. Nunca assumir 'hoje' por default se for omisso no financeiro."
    )
    condicao_pagamento: Optional[Literal["A_VISTA", "A_PRAZO"]] = Field(
        default="A_VISTA", description="A_VISTA ou A_PRAZO"
    )
    forma_pagamento_nome: Optional[str] = Field(
        None, description="Pix, Dinheiro, Boleto, Cartão, etc."
    )
    tipo_documento: Literal["DAV"] = Field(
        default="DAV", description="Tipo de documento padrão: DAV"
    )
    descricao_observacao: Optional[str] = Field(
        None, description="Resumo do motivo ou observação da transação"
    )
    categoria_plano_contas: Optional[str] = Field(
        None, description="Categoria do plano de contas"
    )
    itens_pedido: List[VoiceOrderItemSchema] = Field(
        default_factory=list, description="Lista de itens da venda ou pedido"
    )


class VoiceNLUService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        
        if self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def process_voice_audio(self, audio_file_path: str) -> VoiceCommandSchema:
        """
        Processa o áudio local, envia para o Gemini, obtém o JSON estruturado Pydantic
        e executa o expurgo obrigatório do arquivo remoto no Google (LGPD).
        """
        if not self.model:
            raise RuntimeError("Gemini API Key não configurada ou biblioteca google-generativeai ausente.")

        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_file_path}")

        audio_file = None
        try:
            # Upload temporário para o Gemini
            audio_file = genai.upload_file(path=audio_file_path)
            hoje_str = datetime.now().strftime("%Y-%m-%d (%A)")

            prompt = f"""
            Você é o assistente oficial de voz do ERP da Fábrica de Alho DAATEL.
            Data atual de referência: {hoje_str}.

            Instruções Específicas de Extração:
            1. Identifique a intenção:
               - Venda balcão rápida, pronta entrega, dinheiro/pix no caixa -> PDV_EXPRESS.
               - Solicitação de venda futura, pedido de cliente para entrega posterior -> PEDIDO_VENDA.
               - Pagamento a fornecedor, despesa de compras/insumos -> CONTA_PAGAR.
               - Cobrança de cliente, faturamento a receber -> CONTA_RECEBER.
               - Áudio inaudível ou sem instrução clara -> DESCONHECIDO.
            2. Se for PDV_EXPRESS e nenhum cliente for mencionado, defina nome_parceiro como 'CONSUMIDOR'.
            3. Em CONTA_PAGAR e CONTA_RECEBER, extraia o nome do parceiro comercial se falado.
            4. Para datas relativas (ex: "vence sexta", "vence dia 30"), calcule a data final em YYYY-MM-DD baseando-se em {hoje_str}.
            5. NUNCA coloque data_vencimento como hoje por default se a data não foi falada no financeiro. Deixe null.
            6. Retorne a resposta ESTRITAMENTE conforme o esquema JSON solicitado.
            """

            response = self.model.generate_content(
                [audio_file, prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=VoiceCommandSchema,
                    temperature=0.1
                )
            )

            return VoiceCommandSchema.model_validate_json(response.text)

        finally:
            # Expurgo Remoto Obrigatório (LGPD)
            if audio_file:
                try:
                    genai.delete_file(audio_file.name)
                except Exception as clean_err:
                    logger.warning(f"Falha ao expurgar arquivo remoto no Gemini: {clean_err}")
