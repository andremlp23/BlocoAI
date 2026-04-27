import shlex
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

# ============================================================
# 1. CONFIGURAÇÃO DO MODELO (Na tua Torre)
# ============================================================
llm = ChatOllama(
    model="qwen3.5:9b",
    base_url="http://100.105.95.121:11434",
    temperature=0 
)

# ============================================================
# 2. FUNÇÕES DE LEITURA E FILTRAGEM (Matriz Completa)
# ============================================================
def read_excel_smart(file_path: Path) -> str:
    xls = pd.ExcelFile(file_path)
    text_lines = []
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        cells = df.values.flatten()
        for cell in cells:
            val = str(cell).strip()
            if val.lower() == 'nan' or len(val) < 4: continue
            if val.replace('.', '', 1).isdigit(): continue
            text_lines.append(val)
    return "\n".join(list(dict.fromkeys(text_lines)))

def filtrar_linhas_tecnicas(texto_bruto: str) -> List[str]:
    palavras_chave = [
        "exc", "en 1090", "toleranc", "welding", "soldadura", "fabrication",
        "steel", "grade", "s235", "s275", "s355", "s460", "jr", "j0", "j2",
        "bolt", "fastener", "screw", "en 14399", "8.8", "10.9", "anchor", "chumbad", "grout",
        "paint", "corros", "galvaniz", "zinc", "fire", "intumescent", "flocage", "r30", "r60", "r120",
        "decking", "colaborante", "grating", "gradil", "steplarm", "purlin", "madre", "cladding", "roof",
        "facade", "smoke", "desenfumagem", "polycarbonate", "incoterm", "exw", "fca", "fob", "dap", "ddp"
    ]
    linhas = texto_bruto.split("\n")
    return [l for l in linhas if any(kw in l.lower() for kw in palavras_chave)]

# ============================================================
# 3. LÓGICA DE PROCESSAMENTO
# ============================================================
loaded_file_lines = [] # Guardamos a lista de linhas filtradas
loaded_file_name = None

def handle_line(line: str):
    global loaded_file_lines, loaded_file_name
    line = line.strip()

    if line.startswith("/load "):
        parts = shlex.split(line)
        path = Path(parts[1])
        print(f"\nA ler 2200 linhas de {path.name}... ⚙️")
        
        raw_text = read_excel_smart(path)
        loaded_file_lines = filtrar_linhas_tecnicas(raw_text)
        loaded_file_name = path.name
        print(f"Ficheiro carregado. Encontradas {len(loaded_file_lines)} linhas com relevância técnica. ✅")

    elif line.startswith("/ask "):
        if not loaded_file_lines:
            print("Erro: Carrega um ficheiro primeiro com /load.")
            return
        
        # --- PASSO 1: ANÁLISE POR BLOCOS (Para não estoirar a memória) ---
        tamanho_bloco = 35 
        blocos = [loaded_file_lines[i:i + tamanho_bloco] for i in range(0, len(loaded_file_lines), tamanho_bloco)]
        
        notas_recolhidas = []
        print(f"\nA analisar documento em {len(blocos)} partes na torre... ⚙️")

        for i, bloco in enumerate(blocos):
            print(f"  [{i+1}/{len(blocos)}] A extrair dados técnicos...")
            contexto = "\n".join(bloco)
            
            prompt_bloco = (
                "Extrai apenas factos técnicos (materiais, normas, fogo, aço, parafusos, logística) deste excerto.\n"
                "Se não houver nada relevante, responde 'NADA'.\n\n"
                f"EXCERTO:\n{contexto}"
            )
            
            res = llm.invoke([HumanMessage(content=prompt_bloco)])
            if "nada" not in res.content.lower():
                notas_recolhidas.append(res.content)

        # --- PASSO 2: RELATÓRIO FINAL BASEADO NA TUA MATRIZ ---
        print("\nA consolidar relatório final... ⚙️")
        
        prompt_final = (
            "Age como um Engenheiro Especialista. Com base nas notas recolhidas, cria um relatório técnico "
            "seguindo rigorosamente estas categorias da nossa matriz de verificação:\n\n"
            "1. CLASSE DE EXECUÇÃO E TOLERÂNCIAS\n"
            "2. MATERIAL DE BASE (Grades, Origem, Normas)\n"
            "3. PARAFUSOS E CHUMBADOUROS (Classes, Grout, Fixações)\n"
            "4. PROTEÇÃO ANTICORROSIVA E FOGO (Pintura, Galvanização, Minutos R)\n"
            "5. ELEMENTOS DE CONSTRUÇÃO E ENVOLVENTE (Decking, Gradis, Fachada, Madres)\n"
            "6. LOGÍSTICA (Incoterms)\n\n"
            "NOTAS RECOLHIDAS DO EXCEL:\n" + "\n---\n".join(notas_recolhidas)
        )
        
        try:
            relatorio = llm.invoke([HumanMessage(content=prompt_final)])
            print("\n" + "="*70)
            print(f"📄 RELATÓRIO TÉCNICO FINAL: {loaded_file_name}")
            print("="*70)
            print(relatorio.content)
            print("="*70 + "\n")
        except Exception as e:
            print(f"Erro na consolidação: {e}")

# ============================================================
# 4. CICLO DE EXECUÇÃO
# ============================================================
print("--- SISTEMA DE ANÁLISE DE CADERNO DE ENCARGOS ---")
print("Comandos: /load 'caminho' | /ask 'pergunta' | exit")

while True:
    raw = input("Enter: ")
    if raw.strip().lower() == "exit": break
    try:
        handle_line(raw)
    except Exception as e:
        print(f"Erro: {e}")