from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Grades de tamanho
# ---------------------------------------------------------------------------

GRADES_TAMANHO: dict[str, list[str]] = {
    "Masculino": ["P", "M", "G", "GG", "2XL", "3XL", "4XL"],
    "Feminino": ["P", "M", "G", "GG"],
    "Infantil": ["14", "16", "18", "20", "22", "24", "26", "28"],
}

CATEGORY_GRADE_MAP: dict[str, str] = {
    "Feminina": "Feminino",
    "Infantil": "Infantil",
}

CATEGORIAS = ["Brasileirão Série A", "Europa", "Feminina", "Seleções", "Infantil"]


def grade_para_categoria(category: str) -> str:
    return CATEGORY_GRADE_MAP.get(category, "Masculino")


def tamanhos_da_grade(grade_tamanho: str) -> list[str]:
    return GRADES_TAMANHO.get(grade_tamanho, [])


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TipoPedidoCompraEnum(str, Enum):
    LOTE_FISICO = "Lote Físico"
    DROPSHIPPING = "Dropshipping"


class StatusPedidoCompraEnum(str, Enum):
    COMPRADO = "COMPRADO"
    EM_TRANSITO_PRE_TAXA = "EM TRÂNSITO (PRÉ TAXA)"
    CHEGANDO_POS_TAXA = "CHEGANDO (APÓS PAGAMENTO DA TAXA)"
    ENTREGUE = "ENTREGUE"


class TipoVendaEnum(str, Enum):
    PRONTA_ENTREGA = "Pronta Entrega"
    DROPSHIPPING = "Dropshipping"


# ---------------------------------------------------------------------------
# Produto (Catálogo puro — sem preço/custo/estoque)
# ---------------------------------------------------------------------------


class ProdutoBase(BaseModel):
    name: str
    team: str
    league: str
    type: str
    category: str
    grade_tamanho: str
    cloudinary_images: str = ""


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    name: Optional[str] = None
    team: Optional[str] = None
    league: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    grade_tamanho: Optional[str] = None
    cloudinary_images: Optional[str] = None


class ProdutoResponse(ProdutoBase):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# PedidoCompra
# ---------------------------------------------------------------------------


class PedidoCompraBase(BaseModel):
    tipo: TipoPedidoCompraEnum
    data_pedido: date
    status: StatusPedidoCompraEnum = StatusPedidoCompraEnum.COMPRADO
    taxa_importacao: float = 0.0
    frete: float = 0.0
    nome_identificador: Optional[str] = None
    codigo_rastreio: Optional[str] = None


class PedidoCompraCreate(PedidoCompraBase):
    pass


class PedidoCompraUpdate(BaseModel):
    tipo: Optional[TipoPedidoCompraEnum] = None
    data_pedido: Optional[date] = None
    status: Optional[StatusPedidoCompraEnum] = None
    taxa_importacao: Optional[float] = None
    frete: Optional[float] = None
    nome_identificador: Optional[str] = None
    codigo_rastreio: Optional[str] = None


class PedidoCompraResponse(PedidoCompraBase):
    id: int
    qtd_itens: int = 0
    total_quantidade: int = 0
    total_custo: float = 0.0

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ItemCompra
# ---------------------------------------------------------------------------


class ItemCompraBase(BaseModel):
    produto_id: int
    tamanho: str
    quantidade_comprada: int
    valor_unitario_compra: float


class ItemCompraCreate(ItemCompraBase):
    quantidade_disponivel: Optional[int] = None  # Default = quantidade_comprada


class ItemCompraUpdate(BaseModel):
    quantidade_comprada: Optional[int] = None
    valor_unitario_compra: Optional[float] = None


class ItemCompraResponse(ItemCompraBase):
    id: int
    pedido_compra_id: int
    quantidade_disponivel: int
    produto_nome: str = ""
    produto_team: str = ""

    model_config = {"from_attributes": True}


class ItemCompraDisponivelResponse(BaseModel):
    """Usado no selectbox de venda para mostrar lotes disponiveis."""
    id: int
    pedido_compra_id: int
    lote_label: str  # ex: "Pedido #3 - Lote Físico"
    produto_nome: str
    tamanho: str
    quantidade_disponivel: int
    valor_unitario_compra: float


# ---------------------------------------------------------------------------
# Venda
# ---------------------------------------------------------------------------


class VendaBase(BaseModel):
    tipo_venda: TipoVendaEnum
    forma_pagamento: str
    taxa_pagamento_percentual: float = 0.0
    despesa_venda_extra: float = 0.0
    cliente_nome: Optional[str] = None
    cliente_telefone: Optional[str] = None
    status_pagamento: str = "CONFIRMADO"


class VendaCreate(VendaBase):
    pass


class VendaUpdate(BaseModel):
    tipo_venda: Optional[TipoVendaEnum] = None
    forma_pagamento: Optional[str] = None
    taxa_pagamento_percentual: Optional[float] = None
    despesa_venda_extra: Optional[float] = None
    cliente_nome: Optional[str] = None
    cliente_telefone: Optional[str] = None
    status_pagamento: Optional[str] = None


class VendaStatusUpdate(BaseModel):
    status_pagamento: str


class VendaResponse(VendaBase):
    id: int
    data_venda: datetime
    total_bruto: float = 0.0
    total_itens: int = 0

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ItemVenda
# ---------------------------------------------------------------------------


class ItemVendaCreate(BaseModel):
    venda_id: int
    item_compra_id: Optional[int] = None
    quantidade_vendida: int
    valor_unitario_venda: float


class ItemVendaResponse(BaseModel):
    id: int
    venda_id: int
    item_compra_id: Optional[int] = None
    quantidade_vendida: int
    valor_unitario_venda: float
    # Informações enriquecidas
    produto_nome: str = ""
    produto_team: str = ""
    tamanho: str = ""
    lote_origem: str = ""
    custo_real_unitario: float = 0.0
    lucro_unitario: float = 0.0
    lucro_total: float = 0.0

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# DespesaGeral
# ---------------------------------------------------------------------------


class DespesaGeralCreate(BaseModel):
    descricao: str
    valor: float
    data_despesa: date


class DespesaGeralResponse(BaseModel):
    id: int
    descricao: str
    valor: float
    data_despesa: date

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Reposição (estoque projetado)
# ---------------------------------------------------------------------------


class ReposicaoRow(BaseModel):
    produto_id: int
    produto_nome: str
    produto_team: str
    tamanho: str
    qtd_entregue: int = 0
    qtd_comprado: int = 0
    qtd_em_transito: int = 0
    qtd_chegando: int = 0
    qtd_total_futuro: int = 0


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class LucroItemDetail(BaseModel):
    venda_id: int
    data_venda: str
    produto_nome: str
    produto_team: str
    tamanho: str
    quantidade: int
    valor_venda: float
    valor_liquido: float
    custo_real: float
    despesa_rateada: float
    lucro: float


class DashboardResponse(BaseModel):
    faturamento_bruto: float = 0.0
    lucro_liquido_total: float = 0.0
    total_vendas: int = 0
    total_itens_vendidos: int = 0
    total_despesas_gerais: float = 0.0
    total_despesas_venda: float = 0.0
    pecas_em_estoque: int = 0
    custo_estoque_parado: float = 0.0
    valores_a_receber: float = 0.0
    detalhes_lucro: list[LucroItemDetail] = []
    faturamento_por_time: dict[str, float] = {}
