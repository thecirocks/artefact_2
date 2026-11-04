#Implementação das tools que o LLM pode chamar via function calling

import json
from tools.data_loader import DB
import pandas as pd
import numpy as np
from datetime import date

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_, np.integer, np.floating)):
            return obj.item()
        return super().default(obj)



def buscar_produtos(nome: str = None, categoria: str = None, preco_max: float = None, preco_min: float = None) -> str:
    """Busca produtos por nome, categoria ou faixa de preço. Retorna produtos ativos, descontinuados e em breve."""
    df = DB["products"].merge(DB["categories"], on="category_id", suffixes=("", "_cat"))

    df = df[df["status"].isin(["active", "discontinued", "coming_soon"])]

    if nome:
        df = df[df["name"].str.contains(nome, case=False, na=False)]
    if categoria:
        df = df[df["name_cat"].str.contains(categoria, case=False, na=False)]
    if preco_max is not None:
        df = df[df["price_brl"] <= preco_max]
    if preco_min is not None:
        df = df[df["price_brl"] >= preco_min]

    if df.empty:
        return json.dumps({"resultado": "Nenhum produto encontrado com esses critérios."}, ensure_ascii=False)

    resultados = []

    for _, row in df.iterrows():

        produto = {
            "id": int(row["product_id"]),
            "nome": row["name"],
            "preco": float(row["price_brl"]),
            "categoria": row["name_cat"],
            "estoque": int(row["stock_quantity"]),
            "status": row["status"],
            "disponivel": row["status"] == "active" and row["stock_quantity"] > 0,
            "descricao": row["description"],
        }
        resultados.append(produto)

    return json.dumps({"produtos": resultados, "total": len(resultados)}, ensure_ascii=False)







def consultar_produto_detalhe(product_id: int) -> str:
    """Retorna detalhes completos de um produto específico, incluindo especificacoes e promoção ativa."""
    df = DB["products"]
    produto = df[df["product_id"] == product_id]

    if produto.empty:
        return json.dumps({"erro": "Produto não encontrado."}, ensure_ascii=False)

    row = produto.iloc[0]
    cat = DB["categories"][DB["categories"]["category_id"] == row["category_id"]].iloc[0]

    # Verifica promoção ativa
    promo = DB["promotions"][(DB["promotions"]["product_id"] == product_id) & (DB["promotions"]["is_active"] == 1)]
    promo_info = None
    if not promo.empty:
        p = promo.iloc[0]
        preco_promo = round(row["price_brl"] * (1 - p["discount_percent"] / 100), 2)
        promo_info = {
            "desconto_percent": int(p["discount_percent"]),
            "preco_promocional": preco_promo,
            "campanha": p["description"],
        }

    # Parse specs JSON
    try:
        specs = json.loads(row["specs"]) if isinstance(row["specs"], str) else row["specs"]
    except (json.JSONDecodeError, TypeError):
        specs = {}

    resultado = {
        "id": int(row["product_id"]),
        "nome": row["name"],
        "preco": float(row["price_brl"]),
        "categoria": cat["name"],
        "status": row["status"],
        "estoque": int(row["stock_quantity"]),
        "disponivel": row["status"] == "active" and row["stock_quantity"] > 0,
        "descricao": row["description"],
        "especificacoes": specs,
        "promocao": promo_info,
    }

    return json.dumps(resultado, ensure_ascii=False, cls=NumpyEncoder)









def consultar_pedido(order_id: int = None, email_cliente: str = None, nome_cliente: str = None) -> str:
    """Consulta pedido exigindo os três identificadores: número do pedido, e-mail e nome completo."""
    orders = DB["orders"]
    customers = DB["customers"]
    items = DB["order_items"]
    products = DB["products"]

    # Validação: exige os 3 identificadores
    if not all([order_id, email_cliente, nome_cliente]):
        return json.dumps({
            "erro": "Para sua segurança, preciso de três informações: número do pedido, e-mail e nome completo cadastrado."
        }, ensure_ascii=False)

    # Localiza cliente por e-mail E nome
    clientes = customers[
        (customers["email"].str.lower() == email_cliente.lower()) &
        (customers["name"].str.lower() == nome_cliente.strip().lower())
    ]

    if clientes.empty:
        return json.dumps({"erro": "Não encontrei nenhum cliente com esse e-mail e nome."}, ensure_ascii=False)

    # Localiza pedido do cliente
    pedidos = orders[
        (orders["order_id"] == order_id) &
        (orders["customer_id"].isin(clientes["customer_id"]))
    ]

    if pedidos.empty:
        return json.dumps({"erro": "Nenhum pedido encontrado com essas informações."}, ensure_ascii=False)

    resultados = []
    for _, row in pedidos.iterrows():
        pedido_items = items[items["order_id"] == row["order_id"]]
        itens_lista = []
        for _, item in pedido_items.iterrows():
            prod = products[products["product_id"] == item["product_id"]]
            nome_prod = prod.iloc[0]["name"] if not prod.empty else "Produto desconhecido"
            itens_lista.append({
                "produto": nome_prod,
                "quantidade": int(item["quantity"]),
            })

        cli = customers[customers["customer_id"] == row["customer_id"]]
        nome_cli = cli.iloc[0]["name"] if not cli.empty else "Desconhecido"

        info = {
            "pedido_id": int(row["order_id"]),
            "cliente": nome_cli,
            "data": str(row["order_date"]),
            "status": row["status"],
            "total": float(row["total_brl"]),
            "pagamento": row["payment_method"],
            "itens": itens_lista,
        }

        if pd.notna(row["tracking_code"]) and row["tracking_code"]:
            info["rastreamento"] = row["tracking_code"]
        if pd.notna(row["estimated_delivery"]) and row["estimated_delivery"]:
            info["previsao_entrega"] = str(row["estimated_delivery"])

                # Calcula elegibilidade de devolução para pedidos entregues
        if row["status"] == "delivered" and pd.notna(row.get("estimated_delivery")) and row["estimated_delivery"]:
            try:
                data_entrega = date.fromisoformat(str(row["estimated_delivery"]))
                dias = (date.today() - data_entrega).days
                info["dias_desde_entrega"] = dias
                if dias <= 7:
                    info["elegivel_devolucao"] = True
                    info["prazo_devolucao_restante"] = f"{7 - dias} dias restantes"
                else:
                    info["elegivel_devolucao"] = False
                    info["prazo_devolucao_expirado_ha"] = f"{dias - 7} dias"
            except (ValueError, TypeError):
                pass


        if pd.notna(row["notes"]) and row["notes"]:
            info["observacoes"] = row["notes"]

        resultados.append(info)

    return json.dumps({"pedidos": resultados, "total": len(resultados)}, ensure_ascii=False)








def listar_promocoes_ativas() -> str:
    """Lista todas as promoções ativas com produtos e preços."""
    promos = DB["promotions"][DB["promotions"]["is_active"] == 1]
    products = DB["products"]

    if promos.empty:
        return json.dumps({"resultado": "Nenhuma promoção ativa no momento."}, ensure_ascii=False)

    resultados = []
    for _, row in promos.iterrows():
        prod = products[products["product_id"] == row["product_id"]]
        if prod.empty:
            continue
        p = prod.iloc[0]
        preco_promo = round(p["price_brl"] * (1 - row["discount_percent"] / 100), 2)
        resultados.append({
            "produto": p["name"],
            "preco_original": float(p["price_brl"]),
            "desconto_percent": int(row["discount_percent"]),
            "preco_promocional": preco_promo,
            "campanha": row["description"],
            "disponivel": p["stock_quantity"] > 0,
        })

    return json.dumps({"promocoes": resultados, "total": len(resultados)}, ensure_ascii=False, cls=NumpyEncoder)







def listar_categorias() -> str:
    """Lista todas as categorias de instrumentos disponíveis na loja."""
    cats = DB["categories"]
    resultados = []
    for _, row in cats.iterrows():
        qtd = len(DB["products"][(DB["products"]["category_id"] == row["category_id"]) & (DB["products"]["status"] == "active")])
        resultados.append({
            "categoria": row["name"],
            "descricao": row["description"],
            "produtos_disponiveis": qtd,
        })
    return json.dumps({"categorias": resultados}, ensure_ascii=False)






# Registro das tools no formato function calling
# Registro das tools no formato Anthropic function calling
TOOLS_SCHEMA = [
    {
        "name": "buscar_produtos",
        "description": "Busca produtos por nome, categoria ou faixa de preço. Use quando o cliente quer encontrar um instrumento.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nome": {"type": "string", "description": "Nome ou parte do nome do produto (ex: 'Yamaha', 'violão', 'ukulele')"},
                "categoria": {"type": "string", "description": "Categoria do instrumento (ex: 'Violões', 'Guitarras', 'Ukuleles')"},
                "preco_max": {"type": "number", "description": "Preço máximo em reais"},
                "preco_min": {"type": "number", "description": "Preço mínimo em reais"},
            },
        },
    },
    {
        "name": "consultar_produto_detalhe",
        "description": "Retorna detalhes completos de um produto específico pelo ID, incluindo especificações técnicas e promoção ativa.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "ID do produto"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "consultar_pedido",
        "description": "Consulta pedido exigindo três identificadores obrigatórios: número do pedido, e-mail e nome completo do cliente. Use quando o cliente quer saber status, rastreamento ou detalhes de um pedido. Sempre peça as três informações antes de chamar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "Número do pedido"},
                "email_cliente": {"type": "string", "description": "E-mail cadastrado do cliente"},
                "nome_cliente": {"type": "string", "description": "Nome completo do cliente"},
            },
            "required": ["order_id", "email_cliente", "nome_cliente"],
        },
    },
    {
        "name": "listar_promocoes_ativas",
        "description": "Lista todas as promoções ativas com produtos, descontos e preços promocionais. Use quando o cliente perguntar sobre promoções ou descontos.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "listar_categorias",
        "description": "Lista todas as categorias de instrumentos disponíveis na loja com quantidade de produtos. Use quando o cliente quer saber o que a loja oferece.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]





# Mapa nome -> função para execução
TOOLS_MAP = {
    "buscar_produtos": buscar_produtos,
    "consultar_produto_detalhe": consultar_produto_detalhe,
    "consultar_pedido": consultar_pedido,
    "listar_promocoes_ativas": listar_promocoes_ativas,
    "listar_categorias": listar_categorias,
}
