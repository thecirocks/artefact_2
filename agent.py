"""Lira — Agente de atendimento do Empório da Música."""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import anthropic
from config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS
from tools.functions import TOOLS_SCHEMA, TOOLS_MAP


# Carrega system prompt
with open("prompts/system_prompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

# Inicializa cliente Anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def process_tool_calls(response):
    """Executa as tool calls e retorna os resultados."""
    tool_results = []
    for block in response.content:
        if block.type != "tool_use":
            continue
        tool_name = block.name
        tool_input = block.input

        if tool_name in TOOLS_MAP:
            try:
                result = TOOLS_MAP[tool_name](**tool_input)
            except Exception as e:
                result = f"Erro ao executar {tool_name}: {str(e)}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": True,
                })
                continue
        else:
            result = f"Tool '{tool_name}' não encontrada."

        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": result,
        })

    return tool_results


def chat(user_message: str, conversation_history: list) -> str:
    """Processa uma mensagem do usuário e retorna a resposta da Lira."""
    conversation_history.append({
        "role": "user",
        "content": user_message,
    })

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS_SCHEMA,
            messages=conversation_history,
        )

        # Se não pediu tool, retorna a resposta final
        if response.stop_reason != "tool_use":
            assistant_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    assistant_text += block.text

            conversation_history.append({
                "role": "assistant",
                "content": response.content,
            })
            return assistant_text

        # Adiciona resposta do assistant (com tool_use) ao histórico
        conversation_history.append({
            "role": "assistant",
            "content": response.content,
        })

        # Executa as tools e adiciona resultados ao histórico
        tool_results = process_tool_calls(response)
        conversation_history.append({
            "role": "user",
            "content": tool_results,
        })


def main():
    """Loop principal do chat via terminal."""
    print("=" * 50)
    print("Olá, eu sou 🎵 Lira, seu assistente AI da loja — Empório da Música")
    print("Como posso ajudar ?")
    print("=" * 50)
    print("Digite 'sair' para encerrar.\n")

    conversation_history = []

    while True:
        user_input = input("Você: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["sair", "exit", "quit"]:
            print("\nLira: Foi um prazer atender você! 🎵 Até a próxima!")
            break

        response = chat(user_input, conversation_history)
        print(f"\nLira: {response}\n")


if __name__ == "__main__":
    main()
