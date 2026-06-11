import enum
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class TipoPedidoCompra(str, enum.Enum):
    LOTE_FISICO = "Lote Físico"
    DROPSHIPPING = "Dropshipping"


class StatusPedidoCompra(str, enum.Enum):
    COMPRADO = "COMPRADO"
    EM_TRANSITO_PRE_TAXA = "EM TRÂNSITO (PRÉ TAXA)"
    CHEGANDO_POS_TAXA = "CHEGANDO (APÓS PAGAMENTO DA TAXA)"
    ENTREGUE = "ENTREGUE"


class TipoVenda(str, enum.Enum):
    PRONTA_ENTREGA = "Pronta Entrega"
    DROPSHIPPING = "Dropshipping"


class Produto(Base):
    __tablename__ = "produto"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    team = Column(String, nullable=False)
    league = Column(String, nullable=False)
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    grade_tamanho = Column(String, nullable=False)
    cloudinary_images = Column(Text, default="")

    itens_compra = relationship("ItemCompra", back_populates="produto")


class PedidoCompra(Base):
    __tablename__ = "pedido_compra"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoPedidoCompra), nullable=False)
    data_pedido = Column(Date, nullable=False, default=date.today)
    status = Column(
        Enum(StatusPedidoCompra),
        nullable=False,
        default=StatusPedidoCompra.COMPRADO,
    )
    taxa_importacao = Column(Float, default=0.0)
    frete = Column(Float, default=0.0)
    nome_identificador = Column(String, nullable=True)
    codigo_rastreio = Column(String, nullable=True)

    itens = relationship(
        "ItemCompra", back_populates="pedido_compra", cascade="all, delete-orphan"
    )


class ItemCompra(Base):
    __tablename__ = "item_compra"

    id = Column(Integer, primary_key=True, index=True)
    pedido_compra_id = Column(Integer, ForeignKey("pedido_compra.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    tamanho = Column(String, nullable=False)
    quantidade_comprada = Column(Integer, nullable=False)
    quantidade_disponivel = Column(Integer, nullable=False)
    valor_unitario_compra = Column(Float, nullable=False)

    pedido_compra = relationship("PedidoCompra", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_compra")
    itens_venda = relationship("ItemVenda", back_populates="item_compra")


class Venda(Base):
    __tablename__ = "venda"

    id = Column(Integer, primary_key=True, index=True)
    data_venda = Column(DateTime, nullable=False, default=datetime.now)
    tipo_venda = Column(Enum(TipoVenda), nullable=False)
    forma_pagamento = Column(String, nullable=False)
    taxa_pagamento_percentual = Column(Float, default=0.0)
    despesa_venda_extra = Column(Float, default=0.0)

    itens = relationship(
        "ItemVenda", back_populates="venda", cascade="all, delete-orphan"
    )


class ItemVenda(Base):
    __tablename__ = "item_venda"

    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("venda.id"), nullable=False)
    item_compra_id = Column(Integer, ForeignKey("item_compra.id"), nullable=True)
    quantidade_vendida = Column(Integer, nullable=False)
    valor_unitario_venda = Column(Float, nullable=False)

    venda = relationship("Venda", back_populates="itens")
    item_compra = relationship("ItemCompra", back_populates="itens_venda")


class DespesaGeral(Base):
    __tablename__ = "despesa_geral"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data_despesa = Column(Date, nullable=False, default=date.today)
