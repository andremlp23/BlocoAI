import os
import json
import sys
from pathlib import Path

# 1. Encontrar a pasta raiz do projeto (BlocoApps), onde vivem as pastas "core" e "ui"
root_dir = Path(__file__).resolve().parent

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st

# Importação dos grafos
from core.langgraph_engine import construir_grafo_extracao, construir_grafo_auditoria

from core.orchestrator import executar_pipeline_completo

from ui.components import (
    ensure_session_defaults,
    render_debug_toggle,
    render_focus_section,
    render_header,
    render_results,
    render_project_context_section, # Novo componente para o JSON
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

    # Configuração da Barra Lateral e Modo de Execução
    api_key_final, model_type, model_name, local_url = setup_sidebar()
    render_header(api_key_final, model_type)
    debug_mode = render_debug_toggle()

    # Inicialização dos Grafos de LangGraph
    grafo_extracao = construir_grafo_extracao()
    grafo_auditoria = construir_grafo_auditoria()

    # ---------------------------------------------------------
    # UI STEPS
    # ---------------------------------------------------------
    
    # STEP 1: Project Baseline JSON (Contexto do Projeto)
    contexto_projeto_raw = render_project_context_section()

    # STEP 2: Upload de documentos (BOQ e SPECS)
    file_boq, files_specs = render_upload_section()
    
    # STEP 3: Instruções de filtragem/foco
    guia_input = render_focus_section()

    # STEP 4: Botão de Início
    iniciar = render_start_section(api_key_final, file_boq, files_specs, contexto_projeto_raw)

    if iniciar:
        if model_type == "api" and not api_key_final:
            st.error("🔑 API Key em falta. Adiciona-a na barra lateral.")
        elif model_type == "local" and not model_name.strip():
            st.error("⚠️ Define o modelo local antes de avançar.")
        elif not file_boq and not files_specs:
            st.warning("Carrega pelo menos um documento para prosseguir.")
        elif not contexto_projeto_raw.strip():
            st.error("⚠️ O Project Baseline JSON é obrigatório para guiar a auditoria.")
        else:
            # Validação técnica do JSON de Contexto
            try:
                contexto_projeto = json.loads(contexto_projeto_raw)
                if not isinstance(contexto_projeto, dict):
                    raise ValueError("O conteúdo deve ser um objeto JSON { ... }.")
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"⚠️ Erro no Project Baseline JSON: {exc}")
                return

            # Guardar contexto no estado da sessão
            st.session_state.contexto_projeto = contexto_projeto

            # Callback vazio para a pipeline (o orchestrator gere o estado interno)
            def pipeline_callback(state: list) -> None:
                pass

            # ---------------------------------------------------------
            # EXECUÇÃO DO PIPELINE UNIFICADO (A "Jarrada")
            # ---------------------------------------------------------
            with st.spinner("A processar documentos e a realizar auditoria cruzada..."):
                resultado_estado = executar_pipeline_completo(
                    grafo_extracao=grafo_extracao,
                    grafo_auditoria=grafo_auditoria,
                    api_key=api_key_final,
                    model_type=model_type,
                    model_name=model_name,
                    local_url=local_url,
                    file_boq=file_boq,
                    files_specs=files_specs,
                    contexto_projeto=contexto_projeto,
                    guia_input=guia_input,
                    app_file=Path(__file__),
                    pipeline_callback=pipeline_callback,
                    debug_mode=debug_mode,
                )
            
            # APAGÁMOS o st.rerun() e colocámos um inspetor de erros!
            erros_finais = resultado_estado.get("erros") or []
            if erros_finais:
                st.error(f"🛑 O pipeline parou devido aos seguintes erros: {'; '.join(erros_finais)}")
            elif not st.session_state.get("processado"):
                st.warning("⚠️ O processo terminou rapidamente mas não gerou o relatório. Verifica se os documentos têm texto legível.")
            else:
                st.success("✅ Auditoria concluída com sucesso!")

    # Exibição dos resultados (Relatório, Erros, etc.)
    render_results()


if __name__ == "__main__":
    main()