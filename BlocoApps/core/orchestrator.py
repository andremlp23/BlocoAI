import re
import json
import streamlit as st

from datetime import datetime
from pathlib import Path
from typing import Callable


from core.document_reader import read_document
from core.langgraph_engine import AuditoriaState


def _pipeline_state_from_node(node_name: str, estado_final: dict) -> list:
    if node_name == "extrair":
        return ["done", "active", "idle"]

    if node_name == "auditar":
        auditoria = estado_final.get("auditoria_bruta", "")
        tentativas = estado_final.get("tentativas", 1)
        if len(auditoria.strip()) >= 100:
            return ["done", "done", "active"]
        if tentativas < 2:
            return ["done", "retry", "idle"]
        return ["done", "error", "idle"]

    if node_name == "formatar":
        return ["done", "done", "done"]

    if node_name == "erro":
        erros_acum = estado_final.get("erros", [])
        if any("AGT-01" in e for e in erros_acum):
            return ["error", "idle", "idle"]
        if any("AGT-02" in e for e in erros_acum):
            return ["done", "error", "idle"]
        return ["error", "error", "error"]

    return ["idle", "idle", "idle"]


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
    """
    Tenta normalizar JSON. Se o agente falhou e devolveu texto não JSON,
    guarda mesmo assim dentro de um wrapper para não perder informação.
    """
    if not texto or not texto.strip():
        return json.dumps(
            {
                "status": "EMPTY",
                "name": nome,
                "content": "",
            },
            ensure_ascii=False,
            indent=2,
        )

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


def _persistir_contexto_json(nome: str, conteudo: str, app_file: Path) -> Path:
    """
    Guarda os outputs editáveis dos agentes 1 e 2 em ficheiro.
    """
    pasta = app_file.resolve().parent.parent / "contextos_editaveis"
    pasta.mkdir(exist_ok=True)

    ficheiro = pasta / nome
    ficheiro.write_text(conteudo, encoding="utf-8")

    return ficheiro

def processar_extracao_contextos(
    grafo_extracao,
    api_key_final: str,
    file_boq,
    files_specs,
    guia_input: str,
    app_file: Path,
    pipeline_callback: Callable[[list], None] = None,
    debug_mode: bool = False,
    pre_loaded_specs_json: str = None,
    pre_loaded_boq_json: str = None,
) -> None:
    """
    Passo 1:
    - Se pré-carregados: usa os JSONs fornecidos diretamente;
    - Caso contrário: lê documentos e corre AGT-01 e AGT-02;
    - Guarda Specs JSON e BOQ JSON em session_state.
    """
    # Se ambos os JSONs foram pré-carregados, usá-los diretamente
    if pre_loaded_specs_json and pre_loaded_boq_json:
        try:
            st.info("✓ Usando contextos pré-carregados...")
            
            st.session_state.resumo_specs = pre_loaded_specs_json
            st.session_state.resumo_boq = pre_loaded_boq_json

            st.session_state.edited_specs_json = pre_loaded_specs_json
            st.session_state.edited_boq_json = pre_loaded_boq_json

            st.session_state.contextos_extraidos = True
            st.session_state.contextos_validados = True  # Já validados
            st.session_state.processado = False

            st.session_state.n_ficheiros = 0
            if file_boq:
                st.session_state.n_ficheiros += 1
            if files_specs:
                st.session_state.n_ficheiros += len(files_specs)

            st.session_state.paginas_aviso = []

            st.success("✓ Contextos pré-carregados aplicados com sucesso!")
            return

        except Exception as e:
            st.error(f"Erro ao processar JSONs pré-carregados: {e}")
            return

    # Caso contrário, proceder com extração normal
    texto_boq = ""
    texto_specs = ""
    nomes_specs = []
    nome_boq = ""
    n_ficheiros = 0
    todas_paginas_sem_texto = []

    prog_slot = st.progress(0)
    status_slot = st.empty()

    if file_boq:
        n_ficheiros += 1
        nome_boq = file_boq.name
        texto_boq, sem_texto = read_document(file_boq)
        todas_paginas_sem_texto += [f"{file_boq.name} pág.{p}" for p in sem_texto]

    if files_specs:
        partes_specs = []
        for spec in files_specs:
            n_ficheiros += 1
            nomes_specs.append(spec.name)
            txt, sem_texto = read_document(spec)
            partes_specs.append(txt)
            todas_paginas_sem_texto += [f"{spec.name} pág.{p}" for p in sem_texto]
        texto_specs = "\n\n".join(partes_specs)

    if todas_paginas_sem_texto:
        aviso = ", ".join(todas_paginas_sem_texto[:10])
        extra = f" (+{len(todas_paginas_sem_texto)-10} mais)" if len(todas_paginas_sem_texto) > 10 else ""
        st.markdown(
            f'<div class="pdf-warning">⚠ Páginas sem texto detectadas (possível digitalização): '
            f"{aviso}{extra} — conteúdo não foi analisado.</div>",
            unsafe_allow_html=True,
        )

    st.session_state.pipeline_state = ["active", "idle", "idle"]
    pipeline_callback(st.session_state.pipeline_state)

    try:
        estado_inicial: AuditoriaState = {
            "texto_boq": texto_boq,
            "texto_specs": texto_specs,
            "guia_filtragem": guia_input,
            "nome_boq": nome_boq,
            "nomes_specs": nomes_specs,

            "resumo_boq": "",
            "resumo_specs": "",

            "auditoria_bruta": "",
            "auditoria_normalizada": "",
            "relatorio_final": "",

            "modo": "",
            "tentativas": 0,
            "erros": [],

            "n_ficheiros": n_ficheiros,
            "paginas_sem_texto": todas_paginas_sem_texto,

            "_api_key": api_key_final,
            "_prog_slot": prog_slot,
            "_status_slot": status_slot,
        }

        estado_final = dict(estado_inicial)

        for chunk in grafo_extracao.stream(
            estado_inicial,
            {"recursion_limit": 10},
            stream_mode="updates",
        ):
            for node_name, updates in chunk.items():
                estado_final.update(updates)

        prog_slot.empty()
        status_slot.empty()

        resumo_specs = estado_final.get("resumo_specs", "")
        resumo_boq = estado_final.get("resumo_boq", "")

        specs_json = _normalizar_json_ou_raw(resumo_specs, "AGT-01 Specs Context")
        boq_json = _normalizar_json_ou_raw(resumo_boq, "AGT-02 BOQ Context")

        specs_path = _persistir_contexto_json(
            "AGT01_Specs_Context_Latest.json",
            specs_json,
            app_file,
        )

        boq_path = _persistir_contexto_json(
            "AGT02_BOQ_Context_Latest.json",
            boq_json,
            app_file,
        )

        st.session_state.resumo_specs = specs_json
        st.session_state.resumo_boq = boq_json

        st.session_state.edited_specs_json = specs_json
        st.session_state.edited_boq_json = boq_json

        st.session_state.contextos_extraidos = True
        st.session_state.contextos_validados = True  # Após extração, já estão validados
        st.session_state.processado = False

        st.session_state.n_ficheiros = n_ficheiros
        st.session_state.paginas_aviso = todas_paginas_sem_texto

        st.success(
            f"Contextos extraídos e guardados:\n\n"
            f"- {specs_path.name}\n"
            f"- {boq_path.name}"
        )

    except Exception as e:
        prog_slot.empty()
        status_slot.empty()
        st.session_state.pipeline_state = ["error", "idle", "idle"]
        pipeline_callback(st.session_state.pipeline_state)
        st.error(f"Erro na extração de contextos: {e}")

def processar_auditoria_com_contextos_editados(
    grafo_auditoria,
    api_key_final: str,
    specs_json_editado: str,
    boq_json_editado: str,
    guia_input: str,
    app_file: Path,
    pipeline_callback: Callable[[list], None] = None,
    debug_mode: bool = False,
) -> None:
    """
    Passo 2:
    - recebe os JSONs já revistos/editados;
    - injeta diretamente em resumo_specs e resumo_boq;
    - corre auditoria, dedupe e relatório.
    """
    prog_slot = st.progress(0)
    status_slot = st.empty()

    status_slot.markdown(
        "<div style=\"font-family:'Space Mono',monospace;font-size:0.72rem;color:#3a6aaa\">"
        "<span style=\"color:#5a9aff\">Auditoria</span>"
        " &nbsp;·&nbsp; A usar JSONs editados...</div>",
        unsafe_allow_html=True,
    )

    try:
        # validar antes de enviar ao grafo
        json.loads(specs_json_editado)
        json.loads(boq_json_editado)

        estado_inicial: AuditoriaState = {
            "texto_boq": "",
            "texto_specs": "",
            "guia_filtragem": guia_input,
            "nome_boq": "BOQ_CONTEXT_EDITED",
            "nomes_specs": ["SPECS_CONTEXT_EDITED"],

            # aqui entram os JSONs editados
            "resumo_boq": boq_json_editado,
            "resumo_specs": specs_json_editado,

            "auditoria_bruta": "",
            "auditoria_normalizada": "",
            "relatorio_final": "",

            "modo": "CROSS",
            "tentativas": 0,
            "erros": [],

            "n_ficheiros": st.session_state.get("n_ficheiros", 0),
            "paginas_sem_texto": st.session_state.get("paginas_aviso", []),

            "_api_key": api_key_final,
            "_prog_slot": prog_slot,
            "_status_slot": status_slot,
        }

        estado_final = dict(estado_inicial)

        st.session_state.pipeline_state = ["done", "active", "idle"]
        pipeline_callback(st.session_state.pipeline_state)

        for chunk in grafo_auditoria.stream(
            estado_inicial,
            {"recursion_limit": 10},
            stream_mode="updates",
        ):
            for node_name, updates in chunk.items():
                estado_final.update(updates)

                if node_name == "auditar":
                    st.session_state.pipeline_state = ["done", "done", "active"]
                elif node_name == "dedupe":
                    st.session_state.pipeline_state = ["done", "done", "active"]
                elif node_name == "formatar":
                    st.session_state.pipeline_state = ["done", "done", "done"]

                pipeline_callback(st.session_state.pipeline_state)

        prog_slot.empty()
        status_slot.empty()

        relatorio = estado_final.get("relatorio_final", "")
        erros = estado_final.get("erros", [])
        tentativas = estado_final.get("tentativas", 0)

        if relatorio and len(relatorio.strip()) >= 100:
            st.session_state.relatorio_final = relatorio
            st.session_state.auditoria_bruta = estado_final.get("auditoria_bruta", "")
            st.session_state.auditoria_normalizada = estado_final.get("auditoria_normalizada", "")
            st.session_state.processado = True
            st.session_state.erros_sessao = erros

            fases = len(re.findall(r"(?im)^\s*\*{0,2}phase\s*\d*\s*[:\-–]", relatorio))
            st.session_state.n_fases_hint = fases if fases else "—"

            _persistir_relatorio(relatorio, app_file)

            if erros:
                st.warning(f"⚠ Auditoria concluída com {len(erros)} aviso(s): {'; '.join(erros)}")
            if tentativas > 1:
                st.info(f"ℹ Auditoria precisou de {tentativas} tentativa(s).")

        else:
            msg_erro = "; ".join(erros) if erros else "Output insuficiente após auditoria."
            st.error(f"Erro Crítico no Pipeline: {msg_erro}")

    except Exception as e:
        prog_slot.empty()
        status_slot.empty()
        st.session_state.pipeline_state = ["done", "error", "idle"]
        pipeline_callback(st.session_state.pipeline_state)
        st.error(f"Erro na auditoria com JSONs editados: {e}")

def processar_auditoria(
    grafo_auditoria,
    api_key_final: str,
    file_boq,
    files_specs,
    guia_input: str,
    app_file: Path,
    pipeline_callback: Callable[[list], None] = None,
    debug_mode: bool = False,
) -> None:
    texto_boq = ""
    texto_specs = ""
    nomes_specs = []
    nome_boq = ""
    n_ficheiros = 0
    todas_paginas_sem_texto = []

    prog_slot = st.progress(0)
    status_slot = st.empty()

    if file_boq:
        n_ficheiros += 1
        nome_boq = file_boq.name
        texto_boq, sem_texto = read_document(file_boq)
        todas_paginas_sem_texto += [f"{file_boq.name} pág.{p}" for p in sem_texto]

    if files_specs:
        partes_specs = []
        for spec in files_specs:
            n_ficheiros += 1
            nomes_specs.append(spec.name)
            txt, sem_texto = read_document(spec)
            partes_specs.append(txt)
            todas_paginas_sem_texto += [f"{spec.name} pág.{p}" for p in sem_texto]
        texto_specs = "\n\n".join(partes_specs)

    if todas_paginas_sem_texto:
        aviso = ", ".join(todas_paginas_sem_texto[:10])
        extra = f" (+{len(todas_paginas_sem_texto)-10} mais)" if len(todas_paginas_sem_texto) > 10 else ""
        st.markdown(
            f'<div class="pdf-warning">⚠ Páginas sem texto detectadas (possível digitalização): '
            f"{aviso}{extra} — conteúdo não foi analisado.</div>",
            unsafe_allow_html=True,
        )

    st.session_state.pipeline_state = ["active", "idle", "idle"]
    pipeline_callback(st.session_state.pipeline_state)

    try:
        estado_inicial: AuditoriaState = {
            "texto_boq": texto_boq,
            "texto_specs": texto_specs,
            "guia_filtragem": guia_input,
            "nome_boq": nome_boq,
            "nomes_specs": nomes_specs,
            "resumo_boq": "",
            "resumo_specs": "",
            "auditoria_bruta": "",
            "relatorio_final": "",
            "modo": "",
            "tentativas": 0,
            "erros": [],
            "n_ficheiros": n_ficheiros,
            "paginas_sem_texto": todas_paginas_sem_texto,
            "_api_key": api_key_final,
            "_prog_slot": prog_slot,
            "_status_slot": status_slot,
        }

        estado_final = dict(estado_inicial)

        debug_container = None
        if debug_mode:
            debug_container = st.container()

        for chunk in grafo_auditoria.stream(estado_inicial, {"recursion_limit": 10}, stream_mode="updates"):
            for node_name, updates in chunk.items():
                estado_final.update(updates)
                st.session_state.pipeline_state = _pipeline_state_from_node(node_name, estado_final)
                pipeline_callback(st.session_state.pipeline_state)

                # Debug output condicional
                if debug_mode and debug_container:
                    if node_name == "extrair":
                        resumo_boq = estado_final.get("resumo_boq", "")
                        resumo_specs = estado_final.get("resumo_specs", "")
                        with debug_container.expander("🔍 Output AGT-01 (Extrator)"):
                            if resumo_boq:
                                st.markdown("**BOQ Summary:**")
                                st.text(resumo_boq[:500] + "..." if len(resumo_boq) > 500 else resumo_boq)
                            if resumo_specs:
                                st.markdown("**Specs Summary:**")
                                st.text(resumo_specs[:500] + "..." if len(resumo_specs) > 500 else resumo_specs)

                    elif node_name == "auditar":
                        auditoria_bruta = estado_final.get("auditoria_bruta", "")
                        with debug_container.expander("🧠 Output AGT-02 (Auditor)"):
                            if auditoria_bruta:
                                st.text(auditoria_bruta[:800] + "..." if len(auditoria_bruta) > 800 else auditoria_bruta)
                            else:
                                st.markdown("*Sem output ainda...*")

        prog_slot.empty()
        status_slot.empty()

        relatorio = estado_final.get("relatorio_final", "")
        erros = estado_final.get("erros", [])
        tentativas = estado_final.get("tentativas", 0)

        if relatorio and len(relatorio.strip()) >= 100:
            st.session_state.pipeline_state = ["done", "done", "done"]
            pipeline_callback(st.session_state.pipeline_state)

            st.session_state.relatorio_final = relatorio
            st.session_state.resumo_specs = estado_final.get("resumo_specs", "")
            st.session_state.processado = True
            st.session_state.n_ficheiros = n_ficheiros
            st.session_state.erros_sessao = erros
            st.session_state.paginas_aviso = todas_paginas_sem_texto

            fases = len(re.findall(r"(?im)^\s*\*{0,2}phase\s*\d*\s*[:\-–]", relatorio))
            st.session_state.n_fases_hint = fases if fases else "—"

            _persistir_relatorio(relatorio, app_file)

            if erros:
                st.warning(f"⚠ Auditoria concluída com {len(erros)} aviso(s): {'; '.join(erros)}")
            if tentativas > 1:
                st.info(f"ℹ AGT-02 precisou de {tentativas} tentativa(s) para produzir output válido.")

        else:
            st.session_state.pipeline_state = ["error", "error", "error"]
            pipeline_callback(st.session_state.pipeline_state)
            msg_erro = "; ".join(erros) if erros else "Output insuficiente após tentativas máximas."
            st.error(f"Erro Crítico no Pipeline: {msg_erro}")

    except Exception as e:
        prog_slot.empty()
        status_slot.empty()
        st.session_state.pipeline_state = ["error", "error", "error"]
        pipeline_callback(st.session_state.pipeline_state)
        st.error(f"Erro Crítico: {e}")
