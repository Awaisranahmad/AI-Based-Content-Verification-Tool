import streamlit as st
import os
from datetime import datetime

# --- Imports ---
try:
    from langchain_groq import ChatGroq
    from tavily import TavilyClient
except ModuleNotFoundError as e:
    st.error(f"🚨 Module missing: {e}. Add in requirements.txt")
    st.stop()

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="🛡️ TruthGuard AI — Expert",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS
st.markdown("""
<style>
    .main { background: linear-gradient(180deg, #0f172a 0%, #1e2937 100%); color: #e2e8f0; }
    .stButton>button { height: 52px; font-weight: 600; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { border-radius: 12px; padding: 12px 24px; }
    .result-box { background: rgba(255,255,255,0.08); border-radius: 16px; padding: 24px; border-left: 5px solid #00ff88; }
</style>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
groq_api = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.title("🛡️ TruthGuard Expert")
    if not groq_api or not tavily_api:
        st.warning("API Keys missing in Secrets!")
        groq_api = st.text_input("Groq API Key", type="password")
        tavily_api = st.text_input("Tavily API Key", type="password")
    else:
        st.success("✅ APIs Connected")

    st.divider()
    model_name = st.selectbox("Model", ["llama-3.3-70b-versatile", "llama3-70b-8192"], index=0)
    temperature = st.slider("Temperature", 0.0, 0.7, 0.2, 0.05)
    search_depth = st.selectbox("Search Depth", ["basic", "advanced"], index=1)
    max_results = st.slider("Max Sources", 5, 15, 10)

# ====================== LLM & TAVILY ======================
@st.cache_resource
def get_llm():
    return ChatGroq(groq_api_key=groq_api, model_name=model_name, temperature=temperature, max_tokens=2048)

llm = get_llm() if groq_api else None
tavily = TavilyClient(api_key=tavily_api) if tavily_api else None

# ====================== SESSION STATE INITIALIZATION ======================
if "fact_result" not in st.session_state:
    st.session_state.fact_result = None
if "current_claim" not in st.session_state:
    st.session_state.current_claim = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "search_results" not in st.session_state:
    st.session_state.search_results = None

# ====================== MAIN UI ======================
st.title("🛡️ TruthGuard AI")
st.markdown("**Expert Fact-Checker** — Live Web Search + Deep Analysis")

input_content = st.text_area(
    "Paste your claim, news, tweet, or URL:",
    height=140,
    placeholder="On its 50th anniversary, WhatsApp is giving 500GB of free high-speed data..."
)

col1, col2 = st.columns([3, 1])
with col1:
    if st.button("🔍 Verify This Claim", type="primary", use_container_width=True):
        if not input_content.strip():
            st.warning("Please enter a claim!")
        elif not groq_api or not tavily_api:
            st.error("API keys missing!")
        else:
            with st.spinner("Searching web and analyzing..."):
                try:
                    # Search
                    search_res = tavily.search(
                        query=input_content[:300],
                        search_depth=search_depth,
                        max_results=max_results
                    )
                    st.session_state.search_results = search_res

                    context = "\n\n".join([f"Source: {r['url']}\n{r['content'][:600]}" 
                                         for r in search_res.get('results', [])])

                    prompt = f"""
You are TruthGuard — expert fact-checker.

Claim: {input_content}

Evidence:
{context}

Return in this format:
**Veracity Score:** X/100
**Verdict:** True | Mostly True | Misleading | False | Unverified

**Step-by-Step Analysis:**
(4-6 clear points)

**Key Evidence:**
**Bias Check:**
**Trusted Sources:**
**Recommendation:**
"""

                    response = llm.invoke(prompt)
                    st.session_state.fact_result = response.content
                    st.session_state.current_claim = input_content
                    st.session_state.chat_history = []   # Reset chat for new claim

                except Exception as e:
                    st.error(f"Error: {e}")

# ====================== SHOW RESULTS IF AVAILABLE ======================
if st.session_state.fact_result:
    st.success("✅ Analysis Complete!")

    tab1, tab2, tab3, tab4 = st.tabs(["⚖️ Verdict", "🔍 Detailed Analysis", "📌 Sources", "💬 Follow-up Chat"])

    with tab1:
        st.markdown(f"**Claim:** {st.session_state.current_claim}")
        st.markdown(st.session_state.fact_result)

    with tab2:
        st.subheader("Step-by-Step Analysis")
        st.markdown(st.session_state.fact_result)

    with tab3:
        st.subheader("Sources Used")
        if st.session_state.search_results:
            for i, r in enumerate(st.session_state.search_results.get('results', [])):
                st.markdown(f"**{i+1}.** [{r['url']}]({r['url']})")
                st.caption(r.get('content', '')[:400] + "...")

    with tab4:
        st.markdown("**Ask follow-up questions about this claim**")

        # Display existing chat
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input (Fixed with key)
        if user_q := st.chat_input("Type your question here...", key="chat_input_key"):
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            with st.chat_message("user"):
                st.markdown(user_q)

            with st.spinner("Thinking..."):
                chat_prompt = f"""
Claim: {st.session_state.current_claim}

Previous Analysis:
{st.session_state.fact_result}

Question: {user_q}

Answer accurately and concisely based on the above.
"""
                answer = llm.invoke(chat_prompt).content
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.markdown(answer)

    # Export Button
    st.download_button(
        "⬇️ Download Full Report",
        st.session_state.fact_result,
        file_name=f"TruthGuard_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        type="primary"
    )

else:
    st.info("Enter a claim and click **Verify This Claim** to start fact-checking.")

st.caption("🛡️ TruthGuard Expert • Always verify from official sources")
