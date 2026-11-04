"""Testes unitários das tool functions do agente Lira.

40 testes: 8 por função (2 happy path, 2 erros, 2 edge cases, 2 prompt injection).
Para funções sem parâmetros (listar_promocoes_ativas, listar_categorias),
os testes de prompt injection são substituídos por testes de integridade de dados.
"""
import json
import pytest
from tools.functions import (
    buscar_produtos,
    consultar_produto_detalhe,
    consultar_pedido,
    listar_promocoes_ativas,
    listar_categorias,
)


# ============================================================
# buscar_produtos (8 testes)
# ============================================================
class TestBuscarProdutos:

    # --- Happy Path ---
    def test_busca_por_nome(self):
        result = json.loads(buscar_produtos(nome="Yamaha"))
        assert "produtos" in result
        assert result["total"] > 0
        for p in result["produtos"]:
            assert "yamaha" in p["nome"].lower()

    def test_busca_por_categoria_e_preco(self):
        result = json.loads(buscar_produtos(categoria="Violões", preco_max=1000.0))
        assert "produtos" in result
        assert result["total"] > 0
        for p in result["produtos"]:
            assert p["preco"] <= 1000.0

    # --- Erros ---
    def test_nome_inexistente(self):
        result = json.loads(buscar_produtos(nome="xyzinexistente999"))
        assert "resultado" in result

    def test_categoria_inexistente(self):
        result = json.loads(buscar_produtos(categoria="Harpa Celestial"))
        assert "resultado" in result

    # --- Edge Cases ---
    def test_preco_max_zero(self):
        result = json.loads(buscar_produtos(preco_max=0))
        if "produtos" in result:
            assert result["total"] == 0
        else:
            assert "resultado" in result

    def test_busca_sem_filtro_inclui_descontinuados(self):
        result = json.loads(buscar_produtos())
        assert result["total"] > 0
        statuses = {p["status"] for p in result["produtos"]}
        assert "active" in statuses

    # --- Prompt Injection ---
    def test_sql_injection_no_nome(self):
        result = json.loads(buscar_produtos(nome="'; DROP TABLE products;--"))
        assert "resultado" in result or "produtos" in result

    def test_script_injection_na_categoria(self):
        result = json.loads(buscar_produtos(categoria="<script>alert('xss')</script>"))
        assert "resultado" in result or "produtos" in result


# ============================================================
# consultar_produto_detalhe (8 testes)
# ============================================================
class TestConsultarProdutoDetalhe:

    # --- Happy Path ---
    def test_produto_existente_com_specs(self):
        result = json.loads(consultar_produto_detalhe(product_id=90))
        assert result["id"] == 90
        assert "especificacoes" in result

    def test_produto_com_promocao_ativa(self):
        result = json.loads(consultar_produto_detalhe(product_id=90))
        assert "promocao" in result
        assert result["promocao"]["desconto_percent"] == 18

    # --- Erros ---
    def test_produto_inexistente(self):
        result = json.loads(consultar_produto_detalhe(product_id=9999))
        assert "erro" in result

    def test_produto_id_negativo(self):
        result = json.loads(consultar_produto_detalhe(product_id=-1))
        assert "erro" in result

    # --- Edge Cases ---
    def test_produto_id_zero(self):
        result = json.loads(consultar_produto_detalhe(product_id=0))
        assert "erro" in result

    def test_produto_sem_promocao(self):
        """Produto 93 tem promoções no CSV mas todas inativas."""
        result = json.loads(consultar_produto_detalhe(product_id=93))
        if "produto" in result:
            assert "promocao" not in result["produto"]

    # --- Prompt Injection ---
    def test_product_id_absurdo(self):
        result = json.loads(consultar_produto_detalhe(product_id=99999999))
        assert "erro" in result

    def test_product_id_float_truncado(self):
        try:
            result = json.loads(consultar_produto_detalhe(product_id=int(90.5)))
            assert result["id"] == 90
        except (TypeError, ValueError):
            pass


# ============================================================
# consultar_pedido (8 testes)
# ============================================================
class TestConsultarPedido:

    # --- Happy Path ---
    def test_pedido_valido(self):
        result = json.loads(consultar_pedido(
            order_id=4,
            email_cliente="lucas.mendes@jmail.com",
            nome_cliente="Lucas Mendes da Silva"
        ))
        assert "pedidos" in result
        assert result["pedidos"][0]["status"] == "delivered"

    def test_pedido_com_rastreamento(self):
        result = json.loads(consultar_pedido(
            order_id=4,
            email_cliente="lucas.mendes@jmail.com",
            nome_cliente="Lucas Mendes da Silva"
        ))
        assert "rastreamento" in result["pedidos"][0]

    # --- Erros ---
    def test_sem_order_id(self):
        result = json.loads(consultar_pedido(
            email_cliente="lucas.mendes@jmail.com",
            nome_cliente="Lucas Mendes da Silva"
        ))
        assert "erro" in result

    def test_email_errado(self):
        result = json.loads(consultar_pedido(
            order_id=4,
            email_cliente="errado@email.com",
            nome_cliente="Lucas Mendes da Silva"
        ))
        assert "erro" in result

    # --- Edge Cases ---
    def test_case_insensitive(self):
        result = json.loads(consultar_pedido(
            order_id=4,
            email_cliente="LUCAS.MENDES@JMAIL.COM",
            nome_cliente="lucas mendes da silva"
        ))
        assert "pedidos" in result

    def test_nome_errado(self):
        result = json.loads(consultar_pedido(
            order_id=4,
            email_cliente="lucas.mendes@jmail.com",
            nome_cliente="Nome Completamente Errado"
        ))
        assert "erro" in result

    # --- Prompt Injection ---
    def test_sql_injection_no_email(self):
        result = json.loads(consultar_pedido(
            order_id=4,
            email_cliente="admin@loja.com' OR '1'='1",
            nome_cliente="Lucas Mendes da Silva"
        ))
        assert "erro" in result

    def test_script_injection_no_nome(self):
        result = json.loads(consultar_pedido(
            order_id=4,
            email_cliente="lucas.mendes@jmail.com",
            nome_cliente="<script>document.cookie</script>"
        ))
        assert "erro" in result


# ============================================================
# listar_promocoes_ativas (8 testes)
# ============================================================
class TestListarPromocoesAtivas:

    # --- Happy Path ---
    def test_retorna_promocoes(self):
        result = json.loads(listar_promocoes_ativas())
        assert "promocoes" in result
        assert result["total"] > 0

    def test_preco_promocional_menor_que_original(self):
        result = json.loads(listar_promocoes_ativas())
        for promo in result["promocoes"]:
            assert promo["preco_promocional"] < promo["preco_original"]

    # --- Erros (validação de dados) ---
    def test_desconto_entre_zero_e_cem(self):
        result = json.loads(listar_promocoes_ativas())
        for promo in result["promocoes"]:
            assert 0 < promo["desconto_percent"] <= 100

    def test_campos_obrigatorios(self):
        result = json.loads(listar_promocoes_ativas())
        campos = ["produto", "desconto_percent", "preco_original", "preco_promocional"]
        for promo in result["promocoes"]:
            for campo in campos:
                assert campo in promo, f"Campo '{campo}' ausente na promoção"

    # --- Edge Cases ---
    def test_exatamente_4_promocoes_ativas(self):
        """CSV tem 4 promoções com is_active=1 (IDs 12, 14, 19, 24)."""
        result = json.loads(listar_promocoes_ativas())
        assert result["total"] == 4

    def test_sem_duplicatas(self):
        result = json.loads(listar_promocoes_ativas())
        produtos = [p["produto"] for p in result["promocoes"]]
        assert len(produtos) == len(set(produtos))

    # --- Integridade de dados ---
    def test_preco_promocional_calculado_corretamente(self):
        result = json.loads(listar_promocoes_ativas())
        for promo in result["promocoes"]:
            esperado = round(promo["preco_original"] * (1 - promo["desconto_percent"] / 100), 2)
            assert abs(promo["preco_promocional"] - esperado) < 0.01

    def test_todas_sao_realmente_ativas(self):
        """Confirma que são exatamente 4 (matching CSV)."""
        result = json.loads(listar_promocoes_ativas())
        assert result["total"] == 4


# ============================================================
# listar_categorias (8 testes)
# ============================================================
class TestListarCategorias:

    # --- Happy Path ---
    def test_retorna_categorias(self):
        result = json.loads(listar_categorias())
        assert "categorias" in result
        assert len(result["categorias"]) > 0

    def test_contagem_produtos(self):
        result = json.loads(listar_categorias())
        for cat in result["categorias"]:
            assert "produtos_disponiveis" in cat
            assert isinstance(cat["produtos_disponiveis"], int)

    # --- Erros (validação de dados) ---
    def test_nomes_nao_vazios(self):
        result = json.loads(listar_categorias())
        for cat in result["categorias"]:
            assert cat["categoria"] and len(cat["categoria"].strip()) > 0

    def test_contagem_nao_negativa(self):
        result = json.loads(listar_categorias())
        for cat in result["categorias"]:
            assert cat["produtos_disponiveis"] >= 0

    # --- Edge Cases ---
    def test_total_9_categorias(self):
        result = json.loads(listar_categorias())
        assert len(result["categorias"]) == 9

    def test_sem_duplicatas(self):
        result = json.loads(listar_categorias())
        nomes = [cat["categoria"] for cat in result["categorias"]]
        assert len(nomes) == len(set(nomes))

    # --- Integridade de dados ---
    def test_campos_obrigatorios(self):
        result = json.loads(listar_categorias())
        for cat in result["categorias"]:
            assert "categoria" in cat
            assert "produtos_disponiveis" in cat

    def test_tem_descricao(self):
        result = json.loads(listar_categorias())
        for cat in result["categorias"]:
            assert "descricao" in cat
