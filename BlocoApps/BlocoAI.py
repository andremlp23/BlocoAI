import streamlit as st
import pandas as pd
import time
import pdfplumber
import os
import io
import json
import concurrent.futures # <-- Nova biblioteca para paralelismo

from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from docx import Document

# ============================================================
# 0) CARREGAR AMBIENTE E REGRAS EXTERNAS
# ============================================================
def carregar_env_local():
    base_dir = Path(__file__).resolve().parent
    candidatos = [base_dir / ".env", base_dir.parent / ".env"]
    for env_path in candidatos:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            linha = line.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave = chave.strip()
            if chave.startswith("export "):
                chave = chave[len("export "):].strip()
            valor = valor.strip().strip('"').strip("'")
            if chave:
                os.environ[chave] = valor
        return

carregar_env_local()

@st.cache_data
def carregar_regras_json():
    """Lê as regras de exclusão JSON apenas uma vez e guarda em RAM."""
    file_path = "RegrasMekkin.json"
    
    fallback_regras = {
        "regra_final": "Assumir que toda a informacao e IRRELEVANTE ate demonstrar impacto direto na estrutura metalica.",
        "manter": ["Aço estrutural", "Proteção anticorrosiva", "Proteção ao fogo", "Lajes colaborantes", "EXC2/EXC3", "Interfaces com civil"],
        "ignorar_estritamente": ["Arquitetura", "Cores", "Mobiliario", "AVAC sem carga estrutural", "Betão sem interface", "Eletricidade"]
    }
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.dumps(json.load(f), ensure_ascii=False, indent=2)
    else:
        return json.dumps(fallback_regras, ensure_ascii=False, indent=2)

regras_extracao = carregar_regras_json()


# ============================================================
# 1) STREAMLIT UI
# ============================================================
st.set_page_config(page_title="BlocoAI - Auditoria Hierárquica", layout="wide", page_icon="🏗️")
st.sidebar.title("Configurações")

modo_execucao = st.sidebar.radio("Ligação", ["API Key", "Local"], index=0)
api_key_env = os.getenv("CHATGPT_API_KEY", "")

if modo_execucao == "API Key":
    st.sidebar.caption("Modelos: 4o-mini (Extração) | 5-mini (Auditoria)")
    api_key_input = st.sidebar.text_input("🔑 API Key (Overwrite)", value="", type="password")
    api_key_final = api_key_input.strip() if api_key_input.strip() else api_key_env
else:
    torre_ip = st.sidebar.text_input("🌐 IP da Torre", value="100.105.95.121")
    modelo_selecionado = st.sidebar.selectbox("🧠 LLM", ["qwen3.5:9b", "llama3.2:3b"])


# ============================================================
# 2) LEITURA DE DOCUMENTOS
# ============================================================
def read_pdf_text(file) -> str:
    text_lines = []
    with pdfplumber.open(file) as pdf:
        for i, p in enumerate(pdf.pages):
            t = p.extract_text(layout=True)
            if t:
                for linha in t.splitlines():
                    if linha.strip():
                        text_lines.append(f"[Pág: {i+1}] {linha.strip()}")
    return "\n".join(text_lines)

def read_docx_text(file) -> str:
    doc = Document(io.BytesIO(file.read()))
    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paras)

def read_excel_text(file) -> str:
    xls = pd.ExcelFile(file)
    lines = []
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        for idx, row in df.iterrows():
            vals = [str(v).strip() for v in row if str(v).strip().lower() not in ['nan', 'none', '0.0', '0', 'none']]
            if len(vals) > 1:
                lines.append(f"[Linha: {idx+2}] {' | '.join(vals)}")
    return "\n".join(lines)

def read_document(file) -> str:
    name = file.name.lower()
    if name.endswith(".pdf"): return read_pdf_text(file)
    if name.endswith(".docx"): return read_docx_text(file)
    if name.endswith((".xlsx", ".xls")): return read_excel_text(file)
    return ""

def chunk_by_lines(texto, max_chars=15000):
    lines = [l for l in texto.splitlines() if l.strip()]
    chunks, cur, n = [], [], 0
    for l in lines:
        if n + len(l) + 1 > max_chars and cur:
            chunks.append("\n".join(cur))
            cur, n = [l], len(l)
        else:
            cur.append(l)
            n += len(l) + 1
    if cur: chunks.append("\n".join(cur))
    return chunks


# ============================================================
# 3) AGENTE 1: SPECS -> CONTEXTO (COM MULTITHREADING)
# ============================================================
def gerar_contexto_specs(files, llm, max_chars_per_file=120000, chunk_chars=12000, max_disciplines=4, max_bullets=22, max_final=65000):
    import re
    from collections import defaultdict

    def safe_seek0(f):
        try: f.seek(0)
        except: pass

    def norm_key(s): return re.sub(r"\s+", " ", (s or "").strip().lower())
    
    def dedupe_list(items):
        seen = set()
        out = []
        for it in items:
            k = norm_key(it)
            if k and k not in seen:
                seen.add(k)
                out.append(it.strip())
        return out

    def safe_extract_bullets(text):
        return [ln[2:].strip() for ln in (text or "").splitlines() if ln.strip().startswith("- ")]

    def safe_extract_disciplines(text):
        return [ln[2:].strip() for ln in (text or "").splitlines() if ln.strip().startswith("- ") and len(ln[2:].strip()) <= 60]

    discipline_to_bullets = defaultdict(list)

    system_detect = SystemMessage(content="You are a Construction Specifications Analyst.\nTask: identify high-level construction disciplines.\nOUTPUT RULES: Output ONLY bullet lines starting with '- '.\nEach bullet is ONE discipline label (2–5 words).")

    system_extract = SystemMessage(content=(
        "You are a Construction Specifications Analyst.\n"
        "Task: extract REUSABLE baseline rules ONLY.\n"
        f"CRITICAL EXCLUSION RULES (OBEY STRICTLY):\n{regras_extracao}\n\n"
        "OUTPUT RULES: Output ONLY bullet lines starting with '- '."
    ))

    # Função para processar bloco individual em paralelo
    def processar_bloco_spec(chunk_text):
        human = HumanMessage(content=f"Extract reusable baseline rules from this excerpt.\n\n{chunk_text}")
        r = llm.invoke([system_extract, human])
        return safe_extract_bullets(r.content)

    for f in files:
        safe_seek0(f)
        raw = read_document(f)[:max_chars_per_file]
        safe_seek0(f)
        if not raw.strip(): continue

        chunks = chunk_by_lines(raw, max_chars=chunk_chars)
        if not chunks: continue

        # Deteta disciplinas usando os 2 primeiros blocos (rápido, não precisa ser paralelo)
        detect_excerpt = "\n".join(chunks[:2])
        rdet = llm.invoke([system_detect, HumanMessage(content=detect_excerpt)])
        disciplines = dedupe_list(safe_extract_disciplines(rdet.content))[:max_disciplines] or ["General"]

        file_bullets = []
        # PARALELISMO: Extrai regras de todos os blocos do ficheiro ao mesmo tempo
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(processar_bloco_spec, c) for c in chunks]
            for future in concurrent.futures.as_completed(futures):
                file_bullets.extend(future.result())

        file_bullets = dedupe_list(file_bullets)[:max_bullets]
        for d in disciplines:
            discipline_to_bullets[d].extend(file_bullets)

    if not discipline_to_bullets:
        return "[SPECS_CONTEXT]\nDISCIPLINE: General\n- No rules extracted.\n[END_SPECS_CONTEXT]"

    system_compress = SystemMessage(content="Compress bullets for ONE discipline.\nOutput ONLY bullet lines starting with '- '.\nShorten aggressively; merge related ideas.")

    blocks = []
    for d, bullets in discipline_to_bullets.items():
        bullets_text = "\n".join([f"- {b}" for b in dedupe_list(bullets)[:20]])
        r = llm.invoke([system_compress, HumanMessage(content=f"Discipline: {d}\nCompress:\n\n{bullets_text}")])
        comp = (r.content or "").strip()
        blocks.append(f"DISCIPLINE: {d}\n{comp if '- ' in comp else bullets_text}")

    final = "[SPECS_CONTEXT]\n" + "\n\n".join(blocks) + "\n[END_SPECS_CONTEXT]"
    return final[:max_final]


# ============================================================
# 4) AGENTE 2: BOQ EXTRACTION (COM MULTITHREADING)
# ============================================================
def extrair_sumario_parcial(texto_integral: str, guia_texto: str, llm, specs_context: str):
    chunks = chunk_by_lines(texto_integral, max_chars=15000)
    st.markdown(f"### 📡 Fase 1: Extraindo {len(chunks)} blocos em paralelo...")
    progresso_bar = st.progress(0)

    contexto_txt = f"\n\nAUTHORITATIVE PROJECT SPECS CONTEXT:\n{specs_context}\n" if specs_context else ""

    mensagem_sistema = SystemMessage(content=f"""You are a Technical Data Hunter. Output is strictly line-based.

CRITICAL EXTRACTION RULES (OBEY THIS JSON RULEBOOK STRICTLY):
{regras_extracao}

Normalize: PH1 -> Phase 1.
Extract ONLY technical items that pass the JSON criteria OR match the specs context.
Output format: EXACTLY 7 fields separated by " || "
PHASE || ZONE || SUBZONE || GRADES || STANDARDS/EXEC || PROTECTION || SCOPE/EVIDENCE

Rules:
- Keep technical numbers (S355, EXC2, R60, D60x1.2mm).
- Remove prices/quantities.
{contexto_txt}
""")

    # Função isolada para a Thread
    def extrair_bloco(chunk_text):
        prompt = f"AUDIT MATRIX:\n{guia_texto}\n\nCHUNK:\n{chunk_text}"
        return llm.invoke([mensagem_sistema, HumanMessage(content=prompt)]).content

    resumos_finais = [None] * len(chunks) # Para garantir que a ordem das páginas não se perde

    # PARALELISMO MAXIMO (8 Trabalhadores)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_idx = {executor.submit(extrair_bloco, c): i for i, c in enumerate(chunks)}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_idx)):
            idx = future_to_idx[future]
            try:
                resumos_finais[idx] = future.result()
            except Exception as e:
                resumos_finais[idx] = f"NO_RECORDS (Error: {e})"
            progresso_bar.progress((i + 1) / len(chunks))

    return "\n\n".join([r for r in resumos_finais if r])


# ============================================================
# 5) FASE 3: AUDITORIA E TABELA (NOVO PROMPT)
# ============================================================
def gerar_consolidacao_hierarquica(resumos_acumulados, llm):
    st.markdown("### 🔍 Fase 2: O Auditor está a cruzar a informação...")
    mensagem_sistema = SystemMessage(content="""
You are a Senior Structural Estimator. You ONLY reformat and consolidate the raw data.

Input lines are: PHASE || ZONE || SUBZONE || GRADES || STANDARDS/EXEC || PROTECTION || SCOPE/EVIDENCE

Rules:
1. Include ALL phases found. Normalize PHn->Phase n.
2. Deduplicate technical details. Use comma-separated lists.
3. CROSS-CHECK: Actively look for inconsistencies between the extracted BOQ specs and the Context provided.

Output template:
Project: Analysis
--> Phase: Phase N
    --> Zone: ZZZ
        ---> Subzone: <name>
            ---> TECHNICAL PROFILE: <grades + standards/exec + protections>
            ---> SCOPE ALERTS: <scope/evidence summary>
            ---> LOCAL INCONSISTENCIES: <conflicts or None>

[AT THE VERY END OF THE REPORT, YOU MUST INCLUDE THIS EXACT TABLE]
GLOBAL INCONSISTENCIES (BOQ vs SPECS)
| ID | Category | Location / Zone | Discrepancy Found | Risk / Impact |
""")
    human = HumanMessage(content="Review, cross-check, and polish this data into the final tree:\n\n" + resumos_acumulados)
    return llm.invoke([mensagem_sistema, human]).content


# ============================================================
# 6) UI PRINCIPAL (AGORA COM OS DOIS MODELOS SEPARADOS)
# ============================================================
st.title("🏗️ BlocoAI: Auditoria Técnica Hierárquica (com Contexto de Specs)")

# Instanciação Dinâmica dos Modelos
if modo_execucao == "API Key" and api_key_final:
    # Extrator: Rápido, Barato, Obediente (Para ler PDFs em massa)
    llm_extrator = ChatOpenAI(model="gpt-4o-mini", api_key=api_key_final, temperature=0.0, max_tokens=8000)
    # Auditor: Inteligente, Lento, Raciocínio (Para cruzar e criar a tabela final)
    llm_auditor = ChatOpenAI(model="gpt-5-mini", api_key=api_key_final, temperature=0.1, max_tokens=8000)
elif modo_execucao != "API Key":
    llm_extrator = ChatOllama(model=modelo_selecionado, base_url=f"http://{torre_ip}:11434", temperature=0.0)
    llm_auditor = llm_extrator


st.subheader("A) Carregar Specs (CSPECs) para gerar contexto da obra")
spec_files = st.file_uploader("Carrega PDFs/DOCX de specs", type=["pdf", "docx"], accept_multiple_files=True)

if "specs_context" not in st.session_state:
    st.session_state.specs_context = ""

if st.button("🧠 Gerar Contexto de Specs"):
    if not spec_files:
        st.warning("Carrega pelo menos um ficheiro de specs.")
    elif modo_execucao == "API Key" and not api_key_final:
        st.error("API key em falta.")
    else:
        with st.spinner("A ler specs em paralelo (Super-Speed)..."):
            st.session_state.specs_context = gerar_contexto_specs(spec_files, llm_extrator) # Usa o modelo rápido!

        st.success(f"✅ Contexto gerado com sucesso.")
        with st.expander("📌 Ver contexto de specs", expanded=False):
            st.text(st.session_state.specs_context)

st.markdown("---")

st.subheader("B) Carregar BOQ / Caderno de Encargos")
file_uploaded = st.file_uploader("BOQ / Caderno de Encargos", type=["xlsx", "xls", "pdf"])

guia_padrao = "1. MATERIAIS\n2. PROTEÇÕES (Fogo, Pintura)\n3. INCONSISTÊNCIAS"
guia_input = st.text_area("Checklist de Auditoria:", value=guia_padrao, height=100)

if "relatorio_final" not in st.session_state:
    st.session_state.relatorio_final = ""
    st.session_state.processado = False

if st.button("🚀 Gerar Relatório Hierárquico"):
    if not file_uploaded:
        st.warning("Carrega um BOQ primeiro.")
        st.stop()
    elif modo_execucao == "API Key" and not api_key_final:
        st.error("API key em falta.")
        st.stop()

    texto_cru = read_document(file_uploaded)
    
    # FASE 1: Extrai rápido com gpt-4o-mini
    resumos = extrair_sumario_parcial(texto_cru, guia_input, llm_extrator, st.session_state.specs_context)
    
    # FASE 2: Audita inteligentemente com gpt-5-mini
    with st.spinner("A cruzar dados e gerar tabela final (O Auditor está a pensar)..."):
        st.session_state.relatorio_final = gerar_consolidacao_hierarquica(resumos, llm_auditor)
        st.session_state.processado = True

if st.session_state.processado:
    st.markdown("---")
    st.header("📋 Relatório de Auditoria Master")
    st.markdown(st.session_state.relatorio_final)
    st.download_button("📥 Descarregar Auditoria (TXT)", data=st.session_state.relatorio_final, file_name="Auditoria_Hierarquica_BlocoAI.txt")