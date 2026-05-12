# BlocoAI - Master Cross-Audit

Sistema académico para extração, auditoria e estruturação de documentação técnica de construção civil (Aço mais especificamente), arquitetura criada com LangGraph e interface Streamlit.
Desenvolvido em parceria com a empresa Mekkin.

## 1. Enquadramento

Este projeto foi desenvolvido no contexto de Projeto Informático para apoiar uma tarefa real de engenharia documental:  

- ler documentos de Especificações Técnicas (SPECS)
- ler documento BOQ (Bill of Quantities)
- comparar os dois contextos
- produzir um relatório estruturado de auditoria técnica

O foco é **consistência técnica e rastreabilidade de requisitos**, não estimativa comercial.

## 2. Objetivos do projeto

- Automatizar a extração de requisitos técnicos a partir de documentos heterogéneos.
- Identificar alinhamentos, conflitos e lacunas entre SPECS e BOQ.
- Reduzir ruído (quantidades, preços, dados comerciais) para centrar a análise no conteúdo técnico.
- Gerar saída consolidada para suporte a revisão técnica/académica.

## 3. Funcionalidades principais

- Upload de:
  - BOQ em `.csv`
  - SPECS em `.pdf` e `.docx`
- Definição de **Project Baseline JSON** (colado ou carregado).
- Extração automática por agentes (LangGraph).
- Auditoria automática em sequência após extração.
- Relatório final visual + download `.txt`.
- Guarda de histórico de auditorias com timestamp em `historico_auditorias/`.
- Aviso de páginas PDF sem texto extraível (ex.: digitalizações).

## 4. Arquitetura técnica

Aplicação organizada em camadas simples:

- Interface: Streamlit (`BlocoApps/ui/`)
- Leitura de documentos: parsers para PDF/DOCX/CSV (`BlocoApps/core/document_reader.py`)
- Motor de agentes: nós e grafos LangGraph (`BlocoApps/core/langgraph_engine.py`)
- Orquestração de execução: pipeline extração + auditoria (`BlocoApps/core/orchestrator.py`)

### Fluxo resumido

1. Entrada de baseline + documentos.
2. Extração de contexto SPECS e BOQ.
3. Auditoria técnica cruzada.
4. Normalização/format final do relatório.
5. Apresentação e persistência no histórico.

## 5. Estrutura de pastas relevante

```text
BlocoApps/
  app.py
  RegrasMekkin.json
  requirements.txt
  core/
    document_reader.py
    langgraph_engine.py
    orchestrator.py
  ui/
    components.py
    styles.py
contextos_editaveis/
historico_auditorias/
Docs/
```

## 6. Requisitos

- Linux (testado neste ambiente)
- Python 3.10+
- Chave de API para modelo compatível (OpenAI/OpenRouter)

Dependências Python em `BlocoApps/requirements.txt`.

## 7. Instalação e execução

Na raiz do projeto:

```bash
cd BlocoApps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Iniciar a aplicação:

```bash
streamlit run app.py
```

## 8. Configuração de API

A app aceita chave via barra lateral ou variáveis de ambiente:

- `CHATGPT_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`

Exemplo com `.env` em `BlocoApps/.env` (ou na pasta acima):

```env
OPENAI_API_KEY=sk-...
```

## 9. Como usar (roteiro curto)

1. Abrir a app em Streamlit.
2. Inserir API key (ou garantir variável de ambiente configurada).
3. Fornecer `Project Baseline JSON`.
4. Carregar 1 BOQ (`.csv`) e os SPECS (`.pdf`/`.docx`).
5. (Opcional) ajustar instruções de filtragem.
6. Clicar em **Iniciar Extração Completa**.
7. Ler relatório final e descarregar `.txt`.

## 10. Dados de saída

- Estado em sessão (Streamlit session state).
- Relatório final visível na UI.
- Download manual do relatório (`BlocoAI_Relatorio.txt`).
- Histórico automático em `historico_auditorias/Auditoria_YYYYMMDD_HHMM.txt`.

## 11. Limitações atuais

- Dependência de qualidade de OCR/texto nos PDFs (páginas imagem podem ficar fora da análise).
- Forte dependência da qualidade do BOQ em CSV e da baseline fornecida.
- Custos/latência de API variam com dimensão dos documentos.
- Projeto orientado a protótipo académico; não substitui validação técnica humana.

## 12. Contexto académico

Este repositório privilegia:

- clareza metodológica
- experimentação com agentes e grafos de execução
- documentação de evolução (`Docs/CHANGELOG.md`)
- reprodutibilidade mínima de execução

---

Se necessário, este README pode ser complementado com uma secção de avaliação experimental (métricas, casos de teste e critérios de validação) para entrega formal da unidade curricular.
