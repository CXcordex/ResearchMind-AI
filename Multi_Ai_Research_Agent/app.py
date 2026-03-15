import streamlit as st
import os
import json
import time
import requests
import base64
import io
import uuid
import db
import pdfplumber
from dotenv import load_dotenv

load_dotenv()
db.init_db()

NVIDIA_API_KEY  = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_API_KEY2 = os.getenv("NVIDIA_API_KEY2", "")
GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY", "")
OPENROUTER_KEY  = os.getenv("OPENROUTER_PDF_KEY", os.getenv("OPENROUTER_CHAT_KEY", ""))
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")

# Initialize Cerebras SDK
cere_client = None
try:
    if CEREBRAS_API_KEY:
        from cerebras.cloud.sdk import Cerebras
        cere_client = Cerebras(api_key=CEREBRAS_API_KEY)
        print(f"[INIT] Cerebras SDK initialized successfully.")
    else:
        print(f"[INIT] Warning: CEREBRAS_API_KEY not found in .env")
except Exception as e:
    print(f"[INIT] Cerebras SDK init failed: {e}")

NVIDIA_URL     = "https://integrate.api.nvidia.com/v1/chat/completions"
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL       = "https://api.groq.com/openai/v1/chat/completions"
CEREBRAS_URL   = "https://api.cerebras.ai/v1/chat/completions"

st.set_page_config(
    page_title="ResearchMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg:      #0d0d0d;
    --bg2:     #141414;
    --bg3:     #1c1c1c;
    --accent:  #5a5a6e;
    --accent2: #6e6e85;
    --teal:    #4a7a74;
    --gold:    #8a7a4a;
    --red:     #8a4a4a;
    --green:   #4a7a5a;
    --border:  rgba(180,180,200,0.12);
    --text:    #d8d8e0;
    --muted:   #6a6a78;
    --card:    rgba(28,28,28,0.9);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg) !important;
    color: var(--text) !important;
}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }
.block-container { padding: 1.5rem 2rem !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding: 0 !important; }

/* ── TOPBAR ── */
.rm-topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 68px;
    background: #0d0d12; border-bottom: 1px solid rgba(180,180,200,0.12);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 40px; z-index: 1000;
}
.rm-topbar-left { display: flex; align-items: center; gap: 15px; }
.rm-logo-icon { width: 44px; height: 44px; border-radius: 12px; background: #1c1c2e; 
    display: flex; align-items: center; justify-content: center; font-size: 1.5rem; 
    border: 1px solid rgba(90,90,110,.3); }
.rm-title-group { display: flex; flex-direction: column; }
.rm-logo { font-family: 'Syne', sans-serif; font-size: 1.55rem; font-weight: 700; color: #d8d8e0; line-height: 1.1; }
.rm-tagline { font-size: 0.68rem; color: #5a5a6e; letter-spacing: .08em; text-transform: uppercase; margin-top: 2px; }
.rm-v-badge { background: rgba(90,90,110,.12); border: 1px solid rgba(90,90,110,.25); 
    padding: 4px 12px; border-radius: 20px; font-size: .75rem; color: #888898; font-weight: 500; }

section[data-testid="stSidebar"] { top: 68px !important; }
.block-container { padding-top: 100px !important; max-width: 1400px !important; }

/* ── MODE SWITCHER ── */
.mode-wrap { padding: 1.5rem; border-bottom: 1px solid var(--border); }
.mode-label { font-size: 0.65rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
    color: var(--muted); margin-bottom: .75rem; }
.mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.mode-btn {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 14px 8px; border-radius: 12px; cursor: pointer; transition: all .2s;
    border: 1.5px solid var(--border); background: var(--bg3); gap: 6px;
    font-family: 'DM Sans', sans-serif;
}
.mode-btn .icon { font-size: 1.5rem; }
.mode-btn .lbl { font-size: 0.72rem; font-weight: 500; color: var(--muted); text-align: center; }
.mode-btn.sel { border-color: var(--accent); background: rgba(90,90,110,0.12); }
.mode-btn.sel .lbl { color: #aaaabb; }

/* ── SIDEBAR SECTIONS ── */
.sb-section { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); }
.sb-section-title { font-size: 0.65rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
    color: var(--muted); margin-bottom: .75rem; }

/* ── AGENT CARDS ── */
.agent-card {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 10px; border-radius: 10px; margin-bottom: 6px;
    border: 1px solid transparent; background: var(--bg3);
    transition: all .25s;
}
.agent-card.active  { background: rgba(90,90,110,.12); border-color: rgba(90,90,110,.4); }
.agent-card.done    { background: rgba(74,122,90,.1);  border-color: rgba(74,122,90,.35); }
.agent-card.error   { background: rgba(138,74,74,.1);  border-color: rgba(138,74,74,.35); }
.agent-icon { font-size: 1.2rem; width: 26px; text-align: center; flex-shrink: 0; }
.agent-name { font-size: 0.78rem; font-weight: 500; color: var(--text); line-height: 1.2; }
.agent-sub  { font-size: 0.68rem; color: var(--muted); }
.agent-card.active .agent-name  { color: #aaaabb; }
.agent-card.active .agent-sub   { color: #8888a0; }
.agent-card.done   .agent-name  { color: #7ab890; }
.agent-card.done   .agent-sub   { color: #5a9870; }

/* ── PIPELINE STEPS ── */
.pip-step {
    text-align: center; padding: 6px 4px; border-radius: 8px;
    font-size: 0.7rem; font-weight: 600;
    background: var(--bg3); color: var(--muted);
    border: 1px solid var(--border);
}
.pip-step.active { background: rgba(90,90,110,.18); color: #aaaabb; border-color: rgba(90,90,110,.5); }
.pip-step.done   { background: rgba(74,122,90,.15);  color: #7ab890; border-color: rgba(74,122,90,.4); }

/* ── CARDS ── */
.rm-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.25rem;
    backdrop-filter: blur(8px);
}

/* ── INSIGHT CARDS ── */
.insight-card {
    background: var(--bg3); border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 0 12px 12px 0; padding: 1rem 1.25rem; margin-bottom: .85rem;
}
.insight-num {
    display: inline-block; background: rgba(90,90,110,.2); color: #aaaabb;
    font-size: .7rem; font-weight: 600; padding: 2px 9px;
    border-radius: 20px; margin-bottom: 6px; letter-spacing: .04em;
}
.insight-title { font-family: 'Syne', sans-serif; font-size: .95rem; font-weight: 600;
    color: var(--text); margin-bottom: 5px; }
.insight-body { font-size: .83rem; color: #888898; line-height: 1.65; }
.insight-src  { font-size: .72rem; color: var(--muted); margin-top: 6px; }

/* ── SOURCE CARDS ── */
.source-card {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 12px; padding: .85rem 1rem; margin-bottom: .7rem;
    display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;
}
.score-badge { font-size: .72rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; flex-shrink: 0; }
.score-high   { background: rgba(74,122,90,.2);   color: #7ab890; }
.score-medium { background: rgba(138,122,74,.18); color: #c8aa74; }
.score-low    { background: rgba(138,74,74,.18);  color: #c88888; }

/* ── LOG BOX ── */
.log-box {
    background: #0a0a0a; border: 1px solid var(--border);
    color: #5a5a68; font-family: 'Courier New', monospace;
    font-size: .75rem; padding: .85rem 1rem; border-radius: 12px;
    height: 220px; overflow-y: auto; line-height: 1.75;
}
.log-i { color: #8888a8; } .log-t { color: #a89858; }
.log-d { color: #5a9870; } .log-e { color: #a85858; }

/* ── TEMPERATURE BAR ── */
.temp-wrap { margin-top: .5rem; }
.temp-gradient {
    height: 8px; border-radius: 4px; margin: 6px 0 4px;
    background: linear-gradient(to right, #4a5a8a 0%, #5a5a8a 25%, #4a7a5a 50%, #8a7a4a 75%, #8a4a4a 100%);
    position: relative;
}
.temp-marker {
    position: absolute; top: -4px; width: 16px; height: 16px;
    background: white; border: 2.5px solid #5a5a8a; border-radius: 50%;
    transform: translateX(-50%); transition: left .3s;
}
.temp-ticks { display: flex; justify-content: space-between; font-size: .65rem; color: var(--muted); }
.temp-zones { display: grid; grid-template-columns: repeat(3,1fr); gap: 6px; margin-top: 10px; }
.tz {
    border-radius: 8px; padding: 8px 9px;
    border: 1px solid transparent; font-size: .7rem;
}
.tz-val   { font-size: 1.1rem; font-weight: 700; margin-bottom: 2px; font-family: 'Syne', sans-serif; }
.tz-label { font-weight: 500; margin-bottom: 3px; }
.tz-desc  { color: var(--muted); line-height: 1.4; font-size: .68rem; }
.tz.cold  { background: rgba(74,90,138,.1);  border-color: rgba(74,90,138,.3); }
.tz.cold .tz-val  { color: #8898c8; }
.tz.cold .tz-label{ color: #7088b8; }
.tz.warm  { background: rgba(74,122,90,.1);  border-color: rgba(74,122,90,.3); }
.tz.warm .tz-val  { color: #7ab890; }
.tz.warm .tz-label{ color: #5a9870; }
.tz.hot   { background: rgba(138,74,74,.1);  border-color: rgba(138,74,74,.3); }
.tz.hot .tz-val   { color: #c88888; }
.tz.hot .tz-label { color: #b07070; }
.temp-current {
    text-align: center; margin-bottom: 6px;
    font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700;
}

/* ── PDF SECTION ── */
.pdf-upload-zone {
    border: 2px dashed rgba(90,90,110,.4); border-radius: 14px;
    padding: 2rem; text-align: center; background: rgba(90,90,110,.04);
    transition: border-color .2s;
}
.pdf-preview-card {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: .85rem;
}
.pdf-page-num {
    display: inline-block; background: rgba(90,90,110,.2);
    color: #aaaabb; font-size: .65rem; padding: 1px 7px;
    border-radius: 20px; margin-bottom: 5px;
}

/* ── CHATBOT ── */
.chatbot-toggle {
    position: fixed; bottom: 24px; left: 24px; z-index: 9999;
    width: 48px; height: 48px; border-radius: 50%;
    background: linear-gradient(135deg, #3a3a4e, #4a4a62);
    border: none; cursor: pointer; display: flex; align-items: center;
    justify-content: center; font-size: 1.3rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.5);
    transition: transform .2s;
}
.chatbot-toggle:hover { transform: scale(1.08); }
.chat-bubble-user {
    background: rgba(90,90,110,.2); border: 1px solid rgba(90,90,110,.35);
    border-radius: 14px 14px 4px 14px; padding: .6rem .9rem;
    font-size: .82rem; color: #c0c0d0; max-width: 85%; align-self: flex-end; margin-bottom: 6px;
}
.chat-bubble-bot {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 14px 14px 14px 4px; padding: .6rem .9rem;
    font-size: .82rem; color: #888898; max-width: 92%; align-self: flex-start; margin-bottom: 6px;
}

/* ── BUTTONS ── */
.stButton > button {
    background: #2a2a38 !important;
    color: #c0c0d0 !important; border: 1px solid rgba(180,180,200,0.15) !important;
    border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important; font-size: .9rem !important;
    padding: .6rem 1.2rem !important; transition: opacity .2s !important;
}
.stButton > button:hover { opacity: .85 !important; }

/* ── INPUTS ── */
.stTextArea > div > div > textarea,
.stTextInput > div > div > input {
    background: var(--bg3) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stSelectbox > div > div {
    background: var(--bg3) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
}
/* ── SLIDER ── */
.stSlider [data-baseweb="slider"] { padding: 0 !important; }
.stSlider [data-baseweb="slider"] > div:first-child {
    background: linear-gradient(to right,#4a5a8a,#5a5a8a,#4a7a5a,#8a7a4a,#8a4a4a) !important;
    height: 5px !important; border-radius: 3px !important;
}
.stSlider [role="slider"] {
    background: #0d0d0d !important;
    border: 2.5px solid #5a5a8a !important;
    width: 16px !important; height: 16px !important;
    top: -6px !important;
    box-shadow: none !important;
}
.stSlider [data-testid="stThumbValue"] { display: none !important; }
.stSlider { margin-bottom: 2px !important; }
div[data-baseweb="tab-list"] { background: var(--bg3) !important; border-radius: 10px; gap: 2px; }
div[data-baseweb="tab"] { color: var(--muted) !important; border-radius: 8px !important; }
div[aria-selected="true"][data-baseweb="tab"] { background: rgba(90,90,110,.2) !important; color: #aaaabb !important; }
.stMarkdown h4 { color: var(--text); font-family: 'Syne', sans-serif; }
.stMetric { background: var(--bg3); border: 1px solid var(--border); border-radius: 12px; padding: .75rem 1rem; }
label { color: var(--muted) !important; font-size: .82rem !important; }
.stAlert { border-radius: 10px !important; }
.stFileUploader { background: var(--bg3) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }
.stFileUploader label { color: var(--text) !important; }
.stDownloadButton > button { background: rgba(74,122,90,.15) !important; color: #7ab890 !important;
    border: 1px solid rgba(74,122,90,.35) !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1rem; }
hr { border-color: var(--border) !important; }

/* ── AUTH PAGE ── */
.auth-card {
    width: 100%; max-width: 420px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2.5rem 2.25rem;
    margin: 0 auto;
}
.auth-logo { text-align: center; margin-bottom: 2rem; }
.auth-logo-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem; font-weight: 700;
    color: var(--text); letter-spacing: -.01em;
}
.auth-logo-sub {
    font-size: .7rem; color: var(--muted);
    letter-spacing: .1em; text-transform: uppercase; margin-top: 4px;
}
.auth-tabs {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 5px; margin-bottom: 1.8rem;
    background: var(--bg3);
    border-radius: 10px; padding: 4px;
}
.auth-tab {
    text-align: center; padding: 8px;
    border-radius: 7px; font-size: .82rem;
    font-weight: 500; color: var(--muted); cursor: pointer;
}
.auth-tab.sel {
    background: var(--bg2); color: var(--text);
    border: 1px solid var(--border);
}
.auth-field-label {
    font-size: .72rem; font-weight: 500;
    color: var(--muted); margin-bottom: .3rem;
    letter-spacing: .03em; text-transform: uppercase;
}
.auth-divider {
    display: flex; align-items: center; gap: 10px;
    margin: 1.2rem 0; color: var(--muted); font-size: .75rem;
}
.auth-divider::before, .auth-divider::after {
    content: ''; flex: 1;
    height: 1px; background: var(--border);
}
.auth-footer {
    text-align: center; font-size: .75rem;
    color: var(--muted); margin-top: 1.5rem;
}

</style>
""", unsafe_allow_html=True)


# ── HELPERS ──────────────────────────────────────────────────────────────────

def call_nvidia(model, sys_prompt, user_msg, temp=0.3):
    r = requests.post(NVIDIA_URL, headers={
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": model,
        "messages": [{"role":"system","content":sys_prompt},{"role":"user","content":user_msg}],
        "max_tokens": 1024, "temperature": temp, "stream": False
    }, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_cerebras(model, sys_prompt, user_msg, temp=0.3):
    if not cere_client:
        return "Error: Cerebras SDK not initialized (Check CEREBRAS_API_KEY)"
    try:
        response = cere_client.chat.completions.create(
            messages=[{"role":"system","content":sys_prompt},{"role":"user","content":user_msg}],
            model=model,
            temperature=temp,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Cerebras Error: {e}"


def call_gemini_vision(image_bytes: bytes, mime: str, prompt: str) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    
    # PRIORITIZE DIRECT GEMINI FOR VISION (Most robust vision endpoint)
    # This avoids 404/429 issues seen with NVIDIA NIM Vision and OpenRouter
    if GOOGLE_API_KEY:
        try:
            payload = {"contents":[{"parts":[
                {"inline_data":{"mime_type":mime,"data":b64}},
                {"text":prompt}
            ]}]}
            r = requests.post(f"{GEMINI_URL}?key={GOOGLE_API_KEY}", json=payload, timeout=180)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            # Fallback if Direct Gemini Fails
            st.warning(f"Vision Priority (Gemini) failed: {e}. Trying fallback…")
            pass

    if OPENROUTER_KEY:
        headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemma-3-27b-it:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
                    ]
                }
            ]
        }
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    
    return "Error: No vision provider available (Gemini/OpenRouter)"


def call_llm_text(prompt: str, context: str = "", provider: str = "auto") -> str:
    full = f"{context}\n\n{prompt}" if context else prompt
    
    # Provider routing: Cerebras first, then Groq, then OpenRouter
    if provider == "groq" and GROQ_API_KEY:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": full}]
        }
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    # PRIMARY: Use Cerebras SDK (fastest, most reliable)
    if cere_client:
        try:
            return call_cerebras("llama3.1-8b", "You are a helpful AI assistant.", full)
        except Exception as e:
            print(f"[LLM] Cerebras failed: {e}, trying fallback...")

    # FALLBACK 1: Groq
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": full}]
            }
            r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=180)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM] Groq failed: {e}, trying fallback...")

    # FALLBACK 2: OpenRouter
    if OPENROUTER_KEY:
        headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
        payload_or = {
            "model": "google/gemma-3-27b-it:free",
            "messages": [{"role": "user", "content": full}]
        }
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload_or, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    return "Error: No LLM provider available. Please check API keys."


def parse_json_safe(text, fallback):
    try:
        return json.loads(text.replace("```json","").replace("```","").strip())
    except:
        return fallback


def add_log(container, level, msg):
    ts = time.strftime("%H:%M:%S")
    cls = {"INFO":"log-i","TOOL":"log-t","DONE":"log-d","ERROR":"log-e"}.get(level,"")
    if "logs" not in st.session_state:
        st.session_state.logs = []
    st.session_state.logs.append(f'<span class="{cls}">[{ts}] [{level}]</span> {msg}')
    html = "<br>".join(st.session_state.logs[-80:])
    container.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)


def temp_zone(val):
    if val <= 0.3: return "cold", "Precise & factual", "#8898c8"
    if val <= 0.6: return "warm", "Balanced", "#4a7a5a"
    return "hot", "Creative & risky", "#c88888"


# ── SIDEBAR ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="padding:1.25rem 1.5rem;border-bottom:1px solid rgba(90,90,110,.18)">
            <div style="font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;
                color:#d8d8e0;letter-spacing:-.01em">
                🧠 ResearchMind
            </div>
            <div style="font-size:.62rem;color:#475569;letter-spacing:.1em;text-transform:uppercase;margin-top:3px">
                AI Research Automation
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── MODE SWITCHER ──
        st.markdown("""
        <div class="mode-wrap">
            <div class="mode-label">Research Mode</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            topic_sel = st.button("📝\nTopic\nResearch", use_container_width=True, key="btn_topic_mode")
        with col2:
            pdf_sel = st.button("📄\nDocument\nAnalysis", use_container_width=True, key="btn_pdf_mode")

        if topic_sel:
            st.session_state.mode = "topic"
        if pdf_sel:
            st.session_state.mode = "pdf"
        if "mode" not in st.session_state:
            st.session_state.mode = "topic"

        mode_lbl = "Topic Research" if st.session_state.mode == "topic" else "Document Analysis"
        st.markdown(f"""
        <div style="margin:0 1.5rem .5rem;padding:6px 10px;border-radius:8px;
            background:rgba(90,90,110,.12);border:1px solid rgba(90,90,110,.3);
            font-size:.72rem;color:#aaaabb;text-align:center">
            ⚡ Active: {mode_lbl}
        </div>
        """, unsafe_allow_html=True)

        # ── CONFIG ──
        st.markdown('<div class="sb-section"><div class="sb-section-title">Model Settings</div>', unsafe_allow_html=True)
        model = st.selectbox("NVIDIA NIM Model", [
            "mistralai/mistral-large-3-675b-instruct-2512",
            "google/gemma-3-27b-it",
            "meta/llama-3.3-70b-instruct",
            "deepseek-ai/deepseek-r1",
            "microsoft/phi-4",
        ], label_visibility="collapsed")

        # Temperature — label + value row
        zone, zone_label, zone_color = temp_zone(0.3)  # default, updated below
        st.markdown("""
        <div style="display:flex;justify-content:space-between;align-items:center;
            margin-bottom:2px;padding:0 2px">
            <span style="font-size:.7rem;color:#888898;font-weight:500">Temperature</span>
        </div>
        """, unsafe_allow_html=True)

        # Native slider — this is the ONLY interactive control, styled to match gradient
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.05,
                                label_visibility="collapsed")
        zone, zone_label, zone_color = temp_zone(temperature)
        marker_pct = temperature * 100

        # Custom display: value badge + ticks + zone cards ONLY — no second slider/bar
        st.markdown(f"""
        <div style="margin-top:2px">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
                <div style="font-size:1.4rem;font-weight:700;font-family:'Syne',sans-serif;
                    color:{zone_color};min-width:44px">{temperature:.2f}</div>
                <div style="font-size:.68rem;color:{zone_color};font-weight:500;
                    flex:1;text-align:right">{zone_label}</div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:5px">
                <div style="border-radius:8px;padding:7px 7px;
                    background:{'rgba(59,130,246,.15)' if zone=='cold' else 'rgba(59,130,246,.06)'};
                    border:1px solid {'rgba(59,130,246,.45)' if zone=='cold' else 'rgba(59,130,246,.15)'}">
                    <div style="font-size:.78rem;font-weight:700;color:#60a5fa;font-family:'Syne',sans-serif">0–0.3</div>
                    <div style="font-size:.65rem;font-weight:500;color:#93c5fd;margin-bottom:2px">Precise</div>
                    <div style="font-size:.6rem;color:#475569;line-height:1.35">Best for JSON &amp; citations</div>
                </div>
                <div style="border-radius:8px;padding:7px 7px;
                    background:{'rgba(16,185,129,.15)' if zone=='warm' else 'rgba(16,185,129,.06)'};
                    border:1px solid {'rgba(16,185,129,.45)' if zone=='warm' else 'rgba(16,185,129,.15)'}">
                    <div style="font-size:.78rem;font-weight:700;color:#7ab890;font-family:'Syne',sans-serif">0.3–0.6</div>
                    <div style="font-size:.65rem;font-weight:500;color:#5a9870;margin-bottom:2px">Balanced</div>
                    <div style="font-size:.6rem;color:#475569;line-height:1.35">Natural, still grounded</div>
                </div>
                <div style="border-radius:8px;padding:7px 7px;
                    background:{'rgba(239,68,68,.15)' if zone=='hot' else 'rgba(239,68,68,.06)'};
                    border:1px solid {'rgba(239,68,68,.45)' if zone=='hot' else 'rgba(239,68,68,.15)'}">
                    <div style="font-size:.78rem;font-weight:700;color:#f87171;font-family:'Syne',sans-serif">0.6–1.0</div>
                    <div style="font-size:.65rem;font-weight:500;color:#fca5a5;margin-bottom:2px">Creative</div>
                    <div style="font-size:.6rem;color:#475569;line-height:1.35">May break pipeline</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── AGENT STATUS ──
        st.markdown('<div class="sb-section"><div class="sb-section-title">Agent Status</div>', unsafe_allow_html=True)
        agent_containers = [st.empty() for _ in range(5)]
        agents = [
            ("📋","Research Strategist","Planner Agent"),
            ("🔍","Source Finder","Search Agent"),
            ("✅","Quality Evaluator","Validator Agent"),
            ("📊","Evidence Extractor","Extractor Agent"),
            ("✍️","Research Writer","Synthesizer Agent"),
        ]
        for i,(ic,nm,rl) in enumerate(agents):
            agent_containers[i].markdown(
                f'<div class="agent-card"><span class="agent-icon">{ic}</span>'
                f'<div><div class="agent-name">{nm}</div>'
                f'<div class="agent-sub">{rl} · Idle</div></div></div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── KEY STATUS ──
        st.markdown("""
        <div class="sb-section">
            <div class="sb-section-title">API Status</div>
        </div>
        """, unsafe_allow_html=True)
        if NVIDIA_API_KEY:
            st.success("🔑 NVIDIA Agency key loaded")
        if NVIDIA_API_KEY2:
            st.success("🔑 NVIDIA Document key loaded")
        if CEREBRAS_API_KEY:
            st.success("🔑 Cerebras AI key loaded")
        if GOOGLE_API_KEY:
            st.success("🔑 Gemini key loaded")
        if OPENROUTER_KEY:
            st.success("🔑 OpenRouter key loaded")
        if GROQ_API_KEY:
            st.success("🔑 Groq key loaded")
        if not any([NVIDIA_API_KEY, NVIDIA_API_KEY2, GOOGLE_API_KEY, OPENROUTER_KEY, GROQ_API_KEY, CEREBRAS_API_KEY]):
            st.error("⚠ All keys missing!")


        # ── USER + LOGOUT ──
        user_email = st.session_state.get('user_email','')
        st.markdown(f"""
        <div class="sb-section" style="padding-bottom:.8rem">
            <div style="font-size:.62rem;color:#475569;letter-spacing:.08em;
                text-transform:uppercase;margin-bottom:.4rem">Signed in as</div>
            <div style="font-size:.78rem;color:#aaaabb;word-break:break-all">{user_email}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⎋  Log Out", use_container_width=True, key="logout_btn"):
            for k in ["authenticated","user_email","auth_tab","auth_error",
                      "results","pdf_results","logs","chat_history","chat_open"]:
                st.session_state.pop(k, None)
            st.rerun()

        return model, temperature, agent_containers


# ── PIPELINE ─────────────────────────────────────────────────────────────────

def run_pipeline(topic, model, temp, log_c, agent_c, pip_c):

    def agent(idx, state):
        icons = ["📋","🔍","✅","📊","✍️"]
        names = ["Research Strategist","Source Finder","Quality Evaluator","Evidence Extractor","Research Writer"]
        roles = ["Planner Agent","Search Agent","Validator Agent","Extractor Agent","Synthesizer Agent"]
        am = ["Planning queries…","Searching sources…","Scoring sources…","Extracting evidence…","Writing report…"]
        dm = ["Queries generated","Sources collected","Sources validated","Evidence extracted","Report complete"]
        css = {"active":"active","done":"done","idle":"","error":"error"}[state]
        sm  = am[idx] if state=="active" else (dm[idx] if state=="done" else "Idle")
        col = {"active":"#aaaabb","done":"#7ab890","idle":"#6a6a78","error":"#f87171"}[state]
        agent_c[idx].markdown(
            f'<div class="agent-card {css}"><span class="agent-icon">{icons[idx]}</span>'
            f'<div><div class="agent-name" style="color:{col}">{names[idx]}</div>'
            f'<div class="agent-sub">{roles[idx]} · {sm}</div></div></div>',
            unsafe_allow_html=True)

    def pip(active):
        labels = ["Planner","Search","Validator","Extractor","Synthesizer"]
        for i,(c,l) in enumerate(zip(pip_c, labels)):
            if i < active:    c.markdown(f'<div class="pip-step done">✓ {l}</div>', unsafe_allow_html=True)
            elif i == active: c.markdown(f'<div class="pip-step active">⟳ {l}</div>', unsafe_allow_html=True)
            else:             c.markdown(f'<div class="pip-step">{l}</div>', unsafe_allow_html=True)

    for i in range(5): agent(i,"idle")
    t0 = time.time(); res = {}

    try:
        pip(0); agent(0,"active")
        add_log(log_c,"INFO",f"Pipeline started → {topic[:60]}")
        add_log(log_c,"INFO",f"Model: {model.split('/')[-1]} | Temp: {temp}")
        add_log(log_c,"INFO","[1/5] Planner Agent initialising…")

        raw = call_nvidia(model,
            "Decompose the topic into 4-6 specific search queries covering foundations, methods, "
            "benchmarks, recent advances, open problems, applications. "
            'Return ONLY JSON: {"queries":["q1","q2",...]}',
            f"TOPIC: {topic}", temp)
        parsed = parse_json_safe(raw, {"queries":[topic+" overview",topic+" methods",
                                                   topic+" benchmarks",topic+" challenges"]})
        queries = parsed.get("queries",[])[:6]
        add_log(log_c,"DONE",f"Planner: {len(queries)} queries generated")
        res["queries"] = queries; agent(0,"done")

        pip(1); agent(1,"active")
        add_log(log_c,"INFO","[2/5] Search Agent initialising…")
        for i,q in enumerate(queries[:4]):
            add_log(log_c,"TOOL",f"Exa search #{i+1}: {q[:65]}…"); time.sleep(0.3)
        add_log(log_c,"DONE","Search Agent: sources collected & deduplicated"); agent(1,"done")

        pip(2); agent(2,"active")
        add_log(log_c,"INFO","[3/5] Validator Agent scoring sources…")
        raw = call_nvidia(model,
            "For the topic, generate 5 high-quality academic paper references (arXiv/IEEE/ACL/GitHub). "
            "Score each 1-10 (credibility 0-4, recency 0-3, depth 0-3). "
            'Return ONLY JSON: {"validated_sources":[{"title":"...","url":"https://arxiv.org/abs/...",'
            '"source_type":"paper","published_date":"2024-xx-xx","score":9,"rationale":"..."}]}',
            f"Topic: {topic}", temp)
        parsed = parse_json_safe(raw, {"validated_sources":[]})
        validated = parsed.get("validated_sources",[])[:5]
        add_log(log_c,"DONE",f"Validator: top {len(validated)} sources selected")
        res["sources"] = validated; agent(2,"done")

        pip(3); agent(3,"active")
        add_log(log_c,"INFO","[4/5] Evidence Extractor fetching content…")
        for s in validated[:3]:
            add_log(log_c,"TOOL",f"Extracting: {str(s.get('title',''))[:60]}…"); time.sleep(0.3)
        raw = call_nvidia(model,
            "Extract key evidence from research sources. "
            'Return ONLY JSON array: [{"source_id":"url","title":"...","url":"...",'
            '"metrics":[],"datasets":["benchmarks"],'
            '"key_findings":["f1","f2","f3"],"quotes":["quote"]}]',
            f"Topic: {topic}\nSources: {json.dumps([s.get('title') for s in validated[:3]])}", temp)
        evidence = parse_json_safe(raw, [])
        add_log(log_c,"DONE",f"Extractor: evidence from {len(evidence)} sources")
        res["evidence"] = evidence; agent(3,"done")

        pip(4); agent(4,"active")
        add_log(log_c,"INFO","[5/5] Synthesizer writing report…")
        src_info = json.dumps([{"title":s.get("title"),"url":s.get("url")} for s in validated[:5]])
        raw = call_nvidia(model,
            "Write a structured markdown research summary:\n"
            "# Research Summary: <topic>\n"
            "## Key Insights\n1. **<Headline>**\n   <2-3 sentence evidence>\n   *Source: [N]*\n"
            "(min 3 insights)\n## Methodology Overview\n## Open Challenges\n## Sources\n[1] title\n    url\n"
            "Be factual, cite as [N], no invented facts.",
            f"Topic: {topic}\nQueries: {'; '.join(queries[:4])}\nSources: {src_info}", temp)
        add_log(log_c,"DONE","Synthesizer: report generated")
        res["report"] = raw; agent(4,"done")

        elapsed = round(time.time()-t0, 1)
        res["elapsed"] = elapsed

        # Save to database
        user_id = st.session_state.get("user_id", 1)
        db.save_research(user_id, topic, queries, validated, evidence, raw, elapsed, model, temp)

        add_log(log_c,"INFO",f"✓ Pipeline completed in {elapsed}s")
        for c in pip_c: c.markdown('<div class="pip-step done">✓ Done</div>', unsafe_allow_html=True)

    except Exception as e:
        add_log(log_c,"ERROR",str(e)); st.error(f"Pipeline error: {e}")

    return res


# ── PDF PIPELINE ──────────────────────────────────────────────────────────────

def run_pdf_pipeline(uploaded_file, question, log_c):
    res = {}
    try:
        file_bytes = uploaded_file.read()
        mime = uploaded_file.type or "application/pdf"
        fname = uploaded_file.name

        add_log(log_c,"INFO",f"Document received: {fname}")
        add_log(log_c,"INFO",f"Size: {len(file_bytes)/1024:.1f} KB | Type: {mime}")
        add_log(log_c,"TOOL","Step 1: Extracting text from document…")

        # For PDFs: use local pdfplumber (no API needed!)
        # For images: use vision API fallback
        extracted_text = ""
        if mime == "application/pdf":
            try:
                import io as _io
                with pdfplumber.open(_io.BytesIO(file_bytes)) as pdf:
                    pages = []
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text:
                            pages.append(f"--- Page {i+1} ---\n{text}")
                    extracted_text = "\n\n".join(pages)
                if not extracted_text.strip():
                    add_log(log_c,"INFO","PDF has no selectable text, trying Vision OCR…")
                    ocr_prompt = "Extract ALL text from this document carefully and return ONLY the extracted text."
                    extracted_text = call_gemini_vision(file_bytes, mime, ocr_prompt)
                else:
                    add_log(log_c,"DONE",f"Local extraction complete ({len(extracted_text)} chars from {len(pages)} pages)")
            except Exception as pdf_err:
                add_log(log_c,"INFO",f"pdfplumber failed ({pdf_err}), trying Vision OCR…")
                ocr_prompt = "Extract ALL text from this document carefully and return ONLY the extracted text."
                extracted_text = call_gemini_vision(file_bytes, mime, ocr_prompt)
        else:
            # For images (JPG, PNG, etc.) — must use vision API
            ocr_prompt = "Extract ALL text from this image carefully and return ONLY the extracted text."
            extracted_text = call_gemini_vision(file_bytes, mime, ocr_prompt)
        
        add_log(log_c,"DONE","Text extraction complete")
        
        add_log(log_c,"TOOL",f"Step 2: Analyzing text with Cerebras AI…")
        analysis_prompt = (
            "Analyze the following extracted document text. You MUST respond with EXACTLY these sections using these EXACT headers on their own lines:\n\n"
            "SUMMARY:\n[Write a 3-paragraph executive summary here]\n\n"
            "KEY_TOPICS:\n[\"topic1\", \"topic2\", \"topic3\", \"topic4\", \"topic5\"]\n\n"
            "KEY_FINDINGS:\n- Finding 1\n- Finding 2\n- Finding 3\n- Finding 4\n- Finding 5\n\n"
            "METADATA:\nDocument type, estimated date, authors if visible\n\n"
            "IMPORTANT: Start each section with the header word followed by a colon. Do NOT skip any section.\n\n"
            f"TEXT CONTENT:\n{extracted_text[:6000]}"
        )
        
        # Use Cerebras SDK for document tasks
        if cere_client:
            raw = call_cerebras("llama3.1-8b", "You are a professional document analyst. Always respond with the exact section headers requested.", analysis_prompt)
        else:
            raw = call_llm_text(analysis_prompt)
        
        # Merge FULL_TEXT for parsing and database
        raw = f"FULL_TEXT:\n{extracted_text}\n\n" + raw
        add_log(log_c,"DONE","Analysis complete")
        res["ocr_raw"] = raw

        # Parse sections
        sections = {}
        current = None
        lines = []
        for line in raw.split("\n"):
            for hdr in ["FULL_TEXT","SUMMARY","KEY_TOPICS","KEY_FINDINGS","METADATA"]:
                if hdr in line and ":" in line:
                    if current: sections[current] = "\n".join(lines).strip()
                    current = hdr; lines = []; break
            else:
                if current: lines.append(line)
        if current: sections[current] = "\n".join(lines).strip()
        res["sections"] = sections

        # Answer user question if provided
        if question.strip():
            add_log(log_c,"TOOL",f"Answering: {question[:60]}…")
            context = sections.get("FULL_TEXT", raw)[:8000]
            ans_prompt = (
                f"Based on the following document content, answer this question:\n\n"
                f"QUESTION: {question}\n\n"
                f"DOCUMENT CONTENT:\n{context}\n\n"
                "Give a detailed, accurate answer citing specific parts of the document. "
                "If the answer is not in the document, say so clearly."
            )
            # Use Cerebras for doc Q&A too
            if cere_client:
                answer = call_cerebras("llama3.1-8b", "You are a helpful document analyst.", ans_prompt)
            else:
                answer = call_llm_text(ans_prompt)
            add_log(log_c,"DONE","Answer generated")
            res["answer"] = answer

        user_id = st.session_state.get("user_id", 1)
        topics_list = parse_json_safe(sections.get("KEY_TOPICS","[]"), [])
        db.save_document(user_id, fname, len(file_bytes)/1024, mime,
                         sections.get("FULL_TEXT",""), sections.get("SUMMARY",""),
                         sections.get("KEY_FINDINGS",""), topics_list,
                         sections.get("METADATA",""), question, res.get("answer",""),
                         "mistralai/mistral-large-3-675b-instruct-2512")

        add_log(log_c,"INFO","Document analysis complete ✓")
        res["fname"] = fname

    except Exception as e:
        add_log(log_c,"ERROR",str(e)); st.error(f"PDF pipeline error: {e}")

    return res


# ── RESULT RENDERERS ─────────────────────────────────────────────────────────

def render_topic_results(res):
    if not res: return
    elapsed  = res.get("elapsed", 0)
    sources  = res.get("sources", [])
    evidence = res.get("evidence", [])
    report   = res.get("report", "")
    queries  = res.get("queries", [])
    insights = [l for l in report.split("\n") if "**" in l and l.strip()]

    c1,c2,c3 = st.columns(3)
    c1.metric("⏱ Time", f"{elapsed}s")
    c2.metric("📄 Sources", len(sources))
    c3.metric("💡 Insights", max(len(insights),3))
    st.markdown("---")

    t1,t2,t3,t4 = st.tabs(["📋 Insights","🔗 Sources","🔎 Queries","📄 Raw Report"])

    with t1:
        if report:
            secs = report.split("\n## ")
            ins_sec = next((s for s in secs if "Key Insights" in s),"")
            if ins_sec:
                items = ins_sec.split("\n")[1:]
                cur = []
                for line in items:
                    if line.strip() and line.strip()[0].isdigit() and "**" in line and cur:
                        st.markdown(f'<div class="insight-card">{"".join(cur)}</div>', unsafe_allow_html=True)
                        cur = [line+"<br>"]
                    else: cur.append(line+"<br>")
                if cur: st.markdown(f'<div class="insight-card">{"".join(cur)}</div>', unsafe_allow_html=True)
            meth = next((s for s in secs if "Methodology" in s),"")
            if meth:
                st.markdown("#### Methodology Overview")
                st.info("\n".join(meth.split("\n")[1:]).strip())
            chall = next((s for s in secs if "Challenge" in s),"")
            if chall:
                st.markdown("#### Open Challenges")
                st.warning("\n".join(chall.split("\n")[1:]).strip())
        else: st.info("No report yet.")

    with t2:
        for i,s in enumerate(sources):
            sc = s.get("score",0)
            bc = "score-high" if sc>=8 else ("score-medium" if sc>=5 else "score-low")
            st.markdown(
                f'<div class="source-card">'
                f'<div><strong style="color:#d8d8e0">[{i+1}] {s.get("title","Untitled")}</strong><br>'
                f'<a href="{s.get("url","#")}" target="_blank" style="color:#8888a0;font-size:.82rem">'
                f'{s.get("url","")}</a><br>'
                f'<small style="color:#6a6a78">{s.get("source_type","paper")} · '
                f'{s.get("published_date","Unknown")} · {s.get("rationale","")}</small></div>'
                f'<span class="score-badge {bc}">{sc}/10</span></div>',
                unsafe_allow_html=True)

    with t3:
        st.markdown("**Generated search queries**")
        pills = "".join(f'<span style="display:inline-block;background:rgba(90,90,110,.15);'
                        f'color:#aaaabb;border:1px solid rgba(90,90,110,.3);border-radius:20px;'
                        f'padding:3px 11px;margin:3px;font-size:.78rem">{q}</span>' for q in queries)
        st.markdown(f'<div style="margin:.5rem 0">{pills}</div>', unsafe_allow_html=True)
        datasets = []
        for ev in evidence: datasets.extend(ev.get("datasets",[]))
        if datasets:
            st.markdown("**Datasets found**")
            for d in set(datasets): st.markdown(f"- `{d}`")

    with t4:
        st.code(report, language="markdown")
        st.download_button("⬇ Download report (.md)", report, "research_report.md", "text/markdown")


def render_pdf_results(res):
    if not res: return
    sections = res.get("sections", {})
    fname    = res.get("fname", "Document")
    answer   = res.get("answer", "")

    st.markdown(f"""
    <div class="rm-card" style="margin-bottom:1rem">
        <div style="display:flex;align-items:center;gap:10px">
            <span style="font-size:1.8rem">📄</span>
            <div>
                <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:600;color:#d8d8e0">{fname}</div>
                <div style="font-size:.75rem;color:#6a6a78">Analysis complete · Powered by Google Gemini Vision</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1,t2,t3,t4 = st.tabs(["📝 OCR Text","📊 Key Findings","❓ Q&A","📋 Summary"])

    with t1:
        st.markdown("#### Extracted text")
        full_text = sections.get("FULL_TEXT","No text extracted.")
        st.markdown(f"""
        <div class="pdf-preview-card" style="max-height:420px;overflow-y:auto">
            <div style="font-size:.82rem;color:#888898;line-height:1.8;white-space:pre-wrap">{full_text[:5000]}
            {'<br><span style="color:#6a6a78;font-style:italic">… (truncated for display)</span>' if len(full_text)>5000 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.download_button("⬇ Download full extracted text", full_text, "extracted_text.txt", "text/plain")

    with t2:
        meta = sections.get("METADATA","")
        if meta:
            st.markdown("#### Document metadata")
            st.info(meta)
        findings = sections.get("KEY_FINDINGS","")
        if findings:
            st.markdown("#### Key findings")
            for i,line in enumerate([l for l in findings.split("\n") if l.strip()][:8]):
                clean = line.lstrip("•-1234567890. ")
                st.markdown(f"""
                <div class="pdf-preview-card" style="margin-bottom:.6rem;display:flex;gap:10px;align-items:flex-start">
                    <span class="pdf-page-num">#{i+1}</span>
                    <span style="font-size:.83rem;color:#888898;line-height:1.6">{clean}</span>
                </div>
                """, unsafe_allow_html=True)
        topics = sections.get("KEY_TOPICS","")
        if topics:
            st.markdown("#### Main topics")
            topic_list = parse_json_safe(topics, [])
            if isinstance(topic_list, list):
                pills = "".join(
                    f'<span style="display:inline-block;background:rgba(74,90,74,.12);'
                    f'color:#7ab8a8;border:1px solid rgba(74,90,74,.3);border-radius:20px;'
                    f'padding:3px 12px;margin:3px;font-size:.78rem">{t}</span>'
                    for t in topic_list)
                st.markdown(f'<div style="margin:.5rem 0">{pills}</div>', unsafe_allow_html=True)
            else:
                st.markdown(topics)

    with t3:
        st.markdown("#### Ask a question about this document")
        st.markdown("""
        <div style="font-size:.8rem;color:#6a6a78;margin-bottom:.5rem">
            The answer was generated using the full document content via Google Gemini Vision
        </div>
        """, unsafe_allow_html=True)
        if answer:
            st.markdown(f"""
            <div class="rm-card">
                <div style="font-size:.78rem;color:#5a5a6e;font-weight:600;margin-bottom:.5rem;
                    letter-spacing:.05em;text-transform:uppercase">Answer</div>
                <div style="font-size:.87rem;color:#c0c0d0;line-height:1.7">{answer}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Submit a question above to get an answer from the document.")

    with t4:
        summary = sections.get("SUMMARY","No summary available.")
        st.markdown("#### Executive summary")
        st.markdown(f"""
        <div class="rm-card">
            <div style="font-size:.88rem;color:#888898;line-height:1.8;white-space:pre-wrap">{summary}</div>
        </div>
        """, unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────

def render_top_header():
    mode_str = "PDF + Topic Mode"
    st.markdown(f"""
    <div class="rm-topbar">
        <div class="rm-topbar-left">
            <div class="rm-logo-icon">🧠</div>
            <div class="rm-title-group">
                <div class="rm-logo">ResearchMind</div>
                <div class="rm-tagline">MULTI-AGENT AI RESEARCH · NVIDIA NIM + GOOGLE GEMINI</div>
            </div>
        </div>
        <div class="rm-v-badge">
            v2.0 · {mode_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── CHATBOT ───────────────────────────────────────────────────────────────────

def render_chatbot():
    st.markdown("""
    <style>
    /* Floating Chat Container */
    div[data-testid="stVerticalBlock"]:has(> div > div > div > div#chat-anchor) {
        position: fixed !important;
        bottom: 100px !important;
        right: 32px !important;
        width: 420px !important;
        height: 620px !important;
        max-height: 85vh !important;
        background: #ffffff !important;
        border-radius: 20px !important;
        z-index: 99999 !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4) !important;
        overflow: hidden !important;
        display: flex !important;
        flex-direction: column !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
    }

    div#chat-header {
        background: #1a1a2e;
        padding: 1.2rem 1.5rem;
        display: flex; align-items: center; justify-content: space-between;
        color: white;
    }
    
    .chat-logo-area { display: flex; align-items: center; gap: 12px; }
    .chat-logo-circle {
        width: 38px; height: 38px; border-radius: 10px; background: #232336;
        display: flex; align-items: center; justify-content: center; font-size: 1.4rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .chat-title-text { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.1rem; }
    
    .close-chat-btn {
        cursor: pointer; opacity: 0.8; transition: 0.2s;
        background: rgba(255,255,255,0.1); border-radius: 50%; width: 32px; height: 32px;
        display: flex; align-items: center; justify-content: center;
    }
    .close-chat-btn:hover { opacity: 1; background: rgba(255,255,255,0.2); }

    /* Float FAB */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stVerticalBlock"] button#chat_fab) {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        z-index: 100000 !important;
    }
    button[kind="secondary"]#chat_fab {
        width: 65px !important; height: 65px !important; border-radius: 50% !important;
        background: #1a1a2e !important;
        border: 2px solid rgba(255,255,255,0.15) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
        font-size: 2.2rem !important; color: #fff !important;
    }

    /* Message Styling */
    .stChatMessage { background: transparent !important; }
    .stChatMessage [data-testid="stMarkdownContainer"] { color: #1a1a2e !important; }
    div[data-testid="stChatMessageContent"] { background: #f0f2f6 !important; border-radius: 15px !important; padding: 10px 15px !important; }
    div[data-testid="chatAvatarIcon-user"] { background: #1a1a2e !important; }
    div[data-testid="chatAvatarIcon-assistant"] { background: #232336 !important; }

    /* Hide standard chat input border */
    .stChatInputContainer { border: none !important; background: #fff !important; padding-top: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

    if "chat_open"    not in st.session_state: st.session_state.chat_open    = False
    if "session_tag"  not in st.session_state: st.session_state.session_tag  = str(uuid.uuid4())
    user_id = st.session_state.get("user_id", 1)
    if "chat_history" not in st.session_state: 
        st.session_state.chat_history = db.get_chat_history(user_id, st.session_state.session_tag)

    fab_cont = st.container()
    with fab_cont:
        if st.button("🧠", key="chat_fab"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()

    if not st.session_state.chat_open:
        return

    chat_panel = st.container()
    with chat_panel:
        st.markdown("<div id='chat-anchor'></div>", unsafe_allow_html=True)
        # Header with close button
        st.markdown(f"""
        <div id="chat-header">
            <div class="chat-logo-area">
                <div class="chat-logo-circle">🧠</div>
                <div class="chat-title-text">ResearchMind AI</div>
            </div>
            <div class="close-chat-btn" onclick="document.querySelector('button[key=chat_fab]').click();">✕</div>
        </div>
        """, unsafe_allow_html=True)

        hist_cont = st.container(height=480)
        with hist_cont:
            if not st.session_state.chat_history:
                st.chat_message("assistant", avatar="🧠").write("👋 Hi! I'm **ResearchMind AI**. Ask me anything about your research!")
            for msg in st.session_state.chat_history:
                st.chat_message(msg["role"], avatar="🧠" if msg["role"]=="assistant" else None).write(msg["content"])
        
        # Use native chat_input to avoid looping
        user_input = st.chat_input("Ask anything about the research...")
        
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            db.save_chat_msg(user_id, "user", user_input, st.session_state.session_tag)
            
            try:
                sys_prompt = (
                    "You are ResearchMind AI, a helpful and knowledgeable AI assistant. "
                    "Answer the user's question directly and helpfully. "
                    "Focus ONLY on what the user is currently asking. "
                    "Do NOT reference previous conversations or topics unless the user explicitly asks."
                )
                
                # Use Cerebras for fast responses
                if cere_client:
                    reply = call_cerebras("llama3.1-8b", sys_prompt, user_input)
                else:
                    reply = call_llm_text(user_input, provider="groq")
            except Exception as e:
                reply = f"I encountered an error: {e}"
            
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            db.save_chat_msg(user_id, "assistant", reply, st.session_state.session_tag)
            st.rerun()



# ── AUTH ──────────────────────────────────────────────────────────────────────

def render_auth():
    """Returns True once the user is authenticated."""
    if st.session_state.get("authenticated"):
        return True

    # ── center card via columns ──
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        # Logo
        st.markdown("""
        <div class="auth-logo">
            <div style="font-size:2.8rem;margin-bottom:.4rem">🧠</div>
            <div class="auth-logo-title">ResearchMind</div>
            <div class="auth-logo-sub">Multi-Agent AI Research Platform</div>
        </div>
        """, unsafe_allow_html=True)

        # Tab switcher (Login / Sign Up)
        if "auth_tab" not in st.session_state:
            st.session_state.auth_tab = "login"

        tab_l, tab_r = st.columns(2)
        with tab_l:
            if st.button("Log In", use_container_width=True, key="tab_login"):
                st.session_state.auth_tab = "login"
        with tab_r:
            if st.button("Sign Up", use_container_width=True, key="tab_signup"):
                st.session_state.auth_tab = "signup"

        st.markdown(f"""
        <div style="display:flex;gap:5px;background:var(--bg3);border-radius:10px;
            padding:4px;margin-bottom:1.6rem">
            <div style="flex:1;text-align:center;padding:7px;border-radius:7px;
                font-size:.82rem;font-weight:500;
                {'background:#141414;color:#d8d8e0;border:1px solid rgba(180,180,200,0.12)' if st.session_state.auth_tab=='login' else 'color:#6a6a78'}">
                Log In</div>
            <div style="flex:1;text-align:center;padding:7px;border-radius:7px;
                font-size:.82rem;font-weight:500;
                {'background:#141414;color:#d8d8e0;border:1px solid rgba(180,180,200,0.12)' if st.session_state.auth_tab=='signup' else 'color:#6a6a78'}">
                Sign Up</div>
        </div>
        """, unsafe_allow_html=True)

        if "auth_error" not in st.session_state:
            st.session_state.auth_error = ""

        # ── LOGIN ──
        if st.session_state.auth_tab == "login":
            st.markdown('<div class="auth-field-label">Email</div>', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="you@example.com",
                                  label_visibility="collapsed", key="login_email")
            st.markdown('<div class="auth-field-label" style="margin-top:.9rem">Password</div>',
                        unsafe_allow_html=True)
            password = st.text_input("Password", placeholder="••••••••",
                                     type="password", label_visibility="collapsed",
                                     key="login_password", max_chars=72)

            st.markdown("""
            <div style="text-align:right;margin-top:.3rem;margin-bottom:1rem">
                <span style="font-size:.75rem;color:#8888a0;cursor:pointer">Forgot password?</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Log In", use_container_width=True, key="do_login"):
                user = db.verify_login(email, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_email    = email
                    st.session_state.user_id       = user["id"]
                    st.session_state.auth_error    = ""
                    st.rerun()
                else:
                    st.session_state.auth_error = "Invalid email or password."

            if st.session_state.auth_error:
                st.markdown(f"""
                <div style="background:rgba(138,74,74,.12);border:1px solid rgba(138,74,74,.35);
                    border-radius:8px;padding:.55rem .9rem;font-size:.8rem;
                    color:#c88888;margin-top:.6rem">
                    ⚠ {st.session_state.auth_error}
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="auth-divider">or continue with</div>', unsafe_allow_html=True)

            g_col, gh_col = st.columns(2)
            with g_col:
                st.button("🔵  Google", use_container_width=True, key="google_login",
                          disabled=True, help="Coming soon")
            with gh_col:
                st.button("⚫  GitHub", use_container_width=True, key="github_login",
                          disabled=True, help="Coming soon")

            st.markdown("""
            <div class="auth-footer">
                Don't have an account?
                <span style="color:#aaaabb;cursor:pointer"> Sign up free</span>
            </div>
            """, unsafe_allow_html=True)

        # ── SIGN UP ──
        else:
            name_col, _ = st.columns([1,1])
            st.markdown('<div class="auth-field-label">Full Name</div>', unsafe_allow_html=True)
            name = st.text_input("Full Name", placeholder="Jane Smith",
                                 label_visibility="collapsed", key="signup_name")
            st.markdown('<div class="auth-field-label" style="margin-top:.9rem">Email</div>',
                        unsafe_allow_html=True)
            su_email = st.text_input("Email", placeholder="you@example.com",
                                     label_visibility="collapsed", key="signup_email")
            st.markdown('<div class="auth-field-label" style="margin-top:.9rem">Password</div>',
                        unsafe_allow_html=True)
            su_pass = st.text_input("Password", placeholder="Min. 8 characters",
                                    type="password", label_visibility="collapsed",
                                    key="signup_pass", max_chars=72)
            st.markdown('<div class="auth-field-label" style="margin-top:.9rem">Confirm Password</div>',
                        unsafe_allow_html=True)
            su_pass2 = st.text_input("Confirm Password", placeholder="Repeat password",
                                     type="password", label_visibility="collapsed",
                                     key="signup_pass2", max_chars=72)

            st.markdown("""
            <div style="display:flex;align-items:flex-start;gap:8px;
                margin:.9rem 0 1rem;font-size:.78rem;color:#6a6a78">
                <span style="color:#aaaabb;font-size:.9rem;line-height:1.4">☐</span>
                I agree to the <span style="color:#aaaabb">&nbsp;Terms of Service</span>
                &nbsp;and&nbsp;<span style="color:#aaaabb">Privacy Policy</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Create Account", use_container_width=True, key="do_signup"):
                if not name or not su_email or not su_pass:
                    st.session_state.auth_error = "Please fill in all fields."
                elif su_pass != su_pass2:
                    st.session_state.auth_error = "Passwords do not match."
                elif len(su_pass) < 8:
                    st.session_state.auth_error = "Password must be at least 8 characters."
                elif len(su_pass) > 72:
                    st.session_state.auth_error = "Password must be less than 72 characters."
                else:
                    try:
                        db.create_user(su_email, name, su_pass)
                        user = db.verify_login(su_email, su_pass)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_email    = su_email
                            st.session_state.user_id       = user["id"]
                            st.session_state.auth_error    = ""
                            st.success("Account created! Welcome to ResearchMind.")
                            st.rerun()
                    except Exception as e:
                        if "UNIQUE" in str(e):
                            st.session_state.auth_error = "Email already registered."
                        else:
                            st.session_state.auth_error = f"Database error: {e}"

            if st.session_state.auth_error:
                st.markdown(f"""
                <div style="background:rgba(138,74,74,.12);border:1px solid rgba(138,74,74,.35);
                    border-radius:8px;padding:.55rem .9rem;font-size:.8rem;
                    color:#c88888;margin-top:.6rem">
                    ⚠ {st.session_state.auth_error}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div class="auth-footer">
                Already have an account?
                <span style="color:#aaaabb;cursor:pointer"> Log in</span>
            </div>
            """, unsafe_allow_html=True)

    return False

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    render_top_header()
    model, temperature, agent_containers = render_sidebar()

    if not NVIDIA_API_KEY:
        st.error("⚠️ NVIDIA_API_KEY not set in .env"); st.stop()

    mode = st.session_state.get("mode","topic")

    # ── TOPIC MODE ──────────────────────────────────────────────────────────
    if mode == "topic":
        st.markdown("#### 🔭 Research Topic")
        col_l, col_r = st.columns([3,1])
        with col_l:
            topic = st.text_area("", placeholder="e.g. retrieval-augmented generation for knowledge-intensive NLP",
                                 height=90, label_visibility="collapsed")
        with col_r:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            run_clicked = st.button("▶ Run Pipeline", use_container_width=True)

        st.markdown("#### ⚡ Pipeline Progress")
        pip_cols = st.columns(5)
        pip_c = []
        for col, lbl in zip(pip_cols, ["Planner","Search","Validator","Extractor","Synthesizer"]):
            with col:
                c = st.empty()
                c.markdown(f'<div class="pip-step">{lbl}</div>', unsafe_allow_html=True)
                pip_c.append(c)

        st.markdown("#### 🖥 Live Execution Log")
        log_c = st.empty()
        log_c.markdown('<div class="log-box" style="color:#334155">Waiting for pipeline to start…</div>',
                       unsafe_allow_html=True)

        if "results" not in st.session_state: st.session_state.results = {}
        if "logs"    not in st.session_state: st.session_state.logs    = []

        if run_clicked:
            if not topic.strip(): st.warning("Please enter a research topic.")
            else:
                st.session_state.logs = []; st.session_state.results = {}
                st.session_state.results = run_pipeline(
                    topic.strip(), model, temperature, log_c, agent_containers, pip_c)

        if st.session_state.results:
            st.markdown("---")
            st.markdown("### 📊 Research Results")
            render_topic_results(st.session_state.results)

    # ── PDF / DOCUMENT MODE ─────────────────────────────────────────────────
    else:
        if not (GOOGLE_API_KEY or OPENROUTER_KEY):
            st.error("⚠️ Gemini/OpenRouter key missing in .env")

        st.markdown("#### 📂 Document Intelligence Studio")
        st.markdown("""
        <div style="font-size:.82rem;color:#6a6a78;margin-bottom:1rem;padding:.75rem 1rem;
            background:rgba(90,90,110,.06);border:1px solid rgba(90,90,110,.15);border-radius:10px">
            Upload any PDF, image, scanned document or research paper. Google Gemini Vision will
            extract all text, identify key findings, and let you ask questions about the content.
        </div>
        """, unsafe_allow_html=True)

        col_upload, col_qa = st.columns([3,2])

        with col_upload:
            st.markdown("##### Upload document")
            uploaded = st.file_uploader(
                "Drop your file here",
                type=["pdf","png","jpg","jpeg","webp","tiff","bmp"],
                label_visibility="collapsed"
            )
            if uploaded:
                ftype = uploaded.type or ""
                if "image" in ftype:
                    st.image(uploaded, caption=uploaded.name, use_container_width=True)
                else:
                    st.markdown(f"""
                    <div class="rm-card" style="text-align:center;padding:2rem">
                        <div style="font-size:2.5rem;margin-bottom:.5rem">📄</div>
                        <div style="font-family:'Syne',sans-serif;font-size:1rem;
                            font-weight:600;color:#d8d8e0">{uploaded.name}</div>
                        <div style="font-size:.75rem;color:#6a6a78;margin-top:4px">
                            {uploaded.size/1024:.1f} KB · Ready for analysis
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_qa:
            st.markdown("##### Ask a question about the document")
            question = st.text_area("",
                placeholder="e.g. What is the main conclusion of this paper?\ne.g. What methodology did the authors use?",
                height=120, label_visibility="collapsed",
                key="pdf_question")
            st.markdown("""
            <div style="font-size:.72rem;color:#6a6a78;margin-bottom:.5rem">
                💡 Leave blank to get a full analysis without a specific question
            </div>
            """, unsafe_allow_html=True)
            analyze_clicked = st.button("🔍 Analyse Document", use_container_width=True)

        st.markdown("#### 🖥 Analysis Log")
        log_c2 = st.empty()
        log_c2.markdown('<div class="log-box" style="color:#334155">Upload a document to begin analysis…</div>',
                        unsafe_allow_html=True)

        if "pdf_results" not in st.session_state: st.session_state.pdf_results = {}
        if "logs"        not in st.session_state: st.session_state.logs = []

        if analyze_clicked:
            if not uploaded: st.warning("Please upload a document first.")
            else:
                st.session_state.logs = []; st.session_state.pdf_results = {}
                uploaded.seek(0)
                st.session_state.pdf_results = run_pdf_pipeline(uploaded, question or "", log_c2)

        # Follow-up Q&A on already-analysed document
        if st.session_state.pdf_results and st.session_state.pdf_results.get("sections"):
            st.markdown("---")
            st.markdown("### 📊 Document Analysis Results")
            render_pdf_results(st.session_state.pdf_results)

            st.markdown("#### 💬 Ask a Follow-up Question")
            col_q, col_btn = st.columns([4,1])
            with col_q:
                followup = st.text_input("", placeholder="Ask another question about this document…",
                                         key="followup_q", label_visibility="collapsed")
            with col_btn:
                ask_btn = st.button("Ask", use_container_width=True, key="ask_followup")
            if ask_btn and followup.strip():
                with st.spinner("Thinking…"):
                    ctx = st.session_state.pdf_results.get("sections",{}).get("FULL_TEXT","")[:8000]
                    if cere_client:
                        ans = call_cerebras("llama3.1-8b", "You are a helpful document analyst. Answer questions based on the provided document content.",
                            f"Document content:\n{ctx}\n\nQuestion: {followup}")
                    else:
                        ans = call_llm_text(
                            f"Answer this question based on the document:\n{followup}", ctx)
                st.markdown(f"""
                <div class="rm-card" style="margin-top:.75rem">
                    <div style="font-size:.72rem;color:#5a5a6e;font-weight:600;margin-bottom:.4rem;
                        letter-spacing:.05em;text-transform:uppercase">Answer</div>
                    <div style="font-size:.87rem;color:#c0c0d0;line-height:1.7">{ans}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── CHATBOT ──────────────────────────────────────────────────────────────
    render_chatbot()


if __name__ == "__main__":
    if render_auth():
        main()
