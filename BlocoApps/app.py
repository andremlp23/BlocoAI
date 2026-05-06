import os
import sys
from pathlib import Path

# 1. Encontrar a pasta raiz do projeto (BlocoApps), onde vivem as pastas "core" e "ui"
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
    render_context_upload_section,
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
    debug_mode = render_debug_toggle()

    grafo_extracao = construir_grafo_extracao()
    grafo_auditoria = construir_grafo_auditoria()

    # STEP 1: Upload de documentos
    file_boq, files_specs = render_upload_section()
    
    # STEP 2: Upload de JSONs editados (ANTES de gerar contextos)
    specs_pre_carregado, boq_pre_carregado = render_context_upload_section()
    
    # STEP 3: Instruções de filtragem
    guia_input = render_focus_section()

    # STEP 4: Gerar contextos (ou usar os pré-carregados)
    gerar_contextos = render_start_section(api_key_final, file_boq, files_specs)

    if gerar_contextos:
        if not api_key_final:
            st.error("🔑 API Key em falta. Adiciona-a na barra lateral.")
        elif not file_boq and not files_specs and not (specs_pre_carregado or boq_pre_carregado):
            st.warning("Carrega pelo menos um documento ou JSONs para prosseguir.")
        else:
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
                pre_loaded_specs_json=st.session_state.get("pre_loaded_specs_json"),
                pre_loaded_boq_json=st.session_state.get("pre_loaded_boq_json"),
            )
            
            # STEP 5: Auditoria automática em sequência após gerar contextos
            if st.session_state.get("contextos_extraidos"):
                st.markdown("---")
                st.markdown("""
                <div class="section-card">
                    <span class="section-number">STEP 03 / 03</span>
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
                )

    render_results()


if __name__ == "__main__":
    main()