from __future__ import annotations

import os
from datetime import date, datetime

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

GRADES_TAMANHO = {
    "Masculino": ["P", "M", "G", "GG", "2XL", "3XL", "4XL"],
    "Feminino": ["P", "M", "G", "GG"],
    "Infantil": ["14", "16", "18", "20", "22", "24", "26", "28"],
}

CATEGORY_GRADE_MAP = {
    "Feminina": "Feminino",
    "Infantil": "Infantil",
}

CATEGORIAS = ["Brasileirão Série A", "Europa", "Feminina", "Seleções", "Infantil"]

STATUS_PEDIDO_OPTS = [
    "COMPRADO",
    "EM TRÂNSITO (PRÉ TAXA)",
    "CHEGANDO (APÓS PAGAMENTO DA TAXA)",
    "ENTREGUE",
]


def get_grade_from_category(category: str) -> str:
    return CATEGORY_GRADE_MAP.get(category, "Masculino")


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def api_get(path: str) -> dict | list | None:
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=10)
        resp.raise_for_status()
        return resp.json() if resp.status_code != 204 else None
    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao servidor FastAPI. Execute `python main.py` primeiro.")
        st.stop()
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
        st.error(f"Erro {e.response.status_code}: {detail}")
        return None


def api_post(path: str, data: dict) -> dict | list | None:
    try:
        resp = requests.post(f"{API_BASE}{path}", json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao servidor FastAPI.")
        st.stop()
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
        st.error(f"Erro {e.response.status_code}: {detail}")
        return None


def api_put(path: str, data: dict) -> dict | list | None:
    try:
        resp = requests.put(f"{API_BASE}{path}", json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao servidor FastAPI.")
        st.stop()
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
        st.error(f"Erro {e.response.status_code}: {detail}")
        return None


def api_delete(path: str) -> bool:
    try:
        resp = requests.delete(f"{API_BASE}{path}", timeout=10)
        resp.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao servidor FastAPI.")
        st.stop()
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
        st.error(f"Erro {e.response.status_code}: {detail}")
        return False


# ===================================================================
# PÁGINA 1 — Catálogo de Produtos
# ===================================================================

def page_catalogo():
    st.header("Catálogo de Produtos")

    with st.expander("Cadastrar Novo Produto", expanded=False):
        with st.form("form_produto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nome do Produto")
                team = st.text_input("Time")
                league = st.text_input("Liga")
                type_ = st.text_input("Tipo (ex: Camisa Jogador, Treino)")
            with col2:
                category = st.selectbox("Categoria", CATEGORIAS, key="prod_category")
                grade = get_grade_from_category(category)
                grade_tamanho = st.selectbox(
                    "Grade de Tamanho",
                    list(GRADES_TAMANHO.keys()),
                    index=list(GRADES_TAMANHO.keys()).index(grade),
                )
                st.caption("Tamanhos: " + ", ".join(GRADES_TAMANHO[grade_tamanho]))

            st.subheader("Imagens Cloudinary")
            urls = []
            for i in range(5):
                url = st.text_input(f"URL {i+1}", key=f"cloud_{i}")
                urls.append(url.strip())
            cloudinary_str = ",".join(u for u in urls if u)

            submitted = st.form_submit_button("Salvar Produto")
            if submitted and name and team:
                payload = {
                    "name": name,
                    "team": team,
                    "league": league,
                    "type": type_,
                    "category": category,
                    "grade_tamanho": grade_tamanho,
                    "cloudinary_images": cloudinary_str,
                }
                result = api_post("/produtos", payload)
                if result:
                    st.success(f"Produto '{name}' cadastrado com sucesso!")
                    st.rerun()
            elif submitted:
                st.warning("Preencha Nome e Time do produto.")

    # --- Editar produto existente ---
    with st.expander("Editar Produto", expanded=False):
        produtos = api_get("/produtos")
        if not produtos:
            st.info("Nenhum produto cadastrado para editar.")
        else:
            prod_opts = {p["id"]: f"#{p['id']} {p['name']} - {p['team']}" for p in produtos}
            edit_prod_id = st.selectbox(
                "Selecionar Produto",
                options=list(prod_opts.keys()),
                format_func=lambda x: prod_opts.get(x, ""),
                key="edit_prod_select",
            )
            prod_atual = next((p for p in produtos if p["id"] == edit_prod_id), None)

            if prod_atual:
                with st.form("form_edit_produto"):
                    col1, col2 = st.columns(2)
                    with col1:
                        e_name = st.text_input("Nome do Produto", value=prod_atual.get("name", ""))
                        e_team = st.text_input("Time", value=prod_atual.get("team", ""))
                        e_league = st.text_input("Liga", value=prod_atual.get("league", ""))
                        e_type = st.text_input("Tipo", value=prod_atual.get("type", ""))
                    with col2:
                        cat_index = 0
                        if prod_atual.get("category") in CATEGORIAS:
                            cat_index = CATEGORIAS.index(prod_atual["category"])
                        e_category = st.selectbox("Categoria", CATEGORIAS, index=cat_index, key="edit_cat")
                        e_grade = get_grade_from_category(e_category) if e_category else "Masculino"
                        grade_opts = list(GRADES_TAMANHO.keys())
                        gr_index = 0
                        if prod_atual.get("grade_tamanho") in grade_opts:
                            gr_index = grade_opts.index(prod_atual["grade_tamanho"])
                        e_grade_tamanho = st.selectbox(
                            "Grade de Tamanho", grade_opts, index=gr_index, key="edit_grade"
                        )
                        st.caption("Tamanhos: " + ", ".join(GRADES_TAMANHO[e_grade_tamanho]))

                    st.subheader("Imagens Cloudinary")
                    imagens_atuais = []
                    raw = prod_atual.get("cloudinary_images", "") or ""
                    if raw:
                        imagens_atuais = [img.strip() for img in raw.split(",") if img.strip()]
                    e_urls = []
                    for i in range(5):
                        val = imagens_atuais[i] if i < len(imagens_atuais) else ""
                        url = st.text_input(f"URL {i+1}", value=val, key=f"edit_cloud_{i}")
                        e_urls.append(url.strip())
                    e_cloudinary_str = ",".join(u for u in e_urls if u)

                    submitted = st.form_submit_button("Salvar Alterações")
                    if submitted and e_name and e_team:
                        payload = {
                            "name": e_name,
                            "team": e_team,
                            "league": e_league,
                            "type": e_type,
                            "category": e_category,
                            "grade_tamanho": e_grade_tamanho,
                            "cloudinary_images": e_cloudinary_str,
                        }
                        result = api_put(f"/produtos/{edit_prod_id}", payload)
                        if result:
                            st.success(f"Produto '{e_name}' atualizado com sucesso!")
                            st.rerun()
                    elif submitted:
                        st.warning("Preencha Nome e Time do produto.")

    st.subheader("Produtos Cadastrados")
    produtos = api_get("/produtos")
    if not produtos:
        st.info("Nenhum produto cadastrado.")
        return

    for prod in produtos:
        with st.container(border=True):
            cols = st.columns([3, 2, 2, 1])
            cols[0].write(f"**#{prod['id']} - {prod['name']}** ({prod['team']})")
            cols[1].write(f"Categoria: {prod['category']} | Grade: {prod['grade_tamanho']}")
            cols[2].write(f"Liga: {prod['league']} | Tipo: {prod['type']}")

            with cols[3]:
                if st.button("\U0001f5d1\ufe0f", key=f"del_prod_{prod['id']}", help="Excluir"):
                    if api_delete(f"/produtos/{prod['id']}"):
                        st.success("Produto excluído.")
                        st.rerun()

            if prod.get("cloudinary_images"):
                imagens = [img.strip() for img in prod["cloudinary_images"].split(",") if img.strip()]
                if imagens:
                    st.caption(f"Imagens: {len(imagens)} vinculada(s)")


# ===================================================================
# PÁGINA 2 — Compras e Drop
# ===================================================================

def page_compras():
    st.header("Compras e Drop")
    st.caption("Pedidos de compra, dropshipping e gestão de lotes.")

    # --- Criar novo pedido ---
    with st.expander("Novo Pedido de Compra", expanded=False):
        with st.form("form_pedido", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.selectbox("Tipo", ["Lote Físico", "Dropshipping"])
                data_pedido = st.date_input("Data do Pedido", value=date.today())
                nome_id = st.text_input("Nome/Identificador do Pedido")
            with col2:
                status = st.selectbox("Status", STATUS_PEDIDO_OPTS)
                taxa = st.number_input("Taxa de Importação (R$)", min_value=0.0, step=10.0, format="%.2f")
                frete = st.number_input("Frete (R$)", min_value=0.0, step=10.0, format="%.2f")
                cod_rastreio = st.text_input("Código de Rastreio")

            if st.form_submit_button("Criar Pedido"):
                payload = {
                    "tipo": tipo,
                    "data_pedido": data_pedido.isoformat(),
                    "status": status,
                    "taxa_importacao": taxa,
                    "frete": frete,
                    "nome_identificador": nome_id if nome_id else None,
                    "codigo_rastreio": cod_rastreio if cod_rastreio else None,
                }
                result = api_post("/pedidos-compra", payload)
                if result:
                    st.success(f"Pedido #{result['id']} criado com sucesso!")
                    st.rerun()

    # --- Lista de pedidos ---
    pedidos = api_get("/pedidos-compra")
    if not pedidos:
        st.info("Nenhum pedido de compra cadastrado.")
        return

    for pedido in pedidos:
        pedido_id = pedido["id"]
        with st.container(border=True):
            nome_label = pedido.get("nome_identificador") or ""
            titulo = pedido_id
            if nome_label:
                titulo = f"{pedido_id} - {nome_label}"
            cols = st.columns([1.5, 2, 2, 2, 2, 1, 1])
            cols[0].write(f"**#{titulo}**")
            cols[1].write(f"Tipo: {pedido['tipo']}")
            cols[2].write(f"Data: {pedido['data_pedido']}")
            cols[3].write(f"Status: {pedido['status']}")
            cols[4].write(f"Itens: {pedido['qtd_itens']} ({pedido['total_quantidade']} un)")
            total_custo_val = pedido['total_custo']
            cols[5].write(f"Custo: R$ {total_custo_val:.2f}")
            taxa_val = pedido['taxa_importacao']
            frete_val = pedido['frete']
            rastreio_val = pedido.get("codigo_rastreio") or None
            if rastreio_val:
                cols[6].write(f"Rastreio: {rastreio_val}")
            else:
                cols[6].write(f"Taxa: R$ {taxa_val:.2f} | Frete: R$ {frete_val:.2f}")

            # Botão expandir detalhes
            with st.expander(f"Editar Pedido #{pedido_id} e Gerenciar Itens", expanded=False):
                # Editar cabeçalho
                with st.form(f"edit_pedido_{pedido_id}"):
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        edit_tipo = st.selectbox(
                            "Tipo",
                            ["Lote Físico", "Dropshipping"],
                            index=0 if pedido["tipo"] == "Lote Físico" else 1,
                            key=f"tipo_{pedido_id}",
                        )
                        edit_status = st.selectbox(
                            "Status",
                            STATUS_PEDIDO_OPTS,
                            index=STATUS_PEDIDO_OPTS.index(pedido["status"]),
                            key=f"status_{pedido_id}",
                        )
                        edit_data = st.date_input(
                            "Data",
                            value=date.fromisoformat(pedido["data_pedido"]),
                            key=f"data_{pedido_id}",
                        )
                        edit_nome = st.text_input(
                            "Nome/Identificador",
                            value=pedido.get("nome_identificador") or "",
                            key=f"nome_{pedido_id}",
                        )
                    with sc2:
                        edit_taxa = st.number_input(
                            "Taxa Importação (R$)",
                            value=float(pedido["taxa_importacao"]),
                            min_value=0.0,
                            step=10.0,
                            format="%.2f",
                            key=f"taxa_{pedido_id}",
                        )
                        edit_frete = st.number_input(
                            "Frete (R$)",
                            value=float(pedido["frete"]),
                            min_value=0.0,
                            step=10.0,
                            format="%.2f",
                            key=f"frete_{pedido_id}",
                        )
                        edit_rastreio = st.text_input(
                            "Código de Rastreio",
                            value=pedido.get("codigo_rastreio") or "",
                            key=f"rast_{pedido_id}",
                        )
                    if st.form_submit_button("Atualizar Pedido"):
                        payload = {
                            "tipo": edit_tipo,
                            "data_pedido": edit_data.isoformat(),
                            "status": edit_status,
                            "taxa_importacao": edit_taxa,
                            "frete": edit_frete,
                            "nome_identificador": edit_nome if edit_nome else None,
                            "codigo_rastreio": edit_rastreio if edit_rastreio else None,
                        }
                        if api_put(f"/pedidos-compra/{pedido_id}", payload):
                            st.success("Pedido atualizado!")
                            st.rerun()

                # Itens do pedido
                st.subheader("Itens do Pedido")
                itens = api_get(f"/pedidos-compra/{pedido_id}/itens")
                produtos_catalogo = api_get("/produtos")
                produto_opts = {}
                for p in (produtos_catalogo or []):
                    produto_opts[p["id"]] = f"#{p['id']} {p['name']} - {p['team']}"

                if itens:
                    item_data = []
                    for item in itens:
                        custo_un = item['valor_unitario_compra']
                        total_item = item['quantidade_comprada'] * custo_un
                        item_data.append({
                            "ID": item["id"],
                            "Produto": item["produto_nome"],
                            "Time": item["produto_team"],
                            "Tam": item["tamanho"],
                            "Qtd Comprada": item["quantidade_comprada"],
                            "Qtd Disponível": item["quantidade_disponivel"],
                            "Custo Un.": "R$ {:.2f}".format(custo_un),
                            "Total": "R$ {:.2f}".format(total_item),
                        })
                    st.dataframe(item_data, use_container_width=True, hide_index=True)

                    # Botão deletar item
                    with st.form(f"del_item_{pedido_id}"):
                        item_ids = {}
                        for i in itens:
                            item_ids[i["id"]] = f"#{i['id']} - {i['produto_nome']} ({i['tamanho']})"
                        del_item_id = st.selectbox(
                            "Remover Item",
                            options=list(item_ids.keys()),
                            format_func=lambda x: item_ids.get(x, ""),
                            key=f"del_item_sel_{pedido_id}",
                        )
                        if st.form_submit_button("Remover Item"):
                            if api_delete(f"/itens-compra/{del_item_id}"):
                                st.success("Item removido!")
                                st.rerun()

                    # Editar item existente
                    st.subheader("Editar Item Existente")
                    with st.form(f"edit_item_{pedido_id}"):
                        edit_item_ids = {}
                        for i in itens:
                            edit_item_ids[i["id"]] = f"#{i['id']} - {i['produto_nome']} ({i['tamanho']})"
                        selected_item_id = st.selectbox(
                            "Selecione o Item",
                            options=list(edit_item_ids.keys()),
                            format_func=lambda x: edit_item_ids.get(x, ""),
                            key=f"edit_item_sel_{pedido_id}",
                        )
                        item_atual = None
                        for i in itens:
                            if i["id"] == selected_item_id:
                                item_atual = i
                                break
                        if item_atual:
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                e_qtd = st.number_input(
                                    "Quantidade Comprada",
                                    min_value=0, step=1,
                                    value=int(item_atual["quantidade_comprada"]),
                                    key=f"e_qtd_{pedido_id}",
                                )
                            with ec2:
                                e_vlr = st.number_input(
                                    "Valor Unitário (R$)",
                                    min_value=0.0, step=1.0, format="%.2f",
                                    value=float(item_atual["valor_unitario_compra"]),
                                    key=f"e_vlr_{pedido_id}",
                                )
                            if st.form_submit_button("Atualizar Item"):
                                payload = {
                                    "quantidade_comprada": e_qtd,
                                    "valor_unitario_compra": e_vlr,
                                }
                                if api_put(f"/itens-compra/{selected_item_id}", payload):
                                    st.success("Item atualizado!")
                                    st.rerun()
                else:
                    st.info("Nenhum item neste pedido.")

                # Adicionar item
                st.subheader("Adicionar Item")
                with st.form(f"add_item_{pedido_id}"):
                    ic1, ic2 = st.columns(2)
                    with ic1:
                        prod_id = st.selectbox(
                            "Produto",
                            options=list(produto_opts.keys()),
                            format_func=lambda x: produto_opts.get(x, ""),
                            key=f"prod_{pedido_id}",
                        )
                    with ic2:
                        prod_selecionado = None
                        for p in (produtos_catalogo or []):
                            if p["id"] == prod_id:
                                prod_selecionado = p
                                break
                        grade = prod_selecionado["grade_tamanho"] if prod_selecionado else "Masculino"
                        tamanhos = GRADES_TAMANHO.get(grade, GRADES_TAMANHO["Masculino"])
                        tamanho = st.selectbox("Tamanho", tamanhos, key=f"tam_{pedido_id}")

                    ic3, ic4 = st.columns(2)
                    with ic3:
                        qtd = st.number_input("Quantidade", min_value=1, step=1, value=1, key=f"qtd_{pedido_id}")
                    with ic4:
                        valor_compra = st.number_input(
                            "Valor Unitário (R$)",
                            min_value=0.0,
                            step=1.0,
                            format="%.2f",
                            key=f"vlr_{pedido_id}",
                        )

                    if st.form_submit_button("Adicionar Item"):
                        payload = {
                            "produto_id": prod_id,
                            "tamanho": tamanho,
                            "quantidade_comprada": qtd,
                            "valor_unitario_compra": valor_compra,
                        }
                        result = api_post(f"/pedidos-compra/{pedido_id}/itens", payload)
                        if result:
                            st.success(f"Item adicionado: {result['produto_nome']} ({result['tamanho']}) x {result['quantidade_comprada']}")
                            st.rerun()

                if st.button(f"Excluir Pedido #{pedido_id}", type="secondary", key=f"del_ped_{pedido_id}"):
                    if api_delete(f"/pedidos-compra/{pedido_id}"):
                        st.success("Pedido excluído.")
                        st.rerun()


# ===================================================================
# PÁGINA 3 — Reposição
# ===================================================================

def page_reposicao():
    st.header("Reposição de Estoque")
    st.caption("Estoque projetado por Produto/Tamanho baseado nos pedidos de compra.")

    dados = api_get("/reposicao")
    if not dados:
        st.info("Nenhum dado de reposição disponível.")
        return

    # Summary cards
    total_entregue = sum(d["qtd_entregue"] for d in dados)
    total_comprado = sum(d["qtd_comprado"] for d in dados)
    total_transito = sum(d["qtd_em_transito"] for d in dados)
    total_chegando = sum(d["qtd_chegando"] for d in dados)
    total_futuro = sum(d["qtd_total_futuro"] for d in dados)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Estoque Atual", total_entregue)
    col2.metric("Comprado", total_comprado)
    col3.metric("Em Trânsito", total_transito)
    col4.metric("Chegando", total_chegando)
    col5.metric("Total Futuro", total_futuro)

    # Tabela
    st.subheader("Detalhamento")
    rows = []
    for d in dados:
        rows.append({
            "Produto": d["produto_nome"],
            "Time": d["produto_team"],
            "Tamanho": d["tamanho"],
            "Estoque Atual": d["qtd_entregue"],
            "Comprado": d["qtd_comprado"],
            "Em Trânsito": d["qtd_em_transito"],
            "Chegando": d["qtd_chegando"],
            "Total Futuro": d["qtd_total_futuro"],
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Apenas produtos com estoque atual > 0
    if total_entregue > 0:
        st.subheader("Produtos com Estoque Disponível")
        com_estoque = [r for r in rows if r["Estoque Atual"] > 0]
        st.dataframe(com_estoque, use_container_width=True, hide_index=True)


# ===================================================================
# PÁGINA 4 — Carrinho de Vendas
# ===================================================================

def page_carrinho():
    st.header("Carrinho de Vendas")
    st.caption("Crie uma venda e adicione itens com rastreio de lote.")

    produtos = api_get("/produtos")

    # --- Criar nova venda ---
    with st.expander("Nova Venda", expanded=False):
        with st.form("form_venda_header"):
            cv1, cv2 = st.columns(2)
            with cv1:
                tipo_venda = st.selectbox("Tipo de Venda", ["Pronta Entrega", "Dropshipping"])
                forma_pagamento = st.selectbox(
                    "Forma de Pagamento",
                    ["Pix", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Dinheiro", "Outro"],
                )
                cliente_nome = st.text_input("Nome do Cliente")
            with cv2:
                taxa_percent = st.number_input(
                    "Taxa de Pagamento (%)", min_value=0.0, max_value=100.0, step=0.5, format="%.2f"
                )
                despesa_extra = st.number_input(
                    "Despesa Extra (motoboy, etc) - R$", min_value=0.0, step=5.0, format="%.2f"
                )
                cliente_telefone = st.text_input("Telefone do Cliente")
            status_pgto = st.selectbox("Status do Pagamento", ["CONFIRMADO", "PENDENTE"])

            if st.form_submit_button("Criar Venda"):
                payload = {
                    "tipo_venda": tipo_venda,
                    "forma_pagamento": forma_pagamento,
                    "taxa_pagamento_percentual": taxa_percent,
                    "despesa_venda_extra": despesa_extra,
                    "cliente_nome": cliente_nome if cliente_nome else None,
                    "cliente_telefone": cliente_telefone if cliente_telefone else None,
                    "status_pagamento": status_pgto,
                }
                result = api_post("/vendas", payload)
                if result:
                    st.success(f"Venda #{result['id']} criada!")
                    st.session_state["venda_ativa"] = result["id"]
                    st.rerun()

    # --- Selecionar venda ativa ---
    vendas = api_get("/vendas")
    if not vendas:
        st.info("Nenhuma venda registrada.")
        return

    venda_opts = {}
    for v in vendas:
        data_str = v["data_venda"][:10] if v.get("data_venda") else ""
        cliente = v.get("cliente_nome") or ""
        status = v.get("status_pagamento") or "CONFIRMADO"
        tag = f"[{status}]" if status != "CONFIRMADO" else ""
        nome_tag = f" - {cliente}" if cliente else ""
        venda_opts[v["id"]] = f"Venda #{v['id']}{nome_tag} {tag} - {data_str} ({v['total_itens']} itens)"

    venda_ativa = st.session_state.get("venda_ativa")
    if venda_ativa and venda_ativa not in venda_opts:
        venda_ativa = None

    selected_venda_id = st.selectbox(
        "Selecionar Venda",
        options=list(venda_opts.keys()),
        format_func=lambda x: venda_opts.get(x, ""),
        index=list(venda_opts.keys()).index(venda_ativa) if venda_ativa in venda_opts else 0,
    )
    st.session_state["venda_ativa"] = selected_venda_id

    if not selected_venda_id:
        return

    venda_info = None
    for v in vendas:
        if v["id"] == selected_venda_id:
            venda_info = v
            break
    if not venda_info:
        return

    # --- Cabeçalho da venda ---
    with st.container(border=True):
        cliente_nome = venda_info.get("cliente_nome") or ""
        cliente_telefone = venda_info.get("cliente_telefone") or ""
        status_pgto = venda_info.get("status_pagamento") or "CONFIRMADO"
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.write(f"**Venda #{selected_venda_id}**")
        sc2.write(f"**Tipo:** {venda_info['tipo_venda']}")
        sc3.write(f"**Pagamento:** {venda_info['forma_pagamento']}")
        status_emoji = "\u2705" if status_pgto == "CONFIRMADO" else "\u23f3"
        sc4.write(f"**Status:** {status_emoji} {status_pgto}")

        cliente_tag = f"{cliente_nome} ({cliente_telefone})" if cliente_nome and cliente_telefone else cliente_nome or "-"
        desp_extra = venda_info['despesa_venda_extra']
        total_bruto = venda_info['total_bruto']
        sc5, sc6, sc7 = st.columns(3)
        sc5.write(f"**Cliente:** {cliente_tag}")
        sc6.write(f"**Total Bruto:** R$ {total_bruto:.2f}")
        sc7.write(f"**Itens:** {venda_info['total_itens']}")

        # Editar cabeçalho
        with st.expander("Editar Cabeçalho da Venda"):
            with st.form(f"edit_venda_{selected_venda_id}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_tipo = st.selectbox(
                        "Tipo", ["Pronta Entrega", "Dropshipping"],
                        index=0 if venda_info["tipo_venda"] == "Pronta Entrega" else 1,
                        key=f"ev_tipo_{selected_venda_id}",
                    )
                    pag_opts = ["Pix", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Dinheiro", "Outro"]
                    pag_index = 0
                    if venda_info["forma_pagamento"] in pag_opts:
                        pag_index = pag_opts.index(venda_info["forma_pagamento"])
                    e_forma = st.selectbox(
                        "Forma Pagamento",
                        pag_opts,
                        index=pag_index,
                        key=f"ev_forma_{selected_venda_id}",
                    )
                with ec2:
                    e_cliente_nome = st.text_input(
                        "Nome do Cliente",
                        value=venda_info.get("cliente_nome") or "",
                        key=f"ev_cliente_{selected_venda_id}",
                    )
                    e_cliente_tel = st.text_input(
                        "Telefone do Cliente",
                        value=venda_info.get("cliente_telefone") or "",
                        key=f"ev_tel_{selected_venda_id}",
                    )
                    e_taxa = st.number_input(
                        "Taxa (%)", value=float(venda_info["taxa_pagamento_percentual"]),
                        min_value=0.0, max_value=100.0, step=0.5, format="%.2f",
                        key=f"ev_taxa_{selected_venda_id}",
                    )
                    e_extra = st.number_input(
                        "Desp. Extra (R$)", value=float(venda_info["despesa_venda_extra"]),
                        min_value=0.0, step=5.0, format="%.2f",
                        key=f"ev_extra_{selected_venda_id}",
                    )
                if st.form_submit_button("Atualizar Venda"):
                    payload = {
                        "tipo_venda": e_tipo,
                        "forma_pagamento": e_forma,
                        "taxa_pagamento_percentual": e_taxa,
                        "despesa_venda_extra": e_extra,
                        "cliente_nome": e_cliente_nome if e_cliente_nome else None,
                        "cliente_telefone": e_cliente_tel if e_cliente_tel else None,
                    }
                    if api_put(f"/vendas/{selected_venda_id}", payload):
                        st.success("Venda atualizada!")
                        st.rerun()

    # --- Adicionar item ---
    st.subheader("Adicionar Item à Venda")

    if not produtos:
        st.warning("Cadastre produtos no Catálogo primeiro.")
    else:
        with st.container(border=True):
            st.markdown("**Dados do Item**")
            a1, a2 = st.columns(2)
            with a1:
                prod_opts = {}
                for p in produtos:
                    prod_opts[p["id"]] = f"#{p['id']} {p['name']} - {p['team']}"
                prod_id = st.selectbox(
                    "Produto",
                    options=list(prod_opts.keys()),
                    format_func=lambda x: prod_opts.get(x, ""),
                    key=f"ev_prod_{selected_venda_id}",
                )
            with a2:
                prod_sel = None
                for p in produtos:
                    if p["id"] == prod_id:
                        prod_sel = p
                        break
                grade = prod_sel["grade_tamanho"] if prod_sel else "Masculino"
                tamanhos = GRADES_TAMANHO.get(grade, GRADES_TAMANHO["Masculino"])
                tamanho = st.selectbox("Tamanho", tamanhos, key=f"ev_tam_{selected_venda_id}")

            a3, a4 = st.columns(2)
            with a3:
                qtd = st.number_input("Quantidade", min_value=1, step=1, value=1, key=f"ev_qtd_{selected_venda_id}")
            with a4:
                valor_venda = st.number_input(
                    "Valor Unitário (R$)", min_value=0.0, step=10.0, format="%.2f",
                    key=f"ev_vlr_{selected_venda_id}",
                )

            # Lote de origem (obrigatório para TODOS os tipos de venda)
            item_compra_id = None
            if venda_info["tipo_venda"] == "Pronta Entrega":
                endpoint = f"/itens-disponiveis?produto_id={prod_id}&tamanho={tamanho}"
                label = "Seleção de Lote (Pronta Entrega)"
            else:
                endpoint = f"/itens-dropshipping?produto_id={prod_id}&tamanho={tamanho}"
                label = "Seleção de Lote (Dropshipping)"

            st.markdown(f"**{label} — Obrigatório**")
            lotes = api_get(endpoint)
            if lotes:
                lote_opts = {}
                for l in lotes:
                    custo_real_val = l.get('custo_real', l.get('valor_unitario_compra', 0))
                    lote_opts[l["id"]] = "{} | Disp: {} | Custo Real: R$ {:.2f}".format(l['lote_label'], l['quantidade_disponivel'], custo_real_val)
                item_compra_id = st.selectbox(
                    "Selecione o lote de origem",
                    options=list(lote_opts.keys()),
                    format_func=lambda x: lote_opts.get(x, ""),
                    key=f"ev_lote_{selected_venda_id}",
                )
            else:
                st.warning("Nenhum lote disponível com estoque para este produto/tamanho.")
                item_compra_id = None

            btn_adicionar = st.button("Adicionar à Venda", type="primary")
            if btn_adicionar:
                if not item_compra_id:
                    st.error("Selecione o lote de origem para realizar a venda.")
                else:
                    payload = {
                        "venda_id": selected_venda_id,
                        "item_compra_id": item_compra_id,
                        "quantidade_vendida": qtd,
                        "valor_unitario_venda": valor_venda,
                    }
                    result = api_post(f"/vendas/{selected_venda_id}/itens", payload)
                    if result:
                        st.success(f"Item adicionado: {result.get('produto_nome', '')} x {qtd}")
                        st.rerun()

    # --- Itens da venda ---
    st.subheader("Itens da Venda")
    itens_venda = api_get(f"/vendas/{selected_venda_id}/itens")
    if itens_venda:
        for iv in itens_venda:
            cols = st.columns([2, 1, 1, 1, 1.5, 1.5, 1, 0.5])
            cols[0].write(f"**{iv.get('produto_nome', '')}** ({iv.get('produto_team', '')})")
            cols[1].write(f"Tam: {iv.get('tamanho', '')}")
            cols[2].write(f"Qtd: {iv['quantidade_vendida']}")
            valor_unit = iv['valor_unitario_venda']
            cols[3].write(f"R$ {valor_unit:.2f}")
            cols[4].write(f"Lote: {iv.get('lote_origem', 'DS')}")
            lucro_total = iv.get('lucro_total', 0)
            cols[5].write(f"Lucro: R$ {lucro_total:.2f}")
            if cols[6].button("\U0001f5d1\ufe0f", key=f"del_iv_{iv['id']}", help="Remover item"):
                if api_delete(f"/itens-venda/{iv['id']}"):
                    st.success("Item removido da venda e estoque restaurado!")
                    st.rerun()

        # Confirmar pagamento se estiver PENDENTE
        if venda_info.get("status_pagamento") == "PENDENTE":
            st.subheader("Confirmar Pagamento")
            if st.button("Confirmar Pagamento", type="primary", key=f"confirm_pay_{selected_venda_id}"):
                result = api_put(f"/vendas/{selected_venda_id}/status", {"status_pagamento": "CONFIRMADO"})
                if result:
                    st.success(f"Venda #{selected_venda_id} confirmada!")
                    st.rerun()

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button(f"Excluir Venda #{selected_venda_id}", type="secondary"):
                if api_delete(f"/vendas/{selected_venda_id}"):
                    st.success("Venda excluída.")
                    st.session_state.pop("venda_ativa", None)
                    st.rerun()
    else:
        st.info("Nenhum item nesta venda.")


# ===================================================================
# PÁGINA 5 — Dashboard & Finanças
# ===================================================================

def page_dashboard():
    st.header("Dashboard & Finanças")

    data = api_get("/dashboard")
    if not data:
        st.info("Nenhum dado disponível.")
        return

    # Métricas principais
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    faturamento = data['faturamento_bruto']
    lucro = data['lucro_liquido_total']
    despesas_gerais = data['total_despesas_gerais']
    pecas = data.get('pecas_em_estoque', 0)
    custo_estoque = data.get('custo_estoque_parado', 0.0)
    a_receber = data.get('valores_a_receber', 0.0)
    with col1:
        st.metric("Faturamento Bruto", f"R$ {faturamento:,.2f}")
    with col2:
        st.metric("Lucro Líquido Total", f"R$ {lucro:,.2f}")
    with col3:
        st.metric("Despesas Gerais", f"R$ {despesas_gerais:,.2f}")
    with col4:
        st.metric("Peças em Estoque", int(pecas))
    with col5:
        st.metric("Custo Estoque Parado", f"R$ {custo_estoque:,.2f}")
    with col6:
        st.metric("Valores a Receber", f"R$ {a_receber:,.2f}")

    col4, col5, col6 = st.columns(3)
    total_vendas = data['total_vendas']
    total_itens = data['total_itens_vendidos']
    desp_rateada = data['total_despesas_venda']
    with col4:
        st.metric("Total de Vendas", int(total_vendas))
    with col5:
        st.metric("Itens Vendidos", int(total_itens))
    with col6:
        st.metric("Despesas Rateadas (Vendas)", f"R$ {desp_rateada:,.2f}")

    # Gráfico por time
    fat_por_time = data.get("faturamento_por_time", {})
    if fat_por_time:
        st.subheader("Faturamento por Time")
        st.bar_chart(fat_por_time)

    # Detalhamento de lucro
    detalhes = data.get("detalhes_lucro", [])
    if detalhes:
        st.subheader("Detalhamento de Lucro por Item Vendido")
        rows = []
        for d in detalhes:
            rows.append({
                "Venda #": d["venda_id"],
                "Data": d["data_venda"],
                "Produto": d["produto_nome"],
                "Tam": d["tamanho"],
                "Qtd": d["quantidade"],
                "Valor Venda": "R$ {:.2f}".format(d['valor_venda']),
                "Valor Líquido": "R$ {:.2f}".format(d['valor_liquido']),
                "Custo Real": "R$ {:.2f}".format(d['custo_real']),
                "Desp. Rateada": "R$ {:.2f}".format(d['despesa_rateada']),
                "Lucro": "R$ {:.2f}".format(d['lucro']),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        total_lucro = sum(d["lucro"] for d in detalhes)
        st.metric("Soma do Lucro dos Itens", "R$ {:,}".format(total_lucro))

    # Despesas Gerais
    st.subheader("Despesas Operacionais")
    with st.expander("Nova Despesa", expanded=False):
        with st.form("form_despesa"):
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
            data_despesa = st.date_input("Data", value=date.today())
            if st.form_submit_button("Adicionar"):
                payload = {
                    "descricao": descricao,
                    "valor": valor,
                    "data_despesa": data_despesa.isoformat(),
                }
                result = api_post("/despesas", payload)
                if result:
                    st.success("Despesa adicionada!")
                    st.rerun()

    despesas = api_get("/despesas")
    if despesas:
        rows = []
        for d in despesas:
            dt = str(d.get("data_despesa", ""))[:10] if d.get("data_despesa") else "-"
            rows.append({
                "Data": dt,
                "Descrição": d["descricao"],
                "Valor": "R$ {:.2f}".format(d['valor']),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        total_desp = sum(d["valor"] for d in despesas)
        st.write("**Total de Despesas Operacionais: R$ {:.2f}**".format(total_desp))
    else:
        st.info("Nenhuma despesa registrada.")


# ===================================================================
# Main
# ===================================================================

st.set_page_config(
    page_title="Estoque Veloso Imports - ERP",
    page_icon="\u26bd",
    layout="wide",
)

st.title("Veloso Imports - Sistema de Gestão ERP")
st.caption("Controle de estoque por lote, rastreio de vendas e cálculo de lucro rateado.")

pages = {
    "Catálogo de Produtos": page_catalogo,
    "Compras e Drop": page_compras,
    "Reposição": page_reposicao,
    "Carrinho de Vendas": page_carrinho,
    "Dashboard & Finanças": page_dashboard,
}

page = st.sidebar.selectbox("Navegação", list(pages.keys()))
st.sidebar.markdown("---")
st.sidebar.caption("Sistema ERP v2.0 - Gestão de Estoque e Finanças")

pages[page]()
