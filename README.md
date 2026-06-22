# BlocoAI - Sistema Inteligente de Extração e Auditoria de Documentos de Construção

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Visão Geral

**BlocoAI** é um sistema automatizado e inteligente de extração, auditoria e estruturação de documentos de construção civil. Utiliza modelos de linguagem generativos (LLMs) orquestrados em fluxos de grafo (LangGraph) para processar **Especificações Técnicas (SPECS)** e **Documentos de Orçamento (BOQ)**, extraindo informação técnica, realizando auditorias cruzadas e estruturando dados em formato otimizado para análise de custos.

### Problema Resolvido

- ❌ **Antes**: Processamento manual de documentos heterogéneos, erro-prone e moroso
- ✅ **Depois**: Extração automatizada, auditoria cruzada e estruturação em Trade Packages

---

## 🎯 Funcionalidades Principais

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
   - Atribui cada requisito a categoria única (propriedade exclusiva)
   - Mantém rastreabilidade até à fonte original

### 4. **Estruturação em Trade Packages**
   - Transforma dados de formato baseado em localização para formato de disciplinas
   - Gera relatórios por Trade Package:
     - Aço Estrutural
     - Deck Composto
     - Proteção de Fogo
     - Proteção de Corrosão
     - Metalizações

### 5. **Interface Intuitiva**
   - Dashboard Streamlit para upload e processamento
   - Visualização de resultados em tempo real
   - Exportação em múltiplos formatos

---

## 🏗️ Arquitetura

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
| **AGT-01** | Extração SPECS | Extrai requisitos técnicos de especificações |
| **AGT-02** | Extração BOQ | Extrai estrutura de fases e atividades |
| **AGT-03** | Auditoria | Auditoria cruzada e validação |
| **AGT-04** | Estruturação | Pivota dados em Trade Packages |

---

## 📁 Estrutura de Projeto

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
├── old/                               # Código legado/descontinuado
│   └── *.py                           # Versões anteriores
│
└── .env.example                       # Configuração de ambiente (template)
```

---

## 🚀 Instalação Rápida

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

## 📖 Guia de Utilização

### 1. Upload de Documentos

1. Aceda a **"📤 Upload de Documentos"** na barra lateral
2. Seleccione ficheiros (PDF ou DOCX):
   - **Especificações Técnicas (SPECS)**
   - **Documentos de Orçamento (BOQ)**
3. Clique em **"Processar Documentos"**

### 2. Extração de Dados

- O sistema extrai automaticamente requisitos técnicos
- Resultados aparecem em tempo real
- Dados são armazenados em contextos JSON editáveis

### 3. Auditoria Cruzada

- Compare SPECS com BOQ
- Visualize alinhamentos e conflitos
- Identifique lacunas de informação

### 4. Estruturação em Trade Packages

- Dados são pivotados por disciplina
- Gere relatórios executivos
- Exporte para análise de custos

### 5. Exportação de Resultados

- **Excel**: Para análise em PowerBI/Tableau
- **JSON**: Para integração com sistemas externos
- **PDF**: Para relatórios executivos

---

## ⚙️ Configuração Avançada

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

### Personalizar Contextos

Os ficheiros JSON em `data/contexts/` definem o comportamento dos agentes:

```json
{
  "agent": "AGT-01",
  "purpose": "Extração de Especificações Técnicas",
  "rules": [...],
  "output_schema": {...}
}
```

**Edite estes ficheiros para ajustar extrações e auditorias.**

---

## 🔍 Estrutura de Saídas

### Extração (AGT-01, AGT-02)

```json
{
  "status": "SUCCESS",
  "timestamp": "2026-06-22T10:30:00Z",
  "document_type": "SPECS",
  "requirements": [
    {
      "id": "REQ-001",
      "category": "Aço Estrutural",
      "requirement": "Norma ISO ...",
      "source": "pagina_5"
    }
  ]
}
```

### Auditoria (AGT-03)

```json
{
  "audit_result": "CONFLICT",
  "specs_requirement": "REQ-001",
  "boq_alignment": "NOT_FOUND",
  "severity": "HIGH",
  "message": "Especificação não encontrada no BOQ"
}
```

### Estruturação (AGT-04)

```json
{
  "trade_package": "Aço Estrutural",
  "requirements": [...],
  "summary": {...}
}
```

---

## 🧪 Desenvolvimento

### Executar Testes

```bash
pytest tests/ -v
```

### Adicionar Novo Agente

1. Crie novo contexto em `data/contexts/AGT0X_*.json`
2. Implemente lógica em `core/langgraph_engine.py`
3. Registe em `core/orchestrator.py`

### Debug Mode

Ative em `.env`:
```bash
DEBUG_MODE=true
```

Aparecem informações detalhadas nos logs e interface.

---

## 📊 Casos de Uso

### 1. Validação de Conformidade
- Verificar se BOQ cobre todos os requisitos SPECS
- Identificar desvios de escopo

### 2. Estimating Assistido
- Estruturar dados para análise de custos
- Gerar relatórios por disciplina

### 3. Gestão de Riscos
- Identificar conflitos e lacunas
- Documentar inconsistências

### 4. Auditoria Técnica
- Comparar documentos históricos
- Validar conformidade com normas

---

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY not set"
```bash
# Adicione a chave ao .env
echo "OPENAI_API_KEY=sk_..." >> .env
```

### Erro: "PDF não consegue ser lido"
- Verifique se o PDF não é protegido por password
- Tente converter para DOCX via Word

### Interface lenta
- Verifique conexão à internet (chamadas API)
- Reduza tamanho de documentos
- Ative Debug para identificar gargalos

---

## 📚 Documentação Adicional

- [Instruções de Setup](SETUP.md)
- [Changelog](docs/CHANGELOG.md)
- [Guia de Contribuição](docs/CONTRIBUTING.md)
- [Especificação Técnica](docs/ai_project_v2.html)

---

## 📝 Relatórios Disponíveis

- `docs/RELATORIO_DESENVOLVIMENTO_BlocoAI.txt` - Relatório de desenvolvimento
- `docs/RESPOSTAS_CRITICAS_BlocoAI.txt` - Análise de questões críticas
- `docs/Relatório/` - Pasta com relatórios adicionais

---

## 👥 Autores

Desenvolvido como projeto académico - Projeto Informático 2S

---

## 📄 Licença

Este projeto está sob licença MIT. Veja [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](docs/CONTRIBUTING.md) para guidelines.

---

## 🎓 Citação

Se usar este projeto em investigação ou trabalho académico:

```bibtex
@software{blocoai2026,
  title={BlocoAI: Sistema Inteligente de Extração e Auditoria de Documentos de Construção},
  author={Autor},
  year={2026},
  url={https://github.com/...}
}
```

---

## ⭐ Status do Projeto

- ✅ Extração de Especificações
- ✅ Extração de BOQ
- ✅ Auditoria Cruzada
- ✅ Deduplicação
- ✅ Estruturação em Trade Packages
- ✅ Interface Streamlit
- 🔄 Testes Unitários (em desenvolvimento)
- 🔄 Documentação API (em desenvolvimento)

---

## 📞 Suporte

Para questões ou sugestões:
1. Abra uma issue no repositório
2. Consulte a documentação em `docs/`
3. Verifique o histórico de auditorias em `audit/`

---

**Última Atualização**: 22 de Junho de 2026
