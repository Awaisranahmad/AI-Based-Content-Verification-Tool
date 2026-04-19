import streamlit as st
import os
from langchain_groq import ChatGroq
from tavily import TavilyClient
import validators

# --- Page Config ---
st.set_page_config(page_title="AI Truth Guard", page_icon="🛡️", layout="wide")

# --- API Keys ---
# Groq aur Tavily ki keys secrets mein honi chaiye
groq_api = st.secrets.get("GROQ_API_KEY")
tavily_api = st.secrets.get("TAVILY_API_KEY")

if not groq_api or not tavily_api:
    st.error("🚨 API Keys missing! Add GROQ_API_KEY and TAVILY_API_KEY in Secrets.")
    st.stop()

# Initialize Clients
llm = ChatGroq(groq_api_key=groq_api, model_name="llama-3.3-70b-versatile")
tavily = TavilyClient(api_key=tavily_api)

st.title("🛡️ AI Content Verifier (Fake News Detector)")
st.markdown("Paste news snippets, social media posts, or links to verify their authenticity.")

# Input Section
input_text = st.text_area("Enter Content to Verify:", placeholder="e.g., NASA has found a city on Mars...", height=150)

if st.button("🔍 Verify Authenticity", type="primary"):
    if input_text:
        with st.spinner("Searching the web and analyzing facts..."):
            # 1. Search for related facts
            search_result = tavily.search(query=input_text, search_depth="advanced")
            context = "\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in search_result['results']])

            # 2. LLM Analysis
            prompt = f"""
            You are a professional fact-checker. Compare the 'User Content' with the 'Search Context' provided.
            Analyze for:
            1. Factual accuracy.
            2. Potential bias or misinformation.
            3. Sources credibility.

            User Content: {input_text}
            ---
            Search Context: {context}
            ---
            Provide a:
            - **Veracity Score** (0% to 100%)
            - **Verdict** (True, False, Misleading, or Unverified)
            - **Brief Explanation**
            - **Key Sources**
            """
            
            response = llm.invoke(prompt)
            
            # --- Results Display ---
            st.divider()
            st.subheader("⚖️ Fact-Check Result")
            st.write(response.content)
    else:
        st.warning("Pehle kuch text to likho!")

# Sidebar for Info
with st.sidebar:
    st.info("Ye tool LLM aur real-time web search ko use kar ke content ko verify karta hai.")
    st.caption("Powered by Groq + Tavily")
