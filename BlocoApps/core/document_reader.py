import io

import pandas as pd
import pdfplumber
import json
import os
import concurrent.futures

RUIDO = {
    "nan",
    "none",
    "0.0",
    "0",
    "",
    "n/a",
    "tbd",
    "tbc",
    "-",
    "--",
    "---",
    "#n/a",
    "#ref!",
    "#value!",
    "#name?",
}


def read_document(file) -> tuple[str, list]:
    """Lê Excel ou PDF. Devolve (texto, paginas_sem_texto)."""
    paginas_sem_texto = []

    if file.name.lower().endswith(".pdf"):
        partes = []
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for i, p in enumerate(pdf.pages):
                texto_pag = p.extract_text(layout=True)
                if texto_pag:
                    partes.append(f"[Pág: {i+1}] {texto_pag}")
                else:
                    paginas_sem_texto.append(i + 1)
        return "\n".join(partes), paginas_sem_texto

    xls = pd.ExcelFile(file)
    lines = []
    for sheet in xls.sheet_names:
        df = xls.parse(sheet).astype(str)
        for idx, row in df.iterrows():
            vals = [v.strip() for v in row if v.strip().lower() not in RUIDO and len(v.strip()) > 1]
            if len(vals) > 1:
                lines.append(f"[Linha: {idx+2}] {' | '.join(vals)}")
    return "\n".join(lines), []

# Carregar o JSON do disco (ajusta o caminho se o ficheiro estiver noutra pasta)
def carregar_regras_json():
    caminho_json = os.path.join(os.path.dirname(os.path.dirname(__file__)), "RegrasMekkin.json")
    
    fallback = {
        "regra_final": "Assumir que toda a informacao e IRRELEVANTE ate demonstrar impacto na estrutura.",
        "ignorar_estritamente": ["Arquitetura", "Cores", "AVAC sem carga", "Betão sem interface"]
    }
    
    if os.path.exists(caminho_json):
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.dumps(json.load(f), ensure_ascii=False, indent=2)
    return json.dumps(fallback, ensure_ascii=False, indent=2)

