"""Interface de chat (Streamlit) para a Lira — Assistente do Empório da Música."""

import os

import streamlit as st

# O agent.py lê o system prompt com caminho relativo, então garantimos
# que o diretório de trabalho seja a raiz do projeto.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Lira — Empório da Música", page_icon="🎵")

# A API key vem de st.secrets (Streamlit Cloud). Ela precisa estar no
# ambiente ANTES de importar agent.py, pois config.py lê a variável e o
# cliente Anthropic é criado no momento do import.
try:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error(
        "ANTHROPIC_API_KEY não encontrada em st.secrets. "
        "Configure em .streamlit/secrets.toml (local) ou nas Secrets do app no Streamlit Cloud."
    )
    st.stop()

from agent import chat  # noqa: E402

st.title("🎵 Lira — Assistente do Empório da Música")

# Histórico usado pela API (inclui tool_use/tool_result) e histórico só para exibição.
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        history = st.session_state.conversation_history
        history_len = len(history)
        try:
            with st.spinner("Lira está pensando..."):
                response = chat(prompt, history)
        except Exception as e:
            # Desfaz o que chat() já tinha adicionado, para não deixar o histórico inconsistente.
            del history[history_len:]
            st.session_state.messages.pop()
            st.error(f"Erro ao falar com a Lira: {e}")
        else:
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
