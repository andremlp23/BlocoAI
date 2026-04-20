import re
from datetime import datetime
from pathlib import Path
from typing import Callable

import streamlit as st

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


def processar_auditoria(
    grafo_auditoria,
    api_key_final: str,
    file_boq,
    files_specs,
    guia_input: str,
    app_file: Path,
    pipeline_callback: Callable[[list], None] = None,
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

        for chunk in grafo_auditoria.stream(estado_inicial, {"recursion_limit": 10}, stream_mode="updates"):
            for node_name, updates in chunk.items():
                estado_final.update(updates)
                st.session_state.pipeline_state = _pipeline_state_from_node(node_name, estado_final)
                pipeline_callback(st.session_state.pipeline_state)

        prog_slot.empty()
        status_slot.empty()

        relatorio = estado_final.get("relatorio_final", "")
        erros = estado_final.get("erros", [])
        tentativas = estado_final.get("tentativas", 0)

        if relatorio and len(relatorio.strip()) >= 100:
            st.session_state.pipeline_state = ["done", "done", "done"]
            pipeline_callback(st.session_state.pipeline_state)

            st.session_state.relatorio_final = relatorio
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
