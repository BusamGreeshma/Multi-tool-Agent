import streamlit as st
from tools import run_agent, SYSTEM_PROMPT

# ── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Agent 🤖",
    page_icon="🤖",
    layout="centered"
)

# ── Custom CSS (Clean Chat UI) ──────────────────────────────
st.markdown("""
<style>
.chat-container {
    max-width: 800px;
    margin: auto;
}
.user-msg {
    background-color: #DCF8C6;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
    text-align: right;
}
.bot-msg {
    background-color: #F1F0F0;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.step-box {
    background-color: #222;
    color: #0f0;
    padding: 8px;
    border-radius: 8px;
    font-family: monospace;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# ── Title ───────────────────────────────────────────────────
st.title("🤖 AI Agent with Tools")
st.caption("Weather 🌦️ | Stocks 📈 | System Commands 💻")

# ── Session State ───────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Display Chat History ────────────────────────────────────
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f'<div class="user-msg">{chat["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">{chat["content"]}</div>', unsafe_allow_html=True)

# ── Chat Input ──────────────────────────────────────────────
query = st.chat_input("Type your message...")

if query:
    # Show user message
    st.session_state.chat_history.append({"role": "user", "content": query})
    st.markdown(f'<div class="user-msg">{query}</div>', unsafe_allow_html=True)

    # Placeholder for streaming response
    response_box = st.empty()

    final_answer = ""

    # Run agent
    for step in run_agent(query, st.session_state.messages):

        if step["type"] == "plan":
            response_box.markdown(
                f'<div class="step-box">🧠 PLAN: {step["content"]}</div>',
                unsafe_allow_html=True
            )

        elif step["type"] == "action":
            response_box.markdown(
                f'<div class="step-box">⚙️ ACTION: {step["tool"]}({step["input"]})</div>',
                unsafe_allow_html=True
            )

        elif step["type"] == "observe":
            response_box.markdown(
                f'<div class="step-box">👀 OBSERVE: {step["output"]}</div>',
                unsafe_allow_html=True
            )

        elif step["type"] == "output":
            final_answer = step["content"]
            st.session_state.messages = step["messages"]

    # Show final answer
    st.markdown(f'<div class="bot-msg">{final_answer}</div>', unsafe_allow_html=True)

    st.session_state.chat_history.append({"role": "assistant", "content": final_answer})