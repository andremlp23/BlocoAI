import json
import re
import traceback  # <--- NOVO: O nosso detetive de erros!
import streamlit as st
from pathlib import Path
from datetime import datetime
from core.document_reader import read_document

def _pipeline_state_from_node(node_name: str) -> list:
    """Função auxiliar para animar a barra de progresso na UI."""
    if node_name == "extrair":
        return ["done", "active", "idle"]
    if node_name == "auditar":
        return ["done", "done", "active"]
    if node_name == "formatar":
        return ["done", "done", "done"]
    if node_name == "erro":
        return ["error", "error", "error"]
    return ["active", "idle", "idle"]

def executar_pipeline_completo(
    grafo_extracao,
    grafo_auditoria,
    api_key,
    model_type,
    model_name,
    local_url,
    file_boq,
    files_specs,
    contexto_projeto,
    guia_input,
    app_file,
    pipeline_callback=None,
    debug_mode=False
):
    """
    Versão unificada: Lê ficheiros -> Extrai -> Audita -> Relatório.
    """
    try:
        # 1. LEITURA DOS DOCUMENTOS BLINDADA
        texto_boq = ""
        paginas_sem_texto = []
        
        if file_boq:
            res_boq = read_document(file_boq)
            if isinstance(res_boq, tuple):
                texto_boq = str(res_boq[0] or "")
                paginas_sem_texto.extend(res_boq[1] or [])
            else:
                texto_boq = str(res_boq or "")

        textos_specs = []
        nomes_specs = []
        for f in (files_specs or []):
            res_spec = read_document(f)
            if isinstance(res_spec, tuple):
                textos_specs.append(str(res_spec[0] or ""))
                paginas = res_spec[1] or []
                if paginas:
                    paginas_sem_texto.extend([f"{f.name} pág. {pag}" for pag in paginas])
            else:
                textos_specs.append(str(res_spec or ""))
            nomes_specs.append(f.name)

        texto_specs_total = "\n\n".join(textos_specs)

        # 2. ESTADO INICIAL COMPLETO (Preenchemos TODAS as chaves para acalmar o LangGraph)
        estado = {
            "texto_boq": texto_boq,
            "texto_specs": texto_specs_total,
            "guia_filtragem": guia_input or "",
            "nome_boq": file_boq.name if file_boq else "",
            "nomes_specs": nomes_specs or ["Docs"],
            
            "resumo_boq": "",
            "resumo_specs": "",
            "contexto_projeto": contexto_projeto or {},
            
            "auditoria_bruta": "",
            "auditoria_normalizada": "",
            "relatorio_final": "",
            
            "modo": "CROSS" if (texto_boq and texto_specs_total) else "SINGLE",
            "tentativas": 0,
            "erros": [],
            
            "n_ficheiros": (1 if file_boq else 0) + len(files_specs or []),
            "paginas_sem_texto": paginas_sem_texto,
            
            "_api_key": api_key,
            "_model_type": model_type,
            "_model_name": model_name or ("llama2" if model_type == "local" else "gpt-5.1"),
            "_local_url": local_url,
            "_prog_slot": None,
            "_status_slot": None
        }

        # 3. FASE 1: EXTRAÇÃO 
        for output in grafo_extracao.stream(estado, stream_mode="updates"):
            for node_name, node_state in output.items():
                if node_state and isinstance(node_state, dict):
                    estado.update(node_state)
                if pipeline_callback:
                    pipeline_callback(_pipeline_state_from_node(node_name))

        # 4. FASE 2: AUDITORIA 
        for output in grafo_auditoria.stream(estado, stream_mode="updates"):
            for node_name, node_state in output.items():
                if node_state and isinstance(node_state, dict):
                    estado.update(node_state)
                if pipeline_callback:
                    pipeline_callback(_pipeline_state_from_node(node_name))

        # 5. FINALIZAÇÃO E PERSISTÊNCIA NA UI
        relatorio = estado.get("relatorio_final", "")
        if relatorio:
            st.session_state.relatorio_final = relatorio
            st.session_state.processado = True
            
            st.session_state.erros_sessao = estado.get("erros") or []
            st.session_state.paginas_aviso = estado.get("paginas_sem_texto") or []
            st.session_state.n_ficheiros = estado.get("n_ficheiros", 0)
            
            _persistir_relatorio(relatorio, app_file)
            
        return estado

    except Exception as e:
        msg_erro = f"Erro crítico no pipeline: {str(e)}"
        st.error(msg_erro)
        
        # AQUI: Se falhar, mostra exatamente onde o erro nasceu!
        with st.expander("🔍 Ver detalhes técnicos do erro (Traceback)"):
            st.code(traceback.format_exc(), language="python")
            
        if pipeline_callback:
            pipeline_callback(["error", "error", "error"])
        return {"erros": [msg_erro]}

def _persistir_relatorio(relatorio: str, app_file: Path) -> None:
    try:
        pasta = app_file.resolve().parent.parent / "historico_auditorias"
        pasta.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        ficheiro = pasta / f"Auditoria_{ts}.txt"
        ficheiro.write_text(relatorio, encoding="utf-8")
    except Exception:
        pass

def _normalizar_json_ou_raw(texto: str, nome: str) -> str:
    if not texto or not texto.strip():
        return json.dumps({"status": "EMPTY", "name": nome, "content": ""}, ensure_ascii=False, indent=2)

    try:
        data = json.loads(texto)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        return json.dumps(
            {
                "status": "INVALID_JSON_RAW_OUTPUT",
                "name": nome,
                "raw_output": texto,
                "manual_completion_required": True,
            },
            ensure_ascii=False,
            indent=2,
        )