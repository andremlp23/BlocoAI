import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0e1a !important;
    color: #c8d6f0 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 4rem 2rem !important; max-width: 1280px; }
section[data-testid="stSidebar"] { background: #060912 !important; border-right: 1px solid #1a2540; }
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }

.header-band {
    background: linear-gradient(135deg, #060d1f 0%, #0d1b35 60%, #0a1628 100%);
    border-bottom: 1px solid #1a3a6e;
    padding: 1.8rem 2rem 1.6rem 2rem;
    margin: -1rem -2rem 2.5rem -2rem;
    display: flex; align-items: center; justify-content: space-between;
    position: relative; overflow: hidden;
}
.header-band::before {
    content: ''; position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(30,90,200,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.header-title {
    font-family: 'Space Mono', monospace; font-size: 1.65rem;
    font-weight: 700; color: #e8f0ff; letter-spacing: -0.02em;
    line-height: 1.1; margin: 0;
}
.header-title span { color: #3a8eff; }
.header-tag {
    font-family: 'DM Sans', sans-serif; font-size: 0.78rem;
    font-weight: 400; color: #4a6fa0; letter-spacing: 0.12em;
    text-transform: uppercase; margin-top: 0.3rem;
}
.header-badge {
    font-family: 'Space Mono', monospace; font-size: 0.72rem;
    font-weight: 700; padding: 0.3rem 0.8rem; border-radius: 20px;
    letter-spacing: 0.05em;
}
.badge-ok   { background: rgba(0,200,100,0.12); color: #00c864; border: 1px solid rgba(0,200,100,0.3); }
.badge-fail { background: rgba(255,60,60,0.12);  color: #ff5050; border: 1px solid rgba(255,60,60,0.3); }

.sidebar-label {
    font-family: 'Space Mono', monospace; font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase; color: #2a4a7a;
    margin-bottom: 0.4rem; margin-top: 1.2rem; display: block;
}
.sidebar-divider { border: none; border-top: 1px solid #111e36; margin: 1.2rem 0; }

.section-card {
    background: #0d1628; border: 1px solid #1a2e50; border-radius: 10px;
    padding: 1.5rem 1.6rem; margin-bottom: 1.2rem;
    position: relative; transition: border-color 0.2s;
}
.section-card:hover { border-color: #1e4080; }
.section-number {
    font-family: 'Space Mono', monospace; font-size: 0.6rem; font-weight: 700;
    letter-spacing: 0.2em; color: #1e5ccc; text-transform: uppercase;
    margin-bottom: 0.5rem; display: block;
}
.section-title {
    font-family: 'DM Sans', sans-serif; font-size: 1rem; font-weight: 600;
    color: #dde8ff; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;
}
.upload-label {
    font-family: 'Space Mono', monospace; font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase; color: #3a6aaa;
    margin-bottom: 0.5rem; display: block;
}
.upload-desc { font-size: 0.75rem; color: #3a5a80; margin-bottom: 0.6rem; }
.file-chip {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(30,80,200,0.15); border: 1px solid rgba(30,100,220,0.35);
    border-radius: 20px; padding: 0.25rem 0.75rem;
    font-family: 'Space Mono', monospace; font-size: 0.68rem;
    color: #5a9aff; margin: 0.2rem 0.2rem 0 0;
}

.stTextInput > div > div > input,
.stTextArea textarea {
    background: #080f1f !important; border: 1px solid #1a2e50 !important;
    color: #c8d6f0 !important; border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #2a6aee !important;
    box-shadow: 0 0 0 2px rgba(42,106,238,0.18) !important;
}
.stTextInput > label, .stTextArea > label, .stFileUploader > label {
    color: #4a6fa0 !important; font-size: 0.82rem !important; font-weight: 500 !important;
}
div[data-testid="stFileUploader"] {
    background: #080f1f !important; border: 1.5px dashed #1a3060 !important;
    border-radius: 8px !important;
}
div[data-testid="stFileUploader"]:hover { border-color: #2a5fb0 !important; }

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1a4fc4 0%, #0e3498 100%) !important;
    color: #ffffff !important; border: none !important; border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.82rem !important;
    font-weight: 700 !important; letter-spacing: 0.06em !important;
    padding: 0.7rem 1.8rem !important; transition: all 0.2s !important;
    box-shadow: 0 4px 24px rgba(20,60,180,0.3) !important;
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #2060e8 0%, #1540b8 100%) !important;
    box-shadow: 0 6px 32px rgba(20,80,220,0.45) !important;
    transform: translateY(-1px) !important;
}

.pipeline-wrap {
    display: flex; align-items: stretch; gap: 0; margin: 1.8rem 0;
    background: #080f1f; border: 1px solid #1a2e50;
    border-radius: 10px; overflow: hidden;
}
.pipeline-step {
    flex: 1; padding: 1.1rem 1rem; border-right: 1px solid #1a2e50;
    position: relative; transition: background 0.3s;
}
.pipeline-step:last-child { border-right: none; }
.pipeline-step.idle    { background: #080f1f; }
.pipeline-step.active  { background: linear-gradient(135deg, #0d1e40 0%, #0a1830 100%); }
.pipeline-step.done    { background: linear-gradient(135deg, #051a10 0%, #071512 100%); }
.pipeline-step.error   { background: rgba(120,20,20,0.2); }
.pipeline-step.retry   { background: linear-gradient(135deg, #1a1000 0%, #120c00 100%); }

.step-num { font-family: 'Space Mono', monospace; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.3rem; }
.step-title { font-family: 'DM Sans', sans-serif; font-size: 0.88rem; font-weight: 600; margin-bottom: 0.2rem; }
.step-sub { font-size: 0.72rem; }
.step-num.idle, .step-title.idle, .step-sub.idle     { color: #2a3a5a; }
.step-num.active, .step-title.active { color: #3a7aee; }
.step-sub.active   { color: #4a6fa0; }
.step-num.done, .step-title.done   { color: #00aa55; }
.step-sub.done     { color: #1a6040; }
.step-num.error, .step-title.error { color: #cc4444; }
.step-sub.error    { color: #7a3030; }
.step-num.retry, .step-title.retry { color: #cc8800; }
.step-sub.retry    { color: #7a5000; }
.step-icon { font-size: 1.1rem; float: right; margin-top: -1.8rem; }

@keyframes pulse-blue { 0% { opacity:1; } 50% { opacity:0.5; } 100% { opacity:1; } }
@keyframes pulse-amber { 0% { opacity:1; } 50% { opacity:0.4; } 100% { opacity:1; } }
.pulse       { animation: pulse-blue  1.5s ease-in-out infinite; }
.pulse-amber { animation: pulse-amber 0.9s ease-in-out infinite; }

.results-header {
    background: linear-gradient(135deg, #060d22 0%, #091428 100%);
    border: 1px solid #1a3a6e; border-radius: 10px 10px 0 0;
    padding: 1.2rem 1.6rem; display: flex; align-items: center;
    justify-content: space-between; margin-top: 2rem;
}
.results-title { font-family: 'Space Mono', monospace; font-size: 0.9rem; font-weight: 700; color: #3a8eff; letter-spacing: 0.04em; }
.results-meta  { font-family: 'Space Mono', monospace; font-size: 0.68rem; color: #2a4a7a; }
.results-body  { background: #080e1e; border: 1px solid #1a2e50; border-top: none; border-radius: 0 0 10px 10px; padding: 1.6rem; }

.metric-row { display: flex; gap: 0.8rem; flex-wrap: wrap; margin-bottom: 1.2rem; }
.metric-pill { background: rgba(20,60,160,0.15); border: 1px solid rgba(30,80,200,0.3); border-radius: 6px; padding: 0.5rem 1rem; font-family: 'Space Mono', monospace; }
.metric-val   { font-size: 1.2rem; font-weight: 700; color: #3a8eff; display: block; }
.metric-label { font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: #2a4a7a; display: block; }

.dl-btn div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #0e3a1a 0%, #082810 100%) !important;
    border: 1px solid #1a6a30 !important; color: #40ee88 !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
}
.dl-btn div[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, #144a22 0%, #0a3214 100%) !important;
    box-shadow: 0 4px 20px rgba(0,150,50,0.3) !important;
}

.stProgress > div > div { background: #1a4fc4 !important; }
.stSpinner > div { border-top-color: #1a4fc4 !important; }
.stAlert { border-radius: 8px !important; }
div[data-testid="stMarkdownContainer"] p { color: #8aa0c0; font-size: 0.88rem; }

.report-md { color: #b8ccec !important; line-height: 1.75; }
.report-md h3 { color: #dde8ff !important; font-family: 'Space Mono', monospace; font-size: 0.9rem; letter-spacing: 0.04em; }
.report-md table { border-collapse: collapse; width: 100%; }
.report-md th { background: #0d1e3a; color: #4a8aee; font-family: 'Space Mono', monospace; font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; padding: 0.6rem 0.8rem; border: 1px solid #1a3060; }
.report-md td { padding: 0.55rem 0.8rem; border: 1px solid #131e34; color: #8aa0c0; font-size: 0.82rem; }
.report-md tr:hover td { background: #0d1628; }

.stSidebar .stTextInput > div > div > input {
    font-family: 'Space Mono', monospace !important; font-size: 0.78rem !important;
}

.pdf-warning {
    background: rgba(180,100,0,0.1); border: 1px solid rgba(200,120,0,0.3);
    border-radius: 6px; padding: 0.6rem 1rem; margin-top: 0.4rem;
    font-family: 'Space Mono', monospace; font-size: 0.68rem; color: #cc8800;
}
</style>
"""


def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
