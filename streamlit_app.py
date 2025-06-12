import streamlit as st
from chat_agent import ChatAgent

st.set_page_config(page_title="Agente Groq", page_icon="🤖", layout="centered")
st.title("Asistente de Atención al Cliente")

# Inicializar conversación y agente
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = ChatAgent()

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada de usuario
if prompt := st.chat_input("Escribe tu mensaje..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Procesar respuesta
    respuesta = st.session_state.agent.handle_message(prompt)
    st.chat_message("assistant").markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})
