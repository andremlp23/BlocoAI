import logging
from typing import Any, TypedDict
import json  # <- ADICIONADO PARA O CONTEXTO

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# Importação do Leitor de JSON (regras)
from core.document_reader import carregar_regras_json

_log = logging.getLogger("blocoai.retry")
logging.basicConfig(level=logging.WARNING)


def _criar_llm(state: dict, model_name: str, temperature: float = 0.1, num_ctx: int | None = None):
    """Cria um wrapper LLM adequado consoante o modo (local/API).

    - Se `_model_type` == 'local', tenta usar `ChatOllama` com `base_url`.
    - Caso contrário, usa `ChatOpenAI` com a `_api_key`.
    """
    # Proteção contra model_name inválido vindo do estado ou de JSON editado
    if not isinstance(model_name, str) or not model_name.strip():
        model_name = state.get("_model_name")
    if not isinstance(model_name, str) or not model_name.strip():
        model_name = "gpt-5.1"

    model_type = state.get("_model_type", "api")
    if model_type == "local":
        try:
            from langchain_ollama import ChatOllama

            base_url = state.get("_local_url", "http://localhost:11434")
            kwargs = {"model": model_name, "base_url": base_url, "temperature": temperature}
            if num_ctx is not None:
                kwargs["num_ctx"] = num_ctx
            return ChatOllama(**kwargs)
        except Exception as e:
            print(f"[_criar_llm] Aviso: ChatOllama indisponível ({e}), fallback para ChatOpenAI")

    # Por defeito, usar ChatOpenAI
    return ChatOpenAI(model=model_name, api_key=state.get("_api_key", ""), temperature=temperature)

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
    auditoria_normalizada: str
    relatorio_final: str
    contexto_projeto: dict  # <- ADICIONADO PARA RECEBER O JSON

    modo: str
    tentativas: int
    erros: list

    n_ficheiros: int
    paginas_sem_texto: list

    _api_key: str
    _prog_slot: Any
    _status_slot: Any
    _model_name: str  # <- ADICIONADO PARA O MODELO DINÂMICO
    _stream_callback: Any  # <- ADICIONADO PARA CAPTURAR STREAM


# ─────────────────────────────────────────────────────────────
# Leitura de Documento Completo
# ─────────────────────────────────────────────────────────────
def _obter_documento_completo(texto: str) -> list:
    """Retorna o texto completo num único chunk (sem divisão)."""
    if not texto:
        return []
    return [texto]


# ─────────────────────────────────────────────────────────────
# Invocação LLM com STREAMING (Fim dos Timeouts)
# ─────────────────────────────────────────────────────────────
def _invocar_llm(llm, mensagens: list, stream_callback=None) -> str:
    print(f"[_invocar_llm] Invocando LLM com {len(mensagens)} mensagens... (MODO STREAMING)")
    try:
        conteudo_total = ""
        for chunk in llm.stream(mensagens):
            content = chunk.content
            conteudo_total += content
            print(content, end="", flush=True)
            # Chamar callback se fornecido
            if stream_callback and callable(stream_callback):
                try:
                    stream_callback(content)
                except Exception as e:
                    print(f"[_invocar_llm] Erro no callback: {e}")
        
        print(f"\n\n[_invocar_llm] Geração concluída! {len(conteudo_total)} caracteres.")
        return conteudo_total
    except Exception as e:
        print(f"\n[_invocar_llm] ERRO: {type(e).__name__}: {e}")
        raise


# ======================================================================
# AGT-01: SPECS baseline (sem betão)
# ======================================================================
def extrair_specs(texto_specs: str, nome_ficheiro: str, llm, prog_placeholder, status_placeholder, stream_callback=None) -> str:
    chunks = _obter_documento_completo(texto_specs)
    if not chunks:
        return ""

    sys_msg = SystemMessage(content=f"""You are a Senior Construction Specifications Analyst and Technical Data Structuralist.

Goal: Extract PROJECT-WIDE ENGINEERING BASELINES from technical specification documents and structure into JSON format.

ABSOLUTE RULES:
- Do NOT omit information that is present in the text.
- Do NOT invent information outside what is written.
- Ignore EVERYTHING related to CONCRETE (grades, mixes, reinforcement, slabs, blinding, membranes, waterproofing for concrete, etc.). Concrete is OUT OF SCOPE - NEVER INCLUDE IT.
- NEVER include ANY concrete-related information in the output, no exceptions.
- QUANTITIES ARE NOT IMPORTANT: Do not include volume, weight, linear meters, quantities, or unit prices. Focus ONLY on technical specifications, standards, and execution rules.
- Discard any commercial/purchasing information (quantities, supplier names, delivery dates, costs).

Use these extraction rules exactly as provided (do not rewrite them):
{REGRAS_EXTRACAO}

REQUIRED JSON OUTPUT SCHEMA (MUST FOLLOW EXACTLY):
{{
  "spec_document": {{
    "section_code": "String (ex: '05 12 00' or 'NOT FOUND')",
    "title": "String (ex: 'Structural Steel Framing')"
  }},
  "reference_standards": [
    {{
      "code": "String (ex: 'NBN EN 1090')",
      "description": "String (Brief description of the standard)"
    }}
  ],
  "materials": [
    {{
      "category": "String (ex: 'Structural Steel', 'High-Strength Bolts')",
      "grade_or_type": "String (ex: 'S355JR', 'Grade 8.8')",
      "specific_rules": ["String (Rule 1)", "String (Rule 2)"]
    }}
  ],
  "finishes_and_protection": [
    {{
      "system_type": "String (ex: 'Galvanizing', 'Intumescent Paint')",
      "environment_class": "String (ex: 'C4', 'C2', 'NOT SPECIFIED')",
      "products_or_standards": "String (ex: 'EN ISO 1461', 'FIRETEX FX2003')",
      "preparation_rules": "String (ex: 'Sa 2.5 blast cleaning')"
    }}
  ],
  "execution_and_tolerances": [
    {{
      "element": "String (ex: 'Steel Erection', 'Deck Installation')",
      "execution_class": "String (ex: 'EXC2', 'NOT SPECIFIED')",
      "tolerances_and_rules": ["String (Execution rule 1)", "String (Tolerance rule 2)"]
    }}
  ],
  "qa_qc_and_submittals": [
    {{
      "requirement_type": "String (ex: 'Testing', 'Shop Drawings')",
      "description": "String (Detailed quality/submittal requirement)"
    }}
  ]
}}

EXTRACTION INSTRUCTIONS:
1. SPEC_DOCUMENT: Locate section code and title from document header or intro.
2. REFERENCE_STANDARDS: Extract ALL referenced EN/CEN/ISO/NBN standards with their purposes.
3. MATERIALS: Group by material category; extract grades, types, and all applicable rules (no omissions).
4. FINISHES_AND_PROTECTION: Extract galvanizing, paint systems, corrosion classifications (C2/C4), DFT specs, intumescent details, surface prep standards (Sa 2.5, etc.).
5. EXECUTION_AND_TOLERANCES: Execution classes (EXC2 etc), tolerances, erection rules, temporary bracing, alignment rules.
6. QA_QC_AND_SUBMITTALS: Shop drawings, testing requirements, mill certificates, welder certificates, pre-construction meetings, Quality Plan requirements, DFT control, field inspection.

OUTPUT FORMAT (STRICT):
- ONLY valid JSON (no markdown, no code blocks, no extra text before/after JSON).
- All string fields must be populated (use "NOT FOUND" only if genuinely absent from document).
- Arrays can be empty [] if no data found for that section.
- No recommendations, next steps, questions, or offers in any field.
- Ensure JSON is properly formatted and valid.
""")

    try:
        if status_placeholder:
            status_placeholder.markdown(
                f"<div style=\"font-family:'Space Mono',monospace;font-size:0.72rem;color:#3a6aaa\">"
                f"<span style=\"color:#5a9aff\">AGT-01 (Specs Structurer)</span>"
                f" &nbsp;·&nbsp; Processando documento e estruturando em JSON...</div>",
                unsafe_allow_html=True
            )
        if prog_placeholder:
            prog_placeholder.progress(0.5)

        resumo = _invocar_llm(llm, [
            sys_msg,
            HumanMessage(content=(
                'Extract and structure all technical specifications from this document.\n'
                'Process the ENTIRE document from start to end.\n'
                'Output ONLY valid JSON following the schema provided.\n'
                'Do NOT omit any technical requirements found in the document.\n'
                'Do NOT invent requirements outside the document.\n'
                'STRICT: Do NOT include ANY CONCRETE-related content whatsoever.\n'
                'STRICT: Ignore ALL quantities, volumes, weights, and commercial data.\n\n'
                f'FILE: {nome_ficheiro}\n'
                f'DOCUMENT:\n{chunks[0]}'
            ))
        ], stream_callback=stream_callback)

        if prog_placeholder:
            prog_placeholder.progress(1.0)
        
        return resumo
    except Exception as e:
        return f"[AGT-01 falhou: {type(e).__name__}: {e}]"


# ======================================================================
# AGT-02: Extração estruturada de BOQ em JSON (para CSV)
# ======================================================================
def extrair_boq_json_estruturado(texto_boq: str, nome_ficheiro: str, contexto_specs: str, contexto_projeto: dict, llm, prog_placeholder, status_placeholder, stream_callback=None) -> str:
    chunks = _obter_documento_completo(texto_boq)
    if not chunks:
        return ""

    ctx = contexto_projeto or {}
    
    if ctx:
        sys_content = f"""You are an Expert BOQ Analyst and Data Structuralist.

Goal: Extract COMPLETE Project Structure from BOQ document into JSON format.

PROJECT SCOPE BASELINE (Context & Guide):
{json.dumps(ctx, indent=2)}

CRITICAL INSTRUCTION: The Baseline above outlines the known phases, zones, and expected disciplines for this project. Use it as a mental map to resolve acronyms, understand the project scale, and ensure you do not miss these key elements. 
However, this is NOT a strict filter! If you find other relevant structural phases, zones, or technical details in the text that are NOT in the Baseline, YOU MUST STILL EXTRACT THEM. Your primary duty is to the source text.

ABSOLUTE RULES:
- Do NOT omit STRUCTURAL INFORMATION from the BOQ.
- Do NOT invent information outside what is written.
- Ignore EVERYTHING related to CONCRETE. Concrete is OUT OF SCOPE.
- QUANTITIES ARE NOT IMPORTANT: Exclude volumes, weights, unit prices.

Use these extraction rules:
{REGRAS_EXTRACAO}

SPECS CONTEXT (for Phase/Zone reference only):
{contexto_specs}

EXTRACTION STRATEGY (7-STEP):
1) FULL EXTRACTION (Mandatory Structure)
   Extract Phases and Zones from document. Output ONLY valid JSON with this schema:
   {{
     "phases": [
       {{
         "name": "Phase 1",
         "description": "...",
         "zones": ["ZoneA", "ZoneB"],
         "activities": ["Steel erection", "..."],
         "dependencies": ["Phase 0 complete"],
         "constraints": ["Access via north door"],
         "source": "Section 2.1, Line X-Y"
       }}
     ],
     "zones": [
       {{
         "name": "ZoneA",
         "description": "...",
         "phases": ["Phase 1", "Phase 2"],
         "activities": ["Structural prep", "..."],
         "logistics": "Crane access from main gate",
         "source": "Section 3.2"
       }}
     ]
   }}
2) AGGRESSIVE KEYWORD SWEEP
   Scan for: "phase", "stage", "zone", "area", "sector", "work package"
3) PHASE → ZONE MAPPING (no gaps)
4) SEQUENCING AND DEPENDENCIES
5) CONTEXT ENFORCEMENT
6) CONSISTENCY CHECK
7) FINAL COMPRESSED OUTPUT
   Include metadata in JSON response.
"""
    else:
        sys_content = f"""You are an Expert BOQ Analyst and Data Structuralist.

Goal: Extract COMPLETE Project Structure from BOQ document into JSON format with full Phase→Zone mapping.

ABSOLUTE RULES:
- Do NOT omit STRUCTURAL INFORMATION from the BOQ.
- Do NOT invent information outside what is written.
- Ignore EVERYTHING related to CONCRETE (grades, slabs, reinforcement, waterproofing, membranes for concrete). Concrete is OUT OF SCOPE - NEVER INCLUDE IT.
- NEVER include ANY concrete information whatsoever.
- QUANTITIES ARE NOT IMPORTANT: Exclude volumes, weights, unit prices, delivery dates. Extract ONLY technical/structural content.
- Discard all commercial line items (purchasing info, supplier data, costs, quantities).

Use these extraction rules:
{REGRAS_EXTRACAO}

SPECS CONTEXT (for Phase/Zone reference only):
{contexto_specs}

EXTRACTION STRATEGY (7-STEP):

1) FULL EXTRACTION (Mandatory Structure)
   Extract ALL Phases and Zones from document. Output ONLY valid JSON with this schema:
   {{
     "phases": [
       {{
         "name": "Phase 1",
         "description": "...",
         "zones": ["ZoneA", "ZoneB"],
         "activities": ["Steel erection", "..."],
         "dependencies": ["Phase 0 complete"],
         "constraints": ["Access via north door"],
         "source": "Section 2.1, Line X-Y"
       }}
     ],
     "zones": [
       {{
         "name": "ZoneA",
         "description": "...",
         "phases": ["Phase 1", "Phase 2"],
         "activities": ["Structural prep", "..."],
         "logistics": "Crane access from main gate",
         "source": "Section 3.2"
       }}
     ]
   }}

2) AGGRESSIVE KEYWORD SWEEP
   Scan for: "phase", "stage", "zone", "area", "sector", "work package"
   Extract FULL surrounding context.

3) PHASE → ZONE MAPPING (no gaps)
   Build complete mapping Phase→Zones. If phase has no zone, mark UNDEFINED.
   If zone has no phase, flag it.

4) SEQUENCING AND DEPENDENCIES
   Reconstruct execution order: ordered phases, parallel phases, dependencies.

5) CONTEXT ENFORCEMENT (For EACH Phase and Zone)
   Extract:
   * Work being executed
   * Teams/roles (if present)
   * Constraints (access, safety, sequencing)
   * Risks
   Use "NOT FOUND" if missing.

6) CONSISTENCY CHECK
   Validate: duplicate names, conflicting descriptions, missing links.
   Flag issues with references.

7) FINAL COMPRESSED OUTPUT
   Include in JSON response:
   {{
     ...phases/zones above...,
     "metadata": {{
       "total_phases": N,
       "total_zones": N,
       "key_execution_logic": ["...", "...", "..."],
       "critical_gaps": ["...", "..."]
     }}
   }}

OUTPUT:
- ONLY valid JSON (no markdown, no comments, no extra text).
- All text fields must be populated (no empty strings).
- Include page/section references in "source" fields.
- Deterministic, fully traceable to source.
"""

    sys_msg = SystemMessage(content=sys_content)
    
    try:
        if status_placeholder:
            status_placeholder.markdown(
                f"<div style=\"font-family:'Space Mono',monospace;font-size:0.72rem;color:#3a6aaa\">"
                f"<span style=\"color:#5a9aff\">AGT-02 (BOQ Structurer)</span>"
                f" &nbsp;·&nbsp; Processando estrutura de fases e zonas...</div>",
                unsafe_allow_html=True
            )
        if prog_placeholder:
            prog_placeholder.progress(0.5)

        resumo = _invocar_llm(llm, [
            sys_msg,
            HumanMessage(content=(
                "Extract complete project structure from this BOQ document.\n"
                "Process TOP-TO-BOTTOM and output ONLY valid JSON.\n"
                "Follow all 7 extraction steps above.\n"
                "CRITICAL: Do NOT include ANY concrete-related items whatsoever.\n"
                "CRITICAL: Do NOT include quantities, volumes, weights, or commercial data.\n"
                "Include metadata with summary.\n\n"
                f"FILE: {nome_ficheiro}\n"
                f"DOCUMENT:\n{chunks[0]}"
            ))
        ], stream_callback=stream_callback)

        if prog_placeholder:
            prog_placeholder.progress(1.0)
        
        return resumo
    except Exception as e:
        return f"[AGT-02 (JSON) falhou: {type(e).__name__}: {e}]"


# ======================================================================
# AGT-02: Extração narrativa de BOQ (para PDF/DOCX)
# ======================================================================
def extrair_boq_com_contexto(texto_boq: str, nome_ficheiro: str, contexto_specs: str, contexto_projeto: dict, llm, prog_placeholder, status_placeholder, stream_callback=None) -> str:
    eh_csv = ".csv" in nome_ficheiro.lower()
    
    if eh_csv:
        return extrair_boq_json_estruturado(texto_boq, nome_ficheiro, contexto_specs, contexto_projeto, llm, prog_placeholder, status_placeholder, stream_callback)
    
    chunks = _obter_documento_completo(texto_boq)
    if not chunks:
        return ""

    ctx = contexto_projeto or {}
    
    if ctx:
        sys_content = f"""You are an Expert Estimator and Technical Data Hunter.

PROJECT SCOPE BASELINE (Context & Guide):
{json.dumps(ctx, indent=2)}

Goal: Extract technical specifications and execution requirements from BOQ text.

CRITICAL INSTRUCTION: Use the Baseline above to understand the project's expected phases, zones, and key trades. Use this knowledge to focus your attention and structure your narrative accurately. However, DO NOT use it as a strict filter. If you find important technical structural data for zones, phases or trades not listed in the Baseline, you MUST extract them anyway. Be thorough.

ABSOLUTE RULES:
- Do NOT omit TECHNICAL INFORMATION that is present in the BOQ.
- Ignore EVERYTHING related to CONCRETE.
- QUANTITIES ARE NOT IMPORTANT: Exclude all quantities, volumes, weights.

Use these extraction rules exactly as provided:
{REGRAS_EXTRACAO}

SPECS CONTEXT (for awareness / later comparison):
{contexto_specs}

PHASE RULE: Normalize PH1→Phase 1.
ZONE/SUBZONE RULES:
- Valid ZONE is a 3-letter building code.
- Maintain CURRENT_ZONE and CURRENT_SUBZONE while reading.

WHAT TO EXTRACT:
- Only primary technical drivers for: steel/metal/decking/corrosion/fire protection.

OUTPUT FORMAT (STRICT):
- Plain text only (no JSON, no markdown).
- Structured NARRATIVE.
- Group by Phase → Zone → Subzone → Category.
"""
    else:
        sys_content = f"""You are an Expert Estimator and Technical Data Hunter.

Goal: Extract technical specifications and execution requirements from BOQ text.
You may USE the SPECS context ONLY to:
- recognize what is technical/important,
- and enable later cross-document comparison.
You MUST NOT treat it as truth that overrides BOQ text.

ABSOLUTE RULES:
- Do NOT omit TECHNICAL INFORMATION that is present in the BOQ.
- Do NOT invent information outside what is written.
- Ignore EVERYTHING related to CONCRETE (grades, mixes, reinforcement, slabs, blinding, membranes for concrete works, waterproofing for concrete, etc.). Concrete is OUT OF SCOPE - NEVER INCLUDE IT.
- NEVER include ANY concrete-related information in the output, no exceptions.
- QUANTITIES ARE NOT IMPORTANT: Exclude all quantities, volumes, weights, unit prices, commercial totals, and purchasing data.
- Extract ONLY technical specifications, standards, execution requirements, and structural details.

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
- Maintain CURRENT_ZONE and CURRENT_SUBZONE while reading the ENTIRE DOCUMENT TOP-TO-BOTTOM.

Update CURRENT_ZONE / CURRENT_SUBZONE only using these patterns:
1) Line is EXACTLY one 3-letter token (e.g., "DCH") → CURRENT_ZONE=<token>, CURRENT_SUBZONE=GENERAL
2) Line matches "<ZONE> - <anything>" → CURRENT_ZONE=<ZONE>, CURRENT_SUBZONE=<anything after dash>
3) Line matches "<ZONE>-<anything>" → CURRENT_ZONE=<ZONE>, CURRENT_SUBZONE=<anything after dash>
4) Internal headings like "MEMBRANES", "FLOOR SLABS", "STEEL DECKING" are NOT zones/subzones; they inherit CURRENT_ZONE and CURRENT_SUBZONE.

If you cannot establish CURRENT_ZONE from any header at the beginning, set Zone=UNKNOWN and Subzone=GENERAL.

WHAT TO EXTRACT:
- Only primary technical drivers for: steel/metal/decking/corrosion/fire protection.
- Capture grades, EXC class, standards, galvanizing/paint systems, intumescent rating/DFT, thicknesses like D60x1.2mm.
- Ignore commercial totals and minor sundries unless they carry a technical requirement.

OUTPUT FORMAT (STRICT):
- Plain text only (no JSON, no markdown).
- Structured NARRATIVE (NOT one-line templates).
- Group by Phase → Zone → Subzone, then by category (Structural Steel / Decking / Fire / Corrosion / Metal Fabrics).
- No recommendations, next steps, questions, or offers.
"""

    sys_msg = SystemMessage(content=sys_content)
    
    try:
        if status_placeholder:
            status_placeholder.markdown(
                f"<div style=\"font-family:'Space Mono',monospace;font-size:0.72rem;color:#3a6aaa\">"
                f"<span style=\"color:#5a9aff\">AGT-02 (BOQ Hunter)</span>"
                f" &nbsp;·&nbsp; Processando documento completo...</div>",
                unsafe_allow_html=True
            )
        if prog_placeholder:
            prog_placeholder.progress(0.5)

        resumo = _invocar_llm(llm, [
            sys_msg,
            HumanMessage(content=(
                "Extract and organize all TECHNICAL records from this ENTIRE BOQ document.\n"
                "Process from TOP-TO-BOTTOM maintaining Phase/Zone/Subzone context.\n"
                "Output structured narrative grouped by Phase→Zone→Subzone→Category.\n"
                "CRITICAL: Do NOT include concrete-related items, quantities, or commercial data.\n"
                "Focus ONLY on technical specifications, standards, and execution requirements.\n\n"
                f"FILE: {nome_ficheiro}\n"
                f"DOCUMENT:\n{chunks[0]}"
            ))
        ])

        if prog_placeholder:
            prog_placeholder.progress(1.0)
        
        return resumo
    except Exception as e:
        return f"[AGT-02 falhou: {type(e).__name__}: {e}]"


# ======================================================================
# NÓ: router + extrator
# ======================================================================
def no_router(state: AuditoriaState) -> dict:
    modo = "CROSS" if (state.get("texto_boq") and state.get("texto_specs")) else "SINGLE"
    return {"modo": modo}


def no_extrator(state: AuditoriaState) -> dict:
    model_name = state.get("_model_name", "gpt-5.1")
    llm_specs = _criar_llm(state, model_name, temperature=0.0)
    llm_boq = _criar_llm(state, model_name, temperature=0.0)

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
            status_placeholder=status,
            stream_callback=state.get("_stream_callback")
        )

    if state.get("texto_boq"):
        resumo_boq = extrair_boq_com_contexto(
            texto_boq=state["texto_boq"],
            nome_ficheiro=f"BOQ: {state.get('nome_boq','')}",
            contexto_specs=resumo_specs,
            contexto_projeto=state.get("contexto_projeto", {}), # <- JSON passado aqui
            llm=llm_boq,
            prog_placeholder=prog,
            status_placeholder=status,
            stream_callback=state.get("_stream_callback")
        )

    erros = list(state.get("erros", []))
    if not resumo_boq and not resumo_specs:
        erros.append("AGT-01/02: Nenhum conteúdo extraído dos documentos.")

    return {"resumo_boq": resumo_boq, "resumo_specs": resumo_specs, "erros": erros}


# ======================================================================
# AGT-02B: Auditor (cruza BOQ vs SPECS) -> auditoria_bruta
# ======================================================================
def no_auditor(state: AuditoriaState) -> dict:
    model_name = state.get("_model_name", "gpt-5.1")
    llm = _criar_llm(state, model_name, temperature=0.1)
    tentativas = state.get("tentativas", 0) + 1

    dados = (
        f"=== BOQ EXTRACTS ===\n{state.get('resumo_boq','')}\n\n"
        f"=== SPECS BASELINE BULLETS ===\n{state.get('resumo_specs','')}"
    )

    ctx = state.get("contexto_projeto") or {}
    
    if ctx:
        sys_content = f"""You are a Lead Estimator performing a CROSS-DOCUMENT AUDIT.
        
PROJECT CONTEXT BASELINE (For Guidance):
{json.dumps(ctx, indent=2)}

INPUT:
- BOQ extracts (Phase/Zone/Subzone/Spec)
- SPECS baseline bullets

CRITICAL INSTRUCTION: The Baseline above tells you what the project management expects to see. Use it to verify if expected trades are missing or to understand zone naming conventions. 
However, DO NOT ignore data in the inputs just because it isn't in the Baseline. You must audit all provided input data.

ABSOLUTE RULES:
- Do NOT omit TECHNICAL INFORMATION present in the inputs.
- Do NOT invent information outside the inputs.
- Ignore EVERYTHING related to CONCRETE.

TASK:
- Compare BOQ vs SPECS baseline and flag: ALIGNED / CONFLICT / MISSING BASELINE.
- Keep Phase/Zone/Subzone strictly.

OUTPUT FORMAT (STRICT):
Phase: Phase N
--> Zone: ZZZ
    ---> Subzone: <name>
        * Structural Steel: ...
        * Composite Decking: ...
        * Fire Protection: ...
        * Corrosion Protection: ...
        * Metal Fabrications: ...

GLOBAL INCONSISTENCIES:
- <bullets>
END_OF_REPORT
"""
    else:
        sys_content = """You are a Lead Estimator performing a CROSS-DOCUMENT AUDIT.

INPUT:
- BOQ extracts (Phase/Zone/Subzone/Spec)
- SPECS baseline bullets

ABSOLUTE RULES:
- Do NOT omit TECHNICAL INFORMATION present in the inputs.
- Do NOT invent information outside the inputs.
- Ignore EVERYTHING related to CONCRETE (all concrete-related items are OUT OF SCOPE - NEVER INCLUDE THEM).
- QUANTITIES ARE NOT IMPORTANT: Exclude all quantities, volumes, weights, and commercial data from the audit.
- No recommendations, next steps, questions, or offers.
- Focus ONLY on technical specifications, standards, and execution rules.

EMPTY ZONE RULE (CRITICAL FOR ANTI-HALLUCINATION):
- If a Subzone has NO data related to Steel, Decking, Fire, Corrosion, or Metal Fabrications in the BOQ extract, DO NOT force the 5 categories.
- Instead, simply write under the Subzone: "[OUT OF SCOPE: No relevant structural/metal items]" and move to the next.
- If a specific category within a valid Subzone is completely empty (no BOQ items and no relevant Specs), DO NOT print that category.

TASK:
- Deduplicate within each Phase/Zone/Subzone.
- Compare BOQ vs SPECS baseline and flag: ALIGNED / CONFLICT / MISSING BASELINE.
- Keep Phase/Zone/Subzone strictly; never move specs across zones/phases.

OUTPUT FORMAT (STRICT):
Phase: Phase N
--> Zone: ZZZ
    ---> Subzone: <name>
        [OUT OF SCOPE: No relevant structural/metal items]  <-- USE THIS IF TOTALLY EMPTY
        
        (If NOT empty, use the categories below. Only print the ones that have data or are missing a baseline):
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
"""

    sys_msg = SystemMessage(content=sys_content)
    
    try:
        auditoria = _invocar_llm(llm, [sys_msg, HumanMessage(content=f"Build the structured audit:\n\n{dados}")], stream_callback=state.get("_stream_callback"))
        return {"auditoria_bruta": auditoria, "tentativas": tentativas}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-02B tentativa {tentativas} ({type(e).__name__}): {e}")
        return {"auditoria_bruta": "", "tentativas": tentativas, "erros": erros}


# ======================================================================
# AGT-03: Deduplicador cross-categoria (novo)
# ======================================================================
def no_deduplicador(state: AuditoriaState) -> dict:
    model_name = state.get("_model_name", "gpt-5.1")
    llm = _criar_llm(state, model_name, temperature=0.1)

    base = (state.get("auditoria_bruta") or "").strip()
    if not base:
        return {"auditoria_normalizada": ""}

    sys_msg = SystemMessage(content="""You are a Senior Construction Estimator and Report Normalizer.

INPUT:
- A structured audit with Phase/Zone/Subzone and categories.

ABSOLUTE RULES:
- Do NOT omit any TECHNICAL INFORMATION that exists in the input audit.
- Do NOT invent any information outside the input audit.
- REMOVE/IGNORE EVERYTHING related to CONCRETE (all concrete items are OUT OF SCOPE - NEVER INCLUDE THEM).
- QUANTITIES ARE NOT IMPORTANT: Remove/ignore all quantities, volumes, weights, and commercial information.
- No recommendations, next steps, questions, or offers.
- Keep ONLY technical specifications, standards, and execution requirements.

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
        ], stream_callback=state.get("_stream_callback"))
        return {"auditoria_normalizada": normalizado}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-03 (dedupe) ({type(e).__name__}): {e}")
        return {"auditoria_normalizada": base, "erros": erros}


# ======================================================================
# AGT-04: Apresentador (formata)
# ======================================================================
def no_apresentador(state: AuditoriaState) -> dict:
    # Usamos o gpt-4o para reestruturação complexa de dados (Data Pivot)
    llm = _criar_llm(state, "gpt-4o", temperature=0.1)

    base = (state.get("auditoria_normalizada") or state.get("auditoria_bruta") or "").strip()
    if not base:
        return {"relatorio_final": ""}

    sys_msg = SystemMessage(content="""You are a Lead Estimator and Technical Data Structuralist.
Your task is to PIVOT a location-based technical audit into a TRADE PACKAGE-based Estimating Summary.

ABSOLUTE RULES:
1. PIVOT THE DATA: Pivot input grouped by Phase -> Zone -> Subzone into TRADE PACKAGE groups.
2. PRESERVE TECHNICAL DETAIL: DO NOT summarize technical specs into generic bullets. You MUST extract and preserve all specific technical data, grades, standards, DFTs, bolt types, and execution rules from the input.
3. BASELINE SCOPE: For each Trade Package, provide a comprehensive list of technical requirements (the 'Source of Truth').
4. VARIATIONS TABLE: For each Trade Package, map the BOQ entries into the table. The "Scope Description" column MUST contain the specific BOQ technical data, not just generic names.
5. NO GENERIC TEXT: If the input specifies "TATA D60x1.2mm", do not write "Steel Decking". Write exactly what is in the input.

REQUIRED OUTPUT FORMAT (Markdown STRICT):

# Cross-Document Technical Audit:

## 1. TRADE PACKAGE: [NAME]
**Baseline Scope:**
- [List every technical requirement, standard, grade, and execution rule found in the audit for this trade - NO SUMMARIZATION]

**Scope Variations / Inclusions:**
| Phase | Zone | Scope Description | Deviation / Note |
|-------|------|-------------------|------------------|
| [Phase] | [Zone] | [Full technical BOQ description] | [Status or deviation from SPECS] |

(Repeat for all trades: Structural Steel, Composite Decking, Fire Protection, Corrosion Protection, Metal Fabrications)

## GLOBAL INCONSISTENCIES (ESTIMATING RISK REGISTER)
| ID | Trade Package | Issue | Risk | Estimating Action |
|----|---------------|-------|------|-------------------|
| [N] | [Trade] | [Issue from input] | [High/Medium/Low] | [Specific action] |

END_OF_REPORT
""")

    try:
        relatorio = _invocar_llm(llm, [
            sys_msg, 
            HumanMessage(content=f"Pivot and format this location-based audit into the requested Trade Package Estimating Summary:\n\n{base}")
        ], stream_callback=state.get("_stream_callback"))
        return {"relatorio_final": relatorio}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-04 (Estimating Pivot) ({type(e).__name__}): {e}")
        return {"relatorio_final": base, "erros": erros}


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
def construir_grafo_extracao() -> Any:
    """
    Grafo curto:
    - corre só AGT-01 Specs
    - corre só AGT-02 BOQ
    - para antes da auditoria
    """
    workflow = StateGraph(AuditoriaState)

    workflow.add_node("router", no_router)
    workflow.add_node("extrair", no_extrator)
    workflow.add_node("erro", no_erro)

    workflow.set_entry_point("router")

    workflow.add_edge("router", "extrair")

    workflow.add_conditional_edges(
        "extrair",
        decidir_apos_extracao,
        {
            "auditar": END,
            "erro": "erro",
        },
    )

    workflow.add_edge("erro", END)

    return workflow.compile()


def construir_grafo_auditoria() -> Any:
    """
    Grafo final:
    - recebe resumo_specs e resumo_boq já editados/manualizados
    - corre auditoria
    - corre dedupe
    - formata relatório final
    """
    workflow = StateGraph(AuditoriaState)

    workflow.add_node("auditar", no_auditor)
    workflow.add_node("dedupe", no_deduplicador)
    workflow.add_node("formatar", no_apresentador)
    workflow.add_node("erro", no_erro)

    workflow.set_entry_point("auditar")

    workflow.add_conditional_edges(
        "auditar",
        decidir_apos_auditoria,
        {
            "dedupe": "dedupe",
            "retry": "auditar",
            "erro": "erro",
        },
    )

    workflow.add_conditional_edges(
        "dedupe",
        decidir_apos_dedupe,
        {
            "formatar": "formatar",
        },
    )

    workflow.add_edge("formatar", END)
    workflow.add_edge("erro", END)

    return workflow.compile()