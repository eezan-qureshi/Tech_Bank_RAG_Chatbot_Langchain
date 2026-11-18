import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

import tech_bank as tb
st.set_page_config(page_title="Tech Bank Assistant", page_icon="🏦")


@st.cache_resource
def load_bot():
    """Create the TechBank chains ONCE (Streamlit re-runs this file on every click)."""
    return tb.TechBank()


try:
    bot = load_bot()
except RuntimeError as e:
    st.error(f"{e}   (then reload this page)")
    st.stop()

if "memory" not in st.session_state:
    st.session_state.memory = tb.load_memory()     # what the bot remembers (saved on disk)
if "messages" not in st.session_state:
    st.session_state.messages = []                 # what is shown on the screen (starts empty)


def show_sources(sources):
    with st.expander("Sources"):
        for s in sources:
            st.markdown(f"**Policy document, page {s['page']}**")
            st.caption(s["text"])


# ------------------------------------------------------------------ screen
with st.sidebar:
    st.header("🏦 Tech Bank")
    st.write("Ask about accounts, cards, loans, fees, digital banking and security.")
    st.caption("You can write in English, Roman Urdu or Urdu.")
    st.caption(f"Knowledge base: {bot.chunk_count()} chunks")
    st.caption(f"Messages in memory: {len(st.session_state.memory)}")
    if st.button("Clear screen"):
        st.session_state.messages = []             # memory stays
        st.rerun()
    if st.button("Forget memory"):
        st.session_state.messages = []
        st.session_state.memory = []
        tb.save_memory([])
        st.rerun()

st.title("🏦 Tech Bank Assistant")
st.caption("Built with LangChain. Answers come from Tech Bank's official policy document.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if m.get("sources"):
            show_sources(m["sources"])

question = st.chat_input("Type your question here...")

if question:
    with st.chat_message("user"):
        st.write(question)

    history = st.session_state.memory[-tb.HISTORY_MESSAGES:]    # HumanMessage / AIMessage objects

    with st.chat_message("assistant"):
        reply, sources = None, []
        with st.spinner("Searching and thinking..."):
            try:
                reply, sources = bot.reply(question, history)
            except Exception as e:
                st.error(f"Something went wrong: {type(e).__name__}: {str(e)[:200]}")
        if reply is not None:
            st.write(reply)
            if sources:
                show_sources(sources)

    if reply is not None:
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.messages.append({"role": "assistant", "content": reply, "sources": sources})
        st.session_state.memory += [HumanMessage(content=question), AIMessage(content=reply)]
        tb.save_memory(st.session_state.memory[-100:])          # keep the file small
        st.rerun()      # redraw so the sidebar counter is up to date
