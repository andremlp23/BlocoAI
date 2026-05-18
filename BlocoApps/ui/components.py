import streamlit as st
import json
import os


DEFAULT_PROJECT_BASELINE_JSON = json.dumps(
    {
        "project_info": {
            "name": "Project Name",
            "type": "New Build - CSA Works",
        },
        "scope_definition": {
            "phases": ["PH1", "PH2"],
            "zones": ["FSA", "DCH"],
            "included_trades": {
                "structural_steel": True,
                "steel_decking": True,
                "fire_protection": True,
            },
        },
        "critical_notes": "Add any project-wide exceptions here.",
    },
    ensure_ascii=False,
    indent=2,
)


def setup_sidebar() -> tuple[str, str, str, str]:
    """
    Configura sidebar com modo de execução, autenticação e info do sistema.
    Retorna uma tupla com:
    (api_key_final, model_type, model_name, local_url)
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="margin-bottom:1.4rem">
                <div style="font-family:'Space Mono',monospace;font-size:1.05rem;font-weight:700;color:#ffffff;letter-spacing:-0.01em">
                    Bloco<span style="color:#cc8855">AI</span>
                </div>
                <div style="font-size:0.68rem;color:#c0c0c8;letter-spacing:0.12em;text-transform:uppercase;margin-top:0.2rem">
                    Master Cross-Audit · LangGraph
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown('<span class="sidebar-label">⚙️ Modo de Execução</span>', unsafe_allow_html=True)

        modo_execucao = st.radio(
            "Modo de execução:",
            options=["API Remota (OpenAI/OpenRouter)", "Modelo Local (Ollama)"],
            index=0,
            key="modo_execucao",
            label_visibility="collapsed",
        )
        usar_local = modo_execucao == "Modelo Local (Ollama)"
        model_type = "local" if usar_local else "api"

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown('<span class="sidebar-label">🔑 Configuração</span>', unsafe_allow_html=True)

        if usar_local:
            st.markdown('<span class="sidebar-label">URL Local</span>', unsafe_allow_html=True)
            local_url = st.text_input(
                "URL do Ollama",
                value="http://localhost:11434",
                placeholder="http://localhost:11434",
                label_visibility="collapsed",
            )
            st.markdown('<span class="sidebar-label">Modelo Local</span>', unsafe_allow_html=True)
            local_model_name = st.text_input(
                "Nome do modelo local",
                value="llama2",
                placeholder="e.g., llama2, mistral, neural-chat",
                label_visibility="collapsed",
            )
            model_name = local_model_name.strip() or "llama2"
            api_key_final = ""
            st.markdown(
                '<div style="margin-top:0.5rem"><span class="header-badge badge-ok">✓ Modelo Local Selecionado</span></div>',
                unsafe_allow_html=True,
            )
        else:
            local_url = ""

            # Tentar múltiplas variáveis de ambiente
            api_key_env = (
                os.getenv("CHATGPT_API_KEY")
                or os.getenv("OPENAI_API_KEY")
                or os.getenv("OPENROUTER_API_KEY")
                or ""
            )
            st.markdown('<span class="sidebar-label">API Key</span>', unsafe_allow_html=True)
            api_key_input = st.text_input(
                "API Key (OpenAI/OpenRouter)",
                value="",
                type="password",
                placeholder="sk-…  ou lr-…  (ou definida em .env)",
                label_visibility="collapsed",
            )
            api_key_final = api_key_input.strip() if api_key_input.strip() else api_key_env

            st.markdown('<span class="sidebar-label">Modelo API</span>', unsafe_allow_html=True)
            api_model_name = st.text_input(
                "Modelo API",
                value="gpt-5.1",
                placeholder="gpt-5.1, gpt-4o, gpt-4.5, ...",
                label_visibility="collapsed",
            )
            model_name = api_model_name.strip() or "gpt-5.1"

            if api_key_final:
                st.markdown(
                    '<div style="margin-top:0.5rem"><span class="header-badge badge-ok">✓ Key Configurada</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="margin-top:0.5rem"><span class="header-badge badge-fail">✗ Key em Falta</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size:0.65rem;color:#8a8a96;font-family:'Space Mono',monospace;line-height:1.8">
                v3.0 · LangGraph · BlocoApps Suite<br>
                <span style="color:#505058">© 2025 Blocotelha</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return api_key_final, model_type, model_name, local_url


def render_header(api_key_final: str, model_type: str = "api") -> None:
    """Renderiza header band com título e status do modo de execução."""
    if model_type == "local":
        badge_html = '<span class="header-badge badge-ok">● MODELO LOCAL</span>'
    elif api_key_final:
        badge_html = '<span class="header-badge badge-ok">● API REMOTA</span>'
    else:
        badge_html = '<span class="header-badge badge-fail">● OFFLINE</span>'

    st.markdown(
        f"""
        <div class="header-band">
            <div>
                <div class="header-title">Bloco<span>AI</span> — Master Cross-Audit</div>
                <div class="header-tag">Análise Técnica · Motor LangGraph · Multi-Agentes</div>
            </div>
            <div style="display:flex;align-items:center;gap:0.8rem">{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_debug_toggle() -> bool:
    """Renderiza checkbox de debug na barra principal."""
    col1, col2, col3 = st.columns([1, 8, 1])
    with col3:
        debug_mode = st.checkbox("🐞", help="Ativar Modo Debug", value=False)
    return debug_mode



def ensure_session_defaults() -> None:
    for chave, valor_default in [
        ("api_key_env", ""),
        ("relatorio_final", ""),

        # contexto do projeto
        ("project_context_mode", "Colar JSON"),
        ("project_context_json_text", DEFAULT_PROJECT_BASELINE_JSON),
        ("contexto_projeto", {}),

        # outputs brutos dos agentes
        ("resumo_specs", ""),
        ("resumo_boq", ""),

        # JSONs pré-carregados (ANTES da extração)
        ("pre_loaded_specs_json", None),
        ("pre_loaded_boq_json", None),

        # controlo de fluxo
        ("contextos_extraidos", False),
        ("contextos_validados", False),
        ("processado", False),

        ("pipeline_state", ["idle", "idle", "idle"]),
        ("n_ficheiros", 0),
        ("n_fases_hint", "—"),
        ("erros_sessao", []),
        ("paginas_aviso", []),
    ]:
        if chave not in st.session_state:
            st.session_state[chave] = valor_default


def render_project_context_section() -> str:
    st.markdown(
        """
    <div class="section-card">
        <div class="section-title">1. Project Baseline JSON</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    modo = st.radio(
        "Forma de introduzir o contexto do projeto",
        options=["Carregar .json", "Colar JSON"],
        horizontal=True,
        key="project_context_mode",
    )

    contexto_raw = ""

    if modo == "Carregar .json":
        ficheiro = st.file_uploader(
            "Project Baseline JSON",
            type=["json"],
            key="project_baseline_json_file",
            label_visibility="collapsed",
        )
        if ficheiro is not None:
            contexto_raw = ficheiro.getvalue().decode("utf-8-sig", errors="replace")
            st.caption(f"Ficheiro carregado: {ficheiro.name}")
        else:
            st.info("Carrega um ficheiro .json com a baseline do projeto.")
    else:
        contexto_raw = st.text_area(
            "Project Baseline JSON",
            height=240,
            help="Cole aqui um JSON válido com as chaves project_info, scope_definition e critical_notes.",
            key="project_context_json_text",
        )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    return contexto_raw


def render_upload_section():
    st.markdown("""
    <div class="section-card">
        <div class="section-title">2. Documentos de Entrada</div>
    </div>
    """, unsafe_allow_html=True)

    col_boq, col_specs = st.columns(2, gap="medium")

    with col_boq:
        st.markdown('<div class="upload-label">BOQ — Bill of Quantities</div>'
                    '<div class="upload-desc">Ficheiro de orçamento principal · CSV</div>',
                    unsafe_allow_html=True)
        
        file_boq = st.file_uploader("BOQ", type=["csv"], key="boq", label_visibility="collapsed")

    with col_specs:
        st.markdown('<div class="upload-label">Cadernos de Encargos — Specs</div>'
                    '<div class="upload-desc">PDFs e Word (.docx) com especificações técnicas</div>',
                    unsafe_allow_html=True)
        
        files_specs = st.file_uploader("Specs", type=["pdf", "docx"], accept_multiple_files=True, key="specs", label_visibility="collapsed")

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    return file_boq, files_specs

def render_focus_section() -> str:
    st.markdown("""
    <div class="section-card">
        <div class="section-title">3. Instruções de Filtragem</div>
    </div>
    """, unsafe_allow_html=True)

    guia_padrao = (
        "Foco Exclusivo: Graus de Aço/Betão, Revestimentos, Espessuras, "
        "Proteção Passiva (Fogo/Pintura). Ignorar completamente itens menores "
        "(portas, lancis, tubagens, acessórios)."
    )
    return st.text_area(
        "Instruções de Filtragem",
        value=guia_padrao,
        height=90,
        help="Descreve o que os agentes devem priorizar ou ignorar.",
    )


   


def render_start_section(api_key_final: str, file_boq, files_specs, contexto_projeto_raw: str) -> bool:

    col_btn, col_hint = st.columns([2, 5], gap="medium")
    with col_btn:
        iniciar = st.button("Iniciar Extração Completa", use_container_width=True)
    with col_hint:
        if not api_key_final:
            st.markdown(
                '<div style="font-size:0.78rem;color:#7a3030;padding-top:0.65rem">'
                '⚠ Configura a API Key na barra lateral antes de avançar.</div>',
                unsafe_allow_html=True,
            )
        elif not contexto_projeto_raw.strip():
            st.markdown(
                '<div style="font-size:0.78rem;color:#4a6fa0;padding-top:0.65rem">'
                'Fornece o Project Baseline JSON antes de iniciar a extração.</div>',
                unsafe_allow_html=True,
            )
        elif not file_boq and not files_specs:
            st.markdown(
                '<div style="font-size:0.78rem;color:#4a6fa0;padding-top:0.65rem">'
                'Carrega documentos para gerar os JSONs editáveis.</div>',
                unsafe_allow_html=True,
            )
        else:
            docs_txt = []
            if file_boq:
                docs_txt.append(f"BOQ: <span style='color:#5a9aff'>{file_boq.name}</span>")
            if files_specs:
                docs_txt.append(f"<span style='color:#5a9aff'>{len(files_specs)}</span> Caderno(s)")
            st.markdown(
                f'<div style="font-size:0.78rem;color:#2a6a30;padding-top:0.65rem">'
                f'✓ Pronto — Baseline + {" + ".join(docs_txt)}</div>',
                unsafe_allow_html=True,
            )
    return iniciar


def render_pdf_warning(paginas_sem_texto: list) -> None:
    if not paginas_sem_texto:
        return
    aviso = ", ".join(paginas_sem_texto[:10])
    extra = f" (+{len(paginas_sem_texto)-10} mais)" if len(paginas_sem_texto) > 10 else ""
    st.markdown(
        f'<div class="pdf-warning">⚠ Páginas sem texto detectadas (possível digitalização): '
        f'{aviso}{extra} — conteúdo não foi analisado.</div>',
        unsafe_allow_html=True,
    )


def render_results() -> None:
    if not (st.session_state.processado and st.session_state.relatorio_final):
        return

    st.markdown(
        f"""
        <div class="results-header">
            <div class="results-title">📋 Relatório Completo</div>
            <div class="results-meta">Auditoria concluída · {st.session_state.n_ficheiros} ficheiro(s)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="results-body">', unsafe_allow_html=True)
    if st.session_state.paginas_aviso:
        render_pdf_warning(st.session_state.paginas_aviso)
    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="report-md">', unsafe_allow_html=True)
    st.markdown(st.session_state.relatorio_final)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

 
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
    col_dl1, _ = st.columns([2, 5])
    with col_dl1:
        st.download_button(
            "📥 Descarregar Relatório (.txt)",
            data=st.session_state.relatorio_final,
            file_name="BlocoAI_Relatorio.txt",
            use_container_width=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)



 