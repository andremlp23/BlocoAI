import logging
import time
from typing import Any, TypedDict
import concurrent.futures

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

_log = logging.getLogger("blocoai.retry")
logging.basicConfig(level=logging.WARNING)

# A forma correta de importar a função do teu outro ficheiro Python:.
from core.document_reader import carregar_regras_json

# E logo abaixo, executas a função para guardar as regras na variável:
REGRAS_EXTRACAO = carregar_regras_json()

class AuditoriaState(TypedDict):
    texto_boq: str
    texto_specs: str
    guia_filtragem: str
    nome_boq: str
    nomes_specs: list
    resumo_boq: str
    resumo_specs: str
    auditoria_bruta: str
    relatorio_final: str
    modo: str
    tentativas: int
    erros: list
    n_ficheiros: int
    paginas_sem_texto: list
    _api_key: str
    _prog_slot: Any
    _status_slot: Any

REGRAS_EXTRACAO = carregar_regras_json()

def _chunkar(texto: str, tamanho: int = 75000, overlap_linhas: int = 8) -> list:
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


@retry(
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(_log, logging.WARNING),
    reraise=True,
)
def _invocar_llm(llm, mensagens: list) -> str:
    return llm.invoke(mensagens).content


def _extrair_chunks(texto: str, nome_ficheiro: str, llm, prog_placeholder, status_placeholder, contexto_specs: str = "") -> str:
    """Extracção exaustiva de specs em PARALELO, mantendo a ordem original."""
    chunks = _chunkar(texto) # Usa a tua função existente
    if not chunks:
        return ""

    contexto_str = f"\nPROJECT CONTEXT (Prioritize this):\n{contexto_specs}\n" if contexto_specs else ""

    sys_msg = SystemMessage(content=f"""You are an Expert Engineering Classifier.
    CRITICAL EXTRACTION RULES (OBEY THIS JSON STRICTLY):
    {REGRAS_EXTRACAO}
    {contexto_str}

    ZONE IDENTIFICATION RULE (CRITICAL):
    - A "Zone" is strictly a physical building location, grid reference, or area code (e.g., S03-A2000, S02-A7200, CSA, Roof, Level 1).
    - NEVER use materials, item descriptions, or trades (e.g., "Intumescent Paint", "Reinforcement", "Steel Decking", "Surface treatment") as a Zone.
    - If the text does not explicitly state a physical location, you MUST classify the Zone as "Sitewide".

    FORMAT FOR EVERY ITEM FOUND:
    [FILE: {nome_ficheiro}] | Phase: <phase> | Zone: <zone> | Spec: <exact string>
    """)

    # 1. Pré-alocar a lista para garantir que a ordem dos chunks não se perde
    resumos = [None] * len(chunks)
    
    # 2. Função isolada para o ThreadPool
    def extrair_bloco(chunk_text):
        # O teu _invocar_llm já tem o Tenacity a lidar com os Rate Limits, é perfeito!
        return _invocar_llm(llm, [sys_msg, HumanMessage(
            content=f"Extract all major technical specs from this chunk based on the rules:\n\n{chunk_text}"
        )])

    # 3. Disparo Paralelo (Máximo 6 trabalhadores simultâneos para evitar sobrecarregar a API)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Associa cada execução ao seu índice original (i)
        future_to_idx = {executor.submit(extrair_bloco, chunk): i for i, chunk in enumerate(chunks)}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_idx)):
            idx = future_to_idx[future] # Recupera o índice correto deste bloco
            try:
                resumos[idx] = future.result()
            except Exception as e:
                resumos[idx] = f"[Bloco {idx+1} falhou: {type(e).__name__}]"
            
            # Atualização visual da UI
            if status_placeholder:
                pct = int(((i + 1) / len(chunks)) * 100)
                status_placeholder.markdown(
                    f'<div style="font-family:\'Space Mono\',monospace;font-size:0.72rem;color:#3a6aaa">'
                    f'<span style="color:#5a9aff">{nome_ficheiro}</span>'
                    f' &nbsp;·&nbsp; Processados {i+1}/{len(chunks)} blocos &nbsp;·&nbsp; {pct}%</div>',
                    unsafe_allow_html=True
                )
            if prog_placeholder:
                prog_placeholder.progress((i + 1) / len(chunks))

    # Junta os blocos (já garantidamente na ordem correta)
    return "\n\n".join([r for r in resumos if r])


def no_router(state: AuditoriaState) -> dict:
    modo = "CROSS" if (state["texto_boq"] and state["texto_specs"]) else "SINGLE"
    return {"modo": modo}


def no_extrator(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", api_key=state["_api_key"], temperature=0.0)

    prog = state["_prog_slot"]
    status = state["_status_slot"]

    resumo_boq = ""
    resumo_specs = ""

    # 1. PROCESSAR AS SPECS PRIMEIRO (Para criar a base de conhecimento)
    if state["texto_specs"]:
        resumo_specs = _extrair_chunks(
            texto=state["texto_specs"],
            nome_ficheiro=f"SPECS: {', '.join(state['nomes_specs'])}",
            llm=llm,
            prog_placeholder=prog,
            status_placeholder=status,
            contexto_specs="" # As Specs não têm contexto anterior
        )

    # 2. PROCESSAR O BOQ SEGUNDO (Injetando a base de conhecimento das Specs!)
    if state["texto_boq"]:
        resumo_boq = _extrair_chunks(
            texto=state["texto_boq"],
            nome_ficheiro=f"BOQ: {state['nome_boq']}",
            llm=llm,
            prog_placeholder=prog,
            status_placeholder=status,
            contexto_specs=resumo_specs  # INJEÇÃO DE INTELIGÊNCIA AQUI!
        )

    erros = list(state.get("erros", []))
    if not resumo_boq and not resumo_specs:
        erros.append("AGT-01: Nenhum conteúdo foi extraído dos documentos.")

    return {"resumo_boq": resumo_boq, "resumo_specs": resumo_specs, "erros": erros}


def no_auditor(state: AuditoriaState) -> dict:
    llm = ChatOpenAI(model="gpt-5-mini", api_key=state["_api_key"], temperature=0.1)

    tentativas = state.get("tentativas", 0) + 1

    if state["modo"] == "CROSS":
        dados = f"=== BOQ EXTRACTS ===\n{state['resumo_boq']}\n\n=== PDF SPECS EXTRACTS ===\n{state['resumo_specs']}"
        missao = "CROSS-DOCUMENT AUDIT"
        formato_secao = """
        * [Material/Trade 1] (e.g., Structural Steel):
            - BOQ: [Extracted BOQ details]
            - Specs: [Extracted PDF details]
            - Assessment: [Match / Conflict / Missing detail]
        * [Material/Trade 2] (e.g., Fire Protection):
            - ...
        """
    else:
        dados = state["resumo_boq"] or state["resumo_specs"]
        missao = "SINGLE-DOCUMENT HIERARCHY"
        formato_secao = """
        * [Material/Trade 1]:
            - Specs: [Extracted details]
            - Inconsistencies: [Any local issues found]
        """

    sys_msg = SystemMessage(
        content=f"""You are a Lead Estimator performing a {missao}.
CLEAN, DEDUPLICATE, and ORGANIZE the raw data into a highly readable summary.

CRITICAL RULES:
1. DEDUPLICATION: If a spec appears multiple times in the same Zone, merge it into ONE clear bullet point.
2. GROUP BY MATERIAL: Do not write paragraphs. You MUST group findings by Material/Trade (e.g., Structural Steel, Fire Protection, Concrete, Decking).
3. STRICT ZONING: Group items strictly by their physical Phase and Zone. 
4. GLOBAL AUDIT: Include a "GLOBAL INCONSISTENCIES" section at the end.

OUTPUT TEMPLATE:
Phase: [Phase Name]
--> Zone: [Zone Name]
{formato_secao}

GLOBAL INCONSISTENCIES (CROSS-PHASE / CROSS-DOC)
[List major technical and financial risks]
"""
    )

    try:
        auditoria = _invocar_llm(llm, [sys_msg, HumanMessage(content=f"Build the structured audit:\n\n{dados}")])
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-02 tentativa {tentativas} ({type(e).__name__}): {e}")
        return {"auditoria_bruta": "", "tentativas": tentativas, "erros": erros}

    return {"auditoria_bruta": auditoria, "tentativas": tentativas}


def no_apresentador(state: AuditoriaState) -> dict:
    # Mantemos o gpt-4o (standard) para não perder nenhum detalhe e seguir a formatação visual à risca!
    llm = ChatOpenAI(model="gpt-4o", api_key=state["_api_key"], temperature=0.1)

    sys_msg = SystemMessage(
        content="""You are an Executive Technical Writer for a Construction Firm.
Format the raw audit into a beautiful, user-friendly Executive Summary.

CRITICAL FORMATTING RULES:
1. PRESERVE STRUCTURE: Keep the nested bullet points exactly as the Auditor provided them. Do NOT convert bullet points into dense paragraphs.
2. ZERO DATA LOSS: You are strictly forbidden from summarizing, cutting, or omitting any technical details, grades, or assessments. Transcribe all data precisely.
3. THE TABLE: Convert the "Global Inconsistencies" section into a strict Markdown Table.
   Columns MUST be: | ID | Category | Location / Zone | Discrepancy Found | Risk / Impact |
4. NO ADDED DATA: Do not invent new data. Only format what the Auditor provided.
"""
    )

    try:
        relatorio = _invocar_llm(
            llm,
            [
                sys_msg,
                HumanMessage(content=f"Format this raw audit into a clean Executive Report preserving all bullet points:\n\n{state['auditoria_bruta']}"),
            ],
        )
        return {"relatorio_final": relatorio}
    except Exception as e:
        erros = list(state.get("erros", []))
        erros.append(f"AGT-03 ({type(e).__name__}): {e}")
        return {"relatorio_final": "", "erros": erros}


def no_erro(state: AuditoriaState) -> dict:
    return {}


def decidir_apos_extracao(state: AuditoriaState) -> str:
    tem_dados = bool(state.get("resumo_boq") or state.get("resumo_specs"))
    return "auditar" if tem_dados else "erro"


def decidir_apos_auditoria(state: AuditoriaState) -> str:
    auditoria = state.get("auditoria_bruta", "")
    tentativas = state.get("tentativas", 0)
    if len(auditoria.strip()) >= 100:
        return "formatar"
    if tentativas < 2:
        return "retry"
    return "erro"


def construir_grafo() -> Any:
    workflow = StateGraph(AuditoriaState)

    workflow.add_node("router", no_router)
    workflow.add_node("extrair", no_extrator)
    workflow.add_node("auditar", no_auditor)
    workflow.add_node("formatar", no_apresentador)
    workflow.add_node("erro", no_erro)

    workflow.set_entry_point("router")

    workflow.add_edge("router", "extrair")
    workflow.add_edge("formatar", END)
    workflow.add_edge("erro", END)

    workflow.add_conditional_edges("extrair", decidir_apos_extracao, {"auditar": "auditar", "erro": "erro"})
    workflow.add_conditional_edges(
        "auditar",
        decidir_apos_auditoria,
        {"formatar": "formatar", "retry": "auditar", "erro": "erro"},
    )

    return workflow.compile()
