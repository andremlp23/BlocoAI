import streamlit as st

STEPS = [
    ("AGT-01", "Extrator", "Classificação de Domínio & Extracção"),
    ("AGT-02", "Auditor Sénior", "Cross-Audit & Deduplicação"),
    ("AGT-03", "Apresentador", "Formatação do Relatório Executivo"),
]
ICONS = {"idle": "○", "active": "◉", "done": "✓", "error": "✗", "retry": "↺"}


def setup_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div style="margin-bottom:1.4rem">
                <div style="font-family:'Space Mono',monospace;font-size:1.05rem;font-weight:700;color:#e8f0ff;letter-spacing:-0.01em">
                    Bloco<span style="color:#3a8eff">AI</span>
                </div>
                <div style="font-size:0.68rem;color:#2a4070;letter-spacing:0.12em;text-transform:uppercase;margin-top:0.2rem">
                    Master Cross-Audit · LangGraph
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown('<span class="sidebar-label">🔑 Autenticação</span>', unsafe_allow_html=True)

        api_key_env = st.session_state.get("api_key_env", "")
        api_key_input = st.text_input(
            "API Key OpenAI",
            value="",
            type="password",
            placeholder="sk-…  (ou definida em .env)",
            label_visibility="collapsed",
        )
        api_key_final = api_key_input.strip() if api_key_input.strip() else api_key_env

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
        st.markdown('<span class="sidebar-label">⚙️ Pipeline LangGraph</span>', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background:#060d1f;border:1px solid #111e36;border-radius:6px;padding:0.8rem;font-family:'Space Mono',monospace;font-size:0.7rem;color:#2a4a7a;line-height:1.8">
                <div><span style="color:#1e5ccc">AGT-01</span> &nbsp;Extrator</div>
                <div style="font-size:0.6rem;color:#1a2e50;margin-left:2.4rem">Classificação · gpt-4o-mini · t=0.0</div>
                <div style="margin-top:0.4rem"><span style="color:#1e5ccc">AGT-02</span> &nbsp;Auditor Sénior</div>
                <div style="font-size:0.6rem;color:#1a2e50;margin-left:2.4rem">Cross-Audit · gpt-5-mini · t=0.1 · retry×2</div>
                <div style="margin-top:0.4rem"><span style="color:#1e5ccc">AGT-03</span> &nbsp;Apresentador</div>
                <div style="font-size:0.6rem;color:#1a2e50;margin-left:2.4rem">Formatação · gpt-4o-mini · t=0.1</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size:0.65rem;color:#1a2a44;font-family:'Space Mono',monospace;line-height:1.8">
                v3.0 · LangGraph · BlocoApps Suite<br>
                <span style="color:#111e36">© 2025 Blocotelha</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return api_key_final


def render_header(api_key_final: str) -> None:
    badge_html = (
        '<span class="header-badge badge-ok">● API ONLINE</span>'
        if api_key_final
        else '<span class="header-badge badge-fail">● API OFFLINE</span>'
    )
    st.markdown(
        f"""
        <div class="header-band">
            <div>
                <div class="header-title">Bloco<span>AI</span> — Master Cross-Audit</div>
                <div class="header-tag">Análise Técnica · Motor LangGraph · 3 Agentes Especializados</div>
            </div>
            <div style="display:flex;align-items:center;gap:0.8rem">{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ensure_session_defaults() -> None:
    for chave, valor_default in [
        ("api_key_env", ""),
        ("relatorio_final", ""),
        ("processado", False),
        ("pipeline_state", ["idle", "idle", "idle"]),
        ("n_ficheiros", 0),
        ("n_fases_hint", "—"),
        ("erros_sessao", []),
        ("paginas_aviso", []),
    ]:
        if chave not in st.session_state:
            st.session_state[chave] = valor_default


def render_pipeline(states: list) -> str:
    html = ""
    for (num, title, sub), state in zip(STEPS, states):
        icon = ICONS.get(state, "○")
        pulse_cls = " pulse" if state == "active" else (" pulse-amber" if state == "retry" else "")
        html += f"""
        <div class="pipeline-step {state}">
            <div class="step-num {state}">{num}</div>
            <div class="step-title {state}">{title}</div>
            <div class="step-sub {state}">{sub}</div>
            <div class="step-icon{pulse_cls}">{icon}</div>
        </div>"""
    return f'<div class="pipeline-wrap">{html}</div>'


def render_upload_section() -> tuple:
    st.markdown(
        """
        <div class="section-card">
            <span class="section-number">STEP 01 / 03</span>
            <div class="section-title">📂 Documentos de Entrada</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_boq, col_specs = st.columns(2, gap="medium")
    with col_boq:
        st.markdown(
            '<div class="upload-label">BOQ — Bill of Quantities</div>'
            '<div class="upload-desc">Ficheiro de orçamento principal · Excel ou PDF</div>',
            unsafe_allow_html=True,
        )
        file_boq = st.file_uploader("BOQ", type=["xlsx", "xls", "pdf"], key="boq", label_visibility="collapsed")
        if file_boq:
            ext = file_boq.name.split(".")[-1].upper()
            size_kb = round(file_boq.size / 1024, 1)
            st.markdown(
                f'<span class="file-chip">📄 {file_boq.name} &nbsp;·&nbsp; {ext} &nbsp;·&nbsp; {size_kb} KB</span>',
                unsafe_allow_html=True,
            )

    with col_specs:
        st.markdown(
            '<div class="upload-label">Cadernos de Encargos — Specs</div>'
            '<div class="upload-desc">Múltiplos PDFs de especificações técnicas</div>',
            unsafe_allow_html=True,
        )
        files_specs = st.file_uploader(
            "Specs",
            type=["pdf"],
            accept_multiple_files=True,
            key="specs",
            label_visibility="collapsed",
        )
        if files_specs:
            for f in files_specs:
                size_kb = round(f.size / 1024, 1)
                st.markdown(
                    f'<span class="file-chip">📑 {f.name} &nbsp;·&nbsp; {size_kb} KB</span>',
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    return file_boq, files_specs


def render_focus_section() -> str:
    st.markdown(
        """
        <div class="section-card" style="margin-top:0.8rem">
            <span class="section-number">STEP 02 / 03</span>
            <div class="section-title">🎯 Foco da Auditoria</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    st.markdown(
        """
        <div class="section-card" style="margin-top:0.8rem">
            <span class="section-number">STEP 03 / 03</span>
            <div class="section-title">🚀 Iniciar Processamento</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_btn, col_hint = st.columns([2, 5], gap="medium")
    with col_btn:
        iniciar = st.button("▶  INICIAR AUDITORIA MASTER", use_container_width=True)
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
                'Carrega pelo menos um documento (BOQ ou Caderno de Encargos).</div>',
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

    st.markdown(
        f"""
        <div class="results-header">
            <div class="results-title">📋 Relatório Executivo de Auditoria</div>
            <div class="results-meta">Auditoria concluída · {st.session_state.n_ficheiros} ficheiro(s)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="results-body">', unsafe_allow_html=True)
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
            file_name="Auditoria_Master_BlocoAI.txt",
            use_container_width=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
