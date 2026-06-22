import os
import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent


if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st

from core.langgraph_engine import construir_grafo_extracao, construir_grafo_auditoria
from core.orchestrator import (
    processar_extracao_contextos,
    processar_auditoria_com_contextos_editados,
)
from ui.components import (
    ensure_session_defaults,
    render_debug_toggle,
    render_focus_section,
    render_header,
    render_results,
    render_start_section,
    render_upload_section,
    setup_sidebar,
)
from ui.styles import apply_global_styles


def carregar_env_local() -> None:
    base_dir = Path(__file__).resolve().parent
    for env_path in [base_dir / ".env", base_dir.parent / ".env"]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            linha = line.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave = chave.strip().removeprefix("export ").strip()
            valor = valor.strip().strip('"').strip("'")
            if chave:
                os.environ[chave] = valor
        return


def main() -> None:
    carregar_env_local()

    st.set_page_config(
        page_title="BlocoAI — Master Cross-Audit",
        layout="wide",
        page_icon="🏗️",
        initial_sidebar_state="expanded",
    )

    ensure_session_defaults()
    st.session_state.api_key_env = os.getenv("CHATGPT_API_KEY", "")

    apply_global_styles()

    api_key_final = setup_sidebar()
    render_header(api_key_final)
    debug_mode, stream_enabled = render_debug_toggle()

    grafo_extracao = construir_grafo_extracao()
    grafo_auditoria = construir_grafo_auditoria()

    exemplo_json = {
        "project_name": "Nome do Teu Projeto Aqui (ex: Data Center X)",
        "project_scope_rules": {
            "valid_phases": ["Phase 1", "Phase 2"],
            "valid_zones": ["ZON", "ABC", "XYZ"],
            "expected_trade_packages": {
                "structural_steel": True,
                "composite_decking": True,
                "fire_protection": True,
                "corrosion_protection": True,
                "metal_fabrications": False,
            },
            "strict_exclusions": [
                "concrete",
                "rebar",
                "waterproofing for concrete",
                "civil works",
                "architectural finishes",
            ],
        },
    }
    exemplo_json_str = json.dumps(exemplo_json, ensure_ascii=False, indent=2)

    st.markdown("""
    <div class="section-card">
        <div class="section-title">🏗️ Contexto da Obra</div>
    </div>
    """, unsafe_allow_html=True)

    contexto_raw = ""
    tab_upload, tab_cola = st.tabs(["📤 Carregar Ficheiro", "📋 Colar JSON"])

    with tab_upload:
        file_json = st.file_uploader(
            "Seleciona um ficheiro JSON",
            type=["json"],
            key="json_baseline",
            label_visibility="collapsed",
        )
        if file_json:
            try:
                contexto_raw = file_json.read().decode("utf-8")
                json.loads(contexto_raw)  # validar que é JSON válido
                st.success("✓ Ficheiro JSON carregado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao ler ficheiro JSON: {e}")
                contexto_raw = ""

    with tab_cola:
        contexto_raw = st.text_area(
            "JSON",
            value=exemplo_json_str,
            height=250,
            help="Cola aqui o teu JSON de contexto da obra.",
            label_visibility="collapsed",
        )

    file_boq, files_specs = render_upload_section()
    guia_input = render_focus_section()
    gerar_contextos = render_start_section(api_key_final, file_boq, files_specs)

    if gerar_contextos:
        if not api_key_final:
            st.error("🔑 API Key em falta. Adiciona-a na barra lateral.")
        elif not file_boq and not files_specs:
            st.warning("Carrega pelo menos um documento para prosseguir.")
        else:
            contexto_projeto = {}
            if contexto_raw.strip():
                try:
                    contexto_projeto = json.loads(contexto_raw)
                except json.JSONDecodeError:
                    st.error("❌ JSON inválido fornecido. Verifica a sintaxe e tenta novamente.")
                    st.stop()

            # Inicializar estado do stream se necessário
            if "stream_expanding" not in st.session_state:
                st.session_state.stream_expanding = True

            # Container para stream (escondido após processamento ou se desativado)
            if not st.session_state.get("processado", False) and stream_enabled:
                stream_container = st.container()
                with stream_container:
                    st.markdown("### 🧠 Pensamento do Modelo:")
                    stream_box = st.container(border=True)
                    stream_text = stream_box.empty()
                
                stream_log = []

                def stream_callback(chunk: str) -> None:
                    """Callback que captura chunks do stream da LLM."""
                    if chunk and stream_text is not None:
                        stream_log.append(chunk)
                        # Mostrar os últimos 50 chunks
                        display_text = "".join(stream_log[-50:])
                        stream_text.markdown(
                            f'<div style="font-family:\'Space Mono\',monospace;font-size:0.9rem;'
                            f'color:#5a9aff;background:#0a0a0a;padding:0.8rem;'
                            f'border-left:3px solid #5a9aff;height:250px;overflow-y:auto;'
                            f'white-space:pre-wrap;word-break:break-word">{display_text}</div>',
                            unsafe_allow_html=True,
                        )
            else:
                # Se processamento está completo ou stream desativado, não mostra o stream
                def stream_callback(chunk: str) -> None:
                    pass

            def pipeline_callback(state: list) -> None:
                pass

            processar_extracao_contextos(
                grafo_extracao=grafo_extracao,
                api_key_final=api_key_final,
                file_boq=file_boq,
                files_specs=files_specs,
                guia_input=guia_input,
                app_file=Path(__file__),
                pipeline_callback=pipeline_callback,
                debug_mode=debug_mode,
                contexto_projeto=contexto_projeto,
                stream_callback=stream_callback,
            )
            
            if st.session_state.get("contextos_extraidos"):
                st.markdown("---")
                st.markdown("""
                <div class="section-card">
                    <span class="section-number">STEP 02 / 02</span>
                    <div class="section-title">🔍 Auditoria & Validação</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.info("Contextos gerados com sucesso. Iniciando auditoria automática...")

                def pipeline_callback_auditoria(state: list) -> None:
                    pass

                processar_auditoria_com_contextos_editados(
                    grafo_auditoria=grafo_auditoria,
                    api_key_final=api_key_final,
                    specs_json_editado=st.session_state.edited_specs_json,
                    boq_json_editado=st.session_state.edited_boq_json,
                    guia_input=guia_input,
                    app_file=Path(__file__),
                    pipeline_callback=pipeline_callback_auditoria,
                    debug_mode=debug_mode,
                    stream_callback=stream_callback,
                )

    render_results()


if __name__ == "__main__":
    main()