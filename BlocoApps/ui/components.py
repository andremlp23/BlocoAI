import streamlit as st
import json
import os


def setup_sidebar() -> str:
    """
    Configura sidebar com autenticação e info do sistema.
    Retorna a API key final (input ou .env).
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
        st.markdown('<span class="sidebar-label">🔑 Autenticação</span>', unsafe_allow_html=True)

        # Tentar múltiplas variáveis de ambiente
        api_key_env = (
            os.getenv("CHATGPT_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("OPENROUTER_API_KEY")
            or ""
        )
        api_key_input = st.text_input(
            "API Key (OpenAI/OpenRouter)",
            value="",
            type="password",
            placeholder="sk-…  ou lr-…  (ou definida em .env)",
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
        st.markdown(
            """
            <div style="font-size:0.65rem;color:#8a8a96;font-family:'Space Mono',monospace;line-height:1.8">
                v3.0 · LangGraph · BlocoApps Suite<br>
                <span style="color:#505058">© 2025 Blocotelha</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return api_key_final


def render_header(api_key_final: str) -> None:
    """Renderiza header band com título e status da API."""
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
                <div class="header-tag">Análise Técnica · Motor LangGraph · 3 Agentes</div>
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
        <span class="section-number">STEP 01 / 03</span>
        <div class="section-title">📂 Documentos de Entrada</div>
    </div>
    """, unsafe_allow_html=True)

    col_boq, col_specs = st.columns(2, gap="medium")

    with col_boq:
        st.markdown('<div class="upload-label">BOQ — Bill of Quantities</div>'
                    '<div class="upload-desc">Ficheiro de orçamento principal · Excel, CSV ou PDF</div>',
                    unsafe_allow_html=True)
        
        file_boq = st.file_uploader("BOQ", type=["xlsx","xls","csv","pdf"], key="boq", label_visibility="collapsed")

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


def render_context_upload_section() -> tuple[bool, bool]:
    """
    Secção para carregar JSONs editados de contexto ANTES da extração.
    Retorna (specs_carregado, boq_carregado)
    """
    st.markdown("""
    <div class="section-card">
        <span class="section-number">STEP 02 / 03</span>
        <div class="section-title">📋 Contextos JSON Editados (Opcional)</div>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "Se tens JSONs de contexto já editados, carrega-os aqui. "
        "Caso contrário, serão gerados automaticamente a partir dos documentos."
    )

    col1, col2 = st.columns(2, gap="large")

    specs_carregado = False
    boq_carregado = False

    # SPECS
    with col1:
        st.markdown("### AGT-01 — Specs Context JSON")
        
        uploaded_specs = st.file_uploader(
            "Carregar Specs JSON editado (opcional)",
            type=["json"],
            key="upload_specs_pre_extracao",
        )

        if uploaded_specs is not None:
            try:
                raw = uploaded_specs.read().decode("utf-8")
                parsed = json.loads(raw)
                st.session_state.pre_loaded_specs_json = json.dumps(parsed, ensure_ascii=False, indent=2)
                specs_carregado = True
                st.success("✓ Specs JSON carregado.")
            except Exception as e:
                st.error(f"✗ Erro no Specs JSON: {e}")
        else:
            if st.session_state.get("pre_loaded_specs_json"):
                specs_carregado = True
                st.caption("✓ Specs JSON já carregado")

    # BOQ
    with col2:
        st.markdown("### AGT-02 — BOQ Context JSON")
        
        uploaded_boq = st.file_uploader(
            "Carregar BOQ JSON editado (opcional)",
            type=["json"],
            key="upload_boq_pre_extracao",
        )

        if uploaded_boq is not None:
            try:
                raw = uploaded_boq.read().decode("utf-8")
                parsed = json.loads(raw)
                st.session_state.pre_loaded_boq_json = json.dumps(parsed, ensure_ascii=False, indent=2)
                boq_carregado = True
                st.success("✓ BOQ JSON carregado.")
            except Exception as e:
                st.error(f"✗ Erro no BOQ JSON: {e}")
        else:
            if st.session_state.get("pre_loaded_boq_json"):
                boq_carregado = True
                st.caption("✓ BOQ JSON já carregado")

    return specs_carregado, boq_carregado


def render_start_section(api_key_final: str, file_boq, files_specs) -> bool:

    col_btn, col_hint = st.columns([2, 5], gap="medium")
    with col_btn:
        iniciar = st.button("① GERAR CONTEXTOS JSON", use_container_width=True)
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

    if st.session_state.resumo_specs:
        st.markdown(
            f"""
            <div class="results-subsection">
                <div class="results-subtitle">🧾 Contexto Extraído das SPECS</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.text_area(
            "Resumo extraído das SPECS",
            value=st.session_state.resumo_specs,
            height=220,
            disabled=True,
            key="resumo_specs_preview",
        )
        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
        col_dl2, _ = st.columns([2, 5])
        with col_dl2:
            st.download_button(
                "📥 Descarregar Contexto SPECS (.json)",
                data=st.session_state.resumo_specs,
                file_name="Specs_Extraction_Context.json",
                mime="application/json",
                use_container_width=True,
            )
            if st.session_state.resumo_boq:
                st.download_button(
                    "📥 Descarregar Contexto BOQ (.json)",
                    data=st.session_state.resumo_boq,
                    file_name="BOQ_Extraction_Context.json",
                    mime="application/json",
                    use_container_width=True,
                )
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

def _validar_json_texto(texto: str) -> tuple[bool, str]:
    try:
        json.loads(texto)
        return True, "JSON válido."
    except Exception as e:
        return False, f"JSON inválido: {e}"


def render_context_review_section() -> bool:
    """
    Secção para:
    - descarregar os JSONs gerados pelos agentes
    - carregar versões editadas manualmente (OPCIONAL)
    - usar valores por defeito ou avançar com edições
    - avançar para a auditoria
    """
    if not st.session_state.get("contextos_extraidos"):
        return False

    st.markdown("""
    <div class="section-card" style="margin-top:0.8rem">
        <span class="section-number">REVIEW / EDIT</span>
        <div class="section-title">🧾 Contextos JSON para Revisão Manual</div>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "✓ Podes descarregar os JSONs, editar manualmente e recarregar aqui. "
        "Ou prosseguir com os valores por defeito."
    )

    # Garante defaults
    if not st.session_state.get("edited_specs_json"):
        st.session_state.edited_specs_json = st.session_state.get("resumo_specs", "")

    if not st.session_state.get("edited_boq_json"):
        st.session_state.edited_boq_json = st.session_state.get("resumo_boq", "")

    col1, col2 = st.columns(2, gap="large")

    # ==========================================================
    # SPECS
    # ==========================================================
    with col1:
        st.markdown("### AGT-01 — Specs Context JSON")

        if st.session_state.get("resumo_specs"):
            st.download_button(
                "📥 Descarregar Specs JSON",
                data=st.session_state.resumo_specs,
                file_name="AGT01_Specs_Context_Editavel.json",
                mime="application/json",
                use_container_width=True,
            )

        uploaded_specs = st.file_uploader(
            "Carregar Specs JSON editado manualmente (opcional)",
            type=["json"],
            key="upload_specs_json_editado",
        )

        specs_custom_loaded = False

        if uploaded_specs is not None:
            try:
                raw = uploaded_specs.read().decode("utf-8")
                parsed = json.loads(raw)
                st.session_state.edited_specs_json = json.dumps(parsed, ensure_ascii=False, indent=2)
                specs_custom_loaded = True
                st.success("✓ Specs JSON carregado e validado.")
            except Exception as e:
                st.error(f"✗ Erro no Specs JSON: {e}")
        
        if not uploaded_specs:
            st.caption("Deixar em branco para usar contexto por defeito")

    # ==========================================================
    # BOQ
    # ==========================================================
    with col2:
        st.markdown("### AGT-02 — BOQ Context JSON")

        if st.session_state.get("resumo_boq"):
            st.download_button(
                "📥 Descarregar BOQ JSON",
                data=st.session_state.resumo_boq,
                file_name="AGT02_BOQ_Context_Editavel.json",
                mime="application/json",
                use_container_width=True,
            )

        uploaded_boq = st.file_uploader(
            "Carregar BOQ JSON editado manualmente (opcional)",
            type=["json"],
            key="upload_boq_json_editado",
        )

        boq_custom_loaded = False

        if uploaded_boq is not None:
            try:
                raw = uploaded_boq.read().decode("utf-8")
                parsed = json.loads(raw)
                st.session_state.edited_boq_json = json.dumps(parsed, ensure_ascii=False, indent=2)
                boq_custom_loaded = True
                st.success("✓ BOQ JSON carregado e validado.")
            except Exception as e:
                st.error(f"✗ Erro no BOQ JSON: {e}")
        
        if not uploaded_boq:
            st.caption("Deixar em branco para usar contexto por defeito")

    st.markdown("---")

    # Lógica de decisão: podes prosseguir mesmo sem carregar ficheiros
    ficheiros_editados_carregados = specs_custom_loaded and boq_custom_loaded
    pode_usar_defaults = st.session_state.get("resumo_specs") and st.session_state.get("resumo_boq")

    # Marca se há contextos validados (quer do custom upload, quer dos defaults)
    st.session_state.contextos_validados = True

    if ficheiros_editados_carregados:
        st.markdown(
            '<div style="padding:0.6rem;background:#0a3a1a;border-left:3px solid #4ade80;border-radius:4px;margin-bottom:0.8rem">'
            '<span style="color:#4ade80;font-weight:600">✓ Ficheiros editados carregados</span> — A auditoria será executada com os teus JSONs customizados.</div>',
            unsafe_allow_html=True,
        )
    elif pode_usar_defaults:
        st.markdown(
            '<div style="padding:0.6rem;background:#1a2a3a;border-left:3px solid #5a9aff;border-radius:4px;margin-bottom:0.8rem">'
            '<span style="color:#5a9aff;font-weight:600">ℹ Modo padrão</span> — A auditoria será executada com os contextos gerados automaticamente.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("✗ Sem contextos disponíveis. Volta à etapa anterior para gerar os JSONs.")
        return False

    col_btn_cont, col_btn_skip = st.columns(2, gap="medium")

    with col_btn_cont:
        prosseguir = st.button(
            "✅ Prosseguir para Auditoria",
            use_container_width=True,
            type="primary",
        )
    
    with col_btn_skip:
        st.button(
            "🔄 Regenerar Contextos",
            use_container_width=True,
            disabled=True,
            help="Volta à etapa anterior se precisares de novos contextos.",
        )

    return prosseguir