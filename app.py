import streamlit as st
import os
from datetime import datetime

# --- Safety Check for Imports ---
try:
    from langchain_groq import ChatGroq
    from tavily import TavilyClient
except ModuleNotFoundError as e:
    st.error(f"🚨 Module missing: {e}. Please add 'langchain-groq' and 'tavily-python' in requirements.txt")
    st.stop()

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="🛡️ TruthGuard AI — Expert Fact Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Clean CSS
st.markdown("""
<style>
    .main { background: linear-gradient(180deg, #0f172a 0%, #1e2937 100%); color: #e2e8f0; }
    .stButton>button { height: 52px; font-weight: 600; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { border-radius: 12px; padding: 12px 24px; font-weight: 500; }
    .verdict-card { background: rgba(255,255,255,0.08); border-radius: 16px; padding: 24px; border: 1px solid #00ff88; }
    .chat-message { padding: 12px 16px; border-radius: 12px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
groq_api = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.title("🛡️ TruthGuard Expert")
    st.caption("Real-time Fact Checking")
    
    if not groq_api or not tavily_api:
        st.warning("⚠️ API Keys missing!")
        temp_groq = st.text_input("Groq API Key", type="password")
        temp_tavily = st.text_input("Tavily API Key", type="password")
        if temp_groq and temp_tavily:
            groq_api, tavily_api = temp_groq, temp_tavily
    else:
        st.success("✅ APIs Connected")
    
    st.divider()
    
    model_options = {
        "Llama 3.3 70B (Best)": "llama-3.3-70b-versatile",
        "Llama 3 70B": "llama3-70b-8192",
        "Mixtral 8x7B": "mixtral-8x7b-32768"
    }
    selected_model = st.selectbox("Model", list(model_options.keys()), index=0)
    model_name = model_options[selected_model]
    
    temperature = st.slider("Temperature", 0.0, 0.7, 0.2, 0.05)
    search_depth = st.selectbox("Search Depth", ["basic", "advanced"], index=1)
    max_results = st.slider("Number of Sources", 5, 15, 10)
    
    st.divider()
    include_bias = st.toggle("Detect Bias", value=True)
    enable_chat = st.toggle("Enable Follow-up Chat", value=True)

# ====================== LLM & TAVILY ======================
@st.cache_resource(show_spinner=False)
def get_llm(_model_name, _temp):
    return ChatGroq(
        groq_api_key=groq_api,
        model_name=_model_name,
        temperature=_temp,
        max_tokens=2048
    )

llm = get_llm(model_name, temperature) if groq_api else None
tavily = TavilyClient(api_key=tavily_api) if tavily_api else None

# ====================== MAIN UI ======================
st.title("🛡️ TruthGuard AI")
st.markdown("**Expert Fact-Checker** — Live Web Search + Deep Analysis")
st.caption("Verify any claim, news, tweet or URL instantly")

input_content = st.text_area(
    "Paste your claim, news, tweet, or URL:",
    height=160,
    placeholder="Example: NASA has officially confirmed life on Europa..."
)

if st.button("🔍 Verify This Claim", type="primary", use_container_width=True):
    if not groq_api or not tavily_api:
        st.error("API keys missing. Add them in Streamlit Secrets.")
    elif not input_content.strip():
        st.warning("Please enter a claim to verify!")
    else:
        with st.spinner("🔎 Searching web + Analyzing with Llama 3.3..."):
            try:
                # Tavily Search
                search_results = tavily.search(
                    query=input_content[:250],
                    search_depth=search_depth,
                    max_results=max_results
                )
                
                context = "\n\n".join([
                    f"Source {i+1}: {r['url']}\nContent: {r['content'][:700]}..."
                    for i, r in enumerate(search_results.get('results', []))
                ])

                # Strong Fact-Check Prompt
                prompt = f"""
You are TruthGuard — a highly accurate, neutral fact-checker.

User Claim:
{input_content}

Live Search Evidence:
{context}

Return response in this exact structured format:

**Veracity Score:** X/100  
**Verdict:** True | Mostly True | Misleading | False | Unverified  

**Step-by-Step Analysis:**  
(Write 4-6 clear points explaining your reasoning)

**Key Evidence:**  
- Point 1 with source
- Point 2 with source

**Bias & Context Check:**  
(Any political, emotional or commercial bias detected?)

**Trusted Sources:**  
List 4-5 best sources with URLs

**Final Recommendation:**
"""

                response = llm.invoke(prompt)
                result_text = response.content

                # Save current check in session state
                if "current_claim" not in st.session_state:
                    st.session_state.current_claim = input_content
                    st.session_state.current_result = result_text
                    st.session_state.chat_history = []   # Reset chat for new claim

                st.success("✅ Fact-check completed successfully!")

                # Tabs
                tab_verdict, tab_analysis, tab_sources, tab_chat = st.tabs([
                    "⚖️ Verdict", "🔍 Detailed Analysis", "📌 Sources", "💬 Follow-up Chat"
                ])

                with tab_verdict:
                    st.subheader("Fact-Check Result")
                    st.markdown(result_text)

                with tab_analysis:
                    st.subheader("Step-by-Step Breakdown")
                    st.markdown(result_text)

                with tab_sources:
                    st.subheader("📚 Sources Used")
                    for i, r in enumerate(search_results.get('results', [])):
                        st.markdown(f"**{i+1}.** [{r['url']}]({r['url']})")
                        st.caption(r.get('content', '')[:350] + "...")

                with tab_chat:
                    if enable_chat:
                        st.markdown("**💬 Ask any follow-up question about this claim**")
                        
                        # Display chat history
                        for msg in st.session_state.get("chat_history", []):
                            with st.chat_message(msg["role"]):
                                st.markdown(msg["content"])
                        
                        # Chat Input
                        if user_question := st.chat_input("Type your question here and press Enter..."):
                            if "chat_history" not in st.session_state:
                                st.session_state.chat_history = []
                            
                            st.session_state.chat_history.append({"role": "user", "content": user_question})
                            with st.chat_message("user"):
                                st.markdown(user_question)
                            
                            with st.spinner("Thinking..."):
                                chat_prompt = f"""
User Claim: {st.session_state.current_claim}

Previous Fact-Check Result:
{st.session_state.current_result}

User Follow-up Question: {user_question}

Answer the question based on the claim and previous analysis. Be precise and helpful.
"""
                                answer = llm.invoke(chat_prompt).content
                                
                                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                                with st.chat_message("assistant"):
                                    st.markdown(answer)
                    else:
                        st.info("Follow-up chat is turned off in sidebar settings.")

                # Export
                st.download_button(
                    "⬇️ Download Full Report as Markdown",
                    st.session_state.current_result,
                    file_name=f"TruthGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    type="primary"
                )

            except Exception as e:
                st.error(f"Error: {e}")

# History (last few checks)
if "current_claim" in st.session_state:
    with st.expander("📜 Recent Fact-Checks"):
        st.write(f"**Current:** {st.session_state.current_claim[:100]}...")

st.caption("🛡️ TruthGuard Expert • Always cross-verify important information from official sources")
