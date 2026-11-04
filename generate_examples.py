"""Gera 5 conversas-exemplo com o agente Lira e salva em examples/."""
import os
from agent import chat

CONVERSATIONS = [
    {
        "filename": "01_catalogo_violoes.md",
        "title": "Consulta ao catálogo de produtos",
        "messages": [
            "Quais opções de violões disponíveis custando até R$1000?",
            "Me fala mais sobre o segundo da lista",
            "Ele tem alguma promoção ativa?",
        ],
    },
    {
        "filename": "02_informacoes_loja.md",
        "title": "Informações gerais da loja",
        "messages": [
            "Qual o endereço da loja?",
            "E o horário de funcionamento?",
            "Vocês aceitam PIX?",
        ],
    },
    {
        "filename": "03_consulta_preco.md",
        "title": "Consulta de preço específico",
        "messages": [
            "Quanto custa o Takamine GD20?",
            "Quais as especificações técnicas dele?",
            "Tem algum violão parecido mais barato?",
        ],
    },
    {
        "filename": "04_devolucao_pedido.md",
        "title": "Aplicação de política de devolução",
        "messages": [
            "Me arrependi da minha compra, posso devolver meu pedido?",
            "Meu pedido é o 4, meu nome é Lucas Mendes da Silva, email lucas.mendes@jmail.com",
            "Qual o prazo que eu tenho pra devolver?",
        ],
    },
    {
        "filename": "05_promocoes_e_recomendacao.md",
        "title": "Promoções ativas e recomendação para iniciante",
        "messages": [
            "Quais promoções vocês têm ativas agora?",
            "Estou começando a tocar, qual desses seria melhor pra um iniciante?",
            "E quanto fica com o desconto?",
        ],
    },
]


def run_and_save():
    os.makedirs("examples", exist_ok=True)

    for conv in CONVERSATIONS:
        print(f"\n{'='*60}")
        print(f"Conversa: {conv['title']}")
        print(f"{'='*60}")

        history = []
        lines = [
            f"# {conv['title']}\n",
            f"Conversa gerada automaticamente para demonstrar o agente Lira.\n",
        ]

        for i, msg in enumerate(conv["messages"], 1):
            print(f"\n  [{i}/{len(conv['messages'])}] Enviando: {msg}")
            response = chat(msg, history)
            print(f"  Resposta: {response[:100]}...")

            lines.append(f"---\n")
            lines.append(f"**Cliente:** {msg}\n")
            lines.append(f"\n**Lira:** {response}\n")

        filepath = os.path.join("examples", conv["filename"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\n  Salvo em {filepath}")

    print(f"\n{'='*60}")
    print("5 conversas salvas em examples/")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_and_save()
EOFcat > generate_examples.py << 'EOF'
"""Gera 5 conversas-exemplo com o agente Lira e salva em examples/."""
import os
from agent import chat

CONVERSATIONS = [
    {
        "filename": "01_catalogo_violoes.md",
        "title": "Consulta ao catálogo de produtos",
        "messages": [
            "Quais opções de violões disponíveis custando até R$1000?",
            "Me fala mais sobre o segundo da lista",
            "Ele tem alguma promoção ativa?",
        ],
    },
    {
        "filename": "02_informacoes_loja.md",
        "title": "Informações gerais da loja",
        "messages": [
            "Qual o endereço da loja?",
            "E o horário de funcionamento?",
            "Vocês aceitam PIX?",
        ],
    },
    {
        "filename": "03_consulta_preco.md",
        "title": "Consulta de preço específico",
        "messages": [
            "Quanto custa o Takamine GD20?",
            "Quais as especificações técnicas dele?",
            "Tem algum violão parecido mais barato?",
        ],
    },
    {
        "filename": "04_devolucao_pedido.md",
        "title": "Aplicação de política de devolução",
        "messages": [
            "Me arrependi da minha compra, posso devolver meu pedido?",
            "Meu pedido é o 4, meu nome é Lucas Mendes da Silva, email lucas.mendes@jmail.com",
            "Qual o prazo que eu tenho pra devolver?",
        ],
    },
    {
        "filename": "05_promocoes_e_recomendacao.md",
        "title": "Promoções ativas e recomendação para iniciante",
        "messages": [
            "Quais promoções vocês têm ativas agora?",
            "Estou começando a tocar, qual desses seria melhor pra um iniciante?",
            "E quanto fica com o desconto?",
        ],
    },
]


def run_and_save():
    os.makedirs("examples", exist_ok=True)

    for conv in CONVERSATIONS:
        print(f"\n{'='*60}")
        print(f"Conversa: {conv['title']}")
        print(f"{'='*60}")

        history = []
        lines = [
            f"# {conv['title']}\n",
            f"Conversa gerada automaticamente para demonstrar o agente Lira.\n",
        ]

        for i, msg in enumerate(conv["messages"], 1):
            print(f"\n  [{i}/{len(conv['messages'])}] Enviando: {msg}")
            response = chat(msg, history)
            print(f"  Resposta: {response[:100]}...")

            lines.append(f"---\n")
            lines.append(f"**Cliente:** {msg}\n")
            lines.append(f"\n**Lira:** {response}\n")

        filepath = os.path.join("examples", conv["filename"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\n  Salvo em {filepath}")

    print(f"\n{'='*60}")
    print("5 conversas salvas em examples/")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_and_save()
