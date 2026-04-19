import streamlit as st
import os
from datetime import datetime

# --- Imports ---
try:
    from langchain_groq import ChatGroq
    from tavily import TavilyClient
except ModuleNotFoundError as e:
    st.error(f"🚨 Module missing: {e}")
    st.stop()

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="🛡️ TruthGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== MODERN CSS + ANIMATIONS ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e2937 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: -0.02em;
    }

    /* Glassmorphism Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    /* Modern Button */
    .stButton>button {
        height: 56px;
        font-weight: 600;
        border-radius: 16px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.5);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 14px;
        padding: 14px 28px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255,255,255,0.1);
    }

    /* Verdict Box */
    .verdict-box {
        background: linear-gradient(135deg, #1e2937, #334155);
        border-radius: 20px;
        padding: 28px;
        border: 1px solid #22c55e;
        animation: fadeIn 0.6s ease forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Chat Message */
    .chat-user {
        background: #3b82f6;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 14px 18px;
        margin-bottom: 12px;
        max-width: 85%;
        align-self: flex-end;
    }
    .chat-assistant {
        background: rgba(255,255,255,0.1);
        border-radius: 18px 18px 18px 4px;
        padding: 14px 18px;
        margin-bottom: 12px;
        max-width: 85%;
    }

    .stTextArea textarea {
        border-radius: 16px;
        border: 1px solid #475569;
    }
</style>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
groq_api = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:20px 0;">
        <h1 style="font-size:2.2rem; margin:0; background: linear-gradient(90deg, #60a5fa, #a5b4fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            🛡️ TruthGuard
        </h1>
        <p style="margin:8px 0 0 0; color:#94a3b8;">Expert Fact-Checker</p>
    </div>
    """, unsafe_allow_html=True)

    if not groq_api or not tavily_api:
        st.warning("⚠️ API Keys missing in Secrets")
        groq_api = st.text_input("Groq API Key", type="password", value=groq_api)
        tavily_api = st.text_input("Tavily API Key", type="password", value=tavily_api)
    else:
        st.success("✅ APIs Connected Successfully")

    st.divider()
    st.caption("⚙️ Advanced Settings")
    model_name = st.selectbox("LLM Model", ["llama-3.3-70b-versatile", "llama3-70b-8192"], index=0)
    temperature = st.slider("Temperature", 0.0, 0.7, 0.15, 0.05)
    search_depth = st.selectbox("Search Depth", ["basic", "advanced"], index=1)
    max_results = st.slider("Number of Sources", 5, 20, 12)

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
for key in ["fact_result", "current_claim", "chat_history", "search_results"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "chat_history" else []

# ====================== MAIN UI ======================
st.markdown("<h1 style='text-align:center; margin-bottom:8px;'>🛡️ TruthGuard AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#94a3b8; font-size:1.1rem;'>Live Web Search + Deep Fact Analysis</p>", unsafe_allow_html=True)

# Input Area
st.markdown("### Paste your claim, news, tweet or URL")
input_content = st.text_area(
    "",
    height=160,
    placeholder="On its 50th anniversary, WhatsApp is giving 500GB of free high-speed data to all its users...",
    label_visibility="collapsed"
)

# Verify Button
if st.button("🔍 Verify This Claim", type="primary", use_container_width=True):
    if not input_content.strip():
        st.warning("⚠️ Please enter a claim to verify!")
    elif not groq_api or not tavily_api:
        st.error("API keys are required!")
    else:
        with st.spinner("🔎 Searching the web • Analyzing with Llama 3.3..."):
            try:
                search_res = tavily.search(
                    query=input_content[:300],
                    search_depth=search_depth,
                    max_results=max_results
                )
                st.session_state.search_results = search_res

                context = "\n\n".join([f"Source: {r['url']}\n{r['content'][:650]}" for r in search_res.get('results', [])])

                prompt = f"""
You are TruthGuard — a highly accurate and neutral fact-checker.

Claim: {input_content}

Evidence from web:
{context}

Provide response in this exact format:

**Veracity Score:** X/100
**Verdict:** True | Mostly True | Misleading | False | Unverified

**Step-by-Step Analysis:**
(Write 5-7 clear points)

**Key Evidence:**
**Bias & Context Check:**
**Trusted Sources:**
**Recommendation:**
"""

                response = llm.invoke(prompt)
                st.session_state.fact_result = response.content
                st.session_state.current_claim = input_content
                st.session_state.chat_history = []  # Reset chat for new verification

            except Exception as e:
                st.error(f"Error: {str(e)}")

# ====================== RESULTS SECTION ======================
if st.session_state.fact_result:
    st.markdown("---")
    st.success("✅ Fact-check completed successfully!")

    tab_verdict, tab_analysis, tab_sources, tab_chat = st.tabs([
        "⚖️ Verdict", "🔍 Detailed Analysis", "📌 Sources", "💬 Follow-up Chat"
    ])

    with tab_verdict:
        st.markdown('<div class="verdict-box">', unsafe_allow_html=True)
        st.markdown(f"**Claim:** {st.session_state.current_claim}")
        st.markdown("---")
        st.markdown(st.session_state.fact_result)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_analysis:
        st.subheader("Deep Step-by-Step Analysis")
        st.markdown(st.session_state.fact_result)

    with tab_sources:
        st.subheader("📚 Live Sources Used")
        if st.session_state.search_results:
            for i, r in enumerate(st.session_state.search_results.get('results', [])):
                st.markdown(f"**{i+1}.** [{r['url']}]({r['url']})")
                st.caption(r.get('content', '')[:450] + "...")

    with tab_chat:
        st.markdown("**💬 Ask any follow-up question about this claim**")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

        if user_question := st.chat_input("Type your question and press Enter...", key="chat_input"):
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            st.rerun()   # Force refresh to show user message

            with st.spinner("Thinking..."):
                chat_prompt = f"""
Claim: {st.session_state.current_claim}
Previous Analysis: {st.session_state.fact_result}
Question: {user_question}
Answer concisely and accurately.
"""
                answer = llm.invoke(chat_prompt).content
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()

    # Export
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
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
