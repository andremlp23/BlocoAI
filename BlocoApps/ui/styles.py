import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root{
  --bg: #1a1a1f;          /* fundo geral */
  --panel: #8b4513;       /* cards - laranja escuro */
  --sidebar: #2a2a30;     /* sidebar */
  --border: #3a3a40;      /* linhas/bordas */
  --text: #ffffff;        /* texto principal - branco */
  --muted: #c0c0c8;       /* texto secundário */
  --muted2: #a0a0a8;

  --accent: #cc8855;      /* laranja Blocotelha - desaturado */
  --accent2: #b87744;
  --accentSoft: rgba(204,136,85,0.10);

  --ok: #1f9d62;
  --warn: #c88400;
  --bad: #d43030;
}

/* Base */
html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 4rem 2rem !important; max-width: 1280px; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--sidebar) !important;
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #505058; border-radius: 3px; }

/* Header band */
.header-band {
  background: linear-gradient(135deg, #8b4513 0%, #6b3410 60%, #5a2f0d 100%);
  border-bottom: 1px solid var(--border);
  padding: 1.8rem 2rem 1.4rem 2rem;
  margin: -1rem -2rem 2.2rem -2rem;
  display: flex; align-items: center; justify-content: space-between;
  position: relative; overflow: hidden;
}
.header-band::before {
  content: ''; position: absolute; top: -60px; right: -60px;
  width: 220px; height: 220px;
  background: radial-gradient(circle, rgba(204,136,85,0.10) 0%, transparent 70%);
  pointer-events: none;
}
.header-title {
  font-family: 'Space Mono', monospace;
  font-size: 1.65rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
  line-height: 1.1;
  margin: 0;
}
.header-title span { color: var(--accent); }
.header-tag {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 0.35rem;
}

/* Badges */
.header-badge {
  font-family: 'Space Mono', monospace;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  letter-spacing: 0.05em;
}
.badge-ok   { background: rgba(31,157,98,0.12); color: var(--ok); border: 1px solid rgba(31,157,98,0.35); }
.badge-fail { background: rgba(212,48,48,0.12); color: var(--bad); border: 1px solid rgba(212,48,48,0.35); }

/* Sidebar labels + divider */
.sidebar-label {
  font-family: 'Space Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.4rem;
  margin-top: 1.2rem;
  display: block;
}
.sidebar-divider { border: none; border-top: 1px solid var(--border); margin: 1.2rem 0; }

/* Cards */
.section-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem 1.6rem;
  margin-bottom: 1.2rem;
  position: relative;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}
.section-card:hover {
  border-color: rgba(204,136,85,0.65);
  box-shadow: 0 8px 28px rgba(0,0,0,0.06);
}
.section-number {
  font-family: 'Space Mono', monospace;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: var(--accent);
  text-transform: uppercase;
  margin-bottom: 0.5rem;
  display: block;
}
.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Upload */
.upload-label {
  font-family: 'Space Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.5rem;
  display: block;
}
.upload-desc { font-size: 0.75rem; color: var(--muted); margin-bottom: 0.6rem; }

div[data-testid="stFileUploader"] {
  background: #2a2a30 !important;
  border: 1.5px dashed rgba(204,136,85,0.75) !important;
  border-radius: 10px !important;
}
div[data-testid="stFileUploader"]:hover { border-color: var(--accent2) !important; }

/* Chips */
.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: rgba(204,136,85,0.15);
  border: 1px solid rgba(204,136,85,0.4);
  border-left: 3px solid var(--accent);
  border-radius: 999px;
  padding: 0.28rem 0.75rem;
  font-family: 'Space Mono', monospace;
  font-size: 0.68rem;
  color: #ffffff;
  margin: 0.2rem 0.2rem 0 0;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea textarea {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 8px !important;
  font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
  border-color: rgba(204,136,85,0.9) !important;
  box-shadow: 0 0 0 2px rgba(204,136,85,0.16) !important;
}
.stTextInput > label, .stTextArea > label, .stFileUploader > label {
  color: #c0c0c8 !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
}

/* Buttons (principal) */
div[data-testid="stButton"] > button {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 0.82rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.06em !important;
  padding: 0.75rem 1.8rem !important;
  transition: all 0.2s !important;
  box-shadow: 0 10px 30px rgba(204,136,85,0.22) !important;
}
div[data-testid="stButton"] > button:hover {
  background: linear-gradient(135deg, #d9885f 0%, var(--accent) 100%) !important;
  box-shadow: 0 14px 34px rgba(204,136,85,0.28) !important;
  transform: translateY(-1px) !important;
}

/* Download button */
.dl-btn div[data-testid="stDownloadButton"] > button {
  background: linear-gradient(135deg, #3a3a45 0%, #2f2f39 100%) !important;
  border: 1px solid rgba(204,136,85,0.35) !important;
  color: #ffffff !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.05em !important;
  border-radius: 10px !important;
}
.dl-btn div[data-testid="stDownloadButton"] > button:hover {
  background: linear-gradient(135deg, #4a4a56 0%, #3b3b47 100%) !important;
  box-shadow: 0 10px 28px rgba(0,0,0,0.10) !important;
}

/* Progress + Spinner */
.stProgress > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Alerts */
.stAlert { border-radius: 10px !important; }

/* Results area */
.results-header {
  background: linear-gradient(135deg, #8b4513 0%, #6b3410 100%);
  border: 1px solid var(--border);
  border-radius: 12px 12px 0 0;
  padding: 1.2rem 1.6rem;
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 2rem;
}
.results-title {
  font-family: 'Space Mono', monospace;
  font-size: 0.9rem;
  font-weight: 800;
  color: var(--accent);
  letter-spacing: 0.04em;
}
.results-meta  {
  font-family: 'Space Mono', monospace;
  font-size: 0.68rem;
  color: var(--muted2);
}
.results-body  {
  background: var(--panel);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 12px 12px;
  padding: 1.6rem;
}

/* Metric pills */
.metric-row { display: flex; gap: 0.8rem; flex-wrap: wrap; margin-bottom: 1.2rem; }
.metric-pill {
  background: rgba(204,136,85,0.08);
  border: 1px solid rgba(204,136,85,0.22);
  border-radius: 10px;
  padding: 0.55rem 1rem;
  font-family: 'Space Mono', monospace;
}
.metric-val   { font-size: 1.2rem; font-weight: 800; color: var(--accent); display: block; }
.metric-label { font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted2); display: block; }

/* Markdown report */
.report-md { color: var(--text) !important; line-height: 1.75; }
.report-md h3 {
  color: var(--text) !important;
  font-family: 'Space Mono', monospace;
  font-size: 0.9rem;
  letter-spacing: 0.04em;
}
.report-md table { border-collapse: collapse; width: 100%; }
.report-md th {
  background: #2a2a30;
  color: var(--accent);
  font-family: 'Space Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--border);
}
.report-md td {
  padding: 0.55rem 0.8rem;
  border: 1px solid #3a3a40;
  color: #ffffff;
  font-size: 0.82rem;
}
.report-md tr:hover td { background: #3a3a40; }

/* Sidebar input look */
.stSidebar .stTextInput > div > div > input {
  font-family: 'Space Mono', monospace !important;
  font-size: 0.78rem !important;
}

/* Aviso PDF sem texto */
.pdf-warning {
  background: rgba(204,136,85,0.10);
  border: 1px solid rgba(204,136,85,0.25);
  border-radius: 10px;
  padding: 0.7rem 1rem;
  margin-top: 0.6rem;
  font-family: 'Space Mono', monospace;
  font-size: 0.70rem;
  color: var(--accent2);
}
</style>
"""



def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
