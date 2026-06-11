from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    DespesaGeral,
    ItemCompra,
    ItemVenda,
    PedidoCompra,
    Produto,
    StatusPedidoCompra,
    TipoVenda,
    Venda,
)
from schemas import (
    DashboardResponse,
    DespesaGeralCreate,
    ItemCompraCreate,
    ItemCompraUpdate,
    ItemVendaCreate,
    LucroItemDetail,
    PedidoCompraCreate,
    PedidoCompraUpdate,
    ProdutoCreate,
    ProdutoUpdate,
    ReposicaoRow,
    VendaCreate,
    VendaUpdate,
    tamanhos_da_grade,
)

# ===================================================================
# Helpers de cálculo
# ===================================================================


def calcular_custo_real(item_compra_id: int, db: Session) -> float:
    """Custo real unitário = valor_unitario_compra + rateio de taxa_importacao e frete."""
    item = db.query(ItemCompra).filter(ItemCompra.id == item_compra_id).first()
    if not item:
        return 0.0
    pedido = item.pedido_compra
    if not pedido:
        return item.valor_unitario_compra

    # Soma total de quantidades no pedido
    total_qtd = (
        db.query(func.coalesce(func.sum(ItemCompra.quantidade_comprada), 0))
        .filter(ItemCompra.pedido_compra_id == pedido.id)
        .scalar()
    )
    if total_qtd == 0:
        return item.valor_unitario_compra

    despesas_rateio = (pedido.taxa_importacao + pedido.frete) / total_qtd
    return round(item.valor_unitario_compra + despesas_rateio, 2)


def calcular_lucro_item_venda(item_venda: ItemVenda, db: Session) -> dict:
    """Calcula lucro detalhado de um ItemVenda com rateio completo."""
    venda = item_venda.venda
    item_compra = item_venda.item_compra

    # Valor líquido após taxa de pagamento
    valor_bruto_total = item_venda.valor_unitario_venda * item_venda.quantidade_vendida
    valor_liquido = valor_bruto_total * (1 - venda.taxa_pagamento_percentual / 100)

    # Custo real
    if item_compra:
        custo_real_unit = calcular_custo_real(item_compra.id, db)
    else:
        custo_real_unit = 0.0  # Dropshipping — sem custo de compra próprio
    custo_total = custo_real_unit * item_venda.quantidade_vendida

    # Rateio da despesa_venda_extra
    total_qtd_venda = (
        db.query(func.coalesce(func.sum(ItemVenda.quantidade_vendida), 0))
        .filter(ItemVenda.venda_id == venda.id)
        .scalar()
    )
    if total_qtd_venda > 0 and venda.despesa_venda_extra > 0:
        despesa_rateada_unit = venda.despesa_venda_extra / total_qtd_venda
    else:
        despesa_rateada_unit = 0.0
    despesa_rateada_total = despesa_rateada_unit * item_venda.quantidade_vendida

    lucro_total = round(valor_liquido - custo_total - despesa_rateada_total, 2)
    lucro_unit = round(lucro_total / item_venda.quantidade_vendida, 2) if item_venda.quantidade_vendida else 0

    produto_nome = ""
    produto_team = ""
    tamanho = ""
    lote_origem = ""
    if item_compra:
        produto_nome = item_compra.produto.name if item_compra.produto else ""
        produto_team = item_compra.produto.team if item_compra.produto else ""
        tamanho = item_compra.tamanho
        pedido = item_compra.pedido_compra
        if pedido:
            lote_origem = f"Pedido #{pedido.id} - {pedido.nome_identificador or pedido.tipo.value}"

    return {
        "venda_id": venda.id,
        "data_venda": venda.data_venda.strftime("%d/%m/%Y %H:%M") if venda.data_venda else "",
        "produto_nome": produto_nome,
        "produto_team": produto_team,
        "tamanho": tamanho,
        "quantidade": item_venda.quantidade_vendida,
        "valor_venda": round(valor_bruto_total, 2),
        "valor_liquido": round(valor_liquido, 2),
        "custo_real": round(custo_total, 2),
        "despesa_rateada": round(despesa_rateada_total, 2),
        "lucro": lucro_total,
    }


# ===================================================================
# Produto
# ===================================================================


def listar_produtos(db: Session) -> list[Produto]:
    return db.query(Produto).order_by(Produto.name).all()


def obter_produto(db: Session, produto_id: int) -> Optional[Produto]:
    return db.query(Produto).filter(Produto.id == produto_id).first()


def criar_produto(db: Session, data: ProdutoCreate) -> Produto:
    # Validar grade de tamanho
    grade = data.grade_tamanho
    from schemas import GRADES_TAMANHO
    if grade not in GRADES_TAMANHO:
        raise HTTPException(
            status_code=400,
            detail=f"Grade de tamanho '{grade}' inválida. Opções: {', '.join(GRADES_TAMANHO.keys())}",
        )
    produto = Produto(**data.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def atualizar_produto(db: Session, produto_id: int, data: ProdutoUpdate) -> Produto:
    produto = obter_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    update_data = data.model_dump(exclude_unset=True)
    if "grade_tamanho" in update_data:
        from schemas import GRADES_TAMANHO
        if update_data["grade_tamanho"] not in GRADES_TAMANHO:
            raise HTTPException(status_code=400, detail="Grade de tamanho inválida")
    for key, value in update_data.items():
        setattr(produto, key, value)
    db.commit()
    db.refresh(produto)
    return produto


def deletar_produto(db: Session, produto_id: int) -> None:
    produto = obter_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    # Verifica se há itens de compra vinculados
    itens = db.query(ItemCompra).filter(ItemCompra.produto_id == produto_id).first()
    if itens:
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir produto com itens de compra vinculados. Arquive-o ou remova os vínculos primeiro.",
        )
    db.delete(produto)
    db.commit()


# ===================================================================
# PedidoCompra + ItemCompra
# ===================================================================


def listar_pedidos_compra(db: Session) -> list[PedidoCompra]:
    return db.query(PedidoCompra).order_by(PedidoCompra.data_pedido.desc()).all()


def obter_pedido_compra(db: Session, pedido_id: int) -> Optional[PedidoCompra]:
    return (
        db.query(PedidoCompra)
        .filter(PedidoCompra.id == pedido_id)
        .first()
    )


def criar_pedido_compra(db: Session, data: PedidoCompraCreate) -> PedidoCompra:
    pedido = PedidoCompra(**data.model_dump())
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


def atualizar_pedido_compra(
    db: Session, pedido_id: int, data: PedidoCompraUpdate
) -> PedidoCompra:
    pedido = obter_pedido_compra(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pedido, key, value)
    db.commit()
    db.refresh(pedido)
    return pedido


def deletar_pedido_compra(db: Session, pedido_id: int) -> None:
    pedido = obter_pedido_compra(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    # Verifica se há vendas vinculadas a estes itens
    for item in pedido.itens:
        vendas_vinculadas = (
            db.query(ItemVenda)
            .filter(ItemVenda.item_compra_id == item.id)
            .first()
        )
        if vendas_vinculadas:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível excluir pedido com vendas vinculadas ao ItemCompra #{item.id}",
            )
    db.delete(pedido)
    db.commit()


# --- Itens do Pedido ---


def listar_itens_compra(db: Session, pedido_id: int) -> list[ItemCompra]:
    return (
        db.query(ItemCompra)
        .filter(ItemCompra.pedido_compra_id == pedido_id)
        .all()
    )


def criar_item_compra(db: Session, pedido_id: int, data: ItemCompraCreate) -> ItemCompra:
    pedido = obter_pedido_compra(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    produto = obter_produto(db, data.produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Valida tamanho na grade
    tamanhos_validos = tamanhos_da_grade(produto.grade_tamanho)
    if data.tamanho not in tamanhos_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Tamanho '{data.tamanho}' inválido para grade '{produto.grade_tamanho}'. "
            f"Válidos: {', '.join(tamanhos_validos)}",
        )

    qtd_disponivel = (
        data.quantidade_disponivel
        if data.quantidade_disponivel is not None
        else data.quantidade_comprada
    )

    item = ItemCompra(
        pedido_compra_id=pedido_id,
        produto_id=data.produto_id,
        tamanho=data.tamanho,
        quantidade_comprada=data.quantidade_comprada,
        quantidade_disponivel=qtd_disponivel,
        valor_unitario_compra=data.valor_unitario_compra,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def atualizar_item_compra(
    db: Session, item_id: int, data: ItemCompraUpdate
) -> ItemCompra:
    item = db.query(ItemCompra).filter(ItemCompra.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="ItemCompra não encontrado")
    update_data = data.model_dump(exclude_unset=True)
    # Se a quantidade_comprada mudar, ajusta quantidade_disponivel pelo delta
    if "quantidade_comprada" in update_data:
        nova_qtd = update_data["quantidade_comprada"]
        delta = nova_qtd - item.quantidade_comprada
        item.quantidade_disponivel = max(0, item.quantidade_disponivel + delta)
    for key, value in update_data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def deletar_item_compra(db: Session, item_id: int) -> None:
    item = db.query(ItemCompra).filter(ItemCompra.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="ItemCompra não encontrado")
    # Verifica se há vendas vinculadas
    vendas = (
        db.query(ItemVenda)
        .filter(ItemVenda.item_compra_id == item_id)
        .first()
    )
    if vendas:
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir item com vendas vinculadas",
        )
    db.delete(item)
    db.commit()


def obter_itens_disponiveis_para_venda(
    db: Session, produto_id: int, tamanho: str
) -> list[ItemCompra]:
    """Retorna itens de compra com estoque disponível (status ENTREGUE) para um produto/tamanho."""
    return (
        db.query(ItemCompra)
        .join(PedidoCompra)
        .filter(
            ItemCompra.produto_id == produto_id,
            ItemCompra.tamanho == tamanho,
            ItemCompra.quantidade_disponivel > 0,
            PedidoCompra.status == StatusPedidoCompra.ENTREGUE,
        )
        .order_by(PedidoCompra.data_pedido.asc())
        .all()
    )


# ===================================================================
# Venda + ItemVenda
# ===================================================================


def listar_vendas(db: Session) -> list[Venda]:
    return db.query(Venda).order_by(Venda.data_venda.desc()).all()


def obter_venda(db: Session, venda_id: int) -> Optional[Venda]:
    return db.query(Venda).filter(Venda.id == venda_id).first()


def criar_venda(db: Session, data: VendaCreate) -> Venda:
    venda = Venda(**data.model_dump())
    db.add(venda)
    db.commit()
    db.refresh(venda)
    return venda


def atualizar_venda(db: Session, venda_id: int, data: VendaUpdate) -> Venda:
    venda = obter_venda(db, venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(venda, key, value)
    db.commit()
    db.refresh(venda)
    return venda


def deletar_venda(db: Session, venda_id: int) -> None:
    venda = obter_venda(db, venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    # Restaura estoque dos itens
    for item_venda in venda.itens:
        if item_venda.item_compra_id:
            item_compra = item_venda.item_compra
            if item_compra:
                item_compra.quantidade_disponivel += item_venda.quantidade_vendida
    db.delete(venda)
    db.commit()


# --- Itens da Venda ---


def criar_item_venda(db: Session, data: ItemVendaCreate) -> ItemVenda:
    venda = obter_venda(db, data.venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    # Validação específica para Pronta Entrega
    if venda.tipo_venda == TipoVenda.PRONTA_ENTREGA:
        if not data.item_compra_id:
            raise HTTPException(
                status_code=400,
                detail="Venda do tipo Pronta Entrega deve selecionar o lote de origem (item_compra_id)",
            )
        item_compra = (
            db.query(ItemCompra)
            .filter(ItemCompra.id == data.item_compra_id)
            .first()
        )
        if not item_compra:
            raise HTTPException(status_code=404, detail="ItemCompra não encontrado")

        if item_compra.quantidade_disponivel < data.quantidade_vendida:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente no lote. Disponível: {item_compra.quantidade_disponivel}, "
                f"solicitado: {data.quantidade_vendida}",
            )

        # Baixa no estoque
        item_compra.quantidade_disponivel -= data.quantidade_vendida

    item_venda = ItemVenda(
        venda_id=data.venda_id,
        item_compra_id=data.item_compra_id,
        quantidade_vendida=data.quantidade_vendida,
        valor_unitario_venda=data.valor_unitario_venda,
    )
    db.add(item_venda)
    db.commit()
    db.refresh(item_venda)
    return item_venda


def deletar_item_venda(db: Session, item_venda_id: int) -> None:
    item_venda = (
        db.query(ItemVenda)
        .filter(ItemVenda.id == item_venda_id)
        .first()
    )
    if not item_venda:
        raise HTTPException(status_code=404, detail="ItemVenda não encontrado")

    # Restaura estoque
    if item_venda.item_compra_id and item_venda.item_compra:
        item_venda.item_compra.quantidade_disponivel += item_venda.quantidade_vendida

    db.delete(item_venda)
    db.commit()


def listar_itens_venda(db: Session, venda_id: int) -> list[ItemVenda]:
    return (
        db.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda_id)
        .all()
    )


# ===================================================================
# DespesaGeral
# ===================================================================


def listar_despesas(db: Session) -> list[DespesaGeral]:
    return db.query(DespesaGeral).order_by(DespesaGeral.data_despesa.desc()).all()


def criar_despesa(db: Session, data: DespesaGeralCreate) -> DespesaGeral:
    despesa = DespesaGeral(**data.model_dump())
    db.add(despesa)
    db.commit()
    db.refresh(despesa)
    return despesa


def deletar_despesa(db: Session, despesa_id: int) -> None:
    despesa = db.query(DespesaGeral).filter(DespesaGeral.id == despesa_id).first()
    if not despesa:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    db.delete(despesa)
    db.commit()


# ===================================================================
# Reposição (Estoque Projetado)
# ===================================================================


def obter_reposicao(db: Session) -> list[ReposicaoRow]:
    """Agrupa por produto/tamanho e mostra o estoque futuro projetado."""
    # Pega todos os produtos
    produtos = db.query(Produto).order_by(Produto.name).all()
    rows: list[ReposicaoRow] = []

    from schemas import GRADES_TAMANHO

    for produto in produtos:
        tamanhos = GRADES_TAMANHO.get(produto.grade_tamanho, ["P", "M", "G", "GG"])
        for tamanho in tamanhos:
            # Soma por status do pedido
            qtd_entregue = (
                db.query(func.coalesce(func.sum(ItemCompra.quantidade_disponivel), 0))
                .join(PedidoCompra)
                .filter(
                    ItemCompra.produto_id == produto.id,
                    ItemCompra.tamanho == tamanho,
                    PedidoCompra.status == StatusPedidoCompra.ENTREGUE,
                )
                .scalar()
            ) or 0

            qtd_comprado = (
                db.query(func.coalesce(func.sum(ItemCompra.quantidade_comprada), 0))
                .join(PedidoCompra)
                .filter(
                    ItemCompra.produto_id == produto.id,
                    ItemCompra.tamanho == tamanho,
                    PedidoCompra.status == StatusPedidoCompra.COMPRADO,
                )
                .scalar()
            ) or 0

            qtd_em_transito = (
                db.query(func.coalesce(func.sum(ItemCompra.quantidade_comprada), 0))
                .join(PedidoCompra)
                .filter(
                    ItemCompra.produto_id == produto.id,
                    ItemCompra.tamanho == tamanho,
                    PedidoCompra.status == StatusPedidoCompra.EM_TRANSITO_PRE_TAXA,
                )
                .scalar()
            ) or 0

            qtd_chegando = (
                db.query(func.coalesce(func.sum(ItemCompra.quantidade_comprada), 0))
                .join(PedidoCompra)
                .filter(
                    ItemCompra.produto_id == produto.id,
                    ItemCompra.tamanho == tamanho,
                    PedidoCompra.status == StatusPedidoCompra.CHEGANDO_POS_TAXA,
                )
                .scalar()
            ) or 0

            total = qtd_entregue + qtd_comprado + qtd_em_transito + qtd_chegando
            if total > 0 or qtd_entregue > 0:
                rows.append(
                    ReposicaoRow(
                        produto_id=produto.id,
                        produto_nome=produto.name,
                        produto_team=produto.team,
                        tamanho=tamanho,
                        qtd_entregue=qtd_entregue,
                        qtd_comprado=qtd_comprado,
                        qtd_em_transito=qtd_em_transito,
                        qtd_chegando=qtd_chegando,
                        qtd_total_futuro=total,
                    )
                )

    return rows


# ===================================================================
# Dashboard
# ===================================================================


def obter_dashboard(db: Session) -> DashboardResponse:
    # Todos os itens de venda
    itens_venda = db.query(ItemVenda).all()
    total_itens = sum(iv.quantidade_vendida for iv in itens_venda)

    # Faturamento bruto
    faturamento_bruto = sum(
        iv.valor_unitario_venda * iv.quantidade_vendida for iv in itens_venda
    )

    # Detalhes de lucro
    detalhes: list[LucroItemDetail] = []
    vendas_por_time: dict[str, float] = {}
    lucro_total = 0.0
    total_despesas_venda = 0.0

    # IDs únicos de venda
    venda_ids = set(iv.venda_id for iv in itens_venda)
    total_vendas = len(venda_ids)

    for iv in itens_venda:
        detalhe = calcular_lucro_item_venda(iv, db)
        lucro_total += detalhe["lucro"]
        total_despesas_venda += detalhe["despesa_rateada"]

        # Agrega vendas por time
        team = detalhe["produto_team"]
        if team:
            vendas_por_time[team] = vendas_por_time.get(team, 0.0) + detalhe["valor_venda"]

        detalhes.append(LucroItemDetail(**detalhe))

    # Despesas gerais
    despesas_gerais = db.query(DespesaGeral).all()
    total_despesas_gerais = sum(d.valor for d in despesas_gerais)

    # Lucro líquido final
    lucro_liquido_total = round(lucro_total - total_despesas_gerais, 2)

    # Estoque parado: soma de quantidade_disponivel onde status == ENTREGUE
    itens_estoque = (
        db.query(ItemCompra)
        .join(PedidoCompra)
        .filter(
            ItemCompra.quantidade_disponivel > 0,
            PedidoCompra.status == StatusPedidoCompra.ENTREGUE,
        )
        .all()
    )
    pecas_em_estoque = sum(i.quantidade_disponivel for i in itens_estoque)
    custo_estoque_parado = 0.0
    for i in itens_estoque:
        custo_real_unit = calcular_custo_real(i.id, db)
        custo_estoque_parado += custo_real_unit * i.quantidade_disponivel

    return DashboardResponse(
        faturamento_bruto=round(faturamento_bruto, 2),
        lucro_liquido_total=lucro_liquido_total,
        total_vendas=total_vendas,
        total_itens_vendidos=total_itens,
        total_despesas_gerais=round(total_despesas_gerais, 2),
        total_despesas_venda=round(total_despesas_venda, 2),
        pecas_em_estoque=pecas_em_estoque,
        custo_estoque_parado=round(custo_estoque_parado, 2),
        detalhes_lucro=detalhes,
        faturamento_por_time=vendas_por_time,
    )


# ===================================================================
# Site - Produtos públicos
# ===================================================================


def listar_produtos_site(db: Session) -> list[dict]:
    """Retorna produtos com estoque disponível (soma de itens entregues)."""
    produtos = db.query(Produto).all()
    resultado = []
    for produto in produtos:
        # Estoque dinâmico: soma de quantidade_disponivel onde status == ENTREGUE
        qtd_total = (
            db.query(func.coalesce(func.sum(ItemCompra.quantidade_disponivel), 0))
            .join(PedidoCompra)
            .filter(
                ItemCompra.produto_id == produto.id,
                PedidoCompra.status == StatusPedidoCompra.ENTREGUE,
            )
            .scalar()
        ) or 0

        if qtd_total <= 0:
            continue

        imagens = (
            produto.cloudinary_images.split(",")
            if produto.cloudinary_images
            else []
        )
        imagens = [img.strip() for img in imagens if img.strip()]

        resultado.append(
            {
                "name": produto.name,
                "category": produto.category,
                "league": produto.league,
                "type": produto.type,
                "team": produto.team,
                "cloudinaryImages": imagens,
            }
        )
    return resultado


# ===================================================================
# Relatórios
# ===================================================================


def obter_estoque_atual_por_produto(db: Session) -> list[dict]:
    """Estoque dinâmico agrupado por produto."""
    produtos = db.query(Produto).order_by(Produto.name).all()
    resultado = []
    for produto in produtos:
        from schemas import GRADES_TAMANHO

        tamanhos = GRADES_TAMANHO.get(produto.grade_tamanho, ["P", "M", "G", "GG"])
        estoques = {}
        for tam in tamanhos:
            qtd = (
                db.query(func.coalesce(func.sum(ItemCompra.quantidade_disponivel), 0))
                .join(PedidoCompra)
                .filter(
                    ItemCompra.produto_id == produto.id,
                    ItemCompra.tamanho == tam,
                    PedidoCompra.status == StatusPedidoCompra.ENTREGUE,
                )
                .scalar()
            ) or 0
            if qtd > 0:
                estoques[tam] = qtd

        if estoques:
            resultado.append(
                {
                    "produto_id": produto.id,
                    "produto_nome": produto.name,
                    "produto_team": produto.team,
                    "grade": produto.grade_tamanho,
                    "estoques": estoques,
                }
            )
    return resultado
