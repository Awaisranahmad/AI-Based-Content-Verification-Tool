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
    page_title="🛡️ TruthGuard AI — Expert Fact Checker",
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
    
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }

    /* Glassmorphism Card Effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 32px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
    }

    /* Primary Button Styling */
    .stButton>button {
        height: 60px;
        font-size: 1.1rem !important;
        font-weight: 600;
        border-radius: 16px;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 30px rgba(59, 130, 246, 0.4) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(255,255,255,0.02);
        padding: 8px;
        border-radius: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 12px 28px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(59, 130, 246, 0.2);
        border-bottom: 3px solid #3b82f6;
    }

    /* Text Area Styling */
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        font-size: 1.1rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* Chat Styling */
    .chat-user {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border-radius: 20px 20px 4px 20px;
        padding: 16px 24px;
        margin: 12px 0;
        max-width: 85%;
        align-self: flex-end;
        float: right;
        clear: both;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .chat-assistant {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px 20px 20px 4px;
        padding: 16px 24px;
        margin: 12px 0;
        max-width: 85%;
        float: left;
        clear: both;
    }
</style>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
groq_api = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown("<h1 style='text-align:center; font-size:3.5rem; margin-bottom: 0;'>🛡️</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color: #60a5fa;'>TruthGuard</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    if not groq_api or not tavily_api:
        st.warning("⚠️ API Keys Required")
        groq_api = st.text_input("Groq API Key", type="password")
        tavily_api = st.text_input("Tavily API Key", type="password")
    else:
        st.success("🟢 Systems Online & Connected")

    st.markdown("---")
    st.markdown("### ⚙️ Engine Settings")
    model_name = st.selectbox("LLM Core", ["llama-3.3-70b-versatile", "llama3-70b-8192"], index=0)
    temperature = st.slider("Strictness (Lower is better)", 0.0, 1.0, 0.1, 0.05, help="Lower temperature ensures more factual and less creative responses.")
    search_depth = st.radio("Search Depth", ["basic", "advanced"], index=1, horizontal=True)
    max_results = st.slider("Sources to Analyze", 5, 20, 12)
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.caption("Powered by **Groq LPU** & **Tavily Search**")

# ====================== LLM ======================
@st.cache_resource(show_spinner=False)
def get_llm():
    return ChatGroq(
        groq_api_key=groq_api,
        model_name=model_name,
        temperature=temperature,
        max_tokens=3000
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
col1, col2 = st.columns([1, 5])
with col1:
    st.markdown("<h1 style='font-size: 4rem;'>🛡️</h1>", unsafe_allow_html=True)
with col2:
    st.title("TruthGuard AI")
    st.markdown("<p style='font-size: 1.2rem; color: #94a3b8;'>Enterprise-Grade Fake News Detector & Fact Checker</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

input_content = st.text_area(
    "Analyze any claim, news excerpt, or social media post:",
    height=180,
    placeholder="e.g., WhatsApp is giving 500GB of free data on its 50th anniversary. Click here to claim..."
)

if st.button("🚀 Execute Verification Protocol", type="primary", use_container_width=True):
    if not input_content.strip():
        st.warning("Please provide a claim to verify.")
    elif not groq_api or not tavily_api:
        st.error("API keys are missing. Please configure them in the sidebar.")
    else:
        with st.spinner("🔄 Initiating Global Web Search & Llama 3.3 Analysis..."):
            try:
                search_res = tavily.search(
                    query=input_content[:400], # slightly larger query context
                    search_depth=search_depth,
                    max_results=max_results
                )
                st.session_state.search_results = search_res

                context = "\n\n".join([f"Source: {r['url']}\nContent Snippet: {r['content'][:800]}" 
                                     for r in search_res.get('results', [])])

                prompt = f"""
You are TruthGuard, an elite, unbiased fact-checker. 

User Claim: 
"{input_content}"

Live Search Evidence:
{context}

Based strictly on the evidence, provide a highly professional analysis using this exact markdown structure:

### 🎯 Verdict Summary
- **Veracity Score:** [0-100]%
- **Final Verdict:** [TRUE | MOSTLY TRUE | MISLEADING | FALSE | UNVERIFIED]

### 📊 Step-by-Step Analysis
[Provide 4-5 bullet points explaining why the claim is true or false, citing specific evidence.]

### 🚨 Bias & Logical Fallacy Check
[Identify any emotional manipulation, clickbait tactics, or bias in the original claim.]

### 💡 Final Recommendation
[What should the user do? E.g., "Do not click links," "Safe to share," etc.]
"""
                response = llm.invoke(prompt)
                st.session_state.fact_result = response.content
                st.session_state.current_claim = input_content
                st.session_state.chat_history = []   

            except Exception as e:
                st.error(f"System Error: {e}")

# ====================== RESULTS DISPLAY ======================
if st.session_state.fact_result:
    st.markdown("<br>", unsafe_allow_html=True)
    st.success("✅ Analysis Complete.")

    tab1, tab2, tab3 = st.tabs([
        "⚖️ Official Verdict", "📚 Verified Sources", "💬 AI Interrogation"
    ])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"**Investigating Claim:** _{st.session_state.current_claim}_")
        st.markdown("---")
        st.markdown(st.session_state.fact_result)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📡 Global Sources Scanned")
        if st.session_state.search_results:
            for i, r in enumerate(st.session_state.search_results.get('results', [])):
                st.markdown(f"**{i+1}.** [{r['title'] if 'title' in r else r['url']}]({r['url']})")
                st.caption(f"\"{r.get('content', '')[:300]}...\"")
                st.markdown("<hr style='border-top: 1px dashed rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("**💬 Interrogate the Evidence** (Follow-up Questions)")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant">{msg["content"]}</div>', unsafe_allow_html=True)
        
        st.markdown("<div style='clear: both;'></div>", unsafe_allow_html=True)

        if user_q := st.chat_input("Ask a question about this claim...", key="follow_up_chat"):
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            
            with st.spinner("Formulating response..."):
                chat_prompt = f"""
Claim: {st.session_state.current_claim}
Previous Fact-Check Context: {st.session_state.fact_result}
User Question: {user_q}

Provide a direct, accurate, and concise answer based on the context.
"""
                answer = llm.invoke(chat_prompt).content
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            
            st.rerun() 
        st.markdown('</div>', unsafe_allow_html=True)

    # Download Button
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        "⬇️ Download Official TruthGuard Report",
        st.session_state.fact_result,
        file_name=f"TruthGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        type="primary",
        use_container_width=True
    )

else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("👆 Enter a claim above and click **Execute Verification Protocol** to begin analysis.")

st.markdown("<br><hr><center><p style='color: #64748b; font-size: 0.9rem;'>🛡️ TruthGuard AI v2.0 • AI can hallucinate, always cross-reference critical data.</p></center>", unsafe_allow_html=True)
