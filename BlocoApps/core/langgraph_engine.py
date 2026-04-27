import logging
import time
import concurrent.futures
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from openai import APIConnectionError, APITimeoutError, RateLimitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Importação do Leitor de JSON (regras)
from core.document_reader import carregar_regras_json

_log = logging.getLogger("blocoai.retry")
logging.basicConfig(level=logging.WARNING)

REGRAS_EXTRACAO = carregar_regras_json()  # idealmente string; se vier dict, converte no loader


class AuditoriaState(TypedDict):
    texto_boq: str
    texto_specs: str
    guia_filtragem: str
    nome_boq: str
    nomes_specs: list

    resumo_boq: str
    resumo_specs: str

    auditoria_bruta: str
    auditoria_normalizada: str  # <- NOVO (AGT-03)
    relatorio_final: str

    modo: str
    tentativas: int
    erros: list

    n_ficheiros: int
    paginas_sem_texto: list

    _api_key: str
    _prog_slot: Any
    _status_slot: Any


# ─────────────────────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────────────────────
def _chunkar(texto: str, tamanho: int = 35000, overlap_linhas: int = 5) -> list:
    if not texto:
        return []
    linhas = texto.splitlines(keepends=True)
    chunks = []
    chunk_atual: list[str] = []
    tamanho_atual = 0

    for linha in linhas:
        if tamanho_atual + len(linha) > tamanho and chunk_atual:
            chunks.append("".join(chunk_atual))
            chunk_atual = chunk_atual[-overlap_linhas:]
            tamanho_atual = sum(len(l) for l in chunk_atual)

        chunk_atual.append(linha)
        tamanho_atual += len(linha)

    if chunk_atual:
        chunks.append("".join(chunk_atual))
    return chunks


# ─────────────────────────────────────────────────────────────
# Invocação LLM com retry
# ─────────────────────────────────────────────────────────────
@retry(
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(_log, logging.WARNING),
    reraise=True,
)
def _invocar_llm(llm, mensagens: list) -> str:
    return llm.invoke(mensagens).content


# ======================================================================
# AGT-01: SPECS baseline (sem betão)
# ======================================================================
def extrair_specs(texto_specs: str, nome_ficheiro: str, llm, prog_placeholder, status_placeholder) -> str:
    chunks = _chunkar(texto_specs, tamanho=35000, overlap_linhas=5)
    if not chunks:
        return ""

    sys_msg = SystemMessage(content=f"""You are a Senior Construction Specifications Analyst.

Goal: Extract PROJECT-WIDE ENGINEERING BASELINES from technical specification documents.

ABSOLUTE RULES:
- Do NOT omit information that is present in the text.
- Do NOT invent information outside what is written.
- Ignore EVERYTHING related to CONCRETE (grades, mixes, reinforcement, slabs, blinding, etc.). Concrete is out of scope.
- NEVER include ANY concrete-related information in the output, no exceptions.

Use these extraction rules exactly as provided (do not rewrite them):
{REGRAS_EXTRACAO}

OUTPUT FORMAT (STRICT):
- Plain text only (no JSON, no markdown).
- Each line must start with "- " and be one reusable baseline rule.
- No recommendations, next steps, questions, or offers.
""")

    resumos = [None] * len(chunks)

    def processar_bloco_specs(chunk_text: str, index: int) -> str:
        time.sleep(index * 10.0)
        return _invocar_llm(llm, [
            sys_msg,
            HumanMessage(content=(
                'Extract reusable baseline rules from this chunk.\n'
                'Only output bullet lines starting with "- ".\n'
                'No extra text.\n\n'
                f'FILE: {nome_ficheiro}\n'
                f'CHUNK:\n{chunk_text}'
            ))
        ])

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_idx = {executor.submit(processar_bloco_specs, chunk, i): i for i, chunk in enumerate(chunks)}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_idx)):
            idx = future_to_idx[future]
            try:
                resumos[idx] = future.result()
            except Exception as e:
                resumos[idx] = f"[Bloco SPECS {idx+1} falhou: {type(e).__name__}: {e}]"

            if status_placeholder:
                pct = int(((i + 1) / len(chunks)) * 100)
                status_placeholder.markdown(
                    f"<div style=\"font-family:'Space Mono',monospace;font-size:0.72rem;color:#3a6aaa\">"
                    f"<span style=\"color:#5a9aff\">AGT-01 (Specs Reader)</span>"
                    f" &nbsp;·&nbsp; Processados {i+1}/{len(chunks)} blocos &nbsp;·&nbsp; {pct}%</div>",
                    unsafe_allow_html=True
                )
            if prog_placeholder:
                prog_placeholder.progress((i + 1) / len(chunks))

    return "\n".join([r for r in resumos if r])


# ======================================================================
# AGT-02: BOQ extractor (sem betão) + Phase/Zone/Subzone
# ======================================================================
def extrair_boq_com_contexto(texto_boq: str, nome_ficheiro: str, contexto_specs: str, llm, prog_placeholder, status_placeholder) -> str:
    chunks = _chunkar(texto_boq, tamanho=35000, overlap_linhas=5)
    if not chunks:
        return ""

    sys_msg = SystemMessage(content=f"""You are an Expert Estimator and Technical Data Hunter.

Goal: Extract technical cost drivers from BOQ text.
You may USE the SPECS context ONLY to:
- recognize what is technical/important,
- and enable later cross-document comparison.
You MUST NOT treat it as truth that overrides BOQ text.

ABSOLUTE RULES:
- Do NOT omit information that is present in the BOQ.
- Do NOT invent information outside what is written.
- Ignore EVERYTHING related to CONCRETE (grades, mixes, reinforcement, slabs, blinding, membranes for concrete works, etc.). Concrete is out of scope.
- NEVER include ANY concrete-related information in the output, no exceptions.

Use these extraction rules exactly as provided (do not rewrite them):
{REGRAS_EXTRACAO}

SPECS CONTEXT (for awareness / later comparison; do NOT overwrite BOQ facts):
{contexto_specs}

PHASE RULE:
- Phase comes from nearby headers or explicit tokens in the line (PH1/PH2/PH3/PH4 or "Phase 1/2/3/4").
- Normalize PH1→Phase 1 (same for PH2..).
- If you cannot find it, output Phase: UNKNOWN.

ZONE/SUBZONE CONTEXT RULES (MANDATORY, DO NOT GUESS):
- Valid ZONE is a 3-letter building code.
- Maintain CURRENT_ZONE and CURRENT_SUBZONE while reading the chunk TOP-TO-BOTTOM.

Update CURRENT_ZONE / CURRENT_SUBZONE only using these patterns:
1) Line is EXACTLY one 3-letter token (e.g., "DCH") → CURRENT_ZONE=<token>, CURRENT_SUBZONE=GENERAL
2) Line matches "<ZONE> - <anything>" → CURRENT_ZONE=<ZONE>, CURRENT_SUBZONE=<anything after dash>
3) Line matches "<ZONE>-<anything>" → CURRENT_ZONE=<ZONE>, CURRENT_SUBZONE=<anything after dash>
4) Internal headings like "MEMBRANES", "FLOOR SLABS", "STEEL DECKING" are NOT zones/subzones; they inherit CURRENT_ZONE and CURRENT_SUBZONE.

If you cannot establish CURRENT_ZONE from any header above in the chunk, set Zone=UNKNOWN and Subzone=GENERAL.

WHAT TO EXTRACT:
- Only primary technical drivers for: steel/metal/decking/corrosion/fire protection.
- Capture grades, EXC class, standards, galvanizing/paint systems, intumescent rating/DFT, thicknesses like D60x1.2mm.
- Ignore commercial totals and minor sundries unless they carry a technical requirement.

OUTPUT FORMAT (STRICT):
- Plain text only (no JSON, no markdown).
- One line per item, EXACTLY:
[FILE: {nome_ficheiro}] | Phase: <phase> | Zone: <zone> | Subzone: <subzone> | Spec: <exact wording + [Linha]/[Pág] tag if present>
- If nothing relevant in this chunk: output exactly "NO_RECORDS"
- No recommendations, next steps, questions, or offers.
""")

    resumos = [None] * len(chunks)

    def processar_bloco_boq(chunk_text: str, index: int) -> str:
        time.sleep(index * 10.0)
        return _invocar_llm(llm, [
            sys_msg,
            HumanMessage(content=(
                "Extract records from this BOQ chunk TOP-TO-BOTTOM.\n"
                "Preserve exact wording in Spec.\n"
                "Include [Linha: X] or [Pág: Y] tag in Spec if present.\n"
                "Output only strict template lines or NO_RECORDS.\n\n"
                f"CHUNK:\n{chunk_text}"
            ))
        ])

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_idx = {executor.submit(processar_bloco_boq, chunk, i): i for i, chunk in enumerate(chunks)}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_idx)):
            idx = future_to_idx[future]
            try:
                resumos[idx] = future.result()
            except Exception as e:
                resumos[idx] = f"[Bloco BOQ {idx+1} falhou: {type(e).__name__}: {e}]"

            if status_placeholder:
                pct = int(((i + 1) / len(chunks)) * 100)
                status_placeholder.markdown(
                    f"<div style=\"font-family:'Space Mono',monospace;font-size:0.72rem;color:#3a6aaa\">"
                    f"<span style=\"color:#5a9aff\">AGT-02 (BOQ Hunter)</span>"
                    f" &nbsp;·&nbsp; Processados {i+1}/{len(chunks)} blocos &nbsp;·&nbsp; {pct}%</div>",
                    unsafe_allow_html=True
                )
            if prog_placeholder:
                prog_placeholder.progress((i + 1) / len(chunks))

    return "\n\n".join([r for r in resumos if r])


# ======================================================================
# NÓ: router + extrator
# ======================================================================
def no_router(state: AuditoriaState) -> dict:
    modo = "CROSS" if (state.get("texto_boq") and state.get("texto_specs")) else "SINGLE"
    return {"modo": modo}


def no_extrator(state: AuditoriaState) -> dict:
    llm_specs = ChatOpenAI(model="gpt-5-mini", api_key=state["_api_key"], temperature=0.0)
    llm_boq = ChatOpenAI(model="gpt-5-mini", api_key=state["_api_key"], temperature=0.0)

    prog = state["_prog_slot"]
    status = state["_status_slot"]

    resumo_specs = ""
    resumo_boq = ""

    if state.get("texto_specs"):
        resumo_specs = extrair_specs(
            texto_specs=state["texto_specs"],
            nome_ficheiro=f"SPECS: {', '.join(state.get('nomes_specs', []))}",
            llm=llm_specs,
            prog_placeholder=prog,
            status_placeholder=status
        )

    if state.get("texto_boq"):
        resumo_boq = extrair_boq_com_contexto(
            texto_boq=state["texto_boq"],
            nome_ficheiro=f"BOQ: {state.get('nome_boq','')}",
            contexto_specs=resumo_specs,
            llm=llm_boq,
            prog_placeholder=prog,
            status_placeholder=status
        )

    erros = list(state.get("erros", []))
    if not resumo_boq and not resumo_specs:
        erros.append("AGT-01/02: Nenhum conteúdo extraído dos documentos.")

    return {"resumo_boq": resumo_boq, "resumo_specs": resumo_specs, "erros": erros}


# ======================================================================
# AGT-02B: Auditor (cruza BOQ vs SPECS) -> auditoria_bruta
# ======================================================================
def no_auditor(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(model="gpt-5-mini", api_key=state["_api_key"], temperature=0.1)
    tentativas = state.get("tentativas", 0) + 1

    dados = (
        f"=== BOQ EXTRACTS ===\n{state.get('resumo_boq','')}\n\n"
        f"=== SPECS BASELINE BULLETS ===\n{state.get('resumo_specs','')}"
    )

    sys_msg = SystemMessage(content="""You are a Lead Estimator performing a CROSS-DOCUMENT AUDIT.

INPUT:
- BOQ extracts (Phase/Zone/Subzone/Spec)
- SPECS baseline bullets

ABSOLUTE RULES:
- Do NOT omit information present in the inputs.
- Do NOT invent information outside the inputs.
- Ignore EVERYTHING related to CONCRETE. Concrete is out of scope.
- No recommendations, next steps, questions, or offers.

TASK:
- Deduplicate within each Phase/Zone/Subzone.
- Compare BOQ vs SPECS baseline and flag: ALIGNED / CONFLICT / MISSING BASELINE.
- Keep Phase/Zone/Subzone strictly; never move specs across zones/phases.

OUTPUT FORMAT (STRICT):
Phase: Phase N
--> Zone: ZZZ
    ---> Subzone: <name>
        * Structural Steel:
            - BOQ: ...
            - SPECS: ...
            - STATUS: ...
        * Composite Decking:
            - BOQ: ...
            - SPECS: ...
            - STATUS: ...
        * Fire Protection:
            - BOQ: ...
            - SPECS: ...
            - STATUS: ...
        * Corrosion Protection:
            - BOQ: ...
            - SPECS: ...
            - STATUS: ...
        * Metal Fabrications (Stairs/Railings/Gratings):
            - BOQ: ...
            - SPECS: ...
            - STATUS: ...

GLOBAL INCONSISTENCIES:
- <bullets only from findings above, no new info>
END_OF_REPORT
""")

    try:
        auditoria = _invocar_llm(llm, [sys_msg, HumanMessage(content=f"Build the structured audit:\n\n{dados}")])
        return {"auditoria_bruta": auditoria, "tentativas": tentativas}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-02B tentativa {tentativas} ({type(e).__name__}): {e}")
        return {"auditoria_bruta": "", "tentativas": tentativas, "erros": erros}


# ======================================================================
# AGT-03: Deduplicador cross-categoria (novo)
# ======================================================================
def no_deduplicador(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(model="gpt-5-mini", api_key=state["_api_key"], temperature=0.1)

    base = (state.get("auditoria_bruta") or "").strip()
    if not base:
        return {"auditoria_normalizada": ""}

    sys_msg = SystemMessage(content="""You are a Senior Construction Estimator and Report Normalizer.

INPUT:
- A structured audit with Phase/Zone/Subzone and categories.

ABSOLUTE RULES:
- Do NOT omit any information that exists in the input audit.
- Do NOT invent any information outside the input audit.
- Remove/ignore EVERYTHING related to CONCRETE. Concrete is out of scope.
- No recommendations, next steps, questions, or offers.

GOAL:
- Prevent the SAME technical spec from appearing in multiple categories within the same Subzone.
- Assign each spec to ONE canonical category only (ownership rules below).
- If a category loses items due to ownership, keep the category but replace duplicates with a single pointer line: "(See <Owner Category>)"
  - Do NOT repeat spec text in the pointer.

CANONICAL CATEGORIES (use exactly these names and this order):
1) Structural Steel
2) Composite Decking
3) Fire Protection
4) Corrosion Protection
5) Metal Fabrications (Stairs/Railings/Gratings)

OWNERSHIP RULES (first match wins):
- Composite Decking: deck profiles, deck gauge/thickness, puddle welds, side-lap rules, studs through deck, end laps/bearing, deck fasteners, closures, pour stops.
- Fire Protection: intumescent/fireproofing, fire rating (R30/R60/1hr/2hr), DFT rules, EN 13381/EN 13501, fireproofing QA.
- Corrosion Protection: galvanizing EN ISO 1461, paint systems EN ISO 12944, blast Sa2.5, surface prep EN ISO 8501/8502/8503, DFT measurement EN ISO 2808.
- Metal Fabrications (Stairs/Railings/Gratings): stairs, handrails, guardrails, ladders, gratings, bollards, gates, misc metalwork.
- Structural Steel: S355/S275 grades, EXC class, EN 1090, NSSSBC erection, connections/bolting EN 14399/15048, welding EN ISO 9606-1/EN 1011, anchors/H.D.A. if steel-related.

DEDUPLICATION METHOD:
- Consider two items duplicates if they express the same requirement even if phrased slightly differently.
- Keep the most complete wording in the owner category.

OUTPUT:
- Output ONLY the cleaned audit.
- Keep the same Phase → Zone → Subzone structure.
- End with: END_OF_REPORT
""")

    try:
        normalizado = _invocar_llm(llm, [
            sys_msg,
            HumanMessage(content="Normalize and deduplicate this audit:\n\n" + base)
        ])
        return {"auditoria_normalizada": normalizado}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-03 (dedupe) ({type(e).__name__}): {e}")
        return {"auditoria_normalizada": base, "erros": erros}


# ======================================================================
# AGT-04: Apresentador (formata)
# ======================================================================
def no_apresentador(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(model="gpt-5-mini", api_key=state["_api_key"], temperature=0.1)

    base = (state.get("auditoria_normalizada") or state.get("auditoria_bruta") or "").strip()
    if not base:
        return {"relatorio_final": ""}

    sys_msg = SystemMessage(content="""You are an Executive Technical Writer.

Task: format the audit into a clean, readable report.

ABSOLUTE RULES:
- Do NOT add any new info.
- Do NOT omit any info.
- Do NOT add recommendations, next steps, questions, or offers.
- Preserve Phase/Zone/Subzone structure.
- Ignore/remove any CONCRETE content if still present.

Formatting:
- Convert GLOBAL INCONSISTENCIES into a Markdown table:
| ID | Category | Location (Phase/Zone/Subzone) | Issue | Risk |
""")

    try:
        relatorio = _invocar_llm(llm, [sys_msg, HumanMessage(content=f"Format this audit:\n\n{base}")])
        return {"relatorio_final": relatorio}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-04 (format) ({type(e).__name__}): {e}")
        return {"relatorio_final": "", "erros": erros}


# ======================================================================
# Nó de erro
# ======================================================================
def no_erro(state: AuditoriaState) -> dict:
    return {}


# ======================================================================
# Condições / routing
# ======================================================================
def decidir_apos_extracao(state: AuditoriaState) -> str:
    tem_dados = bool((state.get("resumo_boq") or "").strip() or (state.get("resumo_specs") or "").strip())
    return "auditar" if tem_dados else "erro"


def decidir_apos_auditoria(state: AuditoriaState) -> str:
    auditoria = (state.get("auditoria_bruta") or "").strip()
    tentativas = state.get("tentativas", 0)
    if len(auditoria) >= 100:
        return "dedupe"
    if tentativas < 2:
        return "retry"
    return "erro"


def decidir_apos_dedupe(state: AuditoriaState) -> str:
    # mesmo que esteja curto, seguimos para formatar
    return "formatar"


# ======================================================================
# Construção do grafo
# ======================================================================
def construir_grafo() -> Any:
    workflow = StateGraph(AuditoriaState)

    workflow.add_node("router", no_router)
    workflow.add_node("extrair", no_extrator)
    workflow.add_node("auditar", no_auditor)        # AGT-02B
    workflow.add_node("dedupe", no_deduplicador)    # AGT-03
    workflow.add_node("formatar", no_apresentador)  # AGT-04
    workflow.add_node("erro", no_erro)

    workflow.set_entry_point("router")

    workflow.add_edge("router", "extrair")

    workflow.add_conditional_edges(
        "extrair",
        decidir_apos_extracao,
        {"auditar": "auditar", "erro": "erro"}
    )

    workflow.add_conditional_edges(
        "auditar",
        decidir_apos_auditoria,
        {"dedupe": "dedupe", "retry": "auditar", "erro": "erro"}
    )

    workflow.add_conditional_edges(
        "dedupe",
        decidir_apos_dedupe,
        {"formatar": "formatar"}
    )

    workflow.add_edge("formatar", END)
    workflow.add_edge("erro", END)

    return workflow.compile()