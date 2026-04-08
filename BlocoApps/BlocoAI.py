import streamlit as st
import pandas as pd
import time
import pdfplumber 
import os
import io 
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# --- 0. CARREGAR AMBIENTE ---
def carregar_env_local():
    base_dir = Path(__file__).resolve().parent
    candidatos = [base_dir / ".env", base_dir.parent / ".env"]
    for env_path in candidatos:
        if not env_path.exists(): continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            linha = line.strip()
            if not linha or linha.startswith("#") or "=" not in linha: continue
            chave, valor = linha.split("=", 1)
            chave = chave.strip()
            if chave.startswith("export "): chave = chave[len("export "):].strip()
            valor = valor.strip().strip('"').strip("'")
            if chave: os.environ[chave] = valor
        return

carregar_env_local()

# --- 1. CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="BlocoAI - Master Cross-Audit", layout="wide", page_icon="🏗️")

st.sidebar.title("Configurações")
modo_execucao = st.sidebar.radio("Ligação", ["API Key", "Local"], index=0)
api_key_env = os.getenv("CHATGPT_API_KEY", "")

if modo_execucao == "API Key":
    api_key_input = st.sidebar.text_input("🔑 API Key (Overwrite)", value="", type="password")
    api_key_final = api_key_input.strip() if api_key_input.strip() else api_key_env
else:
    torre_ip = st.sidebar.text_input("🌐 IP da Torre", value="100.105.95.121")
    modelo_selecionado = st.sidebar.selectbox("🧠 LLM", ["qwen3.5:9b", "llama3.2:3b"])

# --- 2. LEITURA DE DOCUMENTOS ---
def read_document(file) -> str:
    if file.name.endswith('.pdf'):
        with pdfplumber.open(file) as pdf:
            return "\n".join([f"[Pág: {i+1}] {p.extract_text(layout=True)}" for i, p in enumerate(pdf.pages) if p.extract_text()])
    else:
        xls = pd.ExcelFile(file)
        lines = []
        for sheet in xls.sheet_names:
            df = xls.parse(sheet).astype(str)
            for idx, row in df.iterrows():
                vals = [v.strip() for v in row if v.strip().lower() not in ['nan', 'none', '0.0', '0', '']]
                if len(vals) > 1: lines.append(f"[Linha: {idx+2}] {' | '.join(vals)}")
        return "\n".join(lines)

# --- 3. FASE 1: AGENTE EXTRATOR (gpt-4o-mini) ---
def extrair_sumario_parcial(texto_integral: str, nome_ficheiro: str, llm):
    # Janela gigante para aproveitar o contexto e reduzir latência
    tamanho_max_chunk = 75000 
    chunks = [texto_integral[i:i + tamanho_max_chunk] for i in range(0, len(texto_integral), tamanho_max_chunk)]
    resumos_finais = []
    
    st.markdown(f"**Lendo e classificando:** `{nome_ficheiro}`...")
    progresso_bar = st.progress(0)

    mensagem_sistema = SystemMessage(
        content=f"""You are an Expert Engineering Classifier and Transcriber.
        Your job is to read the text, DETERMINE ITS TECHNICAL DOMAIN, and extract the primary cost drivers.
        
        CRITICAL RULES:
        1. DETERMINE DOMAIN: Classify the primary subject (e.g., "Fire Protection", "Concrete Works", "Structural Steel", "Envelope").
        2. FOCUS ON COST DRIVERS: Extract ONLY Structural Steel grades, Concrete grades, Decking, Cladding panels, Insulation, and Fire/Corrosion Protection.
        3. IGNORE SUNDRIES: Completely ignore minor items (doors, louvres, kerbs, fences, gates, drainage pipes, and small accessories).
        4. IGNORE QUANTITIES: Ignore commercial totals (e.g., 747 tn, 1000m2).
        5. EXACT STRINGS: Use exact names found in text (e.g., "S355", "TATA D60x1.2mm", "Intumescent 1 Hr").
        
        FORMAT FOR EVERY ITEM FOUND:
        [FILE: {nome_ficheiro} | DOMAIN: Your deduced domain] | Phase: [Phase] | Zone: [Zone] | Spec: [Exact Technical String]
        """
    )

    for i, chunk in enumerate(chunks):
        progresso_bar.progress((i + 1) / len(chunks))
        try:
            prompt_extracao = f"Classify the domain of this chunk and extract all major technical specs strictly following the rules:\n\n{chunk}"
            res = llm.invoke([mensagem_sistema, HumanMessage(content=prompt_extracao)])
            resumos_finais.append(res.content)
            time.sleep(0.5)
        except Exception as e: st.error(f"Erro no bloco {i}: {e}")
    
    progresso_bar.empty()
    return "\n\n".join(resumos_finais)

# --- 4. FASE 2: AGENTE AUDITOR (gpt-5-mini / Avançado) ---
def gerar_auditoria_cruzada(resumo_boq, resumo_specs, llm):
    st.markdown("### 🔍 Fase 2: O Auditor Sénior está a consolidar os dados...")
    
    # Deteta se é uma auditoria simples (1 doc) ou cruzada (BOQ vs Specs)
    if resumo_boq and resumo_specs:
        dados_completos = f"=== BOQ EXTRACTS ===\n{resumo_boq}\n\n=== PDF SPECS EXTRACTS ===\n{resumo_specs}"
        missao = "CROSS-DOCUMENT AUDIT"
    else:
        dados_completos = resumo_boq or resumo_specs
        missao = "SINGLE-DOCUMENT HIERARCHY"

    mensagem_sistema = SystemMessage(
        content=f"""You are a Lead Estimator performing a {missao}.
        Your job is to CLEAN, DEDUPLICATE, and ORGANIZE the raw data into a readable executive summary.
        
        CRITICAL RULES:
        1. DEDUPLICATION IS MANDATORY: If a spec (e.g., 'TATA D60x1.2mm') appears multiple times in the same Zone, write it ONLY ONCE.
        2. NO LONG BULLETED LISTS: You must combine the specs into a neat, comma-separated paragraph.
        3. GLOBAL AUDIT: You MUST include a "GLOBAL INCONSISTENCIES" section at the end analyzing project-wide conflicts (e.g., 1 Hr vs 2 Hr paint, different concrete grades).
        
        IF {missao} == "CROSS-DOCUMENT AUDIT":
           COMPARE the BOQ data against the SPECS data. Highlight if a spec in the BOQ contradicts the PDF Specs.
           FORMAT TO FOLLOW:
           Phase: [Name]
           --> Zone: [Name]
              ---> BOQ SPECS: [Comma-separated major specs]
              ---> SPECIFICATIONS (PDF): [Comma-separated major specs]
              ---> MATCH STATUS: ['Aligned' OR detailed description of the conflict]

        IF {missao} == "SINGLE-DOCUMENT HIERARCHY":
           FORMAT TO FOLLOW:
           Phase: [Name]
           --> Zone: [Name]
              ---> TECHNICAL PROFILE: [Comma-separated unique specs]
              ---> LOCAL INCONSISTENCIES: [Conflicts in this zone or 'None']

        [END OF REPORT EXPLICIT REQUIREMENT:]
        GLOBAL INCONSISTENCIES (CROSS-PHASE / CROSS-DOC)
        [List the major technical and financial risks found across the data]
        """
    )
    
    try:
        prompt_auditoria = f"Build the clean, deduplicated tree and generate the global audit based on this data:\n\n{dados_completos}"
        res = llm.invoke([mensagem_sistema, HumanMessage(content=prompt_auditoria)])
        return res.content
    except Exception as e: return f"Erro na consolidação: {e}"

# --- 5. FASE 3: AGENTE APRESENTADOR / FORMATADOR ---
def formatar_relatorio_executivo(auditoria_bruta, llm):
    st.markdown("### 🎨 Fase 3: A formatar o Relatório Executivo (Tabelas e UI)...")
    
    mensagem_sistema = SystemMessage(
        content="""You are an Executive Technical Writer for a Construction Firm.
        Your job is to take a raw, dense engineering audit and format it into a beautiful, user-friendly Executive Summary.
        
        CRITICAL FORMATTING RULES:
        1. TONE: Professional, concise, and user-friendly. No huge walls of text.
        2. HIERARCHY: Format the Phase/Zone breakdown cleanly. Use comma-separated lists for the technical profiles, not long bullet points.
        3. THE TABLE: You MUST convert the "Global Inconsistencies" or any cross-phase conflicts into a highly readable Markdown Table.
           Table Columns: | ID | Category | Location / Zone | Discrepancy Found | Risk / Impact |
        4. NO ADDED DATA: Do not invent new data. Only format what the Auditor provided.
        """
    )
    
    try:
        prompt_formatacao = f"Please format this raw engineering audit into a clean, user-friendly Executive Report with a final table:\n\n{auditoria_bruta}"
        res = llm.invoke([mensagem_sistema, HumanMessage(content=prompt_formatacao)])
        return res.content
    except Exception as e: return f"Erro na formatação: {e}"

# --- 6. INTERFACE PRINCIPAL ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Documentos de Entrada")
    file_boq = st.file_uploader("📁 Carregar BOQ (Excel ou PDF)", type=["xlsx", "xls", "pdf"], key="boq")
    files_specs = st.file_uploader("📚 Carregar Cadernos de Encargos (Múltiplos PDFs)", type=["pdf"], accept_multiple_files=True, key="specs")

with col2:
    st.subheader("2. Foco da Auditoria")
    guia_padrao = "Foco Exclusivo: Graus de Aço/Betão, Revestimentos, Espessuras, Proteção Passiva (Fogo/Pintura). Ignorar completamente itens menores (portas, lancis, tubagens)."
    guia_input = st.text_area("Instruções de Filtragem:", value=guia_padrao, height=150)

if "relatorio_final" not in st.session_state:
    st.session_state.relatorio_final = ""
    st.session_state.processado = False

if st.button("🚀 Iniciar Auditoria Master"):
    if file_boq or files_specs:
        try:
            # SETUP DOS AGENTES
            if modo_execucao == "API Key":
                if not api_key_final: st.error("API Key em falta."); st.stop()
                # Agente 1 (Extrator): Rápido, barato, frio e obediente.
                llm_extrator = ChatOpenAI(model="gpt-4o-mini", api_key=api_key_final, temperature=0.0)
                # Agente 2 (Auditor): Poderoso e analítico (ajusta o nome 'gpt-5-mini' / 'o1-mini' se necessário pela tua API).
                llm_auditor = ChatOpenAI(model="gpt-5-mini", api_key=api_key_final, temperature=0.1)
            else:
                llm_extrator = ChatOllama(model=modelo_selecionado, base_url=f"http://{torre_ip}:11434", temperature=0.0)
                llm_auditor = llm_extrator # Se for local, usamos o mesmo modelo para ambos

            st.markdown("---")
            st.markdown("### ⚙️ Fase 1: Trabalho Braçal de Extração (Agente 1)")
            
            resumo_boq = ""
            resumo_specs = ""

            # 1. PROCESSAR BOQ (Se existir)
            if file_boq:
                texto_boq = read_document(file_boq)
                resumo_boq = extrair_sumario_parcial(texto_boq, f"BOQ: {file_boq.name}", llm_extrator)

            # 2. PROCESSAR PDFs DE SPECS (Se existirem)
            if files_specs:
                for spec in files_specs:
                    conteudo_pdf = read_document(spec)
                    extracao_local = extrair_sumario_parcial(conteudo_pdf, f"PDF: {spec.name}", llm_extrator)
                    resumo_specs += f"\n{extracao_local}\n"

            # 3. CONSOLIDAÇÃO E AUDITORIA (Agente 2 - O Cérebro)
            with st.spinner("🧠 Fase 2: O Auditor Sénior está a cruzar variáveis (Raw Audit)..."):
                auditoria_bruta = gerar_auditoria_cruzada(resumo_boq, resumo_specs, llm_auditor)

            # 4. FORMATAÇÃO FINAL (Agente 3 - O Apresentador)
            with st.spinner("🎨 Fase 3: A desenhar as Tabelas e o Relatório Executivo..."):
                # Passamos o llm_extrator (que é o modelo rápido) para formatar, é mais do que suficiente!
                st.session_state.relatorio_final = formatar_relatorio_executivo(auditoria_bruta, llm_extrator)
                st.session_state.processado = True

        except Exception as e: st.error(f"Erro Crítico: {e}")
    else: st.warning("Carrega pelo menos um documento (BOQ ou PDF) para iniciar.")

# --- 7. RESULTADOS ---
if st.session_state.processado:
    st.markdown("---")
    st.header("📋 Relatório Executivo de Auditoria")
    st.markdown(st.session_state.relatorio_final)
    
    st.download_button("📥 Descarregar Relatório (TXT)", 
                       data=st.session_state.relatorio_final, 
                       file_name="Auditoria_Master_BlocoAI.txt")