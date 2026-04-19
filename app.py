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
    page_title="🛡️ TruthGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== MODERN + PREMIUM CSS ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e2937 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }

    /* Glass Card Effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 24px;
    }

    .stButton>button {
        height: 56px;
        font-weight: 600;
        border-radius: 16px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 14px;
        padding: 12px 26px;
        font-weight: 600;
    }

    /* Verdict Box */
    .verdict-box {
        background: linear-gradient(135deg, #1e2937, #334155);
        border-radius: 20px;
        padding: 28px;
        border: 1px solid #22c55e;
        margin: 20px 0;
    }

    /* Chat Styling */
    .chat-user {
        background: #3b82f6;
        color: white;
        border-radius: 20px 20px 4px 20px;
        padding: 14px 20px;
        margin: 8px 0;
        max-width: 80%;
        align-self: flex-end;
    }
    .chat-assistant {
        background: rgba(255,255,255,0.1);
        border-radius: 20px 20px 20px 4px;
        padding: 14px 20px;
        margin: 8px 0;
        max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
groq_api = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown("<h1 style='text-align:center; font-size:2.4rem;'>🛡️</h1>", unsafe_allow_html=True)
    st.title("TruthGuard Expert")
    
    if not groq_api or not tavily_api:
        st.warning("⚠️ API Keys missing!")
        groq_api = st.text_input("Groq API Key", type="password")
        tavily_api = st.text_input("Tavily API Key", type="password")
    else:
        st.success("✅ APIs Connected")

    st.divider()
    model_name = st.selectbox("Model", ["llama-3.3-70b-versatile", "llama3-70b-8192"], index=0)
    temperature = st.slider("Temperature", 0.0, 0.7, 0.2, 0.05)
    search_depth = st.selectbox("Search Depth", ["basic", "advanced"], index=1)
    max_results = st.slider("Max Sources", 5, 15, 10)

# ====================== LLM ======================
@st.cache_resource(show_spinner=False)
def get_llm():
    return ChatGroq(
        groq_api_key=groq_api,
        model_name=model_name,
        temperature=temperature,
        max_tokens=2048
    )

llm = get_llm() if groq_api else None
tavily = TavilyClient(api_key=tavily_api) if tavily_api else None

# ====================== SESSION STATE ======================
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
    height=160,
    placeholder="On its 50th anniversary, WhatsApp is giving 500GB of free high-speed data to all its users..."
)

if st.button("🔍 Verify This Claim", type="primary", use_container_width=True):
    if not input_content.strip():
        st.warning("Please enter a claim!")
    elif not groq_api or not tavily_api:
        st.error("API keys missing!")
    else:
        with st.spinner("🔎 Searching the web and analyzing with Llama 3.3..."):
            try:
                search_res = tavily.search(
                    query=input_content[:300],
                    search_depth=search_depth,
                    max_results=max_results
                )
                st.session_state.search_results = search_res

                context = "\n\n".join([f"Source: {r['url']}\n{r['content'][:650]}" 
                                     for r in search_res.get('results', [])])

                prompt = f"""
You are TruthGuard — expert fact-checker.

Claim: {input_content}

Evidence:
{context}

Return in this format:
**Veracity Score:** X/100
**Verdict:** True | Mostly True | Misleading | False | Unverified

**Step-by-Step Analysis:** (4-6 clear points)
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

# ====================== RESULTS DISPLAY ======================
if st.session_state.fact_result:
    st.success("✅ Fact-check completed successfully!")

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚖️ Verdict", "🔍 Detailed Analysis", "📌 Sources", "💬 Follow-up Chat"
    ])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"**Claim:** {st.session_state.current_claim}")
        st.markdown("---")
        st.markdown(st.session_state.fact_result)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("Step-by-Step Analysis")
        st.markdown(st.session_state.fact_result)

    with tab3:
        st.subheader("📚 Sources Used")
        if st.session_state.search_results:
            for i, r in enumerate(st.session_state.search_results.get('results', [])):
                st.markdown(f"**{i+1}.** [{r['url']}]({r['url']})")
                st.caption(r.get('content', '')[:400] + "...")

    with tab4:
        st.markdown("**💬 Ask any follow-up question about this claim**")

        # Show chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

        # Fixed Chat Input
        if user_q := st.chat_input("Type your question here and press Enter...", key="follow_up_chat"):
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            
            with st.spinner("Thinking..."):
                chat_prompt = f"""
Claim: {st.session_state.current_claim}

Previous Fact-Check:
{st.session_state.fact_result}

Question: {user_q}

Answer accurately and concisely.
"""
                answer = llm.invoke(chat_prompt).content
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            
            st.rerun()   # Important: Refresh to show new messages

    # Download Button
    st.download_button(
        "⬇️ Download Full Fact-Check Report",
        st.session_state.fact_result,
        file_name=f"TruthGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        type="primary",
        use_container_width=True
    )

else:
    st.info("👆 Enter a claim above and click **Verify This Claim** to start.")

st.caption("🛡️ TruthGuard AI • Always cross-verify important claims from official sources")
