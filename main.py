from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, init_db
from crud import (
    atualizar_item_compra,
    atualizar_pedido_compra,
    atualizar_produto,
    atualizar_status_venda,
    atualizar_venda,
    calcular_custo_real,
    criar_despesa,
    criar_item_compra,
    criar_item_venda,
    criar_pedido_compra,
    criar_produto,
    criar_venda,
    deletar_despesa,
    deletar_item_compra,
    deletar_item_venda,
    deletar_pedido_compra,
    deletar_produto,
    deletar_venda,
    listar_despesas,
    listar_itens_compra,
    listar_itens_venda,
    listar_pedidos_compra,
    listar_produtos,
    listar_produtos_site,
    listar_vendas,
    obter_dashboard,
    obter_estoque_atual_por_produto,
    obter_itens_disponiveis_dropshipping,
    obter_itens_disponiveis_para_venda,
    obter_pedido_compra,
    obter_produto,
    obter_reposicao,
    obter_venda,
)
from schemas import (
    DashboardResponse,
    DespesaGeralCreate,
    DespesaGeralResponse,
    ItemCompraCreate,
    ItemCompraResponse,
    ItemCompraUpdate,
    ItemVendaCreate,
    ItemVendaResponse,
    PedidoCompraCreate,
    PedidoCompraResponse,
    PedidoCompraUpdate,
    ProdutoCreate,
    ProdutoResponse,
    ProdutoUpdate,
    ReposicaoRow,
    VendaCreate,
    VendaResponse,
    VendaStatusUpdate,
    VendaUpdate,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Estoque Veloso Imports ERP API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


# ===================================================================
# Produto (Catálogo)
# ===================================================================


@app.get("/api/v1/produtos", response_model=list[ProdutoResponse])
def get_produtos(db: Session = Depends(get_db)):
    return listar_produtos(db)


@app.get("/api/v1/produtos/{produto_id}", response_model=ProdutoResponse)
def get_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = obter_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


@app.post("/api/v1/produtos", response_model=ProdutoResponse, status_code=201)
def post_produto(data: ProdutoCreate, db: Session = Depends(get_db)):
    return criar_produto(db, data)


@app.put("/api/v1/produtos/{produto_id}", response_model=ProdutoResponse)
def put_produto(produto_id: int, data: ProdutoUpdate, db: Session = Depends(get_db)):
    return atualizar_produto(db, produto_id, data)


@app.delete("/api/v1/produtos/{produto_id}", status_code=204)
def delete_produto(produto_id: int, db: Session = Depends(get_db)):
    deletar_produto(db, produto_id)


# ===================================================================
# PedidoCompra
# ===================================================================


@app.get("/api/v1/pedidos-compra", response_model=list[PedidoCompraResponse])
def get_pedidos_compra(db: Session = Depends(get_db)):
    pedidos = listar_pedidos_compra(db)
    result = []
    for p in pedidos:
        total_qtd = sum(i.quantidade_comprada for i in p.itens)
        total_custo = sum(i.valor_unitario_compra * i.quantidade_comprada for i in p.itens)
        result.append(
            PedidoCompraResponse(
                id=p.id,
                tipo=p.tipo.value if hasattr(p.tipo, "value") else p.tipo,
                data_pedido=p.data_pedido,
                status=p.status.value if hasattr(p.status, "value") else p.status,
                taxa_importacao=p.taxa_importacao,
                frete=p.frete,
                nome_identificador=p.nome_identificador,
                codigo_rastreio=p.codigo_rastreio,
                qtd_itens=len(p.itens),
                total_quantidade=total_qtd,
                total_custo=round(total_custo, 2),
            )
        )
    return result


@app.get("/api/v1/pedidos-compra/{pedido_id}", response_model=PedidoCompraResponse)
def get_pedido_compra(pedido_id: int, db: Session = Depends(get_db)):
    p = obter_pedido_compra(db, pedido_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    total_qtd = sum(i.quantidade_comprada for i in p.itens)
    total_custo = sum(i.valor_unitario_compra * i.quantidade_comprada for i in p.itens)
    return PedidoCompraResponse(
        id=p.id,
        tipo=p.tipo.value if hasattr(p.tipo, "value") else p.tipo,
        data_pedido=p.data_pedido,
        status=p.status.value if hasattr(p.status, "value") else p.status,
        taxa_importacao=p.taxa_importacao,
        frete=p.frete,
        nome_identificador=p.nome_identificador,
        codigo_rastreio=p.codigo_rastreio,
        qtd_itens=len(p.itens),
        total_quantidade=total_qtd,
        total_custo=round(total_custo, 2),
    )


@app.post("/api/v1/pedidos-compra", response_model=PedidoCompraResponse, status_code=201)
def post_pedido_compra(data: PedidoCompraCreate, db: Session = Depends(get_db)):
    pedido = criar_pedido_compra(db, data)
    return PedidoCompraResponse(
        id=pedido.id,
        tipo=pedido.tipo.value if hasattr(pedido.tipo, "value") else pedido.tipo,
        data_pedido=pedido.data_pedido,
        status=pedido.status.value if hasattr(pedido.status, "value") else pedido.status,
        taxa_importacao=pedido.taxa_importacao,
        frete=pedido.frete,
        nome_identificador=pedido.nome_identificador,
        codigo_rastreio=pedido.codigo_rastreio,
        qtd_itens=0,
        total_quantidade=0,
        total_custo=0.0,
    )


@app.put("/api/v1/pedidos-compra/{pedido_id}", response_model=PedidoCompraResponse)
def put_pedido_compra(
    pedido_id: int, data: PedidoCompraUpdate, db: Session = Depends(get_db)
):
    p = atualizar_pedido_compra(db, pedido_id, data)
    total_qtd = sum(i.quantidade_comprada for i in p.itens)
    total_custo = sum(i.valor_unitario_compra * i.quantidade_comprada for i in p.itens)
    return PedidoCompraResponse(
        id=p.id,
        tipo=p.tipo.value if hasattr(p.tipo, "value") else p.tipo,
        data_pedido=p.data_pedido,
        status=p.status.value if hasattr(p.status, "value") else p.status,
        taxa_importacao=p.taxa_importacao,
        frete=p.frete,
        nome_identificador=p.nome_identificador,
        codigo_rastreio=p.codigo_rastreio,
        qtd_itens=len(p.itens),
        total_quantidade=total_qtd,
        total_custo=round(total_custo, 2),
    )


@app.delete("/api/v1/pedidos-compra/{pedido_id}", status_code=204)
def delete_pedido_compra(pedido_id: int, db: Session = Depends(get_db)):
    deletar_pedido_compra(db, pedido_id)


# ===================================================================
# ItemCompra (itens de um pedido)
# ===================================================================


@app.get(
    "/api/v1/pedidos-compra/{pedido_id}/itens",
    response_model=list[ItemCompraResponse],
)
def get_itens_compra(pedido_id: int, db: Session = Depends(get_db)):
    itens = listar_itens_compra(db, pedido_id)
    result = []
    for item in itens:
        produto_nome = item.produto.name if item.produto else ""
        produto_team = item.produto.team if item.produto else ""
        result.append(
            ItemCompraResponse(
                id=item.id,
                pedido_compra_id=item.pedido_compra_id,
                produto_id=item.produto_id,
                tamanho=item.tamanho,
                quantidade_comprada=item.quantidade_comprada,
                quantidade_disponivel=item.quantidade_disponivel,
                valor_unitario_compra=item.valor_unitario_compra,
                produto_nome=produto_nome,
                produto_team=produto_team,
            )
        )
    return result


@app.post(
    "/api/v1/pedidos-compra/{pedido_id}/itens",
    response_model=ItemCompraResponse,
    status_code=201,
)
def post_item_compra(
    pedido_id: int, data: ItemCompraCreate, db: Session = Depends(get_db)
):
    item = criar_item_compra(db, pedido_id, data)
    produto_nome = item.produto.name if item.produto else ""
    produto_team = item.produto.team if item.produto else ""
    return ItemCompraResponse(
        id=item.id,
        pedido_compra_id=item.pedido_compra_id,
        produto_id=item.produto_id,
        tamanho=item.tamanho,
        quantidade_comprada=item.quantidade_comprada,
        quantidade_disponivel=item.quantidade_disponivel,
        valor_unitario_compra=item.valor_unitario_compra,
        produto_nome=produto_nome,
        produto_team=produto_team,
    )


@app.put("/api/v1/itens-compra/{item_id}", response_model=ItemCompraResponse)
def put_item_compra(item_id: int, data: ItemCompraUpdate, db: Session = Depends(get_db)):
    item = atualizar_item_compra(db, item_id, data)
    produto_nome = item.produto.name if item.produto else ""
    produto_team = item.produto.team if item.produto else ""
    return ItemCompraResponse(
        id=item.id,
        pedido_compra_id=item.pedido_compra_id,
        produto_id=item.produto_id,
        tamanho=item.tamanho,
        quantidade_comprada=item.quantidade_comprada,
        quantidade_disponivel=item.quantidade_disponivel,
        valor_unitario_compra=item.valor_unitario_compra,
        produto_nome=produto_nome,
        produto_team=produto_team,
    )


@app.delete("/api/v1/itens-compra/{item_id}", status_code=204)
def delete_item_compra(item_id: int, db: Session = Depends(get_db)):
    deletar_item_compra(db, item_id)


# ===================================================================
# Itens disponíveis para venda (lote tracking)
# ===================================================================


@app.get("/api/v1/itens-disponiveis")
def get_itens_disponiveis(
    produto_id: int, tamanho: str, db: Session = Depends(get_db)
):
    itens = obter_itens_disponiveis_para_venda(db, produto_id, tamanho)
    result = []
    for item in itens:
        pedido = item.pedido_compra
        nome_ped = pedido.nome_identificador or f"Pedido #{pedido.id}" if pedido else "N/A"
        result.append(
            {
                "id": item.id,
                "pedido_compra_id": item.pedido_compra_id,
                "lote_label": f"[{nome_ped}] - {item.produto.name} - Tam: {item.tamanho}",
                "produto_nome": item.produto.name if item.produto else "",
                "tamanho": item.tamanho,
                "quantidade_disponivel": item.quantidade_disponivel,
                "valor_unitario_compra": item.valor_unitario_compra,
                "custo_real": calcular_custo_real(item.id, db),
            }
        )
    return result


@app.get("/api/v1/itens-dropshipping")
def get_itens_dropshipping(
    produto_id: int, tamanho: str, db: Session = Depends(get_db)
):
    itens = obter_itens_disponiveis_dropshipping(db, produto_id, tamanho)
    result = []
    for item in itens:
        pedido = item.pedido_compra
        nome_pedido = pedido.nome_identificador or f"Pedido #{pedido.id}"
        result.append(
            {
                "id": item.id,
                "pedido_compra_id": item.pedido_compra_id,
                "lote_label": f"[{nome_pedido}] - {item.produto.name} - Tam: {item.tamanho}",
                "produto_nome": item.produto.name if item.produto else "",
                "tamanho": item.tamanho,
                "quantidade_disponivel": item.quantidade_disponivel,
                "valor_unitario_compra": item.valor_unitario_compra,
                "custo_real": calcular_custo_real(item.id, db),
            }
        )
    return result


# ===================================================================
# Venda
# ===================================================================


@app.get("/api/v1/vendas", response_model=list[VendaResponse])
def get_vendas(db: Session = Depends(get_db)):
    vendas = listar_vendas(db)
    result = []
    for v in vendas:
        total_bruto = sum(
            iv.valor_unitario_venda * iv.quantidade_vendida for iv in v.itens
        )
        result.append(
            VendaResponse(
                id=v.id,
                data_venda=v.data_venda,
                tipo_venda=v.tipo_venda.value if hasattr(v.tipo_venda, "value") else v.tipo_venda,
                forma_pagamento=v.forma_pagamento,
                taxa_pagamento_percentual=v.taxa_pagamento_percentual,
                despesa_venda_extra=v.despesa_venda_extra,
                cliente_nome=v.cliente_nome,
                cliente_telefone=v.cliente_telefone,
                status_pagamento=v.status_pagamento,
                total_bruto=round(total_bruto, 2),
                total_itens=len(v.itens),
            )
        )
    return result


@app.get("/api/v1/vendas/{venda_id}", response_model=VendaResponse)
def get_venda(venda_id: int, db: Session = Depends(get_db)):
    v = obter_venda(db, venda_id)
    if not v:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    total_bruto = sum(
        iv.valor_unitario_venda * iv.quantidade_vendida for iv in v.itens
    )
    return VendaResponse(
        id=v.id,
        data_venda=v.data_venda,
        tipo_venda=v.tipo_venda.value if hasattr(v.tipo_venda, "value") else v.tipo_venda,
        forma_pagamento=v.forma_pagamento,
        taxa_pagamento_percentual=v.taxa_pagamento_percentual,
        despesa_venda_extra=v.despesa_venda_extra,
        total_bruto=round(total_bruto, 2),
        total_itens=len(v.itens),
    )


@app.post("/api/v1/vendas", response_model=VendaResponse, status_code=201)
def post_venda(data: VendaCreate, db: Session = Depends(get_db)):
    venda = criar_venda(db, data)
    return VendaResponse(
        id=venda.id,
        data_venda=venda.data_venda,
        tipo_venda=venda.tipo_venda.value if hasattr(venda.tipo_venda, "value") else venda.tipo_venda,
        forma_pagamento=venda.forma_pagamento,
        taxa_pagamento_percentual=venda.taxa_pagamento_percentual,
        despesa_venda_extra=venda.despesa_venda_extra,
        cliente_nome=venda.cliente_nome,
        cliente_telefone=venda.cliente_telefone,
        status_pagamento=venda.status_pagamento,
        total_bruto=0.0,
        total_itens=0,
    )


@app.put("/api/v1/vendas/{venda_id}", response_model=VendaResponse)
def put_venda(venda_id: int, data: VendaUpdate, db: Session = Depends(get_db)):
    v = atualizar_venda(db, venda_id, data)
    total_bruto = sum(
        iv.valor_unitario_venda * iv.quantidade_vendida for iv in v.itens
    )
    return VendaResponse(
        id=v.id,
        data_venda=v.data_venda,
        tipo_venda=v.tipo_venda.value if hasattr(v.tipo_venda, "value") else v.tipo_venda,
        forma_pagamento=v.forma_pagamento,
        taxa_pagamento_percentual=v.taxa_pagamento_percentual,
        despesa_venda_extra=v.despesa_venda_extra,
        total_bruto=round(total_bruto, 2),
        total_itens=len(v.itens),
    )


@app.delete("/api/v1/vendas/{venda_id}", status_code=204)
def delete_venda(venda_id: int, db: Session = Depends(get_db)):
    deletar_venda(db, venda_id)


@app.put("/api/v1/vendas/{venda_id}/status", response_model=VendaResponse)
def put_venda_status(
    venda_id: int, data: VendaStatusUpdate, db: Session = Depends(get_db)
):
    venda = atualizar_status_venda(db, venda_id, data.status_pagamento)
    total_bruto = sum(
        iv.valor_unitario_venda * iv.quantidade_vendida for iv in venda.itens
    )
    return VendaResponse(
        id=venda.id,
        data_venda=venda.data_venda,
        tipo_venda=venda.tipo_venda.value if hasattr(venda.tipo_venda, "value") else venda.tipo_venda,
        forma_pagamento=venda.forma_pagamento,
        taxa_pagamento_percentual=venda.taxa_pagamento_percentual,
        despesa_venda_extra=venda.despesa_venda_extra,
        cliente_nome=venda.cliente_nome,
        cliente_telefone=venda.cliente_telefone,
        status_pagamento=venda.status_pagamento,
        total_bruto=round(total_bruto, 2),
        total_itens=len(venda.itens),
    )


# ===================================================================
# ItemVenda
# ===================================================================


@app.get(
    "/api/v1/vendas/{venda_id}/itens",
    response_model=list[ItemVendaResponse],
)
def get_itens_venda(venda_id: int, db: Session = Depends(get_db)):
    itens = listar_itens_venda(db, venda_id)
    result = []
    for iv in itens:
        from crud import calcular_lucro_item_venda
        lucro_info = calcular_lucro_item_venda(iv, db)
        item_compra = iv.item_compra
        produto_nome = ""
        produto_team = ""
        tamanho = ""
        lote_origem = ""
        custo_real = 0.0
        if item_compra:
            produto_nome = item_compra.produto.name if item_compra.produto else ""
            produto_team = item_compra.produto.team if item_compra.produto else ""
            tamanho = item_compra.tamanho
            pedido = item_compra.pedido_compra
            if pedido:
                lote_origem = f"Pedido #{pedido.id} - {pedido.tipo.value}"
        result.append(
            ItemVendaResponse(
                id=iv.id,
                venda_id=iv.venda_id,
                item_compra_id=iv.item_compra_id,
                quantidade_vendida=iv.quantidade_vendida,
                valor_unitario_venda=iv.valor_unitario_venda,
                produto_nome=produto_nome,
                produto_team=produto_team,
                tamanho=tamanho,
                lote_origem=lote_origem,
                custo_real_unitario=round(
                    lucro_info["custo_real"] / iv.quantidade_vendida, 2
                )
                if iv.quantidade_vendida
                else 0.0,
                lucro_unitario=lucro_info["lucro"] / iv.quantidade_vendida
                if iv.quantidade_vendida
                else 0.0,
                lucro_total=lucro_info["lucro"],
            )
        )
    return result


@app.post(
    "/api/v1/vendas/{venda_id}/itens",
    response_model=ItemVendaResponse,
    status_code=201,
)
def post_item_venda(
    venda_id: int, data: ItemVendaCreate, db: Session = Depends(get_db)
):
    data.venda_id = venda_id
    iv = criar_item_venda(db, data)
    from crud import calcular_lucro_item_venda
    lucro_info = calcular_lucro_item_venda(iv, db)
    item_compra = iv.item_compra
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
            lote_origem = f"Pedido #{pedido.id} - {pedido.tipo.value}"
    return ItemVendaResponse(
        id=iv.id,
        venda_id=iv.venda_id,
        item_compra_id=iv.item_compra_id,
        quantidade_vendida=iv.quantidade_vendida,
        valor_unitario_venda=iv.valor_unitario_venda,
        produto_nome=produto_nome,
        produto_team=produto_team,
        tamanho=tamanho,
        lote_origem=lote_origem,
        custo_real_unitario=round(
            lucro_info["custo_real"] / iv.quantidade_vendida, 2
        )
        if iv.quantidade_vendida
        else 0.0,
        lucro_unitario=lucro_info["lucro"] / iv.quantidade_vendida
        if iv.quantidade_vendida
        else 0.0,
        lucro_total=lucro_info["lucro"],
    )


@app.delete("/api/v1/itens-venda/{item_venda_id}", status_code=204)
def delete_item_venda(item_venda_id: int, db: Session = Depends(get_db)):
    deletar_item_venda(db, item_venda_id)


# ===================================================================
# DespesaGeral
# ===================================================================


@app.get("/api/v1/despesas", response_model=list[DespesaGeralResponse])
def get_despesas(db: Session = Depends(get_db)):
    return listar_despesas(db)


@app.post("/api/v1/despesas", response_model=DespesaGeralResponse, status_code=201)
def post_despesa(data: DespesaGeralCreate, db: Session = Depends(get_db)):
    return criar_despesa(db, data)


@app.delete("/api/v1/despesas/{despesa_id}", status_code=204)
def delete_despesa(despesa_id: int, db: Session = Depends(get_db)):
    deletar_despesa(db, despesa_id)


# ===================================================================
# Reposição
# ===================================================================


@app.get("/api/v1/reposicao", response_model=list[ReposicaoRow])
def get_reposicao(db: Session = Depends(get_db)):
    return obter_reposicao(db)


# ===================================================================
# Dashboard
# ===================================================================


@app.get("/api/v1/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    return obter_dashboard(db)


# ===================================================================
# Site - endpoint público
# ===================================================================


@app.get("/api/v1/site/produtos")
def get_produtos_site(db: Session = Depends(get_db)):
    return listar_produtos_site(db)


# ===================================================================
# Estoque atual (relatório simplificado)
# ===================================================================


@app.get("/api/v1/estoque-atual")
def get_estoque_atual(db: Session = Depends(get_db)):
    return obter_estoque_atual_por_produto(db)


# ===================================================================
# Entrypoint
# ===================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
