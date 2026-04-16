import streamlit as st
import pandas as pd
import time
import pdfplumber
import os
import io
from pathlib import Path
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from openai import RateLimitError, APIConnectionError, APITimeoutError
import logging

# Logger para tenacity — regista cada retry na consola (visível no terminal do Streamlit)
_log = logging.getLogger("blocoai.retry")
logging.basicConfig(level=logging.WARNING)

# ─────────────────────────────────────────────
# 0. AMBIENTE
# ─────────────────────────────────────────────
def carregar_env_local():
    base_dir = Path(__file__).resolve().parent
    for env_path in [base_dir / ".env", base_dir.parent / ".env"]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            linha = line.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave = chave.strip().removeprefix("export ").strip()
            valor = valor.strip().strip('"').strip("'")
            if chave:
                os.environ[chave] = valor
        return

carregar_env_local()

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BlocoAI — Master Cross-Audit",
    layout="wide",
    page_icon="🏗️",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 2. CSS GLOBAL — Dark + Azul Técnico
# ─────────────────────────────────────────────
st.markdown("""
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

/* Aviso de páginas sem texto */
.pdf-warning {
    background: rgba(180,100,0,0.1); border: 1px solid rgba(200,120,0,0.3);
    border-radius: 6px; padding: 0.6rem 1rem; margin-top: 0.4rem;
    font-family: 'Space Mono', monospace; font-size: 0.68rem; color: #cc8800;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:1.4rem">
        <div style="font-family:'Space Mono',monospace;font-size:1.05rem;font-weight:700;color:#e8f0ff;letter-spacing:-0.01em">
            Bloco<span style="color:#3a8eff">AI</span>
        </div>
        <div style="font-size:0.68rem;color:#2a4070;letter-spacing:0.12em;text-transform:uppercase;margin-top:0.2rem">
            Master Cross-Audit · LangGraph
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.markdown('<span class="sidebar-label">🔑 Autenticação</span>', unsafe_allow_html=True)

    api_key_env   = os.getenv("CHATGPT_API_KEY", "")
    api_key_input = st.text_input(
        "API Key OpenAI", value="", type="password",
        placeholder="sk-…  (ou definida em .env)",
        label_visibility="collapsed",
    )
    api_key_final = api_key_input.strip() if api_key_input.strip() else api_key_env

    if api_key_final:
        st.markdown('<div style="margin-top:0.5rem"><span class="header-badge badge-ok">✓ Key Configurada</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin-top:0.5rem"><span class="header-badge badge-fail">✗ Key em Falta</span></div>', unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.markdown('<span class="sidebar-label">⚙️ Pipeline LangGraph</span>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#060d1f;border:1px solid #111e36;border-radius:6px;padding:0.8rem;font-family:'Space Mono',monospace;font-size:0.7rem;color:#2a4a7a;line-height:1.8">
        <div><span style="color:#1e5ccc">AGT-01</span> &nbsp;Extrator</div>
        <div style="font-size:0.6rem;color:#1a2e50;margin-left:2.4rem">Classificação · gpt-4o-mini · t=0.0</div>
        <div style="margin-top:0.4rem"><span style="color:#1e5ccc">AGT-02</span> &nbsp;Auditor Sénior</div>
        <div style="font-size:0.6rem;color:#1a2e50;margin-left:2.4rem">Cross-Audit · gpt-4o-mini · t=0.1 · retry×2</div>
        <div style="margin-top:0.4rem"><span style="color:#1e5ccc">AGT-03</span> &nbsp;Apresentador</div>
        <div style="font-size:0.6rem;color:#1a2e50;margin-left:2.4rem">Formatação · gpt-4o-mini · t=0.1</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.65rem;color:#1a2a44;font-family:'Space Mono',monospace;line-height:1.8">
        v3.0 · LangGraph · BlocoApps Suite<br>
        <span style="color:#111e36">© 2025 Blocotelha</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 4. HEADER BAND
# ─────────────────────────────────────────────
badge_html = (
    '<span class="header-badge badge-ok">● API ONLINE</span>'
    if api_key_final else
    '<span class="header-badge badge-fail">● API OFFLINE</span>'
)
st.markdown(f"""
<div class="header-band">
    <div>
        <div class="header-title">Bloco<span>AI</span> — Master Cross-Audit</div>
        <div class="header-tag">Análise Técnica · Motor LangGraph · 3 Agentes Especializados</div>
    </div>
    <div style="display:flex;align-items:center;gap:0.8rem">{badge_html}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 5. LANGGRAPH — ESTADO PARTILHADO
# ─────────────────────────────────────────────
class AuditoriaState(TypedDict):
    # Input do utilizador
    texto_boq:       str
    texto_specs:     str
    guia_filtragem:  str
    nome_boq:        str
    nomes_specs:     list

    # Inter-agentes (preenchido durante o grafo)
    resumo_boq:      str
    resumo_specs:    str
    auditoria_bruta: str
    relatorio_final: str

    # Controlo de fluxo
    modo:            str   # "CROSS" ou "SINGLE"
    tentativas:      int   # retry counter para AGT-02
    erros:           list  # lista de mensagens de erro acumuladas

    # Métricas para UI
    n_ficheiros:     int
    paginas_sem_texto: list  # páginas PDF sem texto detectável


# ─────────────────────────────────────────────
# 6. FUNÇÕES DE LEITURA DE DOCUMENTOS
# ─────────────────────────────────────────────
RUIDO = {'nan','none','0.0','0','','n/a','tbd','tbc','-','--',
         '---','#n/a','#ref!','#value!','#name?'}

def read_document(file) -> tuple[str, list]:
    """Lê Excel ou PDF. Devolve (texto, paginas_sem_texto)."""
    paginas_sem_texto = []

    if file.name.lower().endswith('.pdf'):
        partes = []
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for i, p in enumerate(pdf.pages):
                texto_pag = p.extract_text(layout=True)
                if texto_pag:
                    partes.append(f"[Pág: {i+1}] {texto_pag}")
                else:
                    paginas_sem_texto.append(i + 1)
        return "\n".join(partes), paginas_sem_texto

    else:
        xls   = pd.ExcelFile(file)
        lines = []
        for sheet in xls.sheet_names:
            df = xls.parse(sheet).astype(str)
            for idx, row in df.iterrows():
                vals = [v.strip() for v in row
                        if v.strip().lower() not in RUIDO and len(v.strip()) > 1]
                if len(vals) > 1:
                    lines.append(f"[Linha: {idx+2}] {' | '.join(vals)}")
        return "\n".join(lines), []


# ─────────────────────────────────────────────
# 7. LANGGRAPH — NÓS (AGENTES)
# ─────────────────────────────────────────────

def _chunkar(texto: str, tamanho: int = 75000, overlap_linhas: int = 8) -> list:
    """Divide texto em chunks com sobreposição por linhas completas.

    Estratégia:
      1. Divide por linhas para nunca cortar uma spec a meio.
      2. Acumula linhas até atingir `tamanho` caracteres → fecha o chunk.
      3. As últimas `overlap_linhas` linhas do chunk anterior abrem o chunk seguinte,
         garantindo que specs na fronteira são sempre vistas em contexto completo.

    Args:
        texto:         Texto plano anotado (ex: "[Linha: 47] S355 | EXC3 | ...").
        tamanho:       Tamanho máximo de cada chunk em caracteres (default 75k).
        overlap_linhas: Número de linhas a repetir entre chunks consecutivos (default 8).
    """
    if not texto:
        return []

    linhas = texto.splitlines(keepends=True)
    chunks = []
    chunk_atual: list[str] = []
    tamanho_atual = 0

    for linha in linhas:
        # Se adicionar esta linha ultrapassa o limite e já temos conteúdo → fecha chunk
        if tamanho_atual + len(linha) > tamanho and chunk_atual:
            chunks.append("".join(chunk_atual))
            # As últimas N linhas tornam-se o início do próximo chunk (overlap)
            chunk_atual = chunk_atual[-overlap_linhas:]
            tamanho_atual = sum(len(l) for l in chunk_atual)

        chunk_atual.append(linha)
        tamanho_atual += len(linha)

    if chunk_atual:
        chunks.append("".join(chunk_atual))

    return chunks


@retry(
    # Só faz retry para erros transitórios — rate limit, rede, timeout.
    # Erros de autenticação, formato, etc. falham imediatamente (correcto).
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)),
    # 4 tentativas no total (1 original + 3 retries)
    stop=stop_after_attempt(4),
    # Espera: 2s → 4s → 8s (backoff exponencial com jitter automático do tenacity)
    wait=wait_exponential(multiplier=1, min=2, max=30),
    # Regista cada retry no terminal com o motivo
    before_sleep=before_sleep_log(_log, logging.WARNING),
    # Mantém o erro original em vez de re-lançar como RetryError
    reraise=True,
)
def _invocar_llm(llm, mensagens: list) -> str:
    """Chama o LLM com retry automático para erros transitórios.

    Comportamento por tipo de erro:
      RateLimitError (429)  → espera e tenta de novo (até 4x)
      APIConnectionError    → espera e tenta de novo (até 4x)
      APITimeoutError       → espera e tenta de novo (até 4x)
      Qualquer outro erro   → falha imediatamente, sem retry

    Espera entre tentativas: 2s → 4s → 8s (máx 30s).
    """
    return llm.invoke(mensagens).content


def _extrair_chunks(texto: str, nome_ficheiro: str, llm,
                    prog_placeholder, status_placeholder) -> str:
    """Extracção exaustiva de specs por chunks com sobreposição."""
    chunks = _chunkar(texto)
    if not chunks:
        return ""

    sys_msg = SystemMessage(content=f"""You are an Expert Engineering Classifier and Transcriber.
Read the text, DETERMINE ITS TECHNICAL DOMAIN, and extract the primary cost drivers.

CRITICAL RULES:
1. DETERMINE DOMAIN: Classify the primary subject (e.g. "Fire Protection", "Structural Steel", "Concrete").
2. FOCUS ON COST DRIVERS: Extract ONLY Steel grades, Concrete grades, Decking, Cladding, Insulation, Fire/Corrosion Protection.
3. IGNORE SUNDRIES: Ignore minor items (doors, kerbs, fences, drainage pipes, small accessories).
4. IGNORE QUANTITIES: Ignore commercial totals (747 tn, 1000m2).
5. EXACT STRINGS: Use exact names found in text ("S355", "TATA D60x1.2mm", "Intumescent 1 Hr").

FORMAT FOR EVERY ITEM FOUND:
[FILE: {nome_ficheiro} | DOMAIN: <domain>] | Phase: <phase> | Zone: <zone> | Spec: <exact string>
""")

    resumos = []
    for i, chunk in enumerate(chunks):
        pct = int(((i + 1) / len(chunks)) * 100)
        status_placeholder.markdown(
            f'<div style="font-family:\'Space Mono\',monospace;font-size:0.72rem;color:#3a6aaa">'
            f'<span style="color:#5a9aff">{nome_ficheiro}</span>'
            f' &nbsp;·&nbsp; Bloco {i+1}/{len(chunks)} &nbsp;·&nbsp; {pct}%</div>',
            unsafe_allow_html=True
        )
        prog_placeholder.progress((i + 1) / len(chunks))
        try:
            # _invocar_llm faz retry automático para 429 / rede / timeout
            conteudo = _invocar_llm(llm, [sys_msg, HumanMessage(
                content=f"Extract all major technical specs from this chunk:\n\n{chunk}"
            )])
            resumos.append(conteudo)
            time.sleep(0.3)   # cortesia mínima para a API
        except Exception as e:
            # Só chega aqui se falhou nas 4 tentativas OU erro não-transitório
            resumos.append(f"[Bloco {i+1} não processado após retries: {type(e).__name__}]")

    return "\n\n".join(resumos)


# ── NÓ 0 — Router ──────────────────────────────────────────────────────────
def nó_router(state: AuditoriaState) -> dict:
    modo = "CROSS" if (state["texto_boq"] and state["texto_specs"]) else "SINGLE"
    return {"modo": modo}


# ── NÓ 1 — Extrator ────────────────────────────────────────────────────────
def nó_extrator(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=state["_api_key"],
        temperature=0.0
    )

    prog    = state["_prog_slot"]
    status  = state["_status_slot"]

    resumo_boq   = ""
    resumo_specs = ""

    if state["texto_boq"]:
        resumo_boq = _extrair_chunks(
            state["texto_boq"], f"BOQ: {state['nome_boq']}",
            llm, prog, status
        )

    if state["texto_specs"]:
        for nome in state["nomes_specs"]:
            # cada spec é delimitada no texto por marcador de ficheiro
            pass
        resumo_specs = _extrair_chunks(
            state["texto_specs"],
            f"SPECS: {', '.join(state['nomes_specs'])}",
            llm, prog, status
        )

    erros = list(state.get("erros", []))
    if not resumo_boq and not resumo_specs:
        erros.append("AGT-01: Nenhum conteúdo foi extraído dos documentos.")

    return {
        "resumo_boq":   resumo_boq,
        "resumo_specs": resumo_specs,
        "erros":        erros,
    }


# ── NÓ 2 — Auditor Sénior (com retry) ──────────────────────────────────────
def nó_auditor(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=state["_api_key"],
        temperature=0.1
    )

    tentativas = state.get("tentativas", 0) + 1

    if state["modo"] == "CROSS":
        dados   = (f"=== BOQ EXTRACTS ===\n{state['resumo_boq']}\n\n"
                   f"=== PDF SPECS EXTRACTS ===\n{state['resumo_specs']}")
        missao  = "CROSS-DOCUMENT AUDIT"
    else:
        dados   = state["resumo_boq"] or state["resumo_specs"]
        missao  = "SINGLE-DOCUMENT HIERARCHY"

    sys_msg = SystemMessage(content=f"""You are a Lead Estimator performing a {missao}.
CLEAN, DEDUPLICATE, and ORGANIZE the raw data into a readable executive summary.

CRITICAL RULES:
1. DEDUPLICATION IS MANDATORY: If a spec appears multiple times in the same Zone, write it ONLY ONCE.
2. NO LONG BULLETED LISTS: Combine specs into neat, comma-separated paragraphs.
3. GLOBAL AUDIT: Include a "GLOBAL INCONSISTENCIES" section at the end.

{"CROSS-DOCUMENT FORMAT:" if missao == "CROSS-DOCUMENT AUDIT" else "SINGLE-DOCUMENT FORMAT:"}
Phase: [Name]
--> Zone: [Name]
{"   ---> BOQ SPECS: [...]\n   ---> SPECIFICATIONS (PDF): [...]\n   ---> MATCH STATUS: [Aligned / conflict description]" if missao == "CROSS-DOCUMENT AUDIT" else "   ---> TECHNICAL PROFILE: [...]\n   ---> LOCAL INCONSISTENCIES: [...]"}

GLOBAL INCONSISTENCIES (CROSS-PHASE / CROSS-DOC)
[List major technical and financial risks]
""")

    try:
        auditoria = _invocar_llm(llm, [sys_msg, HumanMessage(
            content=f"Build the clean deduplicated audit:\n\n{dados}"
        )])
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-02 tentativa {tentativas} ({type(e).__name__}): {e}")
        return {"auditoria_bruta": "", "tentativas": tentativas, "erros": erros}

    return {"auditoria_bruta": auditoria, "tentativas": tentativas}


# ── NÓ 3 — Apresentador ────────────────────────────────────────────────────
def nó_apresentador(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=state["_api_key"],
        temperature=0.1
    )

    sys_msg = SystemMessage(content="""You are an Executive Technical Writer for a Construction Firm.
Format the raw audit into a beautiful, user-friendly Executive Summary.

CRITICAL FORMATTING RULES:
1. TONE: Professional, concise, user-friendly.
2. HIERARCHY: Clean Phase/Zone breakdown with comma-separated specs.
3. THE TABLE: Convert "Global Inconsistencies" into a Markdown Table.
   Columns: | ID | Category | Location / Zone | Discrepancy Found | Risk / Impact |
4. NO ADDED DATA: Do not invent new data. Only format what the Auditor provided.
""")

    try:
        relatorio = _invocar_llm(llm, [sys_msg, HumanMessage(
            content=f"Format this raw audit into a clean Executive Report:\n\n{state['auditoria_bruta']}"
        )])
        return {"relatorio_final": relatorio}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-03 ({type(e).__name__}): {e}")
        return {"relatorio_final": "", "erros": erros}


# ── NÓ DE ERRO ─────────────────────────────────────────────────────────────
def nó_erro(state: AuditoriaState) -> dict:
    # Estado final de erro — não altera dados, apenas sinaliza
    return {}


# ─────────────────────────────────────────────
# 8. LANGGRAPH — EDGES CONDICIONAIS
# ─────────────────────────────────────────────

def decidir_após_extracção(state: AuditoriaState) -> str:
    tem_dados = bool(state.get("resumo_boq") or state.get("resumo_specs"))
    return "auditar" if tem_dados else "erro"


def decidir_após_auditoria(state: AuditoriaState) -> str:
    auditoria  = state.get("auditoria_bruta", "")
    tentativas = state.get("tentativas", 0)
    if len(auditoria.strip()) >= 100:
        return "formatar"
    if tentativas < 2:
        return "retry"      # volta ao nó_auditor
    return "erro"           # desiste após 2 tentativas


# ─────────────────────────────────────────────
# 9. CONSTRUÇÃO DO GRAFO
# ─────────────────────────────────────────────

def construir_grafo() -> any:
    workflow = StateGraph(AuditoriaState)

    workflow.add_node("router",    nó_router)
    workflow.add_node("extrair",   nó_extrator)
    workflow.add_node("auditar",   nó_auditor)
    workflow.add_node("formatar",  nó_apresentador)
    workflow.add_node("erro",      nó_erro)

    workflow.set_entry_point("router")

    workflow.add_edge("router",  "extrair")
    workflow.add_edge("formatar", END)
    workflow.add_edge("erro",     END)

    workflow.add_conditional_edges(
        "extrair",
        decidir_após_extracção,
        {"auditar": "auditar", "erro": "erro"}
    )
    workflow.add_conditional_edges(
        "auditar",
        decidir_após_auditoria,
        {"formatar": "formatar", "retry": "auditar", "erro": "erro"}
    )

    return workflow.compile()

grafo_auditoria = construir_grafo()


# ─────────────────────────────────────────────
# 10. SESSION STATE
# ─────────────────────────────────────────────
for chave, valor_default in [
    ("relatorio_final",   ""),
    ("processado",        False),
    ("pipeline_state",    ["idle", "idle", "idle"]),
    ("n_ficheiros",       0),
    ("n_fases_hint",      "—"),
    ("erros_sessao",      []),
    ("paginas_aviso",     []),
]:
    if chave not in st.session_state:
        st.session_state[chave] = valor_default


# ─────────────────────────────────────────────
# 11. PIPELINE VISUAL
# ─────────────────────────────────────────────
STEPS = [
    ("AGT-01", "Extrator",       "Classificação de Domínio & Extracção"),
    ("AGT-02", "Auditor Sénior", "Cross-Audit & Deduplicação"),
    ("AGT-03", "Apresentador",   "Formatação do Relatório Executivo"),
]
ICONS = {"idle": "○", "active": "◉", "done": "✓", "error": "✗", "retry": "↺"}


def render_pipeline(states: list) -> str:
    html = ""
    for (num, title, sub), state in zip(STEPS, states):
        icon        = ICONS.get(state, "○")
        pulse_cls   = " pulse" if state == "active" else (" pulse-amber" if state == "retry" else "")
        html += f"""
        <div class="pipeline-step {state}">
            <div class="step-num {state}">{num}</div>
            <div class="step-title {state}">{title}</div>
            <div class="step-sub {state}">{sub}</div>
            <div class="step-icon{pulse_cls}">{icon}</div>
        </div>"""
    return f'<div class="pipeline-wrap">{html}</div>'


pipeline_slot = st.empty()
pipeline_slot.markdown(
    render_pipeline(st.session_state.pipeline_state),
    unsafe_allow_html=True
)


# ─────────────────────────────────────────────
# 12. BLOCO 1 — UPLOAD
# ─────────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <span class="section-number">STEP 01 / 03</span>
    <div class="section-title">📂 Documentos de Entrada</div>
</div>
""", unsafe_allow_html=True)

col_boq, col_specs = st.columns(2, gap="medium")

with col_boq:
    st.markdown('<div class="upload-label">BOQ — Bill of Quantities</div>'
                '<div class="upload-desc">Ficheiro de orçamento principal · Excel ou PDF</div>',
                unsafe_allow_html=True)
    file_boq = st.file_uploader("BOQ", type=["xlsx","xls","pdf"],
                                key="boq", label_visibility="collapsed")
    if file_boq:
        ext     = file_boq.name.split(".")[-1].upper()
        size_kb = round(file_boq.size / 1024, 1)
        st.markdown(
            f'<span class="file-chip">📄 {file_boq.name} &nbsp;·&nbsp; {ext} &nbsp;·&nbsp; {size_kb} KB</span>',
            unsafe_allow_html=True
        )

with col_specs:
    st.markdown('<div class="upload-label">Cadernos de Encargos — Specs</div>'
                '<div class="upload-desc">Múltiplos PDFs de especificações técnicas</div>',
                unsafe_allow_html=True)
    files_specs = st.file_uploader("Specs", type=["pdf"], accept_multiple_files=True,
                                   key="specs", label_visibility="collapsed")
    if files_specs:
        for f in files_specs:
            size_kb = round(f.size / 1024, 1)
            st.markdown(
                f'<span class="file-chip">📑 {f.name} &nbsp;·&nbsp; {size_kb} KB</span>',
                unsafe_allow_html=True
            )

st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 13. BLOCO 2 — INSTRUÇÕES
# ─────────────────────────────────────────────
st.markdown("""
<div class="section-card" style="margin-top:0.8rem">
    <span class="section-number">STEP 02 / 03</span>
    <div class="section-title">🎯 Foco da Auditoria</div>
</div>
""", unsafe_allow_html=True)

guia_padrao = (
    "Foco Exclusivo: Graus de Aço/Betão, Revestimentos, Espessuras, "
    "Proteção Passiva (Fogo/Pintura). Ignorar completamente itens menores "
    "(portas, lancis, tubagens, acessórios)."
)
guia_input = st.text_area(
    "Instruções de Filtragem", value=guia_padrao, height=90,
    help="Descreve o que os agentes devem priorizar ou ignorar.",
)


# ─────────────────────────────────────────────
# 14. BLOCO 3 — ARRANQUE
# ─────────────────────────────────────────────
st.markdown("""
<div class="section-card" style="margin-top:0.8rem">
    <span class="section-number">STEP 03 / 03</span>
    <div class="section-title">🚀 Iniciar Processamento</div>
</div>
""", unsafe_allow_html=True)

col_btn, col_hint = st.columns([2, 5], gap="medium")
with col_btn:
    iniciar = st.button("▶  INICIAR AUDITORIA MASTER", use_container_width=True)
with col_hint:
    if not api_key_final:
        st.markdown('<div style="font-size:0.78rem;color:#7a3030;padding-top:0.65rem">'
                    '⚠ Configura a API Key na barra lateral antes de avançar.</div>',
                    unsafe_allow_html=True)
    elif not file_boq and not files_specs:
        st.markdown('<div style="font-size:0.78rem;color:#4a6fa0;padding-top:0.65rem">'
                    'Carrega pelo menos um documento (BOQ ou Caderno de Encargos).</div>',
                    unsafe_allow_html=True)
    else:
        docs_txt = []
        if file_boq:
            docs_txt.append(f"BOQ: <span style='color:#5a9aff'>{file_boq.name}</span>")
        if files_specs:
            docs_txt.append(f"<span style='color:#5a9aff'>{len(files_specs)}</span> Caderno(s)")
        st.markdown(
            f'<div style="font-size:0.78rem;color:#2a6a30;padding-top:0.65rem">'
            f'✓ Pronto — {" + ".join(docs_txt)}</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# 15. PROCESSAMENTO — ORQUESTRADO PELO GRAFO
# ─────────────────────────────────────────────
if iniciar:
    if not api_key_final:
        st.error("🔑 API Key em falta. Adiciona-a na barra lateral.")
    elif not file_boq and not files_specs:
        st.warning("Carrega pelo menos um documento para iniciar.")
    else:
        # ── Ler documentos ──
        texto_boq    = ""
        texto_specs  = ""
        nomes_specs  = []
        nome_boq     = ""
        n_ficheiros  = 0
        todas_paginas_sem_texto = []

        prog_slot   = st.progress(0)
        status_slot = st.empty()

        if file_boq:
            n_ficheiros += 1
            nome_boq = file_boq.name
            texto_boq, sem_texto = read_document(file_boq)
            todas_paginas_sem_texto += [f"{file_boq.name} pág.{p}" for p in sem_texto]

        if files_specs:
            partes_specs = []
            for spec in files_specs:
                n_ficheiros += 1
                nomes_specs.append(spec.name)
                txt, sem_texto = read_document(spec)
                partes_specs.append(txt)
                todas_paginas_sem_texto += [f"{spec.name} pág.{p}" for p in sem_texto]
            texto_specs = "\n\n".join(partes_specs)

        # ── Aviso páginas sem texto ──
        if todas_paginas_sem_texto:
            aviso = ", ".join(todas_paginas_sem_texto[:10])
            extra = f" (+{len(todas_paginas_sem_texto)-10} mais)" if len(todas_paginas_sem_texto) > 10 else ""
            st.markdown(
                f'<div class="pdf-warning">⚠ Páginas sem texto detectadas (possível digitalização): '
                f'{aviso}{extra} — conteúdo não foi analisado.</div>',
                unsafe_allow_html=True
            )

        # ── Pipeline visual: AGT-01 activo ──
        st.session_state.pipeline_state = ["active", "idle", "idle"]
        pipeline_slot.markdown(render_pipeline(st.session_state.pipeline_state), unsafe_allow_html=True)

        try:
            # Estado inicial para o grafo
            estado_inicial: AuditoriaState = {
                "texto_boq":           texto_boq,
                "texto_specs":         texto_specs,
                "guia_filtragem":      guia_input,
                "nome_boq":            nome_boq,
                "nomes_specs":         nomes_specs,
                "resumo_boq":          "",
                "resumo_specs":        "",
                "auditoria_bruta":     "",
                "relatorio_final":     "",
                "modo":                "",
                "tentativas":          0,
                "erros":               [],
                "n_ficheiros":         n_ficheiros,
                "paginas_sem_texto":   todas_paginas_sem_texto,
                # Slots de UI passados via estado (não persistem em session_state)
                "_api_key":            api_key_final,
                "_prog_slot":          prog_slot,
                "_status_slot":        status_slot,
            }

            # ── Executar grafo com stream — pipeline visual actualiza a cada nó ──
            # stream_mode="updates" emite {node_name: {campos alterados}} após cada nó.
            # Isto permite reflectir o estado real do grafo (incluindo retry) em tempo real.
            estado_final = dict(estado_inicial)

            for chunk in grafo_auditoria.stream(
                estado_inicial,
                {"recursion_limit": 10},
                stream_mode="updates",
            ):
                for node_name, updates in chunk.items():
                    # Acumular estado completo
                    estado_final.update(updates)

                    # Actualizar pipeline visual com base no nó que acabou de correr
                    if node_name == "extrair":
                        # AGT-01 concluído → AGT-02 começa
                        st.session_state.pipeline_state = ["done", "active", "idle"]

                    elif node_name == "auditar":
                        auditoria  = estado_final.get("auditoria_bruta", "")
                        tentativas = estado_final.get("tentativas", 1)
                        if len(auditoria.strip()) >= 100:
                            # output válido → AGT-03 começa
                            st.session_state.pipeline_state = ["done", "done", "active"]
                        elif tentativas < 2:
                            # output fraco, ainda tem tentativas → mostra retry
                            st.session_state.pipeline_state = ["done", "retry", "idle"]
                        else:
                            # esgotou tentativas → vai para erro
                            st.session_state.pipeline_state = ["done", "error", "idle"]

                    elif node_name == "formatar":
                        st.session_state.pipeline_state = ["done", "done", "done"]

                    elif node_name == "erro":
                        # Identifica qual agente falhou para feedback mais preciso
                        erros_acum = estado_final.get("erros", [])
                        if any("AGT-01" in e for e in erros_acum):
                            st.session_state.pipeline_state = ["error", "idle", "idle"]
                        elif any("AGT-02" in e for e in erros_acum):
                            st.session_state.pipeline_state = ["done", "error", "idle"]
                        else:
                            st.session_state.pipeline_state = ["error", "error", "error"]

                    pipeline_slot.markdown(
                        render_pipeline(st.session_state.pipeline_state),
                        unsafe_allow_html=True,
                    )

            prog_slot.empty()
            status_slot.empty()

            # Determinar resultado final
            relatorio  = estado_final.get("relatorio_final", "")
            erros      = estado_final.get("erros", [])
            tentativas = estado_final.get("tentativas", 0)

            if relatorio and len(relatorio.strip()) >= 100:
                # Garantir estado final correcto (pode já estar done, mas confirmamos)
                st.session_state.pipeline_state = ["done", "done", "done"]
                pipeline_slot.markdown(render_pipeline(st.session_state.pipeline_state), unsafe_allow_html=True)

                # Guardar resultado
                st.session_state.relatorio_final = relatorio
                st.session_state.processado      = True
                st.session_state.n_ficheiros     = n_ficheiros
                st.session_state.erros_sessao    = erros
                st.session_state.paginas_aviso   = todas_paginas_sem_texto

                import re
                fases = len(re.findall(r'(?im)^\s*\*{0,2}phase\s*\d*\s*[:\-–]', relatorio))
                st.session_state.n_fases_hint = fases if fases else "—"

                # Persistência automática
                try:
                    from datetime import datetime
                    pasta = Path(__file__).resolve().parent.parent / "historico_auditorias"
                    pasta.mkdir(exist_ok=True)
                    ts       = datetime.now().strftime("%Y%m%d_%H%M")
                    ficheiro = pasta / f"Auditoria_{ts}.txt"
                    ficheiro.write_text(relatorio, encoding="utf-8")
                except Exception:
                    pass  # falha silenciosa — não bloqueia o utilizador

                if erros:
                    st.warning(f"⚠ Auditoria concluída com {len(erros)} aviso(s): {'; '.join(erros)}")
                if tentativas > 1:
                    st.info(f"ℹ AGT-02 precisou de {tentativas} tentativa(s) para produzir output válido.")

            else:
                st.session_state.pipeline_state = ["error", "error", "error"]
                pipeline_slot.markdown(render_pipeline(st.session_state.pipeline_state), unsafe_allow_html=True)
                msg_erro = "; ".join(erros) if erros else "Output insuficiente após tentativas máximas."
                st.error(f"Erro Crítico no Pipeline: {msg_erro}")

        except Exception as e:
            prog_slot.empty()
            status_slot.empty()
            st.session_state.pipeline_state = ["error", "error", "error"]
            pipeline_slot.markdown(render_pipeline(st.session_state.pipeline_state), unsafe_allow_html=True)
            st.error(f"Erro Crítico: {e}")


# ─────────────────────────────────────────────
# 16. RESULTADOS
# ─────────────────────────────────────────────
if st.session_state.processado and st.session_state.relatorio_final:

    st.markdown(f"""
    <div class="results-header">
        <div class="results-title">📋 Relatório Executivo de Auditoria</div>
        <div class="results-meta">Auditoria concluída · {st.session_state.n_ficheiros} ficheiro(s)</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="results-body">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-pill">
            <span class="metric-val">{st.session_state.n_ficheiros}</span>
            <span class="metric-label">Ficheiros</span>
        </div>
        <div class="metric-pill">
            <span class="metric-val">{st.session_state.n_fases_hint}</span>
            <span class="metric-label">Fases Detectadas</span>
        </div>
        <div class="metric-pill">
            <span class="metric-val" style="color:#40ee88">✓</span>
            <span class="metric-label">Auditoria OK</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="report-md">', unsafe_allow_html=True)
    st.markdown(st.session_state.relatorio_final)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
    col_dl1, _ = st.columns([2, 5])
    with col_dl1:
        st.download_button(
            "📥 Descarregar Relatório (.txt)",
            data=st.session_state.relatorio_final,
            file_name="Auditoria_Master_BlocoAI.txt",
            use_container_width=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)
