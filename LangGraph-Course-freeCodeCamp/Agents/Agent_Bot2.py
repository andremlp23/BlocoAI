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
    global loaded_file_text, loaded_file_name
    line = line.strip()

    if line.startswith("/load "):
        parts = shlex.split(line)
        path = Path(parts[1])
        # LER TUDO - SEM FILTROS
        loaded_file_text = read_excel_smart(path) 
        loaded_file_name = path.name
        print(f"\nFicheiro carregado: {loaded_file_name}. Total de caracteres: {len(loaded_file_text)}")

    elif line.startswith("/ask "):
        if not loaded_file_text: return
        
        # DIVIDIR EM BLOCOS DE TEXTO PURO (ex: 3000 chars cada)
        tamanho_chunk = 3000 
        chunks = [loaded_file_text[i:i + tamanho_chunk] for i in range(0, len(loaded_file_text), tamanho_chunk)]
        
        notas_recolhidas = []
        print(f"\nVARREDURA TOTAL: A processar {len(chunks)} blocos de texto integral... ⚙️")

        for i, chunk in enumerate(chunks):
            print(f"  [{i+1}/{len(chunks)}] A ler tudo...")
            
            prompt_bloco = (
                "Age como um perito em revisão de cadernos de encargos.\n"
                "Lê o extrato de Excel abaixo e extrai TODOS os detalhes técnicos: "
                "normas, materiais, espessuras, tratamentos, parafusos, exigências de soldadura e logística.\n"
                "NÃO ignores nada que pareça uma especificação.\n"
                "Se não houver nada técnico, responde 'NADA'.\n\n"
                f"TEXTO:\n{chunk}"
            )
            
            res = llm.invoke([HumanMessage(content=prompt_bloco)])
            if "nada" not in res.content.lower():
                notas_recolhidas.append(res.content)

        # CONSOLIDAÇÃO FINAL
        print("\nA gerar Relatório Final de Alta Precisão... ⚙️")
        prompt_final = (
            "Com base em TODA a leitura do documento (notas abaixo), cria um relatório técnico exaustivo.\n"
            "Sê específico. Se mencionarem espessuras, marcas ou normas EN, inclui-as.\n\n"
            "NOTAS TÉCNICAS:\n" + "\n---\n".join(notas_recolhidas)
        )
        
        relatorio = llm.invoke([HumanMessage(content=prompt_final)])
        print("\n" + "="*80)
        print(relatorio.content)
        print("="*80)

        
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