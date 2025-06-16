import streamlit as st
from datetime import datetime
from app.agent.chat_agent import ChatAgent

# Configurar la página
st.set_page_config(page_title="Agente Groq", page_icon="🤖", layout="wide")

# === SIDEBAR ===
with st.sidebar:
    st.markdown("## Asistente Virtual")
    st.markdown("Consulta información de abonados, incidencias, facturas y más.")
    st.markdown("---")
    st.markdown("**Desarrollado por:** Bernardo Martínez Romero")
    st.markdown(f"{datetime.now().strftime('%d/%m/%Y')}")
    st.markdown("---")
    st.caption("Versión beta - Proyecto Groq + FastAPI + SQLite")

# === HEADER ===
st.title("Asistente de Atención al Cliente")

# Inicializar estado
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = ChatAgent()

# Mostrar historial de conversación
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada del usuario
if prompt := st.chat_input("Escribe tu mensaje aquí..."):
    # Mostrar entrada del usuario
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Spinner de carga
    with st.spinner("Pensando..."):
        respuesta = st.session_state.agent.handle_message(prompt)

    # Mostrar respuesta del asistente
    st.chat_message("assistant").markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})
