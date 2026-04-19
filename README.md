# 🛡️ TruthGuard AI — Expert Content Verification Tool

An enterprise-grade, AI-powered fact-checking application designed to combat misinformation. TruthGuard AI utilizes **Tavily's Advanced Search API** to scour the web in real-time and **Groq's Llama 3.3 LPU** to critically analyze claims, ensuring you always know what's fact and what's fiction.

---

## ✨ Core Features

* **Real-Time Fact Checking:** Paste any news, tweet, or claim, and let the AI instantly cross-reference it with live global web data.
* **Comprehensive Verdicts:** Receives a structured report including a Veracity Score (0-100%), Final Verdict (True/False/Misleading), and a Step-by-Step Logical Analysis.
* **Bias Detection:** Identifies clickbait tactics, emotional manipulation, and logical fallacies within the user's claim.
* **Transparent Sourcing:** View all URLs and content snippets the AI used to formulate its decision.
* **Interactive Interrogation (Chat):** Ask follow-up questions directly to the AI regarding the specific claim and evidence.
* **Premium UI/UX:** A responsive, glassmorphism-inspired dark theme built for readability and professional use.
* **Downloadable Reports:** Export full fact-check analyses in Markdown format for record-keeping.

---

## 🛠️ Technology Stack

* **Frontend & Framework:** [Streamlit](https://streamlit.io/) (with Custom CSS)
* **Language Model:** [Llama 3.3 70B](https://groq.com/) (via LangChain)
* **Search Engine:** [Tavily Advanced Search API](https://tavily.com/)
* **Inference Engine:** Groq LPU (for near-instant generation)

---

## 🚀 Getting Started

### Prerequisites
1.  A free [Groq API Key](https://console.groq.com/keys)
2.  A free [Tavily API Key](https://app.tavily.com/)
3.  Python 3.9+

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/truthguard-ai.git](https://github.com/your-username/truthguard-ai.git)
    cd truthguard-ai
    ```

2.  **Install necessary dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Environment Variables:**
    Create a `.streamlit/secrets.toml` file in the root directory and add your keys:
    ```toml
    GROQ_API_KEY = "your_groq_api_key_here"
    TAVILY_API_KEY = "your_tavily_api_key_here"
    ```

4.  **Launch the application:**
    ```bash
    streamlit run app.py
    ```

---

## ⚙️ Configuration (Sidebar Controls)

* **LLM Core:** Switch between `llama-3.3-70b-versatile` and `llama3-70b-8192`.
* **Strictness (Temperature):** Adjust how "creative" the AI is. Lower values (default: 0.1) force strict factual adherence.
* **Search Depth:** Toggle between `basic` (faster) and `advanced` (more comprehensive) Tavily searches.
* **Max Sources:** Control how many distinct web sources the AI analyzes per query.

---

## ⚖️ Disclaimer
TruthGuard AI is a powerful assistant, but AI models can hallucinate or misinterpret context. Always cross-reference critical claims with official, trusted news outlets.
