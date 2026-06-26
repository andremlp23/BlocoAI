# BlocoAI - Sistema Inteligente de Extração e Auditoria de Documentos de Construção

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Visão Geral

**BlocoAI** é um sistema automatizado e inteligente de extração, auditoria e estruturação de documentos de construção civil. Utiliza modelos de linguagem generativos (LLMs) orquestrados em fluxos de grafo (LangGraph) para processar **Especificações Técnicas (SPECS)** e **Documentos de Orçamento (BOQ)**, extraindo informação técnica, realizando auditorias cruzadas e estruturando dados em formato otimizado para análise de custos.

### Problema Resolvido

- **Antes**: Processamento manual de documentos heterogéneos, erro-prone e moroso
- **Depois**: Extração automatizada, auditoria cruzada e estruturação em Trade Packages

---

## Funcionalidades Principais

### 1. **Extração Inteligente de Dados**
   - Extrai especificações técnicas de documentos SPECS (normas, materiais, tolerâncias, acabamentos)
   - Extrai estrutura de fases, zonas e atividades de documentos BOQ
   - Filtra e descarta informação não técnica

### 2. **Auditoria Cruzada**
   - Compara requisitos de SPECS com informação de BOQ
   - Identifica alinhamentos, conflitos e lacunas
   - Classifica status: **ALIGNED** | **CONFLICT** | **MISSING BASELINE**

### 3. **Normalização e Deduplicação**
   - Elimina duplicação de requisitos técnicos
   - Consolida informação repetida entre categorias
   - Mantém rastreabilidade até à fonte original

### 4. **Geração de Relatório Final**
   - Organiza os resultados da auditoria em formato legível
   - Agrupa a informação por categorias técnicas relevantes:
     - Aço Estrutural
     - Deck Composto
     - Proteção contra Fogo
     - Proteção Anticorrosiva
     - Elementos Metálicos Secundários
   - Destaca inconsistências, omissões e ambiguidades

### 5. **Interface Intuitiva**
   - Dashboard Streamlit para upload e processamento
   - Visualização de resultados em tempo real
   - Exportação em múltiplos formatos

---

## Arquitetura

```
┌─────────────────────────────────────────┐
│     Interface Utilizador (Streamlit)     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│      Camada de Orquestração             │
│   (Orchestrator + LangGraph Engine)     │
└──────────────────┬──────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
┌────▼────┐  ┌────▼────┐  ┌────▼────┐
│ Document│  │ LangGraph│  │  LLM   │
│ Reader  │  │ Agents   │  │(OpenAI)│
└────┬────┘  └────┬────┘  └────┬────┘
     │             │             │
┌────▼─────────────▼─────────────▼────┐
│   Processamento de Dados            │
│  (Extração, Auditoria, Estruturação)│
└─────────────────────────────────────┘
```

### Agentes Especializados

| Agente | Função | Responsabilidade |
|--------|--------|-----------------|
| **AGT-01** | Extração de SPECS | Lê os documentos de especificações técnicas e extrai requisitos relevantes, como normas, materiais, classes de execução, sistemas de proteção, tolerâncias, requisitos de inspeção e elementos de controlo de qualidade. Ignora informação fora do âmbito definido, como betão, e devolve uma base técnica estruturada. |
| **AGT-02** | Extração de BOQ | Analisa o mapa de quantidades, identifica fases, zonas, subzonas, atividades e categorias técnicas relevantes. Filtra informação comercial ou puramente quantitativa quando não contribui para a auditoria e organiza o BOQ de forma estruturada para comparação posterior. |
| **AGT-03** | Auditoria Técnica | Compara a informação extraída das SPECS com a informação extraída do BOQ. Identifica alinhamentos, conflitos, omissões, ambiguidades e requisitos sem correspondência, preservando o contexto de fase, zona e subzona. |
| **AGT-04** | Deduplicação e Normalização | Remove requisitos repetidos, consolida informação redundante entre categorias técnicas e aplica uma organização canónica aos resultados. Garante que cada requisito aparece apenas uma vez no relatório sempre que possível. |
| **AGT-05** | Apresentação Final | Transforma a auditoria normalizada num relatório final legível para o utilizador. Organiza a informação por categorias técnicas, destaca inconsistências globais e prepara a saída final para validação humana. |

---

## Estrutura de Projeto

```
BlocoAI/
├── README.md                          # Este ficheiro
├── SETUP.md                           # Instruções de instalação
├── CHANGELOG.md                       # Histórico de versões
│
├── src/                               # Código-fonte principal
│   ├── app.py                         # Aplicação principal (Streamlit)
│   ├── requirements.txt               # Dependências Python
│   │
│   ├── core/                          # Lógica central
│   │   ├── __init__.py
│   │   ├── document_reader.py         # Leitura de PDFs e DOCX
│   │   ├── langgraph_engine.py        # Motor de orquestração (LangGraph)
│   │   └── orchestrator.py            # Orquestrador de processos
│   │
│   └── ui/                            # Interface Streamlit
│       ├── __init__.py
│       ├── components.py              # Componentes reutilizáveis
│       └── styles.py                  # Estilos CSS/Streamlit
│
├── data/                              # Dados do projeto
│   ├── contexts/                      # Contextos editáveis
│   │   ├── AGT01_Specs_Context_Latest.json
│   │   └── AGT02_BOQ_Context_Latest.json
│   │
│   ├── rules/                         # Regras de negócio
│   │   └── RegrasMekkin.json
│   │
│   └── uploads/                       # Uploads de utilizadores (documentos)
│
├── docs/                              # Documentação
│   ├── ai_project_v2.html             # Documentação técnica HTML
│   ├── CHANGELOG.md                   # Histórico de alterações
│   ├── CONTRIBUTING.md                # Guia de contribuição
│   └── Relatório/                     # Relatórios do projeto
│
├── audit/                             # Histórico de auditorias
│   └── historico_auditorias/          # Registos de execução
│
├── examples/                          # Exemplos de utilização
│   └── sample_documents/              # Documentos de exemplo
│
│
└── .env.example                       # Configuração de ambiente (template)
```

---

## Instalação Rápida

### Pré-requisitos
- Python 3.9+
- pip ou conda
- Chave API OpenAI (para LLM)

### Passos

1. **Clone ou descarregue o projeto**
   ```bash
   cd BlocoAI
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # ou
   venv\Scripts\activate  # Windows
   ```

3. **Instale dependências**
   ```bash
   cd src
   pip install -r requirements.txt
   ```

4. **Configure variáveis de ambiente**
   ```bash
   # Copie o template
   cp .env.example .env
   
   # Edite e adicione:
   OPENAI_API_KEY=sk_...
   ```

5. **Inicie a aplicação**
   ```bash
   streamlit run app.py
   ```

A aplicação abrirá em `http://localhost:8501`

---


## Configuração Avançada

### Variáveis de Ambiente

Edite `.env` para configurar:

```bash
# OpenAI
OPENAI_API_KEY=sk_...
OPENAI_MODEL=gpt-4

# Aplicação
STREAMLIT_SERVER_PORT=8501
DEBUG_MODE=false

# Contextos
CONTEXT_SPECS_PATH=data/contexts/AGT01_Specs_Context_Latest.json
CONTEXT_BOQ_PATH=data/contexts/AGT02_BOQ_Context_Latest.json

# Regras de Negócio
RULES_PATH=data/rules/RegrasMekkin.json
```

## Documentação Adicional

- [Instruções de Setup](SETUP.md)


## Autores

Desenvolvido como projeto académico - Projeto Informático 25/26

André Miguel Lourenço Pereira
Diogo Alexandre Lopes Barroso

---


