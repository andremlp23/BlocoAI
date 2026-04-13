import streamlit as st
import pandas as pd
import time
import pdfplumber
import os
import io
import time

from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from docx import Document

# ============================================================
# 0) CARREGAR AMBIENTE
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


# ============================================================
# 1) STREAMLIT UI
# ============================================================
st.set_page_config(page_title="BlocoAI - Auditoria Hierárquica", layout="wide", page_icon="🏗️")
st.sidebar.title("Configurações")

modo_execucao = st.sidebar.radio("Ligação", ["API Key", "Local"], index=0)
api_key_env = os.getenv("CHATGPT_API_KEY", "")

if modo_execucao == "API Key":
    st.sidebar.caption("Modelo API: gpt-5-mini (BOQ)")
    api_key_input = st.sidebar.text_input("🔑 API Key (Overwrite)", value="", type="password")
    api_key_final = api_key_input.strip() if api_key_input.strip() else api_key_env
else:
    torre_ip = st.sidebar.text_input("🌐 IP da Torre", value="100.105.95.121")
    modelo_selecionado = st.sidebar.selectbox("🧠 LLM", ["qwen3.5:9b", "llama3.2:3b"])


# ============================================================
# 2) LEITURA DE DOCUMENTOS (BOQ + SPECS)
# ============================================================
def read_pdf_text(file) -> str:
    text_lines = []
    with pdfplumber.open(file) as pdf:
        for i, p in enumerate(pdf.pages):
            t = p.extract_text(layout=True)
            if t:
                # prefixo por página
                for linha in t.splitlines():
                    if linha.strip():
                        text_lines.append(f"[Pág: {i+1}] {linha.strip()}")
    return "\n".join(text_lines)

def read_docx_text(file) -> str:
    # file é um UploadedFile; precisa de bytes
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
    if name.endswith(".pdf"):
        return read_pdf_text(file)
    if name.endswith(".docx"):
        return read_docx_text(file)
    if name.endswith((".xlsx", ".xls")):
        return read_excel_text(file)
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
    if cur:
        chunks.append("\n".join(cur))
    return chunks


# ============================================================
# 3) AGENTE 1: SPECS -> CONTEXTO
# ============================================================
def gerar_contexto_specs(
    files,
    llm,
    max_chars_per_file: int = 120000,   # quanto texto máximo por ficheiro a considerar
    chunk_chars: int = 12000,           # tamanho do chunk para chamadas ao LLM
    max_disciplines_per_file: int = 4,  # quantas disciplinas no máximo por ficheiro
    max_bullets_per_file: int = 22,     # bullets máximos extraídos por ficheiro (antes de merge)
    max_bullets_per_discipline: int = 18,
    max_final_chars: int = 65000,  # AUMENTADO: era 20000, agora permite muito mais conteúdo
) -> str:
    """
    Converte vários docs de specs num contexto curto e reutilizável.
    Output é TEXTO com marcadores fixos.
    Estratégia 100% genérica:
      - Detecta disciplina(s) pelo conteúdo (não pelo nome do ficheiro)
      - Extrai bullets reutilizáveis por disciplina
      - Junta/deduplica e comprime
    """

    import re
    from collections import defaultdict

    # ---------- helpers ----------
    def safe_seek0(f):
        try:
            f.seek(0)
        except Exception:
            pass

    def chunk_by_lines(texto: str, max_chars: int):
        lines = [l for l in (texto or "").splitlines() if l.strip()]
        chunks, cur, n = [], [], 0
        for l in lines:
            if n + len(l) + 1 > max_chars and cur:
                chunks.append("\n".join(cur))
                cur, n = [l], len(l)
            else:
                cur.append(l)
                n += len(l) + 1
        if cur:
            chunks.append("\n".join(cur))
        return chunks

    def trim_to_size(text: str, limit: int) -> str:
        text = (text or "").strip()
        return text if len(text) <= limit else text[:limit].rstrip()

    def norm_key(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").strip().lower())

    def dedupe_list(items):
        seen = set()
        out = []
        for it in items:
            k = norm_key(it)
            if k and k not in seen:
                seen.add(k)
                out.append(it.strip())
        return out

    def safe_extract_bullets(text: str):
        out = []
        for ln in (text or "").splitlines():
            ln = ln.strip()
            if ln.startswith("- "):
                out.append(ln[2:].strip())
        return out

    def safe_extract_disciplines(text: str):
        # espera lines "- <discipline>"
        ds = []
        for ln in (text or "").splitlines():
            ln = ln.strip()
            if ln.startswith("- "):
                d = ln[2:].strip()
                if d and len(d) <= 60:
                    ds.append(d)
        return ds

    # ---------- 1) por ficheiro: identificar disciplinas + extrair regras ----------
    discipline_to_bullets = defaultdict(list)

    system_detect = SystemMessage(content=(
        "You are a Construction Specifications Analyst.\n"
        "Task: identify high-level construction disciplines covered by the excerpt.\n"
        "OUTPUT RULES:\n"
        "- Output ONLY bullet lines starting with '- '.\n"
        "- Each bullet is ONE discipline label (2–5 words).\n"
        "- No headers, no explanations.\n"
        "Examples of disciplines (use only if supported by text):\n"
        "- Structural Steel\n"
        "- Steel Decking\n"
        "- Metal Fabrications\n"
        "- Stairs & Handrails\n"
        "- Intumescent Fireproofing\n"
        "- Coatings / Galvanizing\n"
        "- Bolting & Fasteners\n"
        "- Welding & QA/QC\n"
    ))

    system_extract = SystemMessage(content=(
        "You are a Construction Specifications Analyst.\n"
        "Task: extract REUSABLE baseline rules ONLY (things that help interpret BOQs later).\n"
        "OUTPUT RULES:\n"
        "- Output ONLY bullet lines starting with '- '.\n"
        "- Each bullet must be ONE short rule (single sentence).\n"
        "- No headers, no explanations, no numbering.\n"
        "- Do NOT add recommendations/next steps/questions/offers.\n"
        "KEEP: grades, execution class defaults, standards families, welding qualifications, bolt classes, "
        "coatings/galv rules, fireproofing test/DFT/QC rules, decking fixing rules, submittals/QA responsibilities.\n"
        "AVOID: long standard enumerations; prefer standard families.\n"
        "Never invent.\n"
    ))

    for f in files:
        safe_seek0(f)
        raw = read_document(f)  # usa a tua função existente
        safe_seek0(f)

        if not raw or not raw.strip():
            continue

        raw = raw[:max_chars_per_file]
        chunks = chunk_by_lines(raw, max_chars=chunk_chars)

        # --- detectar disciplinas (só usando um excerto inicial) ---
        detect_excerpt = "\n".join(chunks[:2])  # 1-2 chunks bastam normalmente
        rdet = llm.invoke([system_detect, HumanMessage(content=detect_excerpt)])
        disciplines = safe_extract_disciplines(rdet.content)
        disciplines = dedupe_list(disciplines)[:max_disciplines_per_file]
        if not disciplines:
            disciplines = ["General"]

        # --- extrair bullets por chunk (sem depender de nomes fixos) ---
        file_bullets = []
        for c in chunks:
            human = HumanMessage(content=(
                "Extract reusable baseline rules from this excerpt.\n"
                "Keep them discipline-agnostic where possible.\n\n"
                f"{c}"
            ))
            r = llm.invoke([system_extract, human])
            file_bullets.extend(safe_extract_bullets(r.content))
            time.sleep(0.08)

        file_bullets = dedupe_list(file_bullets)[:max_bullets_per_file]

        # --- distribuir bullets por disciplina (mesmo ficheiro pode cobrir várias) ---
        # regra simples e genérica: associar todas as bullets às disciplinas detetadas no ficheiro
        for d in disciplines:
            discipline_to_bullets[d].extend(file_bullets)

    if not discipline_to_bullets:
        return "[SPECS_CONTEXT]\nDISCIPLINE: General\n- No reusable baseline rules extracted.\n[END_SPECS_CONTEXT]"

    # ---------- 2) dedupe + limitar por disciplina ----------
    for d in list(discipline_to_bullets.keys()):
        discipline_to_bullets[d] = dedupe_list(discipline_to_bullets[d])[:max_bullets_per_discipline]

    # ---------- 3) compressão final por disciplina ----------
    system_compress = SystemMessage(content=(
        "Compress bullets for ONE discipline.\n"
        "Output ONLY bullet lines starting with '- '.\n"
        "Keep meaning; shorten aggressively; remove duplicates; merge related ideas.\n"
        "No extra text.\n"
    ))

    blocks = []
    for d, bullets in discipline_to_bullets.items():
        bullets_text = "\n".join([f"- {b}" for b in bullets])

        # Aumentar max_tokens para evitar que LLM corte a resposta
        if hasattr(llm, 'max_tokens'):
            llm.max_tokens = 8000
        elif hasattr(llm, 'max_completion_tokens'):
            llm.max_completion_tokens = 8000

        r = llm.invoke([system_compress, HumanMessage(content=(
            f"Discipline: {d}\n"
            "Compress these bullets while preserving critical baselines:\n\n"
            f"{bullets_text}"
        ))])

        comp = (r.content or "").strip()
        if "- " not in comp:
            comp = bullets_text

        blocks.append(f"DISCIPLINE: {d}\n{comp}")
        time.sleep(0.05)

    # ---------- 4) Montagem final com validação de integridade ----------
    final = "[SPECS_CONTEXT]\n" + "\n\n".join(blocks) + "\n[END_SPECS_CONTEXT]"
    final = trim_to_size(final, max_final_chars)

    if "[END_SPECS_CONTEXT]" not in final:
        final = final[: max(0, max_final_chars - len("\n[END_SPECS_CONTEXT]"))].rstrip() + "\n[END_SPECS_CONTEXT]"

    return final


# ============================================================
# 4) AGENTE 2: BOQ EXTRACTION (o teu pipeline atual)
# ============================================================
def extrair_sumario_parcial(texto_integral: str, guia_texto: str, llm, specs_context: str):
    chunks = chunk_by_lines(texto_integral, max_chars=15000)
    resumos_finais = []
    st.markdown("### 📡 Fase 1: Extraindo registos do BOQ...")
    progresso_bar = st.progress(0)

    # injetar contexto (curto). Se estiver vazio, não mete nada.
    contexto_txt = ""
    if specs_context and specs_context.strip():
        contexto_txt = f"\n\nAUTHORITATIVE PROJECT SPECS CONTEXT:\n{specs_context}\n"

    mensagem_sistema = SystemMessage(content=f"""You are a Technical Data Hunter. Output is strictly line-based.

Normalize:
- "PH1" -> "Phase 1" (same for PH2..)
- Zone = 3-letter code (FSA, DCH, EYD, etc.)

Extract EVERYTHING technical you see that matches the audit matrix OR the project specs context.
Do not omit details.

Output format: EXACTLY 7 fields separated by " || "
PHASE || ZONE || SUBZONE || GRADES || STANDARDS/EXEC || PROTECTION || SCOPE/EVIDENCE

Rules:
- Use PROJECT SPECS CONTEXT as baseline to prioritize what matters (standards, grades, execution, coatings, fireproofing).
- Do NOT invent. If missing in BOQ but present in context, you may mention as "BASELINE (from specs context)" only if it clearly applies to that discipline.
- Keep technical numbers (S355, C30/37, EXC2, R60, 1200 gauge, 15 MIL, 1.8mm, D60x1.2mm, EN 124:1994, 5th Edition, 300mm centres, 5m x 5m).
- Remove only BOQ quantities/prices.
- Unknown -> UNKNOWN. None -> NONE.
- If no records: NO_RECORDS.
Only output the lines.

SUBZONE RULE:
- Output a separate record for each distinct subzone.
{contexto_txt}
""")

    for i, chunk in enumerate(chunks):
        progresso_bar.progress((i + 1) / len(chunks))
        prompt = f"""Use the audit matrix as a checklist:

AUDIT MATRIX:
{guia_texto}

Extract records from this chunk. Use [Linha: X] / [Pág: Y] tags in SCOPE/EVIDENCE.

CHUNK:
{chunk}
"""
        res = llm.invoke([mensagem_sistema, HumanMessage(content=prompt)])
        resumos_finais.append(res.content)
        time.sleep(0.2)

    return "\n\n".join(resumos_finais)


def gerar_consolidacao_hierarquica(resumos_acumulados, llm):
    st.markdown("### 🔍 Fase 2: Consolidação hierárquica...")
    mensagem_sistema = SystemMessage(content="""
You are a Senior Structural Estimator. You ONLY reformat and consolidate. Do not add new content.

Input lines are:
PHASE || ZONE || SUBZONE || GRADES || STANDARDS/EXEC || PROTECTION || SCOPE/EVIDENCE

Rules:
- Include ALL phases found. Normalize PHn->Phase n.
- Do NOT delete technical details within a subzone.
- No advice/next steps/questions. Last line must be: END_OF_REPORT.
- Do NOT drop subzones.

Output template:
Project: CSA
--> Phase: Phase N
    --> Zone: ZZZ
        ---> Subzone: <name>
            ---> TECHNICAL PROFILE: <grades + standards/exec + protections>
            ---> SCOPE ALERTS: <scope/evidence summary>
            ---> INCONSISTENCIES: <conflicts or None>
END_OF_REPORT
""")
    human = HumanMessage(content="Review and polish this data into the final tree:\n\n" + resumos_acumulados)
    return llm.invoke([mensagem_sistema, human]).content


# ============================================================
# 5) UI PRINCIPAL
# ============================================================
st.title("🏗️ BlocoAI: Auditoria Técnica Hierárquica (com Contexto de Specs)")

st.subheader("A) Carregar Specs (CSPECs) para gerar contexto da obra")
spec_files = st.file_uploader(
    "Carrega PDFs/DOCX de specs (podes selecionar vários)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if "specs_context" not in st.session_state:
    st.session_state.specs_context = ""

if st.button("🧠 Gerar Contexto de Specs"):
    if not spec_files:
        st.warning("Carrega pelo menos um ficheiro de specs.")
    else:
        # escolhe LLM para specs (podes usar o mesmo)
        if modo_execucao == "API Key":
            if not api_key_final:
                st.error("API key em falta.")
                st.stop()
            llm_specs = ChatOpenAI(model="gpt-5-mini", api_key=api_key_final, temperature=0.1)
        else:
            llm_specs = ChatOllama(model=modelo_selecionado, base_url=f"http://{torre_ip}:11434", temperature=0.1)

        with st.spinner("A gerar contexto de specs..."):
            st.session_state.specs_context = gerar_contexto_specs(spec_files, llm_specs)

        st.success(f"✅ Contexto gerado com sucesso ({len(st.session_state.specs_context)} caracteres).")
        with st.expander("📌 Ver contexto de specs", expanded=False):
            st.text(st.session_state.specs_context)

st.markdown("---")

st.subheader("B) Carregar BOQ / Caderno de Encargos e extrair com contexto")
file_uploaded = st.file_uploader("BOQ / Caderno de Encargos", type=["xlsx", "xls", "pdf"])

guia_padrao = """1. ÂMBITO: Fabrico, Montagem, Engenharia de Ligações.
2. HIERARQUIA: Fases (PH1-3), Zonas (CSA, FSA, DCH).
3. MATERIAIS: Aço (S355/S275), EXC2-4, Perfis.
4. PROTEÇÕES: Pintura (Microns), Fogo (R60/120), Sa2.5.
5. RISCOS: Design Responsibility, Furos MEP, Prevalência de Specs.
6. SUSTENTABILIDADE: Conteúdo Reciclado, EPD, LEED/BREEAM.
7. INCONSISTÊNCIAS: Comparação de dados contraditórios entre linhas/áreas."""
guia_input = st.text_area("Checklist de Auditoria:", value=guia_padrao, height=220)

if "relatorio_final" not in st.session_state:
    st.session_state.relatorio_final = ""
    st.session_state.processado = False

if st.button("🚀 Gerar Relatório Hierárquico (BOQ + Specs Context)"):
    if not file_uploaded:
        st.warning("Carrega um BOQ primeiro.")
        st.stop()

    # LLM para BOQ
    if modo_execucao == "API Key":
        if not api_key_final:
            st.error("API key em falta.")
            st.stop()
        llm_boq = ChatOpenAI(model="gpt-5-mini", api_key=api_key_final, temperature=0.1, max_completion_tokens=8000)
    else:
        llm_boq = ChatOllama(model=modelo_selecionado, base_url=f"http://{torre_ip}:11434", temperature=0.1)

    with st.spinner("A ler BOQ e a extrair..."):
        texto_cru = read_document(file_uploaded)
        resumos = extrair_sumario_parcial(texto_cru, guia_input, llm_boq, st.session_state.specs_context)
        st.session_state.relatorio_final = gerar_consolidacao_hierarquica(resumos, llm_boq)
        st.session_state.processado = True

if st.session_state.processado:
    st.markdown("---")
    st.header("📋 Relatório de Auditoria Master")
    st.markdown(st.session_state.relatorio_final)
    st.download_button("📥 Descarregar Auditoria (TXT)", data=st.session_state.relatorio_final, file_name="Auditoria_Hierarquica_BlocoAI.txt")