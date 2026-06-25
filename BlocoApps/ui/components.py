import streamlit as st
import json
import os


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
            options=["API Remota", "Modelo Local"],
            index=0,
            key="modo_execucao",
            label_visibility="collapsed",
        )
        usar_local = modo_execucao == "Modelo Local"
        model_type = "local" if usar_local else "api"

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown('<span class="sidebar-label">🔑 Configuração</span>', unsafe_allow_html=True)

        if usar_local:
            st.markdown('<span class="sidebar-label">URL Local</span>', unsafe_allow_html=True)
            local_url = st.text_input(
                "URL Local",
                value="http://localhost:11434",
                placeholder="http://localhost:11434",
                label_visibility="collapsed",
            )
            st.markdown('<span class="sidebar-label">Modelo Local</span>', unsafe_allow_html=True)
            local_model_name = st.text_input(
                "Nome do modelo local",
                value="qwen3.5:9b",
                placeholder="e.g., qwen3.5:9b, llama2, mistral, neural-chat",
                label_visibility="collapsed",
            )
            model_name = local_model_name.strip() or "qwen3.5:9b"
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
                "API Key",
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


def render_debug_toggle() -> tuple[bool, bool]:
    """Renderiza checkboxes de debug e pensamento na barra principal."""
    col1, col2, col3, col4 = st.columns([1, 6.5, 1, 1])
    with col3:
        stream_enabled = st.checkbox("🧠", help="Mostrar Pensamento do Modelo", value=True, key="stream_toggle")
    with col4:
        debug_mode = st.checkbox("🐞", help="Ativar Modo Debug", value=False)
    return debug_mode, stream_enabled



def ensure_session_defaults() -> None:
    for chave, valor_default in [
        ("api_key_env", ""),
        ("relatorio_final", ""),

        # outputs brutos dos agentes
        ("resumo_specs", ""),
        ("resumo_boq", ""),

        # versões editáveis
        ("edited_specs_json", ""),
        ("edited_boq_json", ""),

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


def render_upload_section():
    st.markdown("""
    <div class="section-card">
        <div class="section-title">📂 Documentos de Entrada</div>
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


   


def render_start_section(api_key_final: str, file_boq, files_specs) -> bool:

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
                f'✓ Pronto — {" + ".join(docs_txt)}</div>',
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

    # Título simples do relatório
    st.markdown("## 📋 Relatório Completo")
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ficheiros", st.session_state.n_ficheiros)
    with col2:
        st.metric("Fases Detectadas", st.session_state.n_fases_hint)
    with col3:
        st.metric("Status", "✓ OK")
    
    st.divider()
    
    # Relatório em markdown
    st.markdown(st.session_state.relatorio_final)
    
    st.divider()
    st.download_button(
        "📥 Descarregar Relatório (.txt)",
        data=st.session_state.relatorio_final,
        file_name="BlocoAI_Relatorio.txt",
        use_container_width=True,
    )



 