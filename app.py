import streamlit as st
import os
from datetime import datetime
import re

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

# Premium CSS
st.markdown("""
<style>
    .main { background: linear-gradient(180deg, #0f172a 0%, #1e2937 100%); color: #e2e8f0; }
    .stButton>button { height: 52px; font-weight: 600; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { border-radius: 12px; padding: 10px 24px; }
    .verdict-card { background: rgba(255,255,255,0.08); border-radius: 16px; padding: 20px; border: 1px solid #00ff88; }
</style>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
groq_api = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
tavily_api = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

# ====================== SIDEBAR — PRO SETTINGS ======================
with st.sidebar:
    st.title("🛡️ TruthGuard Expert")
    st.caption("Live Fact-Checking • Powered by Groq + Tavily")
    
    if not groq_api or not tavily_api:
        st.warning("⚠️ API Keys missing in Secrets!")
        temp_groq = st.text_input("Groq API Key", type="password")
        temp_tavily = st.text_input("Tavily API Key", type="password")
        if temp_groq and temp_tavily:
            groq_api, tavily_api = temp_groq, temp_tavily
    else:
        st.success("✅ Both APIs Connected")
    
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
    st.markdown("**Advanced Options**")
    include_bias = st.toggle("Detect Political/Social Bias", value=True)
    enable_chat = st.toggle("Enable Follow-up Chat", value=True)

# ====================== LLM & TAVILY INIT ======================
@st.cache_resource(show_spinner=False)
def get_llm(_model_name, _temp):
    return ChatGroq(
        groq_api_key=groq_api,
        model_name=_model_name,
        temperature=_temp,
        max_tokens=2048
    )

llm = get_llm(model_name, temperature)
tavily = TavilyClient(api_key=tavily_api) if tavily_api else None

# ====================== MAIN UI ======================
st.title("🛡️ TruthGuard AI")
st.markdown("**Expert Fact-Checker** — Real-time web search + Deep Llama 3.3 analysis")
st.caption("Verify news, claims, social media posts, articles & URLs instantly")

input_content = st.text_area(
    "Paste claim, news, tweet, article or URL here:",
    height=160,
    placeholder="Example: NASA has confirmed alien life on Europa... or paste any URL"
)

if st.button("🔍 Verify This Claim", type="primary", use_container_width=True):
    if not groq_api or not tavily_api:
        st.error("API keys missing. Please add them in Streamlit Secrets.")
    elif not input_content.strip():
        st.warning("Please enter some content to verify!")
    else:
        with st.spinner("🔎 Searching live web + Analyzing with Llama 3.3..."):
            try:
                # Search the web
                search_query = input_content[:250]
                search_results = tavily.search(
                    query=search_query,
                    search_depth=search_depth,
                    max_results=max_results
                )
                
                context = "\n\n".join([
                    f"Source {i+1}: {r['url']}\nContent: {r['content'][:800]}..."
                    for i, r in enumerate(search_results.get('results', []))
                ])

                # Enhanced prompt for step-by-step detailed output
                prompt = f"""
You are TruthGuard — a world-class, unbiased fact-checker.

User Claim:
{input_content}

Live Web Evidence:
{context}

Provide a detailed, professional fact-check report with these exact sections:

1. **Veracity Score**: Give a score out of 100 (e.g., 92/100)
2. **Final Verdict**: True | Mostly True | Misleading | False | Unverified
3. **Step-by-Step Analysis**: Explain your reasoning in clear numbered steps
4. **Key Evidence**: List the strongest supporting or contradicting facts with sources
5. **Bias & Context Check**: (if enabled) Any political, commercial or emotional bias detected?
6. **Trusted Sources**: List 3-5 most reliable sources with URLs
7. **Recommendation**: What should the reader believe or do next?

Be extremely precise, neutral and evidence-based.
"""

                response = llm.invoke(prompt)
                result_text = response.content

                # Save to session state
                if "fact_checks" not in st.session_state:
                    st.session_state.fact_checks = []
                
                st.session_state.fact_checks.append({
                    "claim": input_content,
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "result": result_text
                })

                # ====================== DISPLAY RESULTS ======================
                st.success("✅ Fact-check completed!")

                tab_verdict, tab_analysis, tab_sources, tab_chat = st.tabs([
                    "⚖️ Verdict", "🔍 Step-by-Step Analysis", "📌 Sources", "💬 Follow-up Chat"
                ])

                with tab_verdict:
                    st.subheader("Fact-Check Result")
                    st.markdown(result_text)

                with tab_analysis:
                    st.subheader("Deep Step-by-Step Breakdown")
                    st.info("Llama 3.3 has analyzed the claim against live web sources.")
                    st.markdown(result_text)

                with tab_sources:
                    st.subheader("📚 All Sources Used")
                    for i, r in enumerate(search_results.get('results', [])):
                        st.markdown(f"**{i+1}.** [{r['url']}]({r['url']})")
                        st.caption(r['content'][:300] + "...")

                with tab_chat:
                    if enable_chat:
                        st.markdown("**Ask follow-up questions about this claim**")
                        for msg in st.session_state.get("chat_history", []):
                            with st.chat_message(msg["role"]):
                                st.markdown(msg["content"])
                        
                        if prompt_chat := st.chat_input("Example: Why is this misleading?"):
                            if "chat_history" not in st.session_state:
                                st.session_state.chat_history = []
                            
                            st.session_state.chat_history.append({"role": "user", "content": prompt_chat})
                            with st.chat_message("user"):
                                st.markdown(prompt_chat)
                            
                            with st.spinner("Thinking..."):
                                chat_prompt = f"User Claim: {input_content}\n\nPrevious Fact-Check:\n{result_text}\n\nQuestion: {prompt_chat}"
                                answer = llm.invoke(chat_prompt).content
                                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                                with st.chat_message("assistant"):
                                    st.markdown(answer)
                    else:
                        st.info("Follow-up chat is disabled in settings.")

                # Export button
                st.download_button(
                    "⬇️ Download Full Fact-Check Report",
                    result_text,
                    file_name=f"truthguard_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    type="primary"
                )

            except Exception as e:
                st.error(f"Error during verification: {e}")

# Previous checks history (optional)
if "fact_checks" in st.session_state and st.session_state.fact_checks:
    with st.expander("📜 Previous Fact-Checks"):
        for check in reversed(st.session_state.fact_checks[-5:]):
            st.write(f"**{check['timestamp']}** — {check['claim'][:80]}...")

st.caption("🛡️ TruthGuard Expert • Made for accurate, transparent fact-checking • Always verify important claims yourself")
