import io
from docx import Document

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
    if file.name.lower().endswith(('.docx')):
        # Lógica para ler documentos .docx  
        partes = []
        try:
            doc = Document(io.BytesIO(file.read()))
            
            # Extrair parágrafos
            para_num = 0
            for para in doc.paragraphs:
                texto = para.text.strip()
                if texto:  # Ignorar parágrafos vazios
                    para_num += 1
                    partes.append(f"[Parágrafo: {para_num}] {texto}")
            
            # Extrair tabelas
            if doc.tables:
                partes.append("\n[TABELAS DO DOCUMENTO]\n")
                for table_idx, table in enumerate(doc.tables, 1):
                    partes.append(f"\n[Tabela: {table_idx}]")
                    for row_idx, row in enumerate(table.rows, 1):
                        cells_text = []
                        for cell in row.cells:
                            cell_text = cell.text.strip()
                            if cell_text.lower() not in RUIDO and cell_text:
                                cells_text.append(cell_text)
                        if cells_text:
                            partes.append(f"  [Linha {row_idx}] {' | '.join(cells_text)}")
            
            return "\n".join(partes), []
        except Exception as e:
            return f"[Erro a ler DOCX: {str(e)}]", []
    else:
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

