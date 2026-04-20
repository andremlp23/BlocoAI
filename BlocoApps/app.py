import os
import sys
from pathlib import Path

# 1. Encontrar a pasta raiz do projeto (BlocoApps), que é o "pai" da pasta "ui"
root_dir = Path(__file__).resolve().parent.parent

# 2. Adicionar essa pasta ao "radar" do Python para ele encontrar a pasta "core" e "ui"
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 3. Agora os imports locais vão funcionar perfeitamente
import streamlit as st

from core.langgraph_engine import construir_grafo
from core.orchestrator import processar_auditoria
from ui.components import (
    ensure_session_defaults,
    render_focus_section,
    render_header,
    render_pipeline,
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

    grafo_auditoria = construir_grafo()

    pipeline_slot = st.empty()

    def on_pipeline_update(states: list) -> None:
        pipeline_slot.markdown(render_pipeline(states), unsafe_allow_html=True)

    on_pipeline_update(st.session_state.pipeline_state)

    file_boq, files_specs = render_upload_section()
    guia_input = render_focus_section()
    iniciar = render_start_section(api_key_final, file_boq, files_specs)

    if iniciar:
        if not api_key_final:
            st.error("🔑 API Key em falta. Adiciona-a na barra lateral.")
        elif not file_boq and not files_specs:
            st.warning("Carrega pelo menos um documento para iniciar.")
        else:
            processar_auditoria(
                grafo_auditoria=grafo_auditoria,
                api_key_final=api_key_final,
                file_boq=file_boq,
                files_specs=files_specs,
                guia_input=guia_input,
                pipeline_callback=on_pipeline_update,
                app_file=Path(__file__),
            )

    render_results()


if __name__ == "__main__":
    main()