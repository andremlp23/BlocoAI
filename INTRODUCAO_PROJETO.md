# INTRODUÇÃO AO PROJETO BLOCOAI

## 1. Objeto do Trabalho

O presente trabalho incide sobre o desenvolvimento de um **sistema inteligente de extração, auditoria e estruturação de documentos de construção civil**, denominado **BlocoAI**. O projeto visa criar uma solução automatizada capaz de processar dois tipos de documentos críticos no sector da construção:

- **Especificações Técnicas (SPECS)**: Documentos que definem os requisitos técnicos, normas aplicáveis, materiais, acabamentos, tolerâncias e procedimentos de qualidade para a execução de obras.
- **Documentos de Orçamento (BOQ – Bill of Quantities)**: Ficheiros que descrevem, de forma estruturada, as fases de execução, zonas de trabalho, atividades e quantidades de trabalho associadas.

O sistema processa estes documentos através de **modelos de linguagem generativos (LLMs)** orquestrados em **fluxos de grafo** (LangGraph), com o objetivo de extrair, normalizar, auditar e estruturar a informação técnica numa formato adequado para estimating (orçamentação) em construção.

---

## 2. Justificação e Pertinência do Tema

### 2.1 Contexto Problemático

A indústria da construção enfrenta desafios significativos relacionados com:

1. **Fragmentação de Informação**: Documentos técnicos e orçamentários encontram-se frequentemente em formatos heterogéneos (PDF, DOCX, CSV) e com estruturações inconsistentes.

2. **Risco de Inconsistências**: Divergências entre as especificações técnicas e os documentos orçamentários podem resultar em:
   - Desvios de custo não previstos
   - Atrasos em obra
   - Conflitos entre disciplinas (estrutura, fogo, corrosão, etc.)

3. **Complexidade Operacional**: Processos manuais de leitura, comparação e auditoria de documentos consomem tempo significativo e são suscetíveis a erros humanos, particularmente quando lidam com múltiplas fases, zonas e subcategorias de trabalho.

4. **Necessidade de Estruturação**: A informação técnica necessita ser reorganizada de um formato baseado em localização (Fase → Zona → Subzona) para um formato baseado em disciplinas comerciais (Trade Packages), facilitando a orçamentação e gestão de riscos.

### 2.2 Relevância da Solução

A aplicação de **Inteligência Artificial** e, especificamente, de **modelos de linguagem avançados** oferece oportunidades para:

- Automatizar a extração de requisitos técnicos de documentos desestruturados
- Realizar auditorias cruzadas entre múltiplos documentos
- Identificar inconsistências e lacunas de informação
- Estruturar dados complexos em formatos otimizados para análise e estimating
- Reduzir erros operacionais e tempo de processamento

Este projeto contribui para a **transformação digital no sector da construção**, demonstrando como tecnologias de IA podem melhorar a qualidade, precisão e eficiência de processos críticos.

---

## 3. Objetivos do Trabalho

### 3.1 Objetivo Geral

Desenvolver e validar um sistema automatizado capaz de processar documentos de construção (Especificações Técnicas e BOQ), extrair informação técnica relevante, realizar auditoria cruzada entre fontes e estruturar os resultados num formato otimizado para análise de custos e gestão de riscos em construção.

### 3.2 Objetivos Específicos

#### OE1: Extração Inteligente de Dados Técnicos
- Extrair especificações técnicas de documentos SPECS (normas, materiais, tolerâncias, acabamentos)
- Extrair estrutura de fases, zonas e atividades de documentos BOQ
- Filtrar e descartar informação não técnica (quantidades, dados comerciais, preços)

#### OE2: Auditoria e Validação Cruzada
- Comparar requisitos extraídos de SPECS com informação do BOQ
- Identificar alinhamentos, conflitos e lacunas entre documentos
- Classificar status de cada requisito (ALIGNED / CONFLICT / MISSING BASELINE)

#### OE3: Normalização e Deduplicação
- Eliminar duplicação de requisitos técnicos nas várias categorias de disciplinas
- Atribuir cada requisito a uma única categoria canonical (propriedade exclusiva)
- Manter rastreabilidade de cada informação até à fonte original

#### OE4: Estruturação em Trade Packages
- Pivotar dados de um formato baseado em localização para um formato baseado em disciplinas
- Gerar relatórios executivos estruturados por Trade Package (Aço Estrutural, Deck Composto, Proteção de Fogo, Proteção de Corrosão, Metalizações)
- Produzir tabelas de variações de escopo para suporte à orçamentação

#### OE5: Orquestração de Fluxo Multi-Agente
- Implementar um grafo de execução coordenado (LangGraph) com múltiplos agentes especializados (AGT-01 a AGT-04)
- Garantir gestão de erros, retry automático e persistência de estados
- Produzir interface utilizador intuitiva (Streamlit) para interação com o sistema

### 3.3 Questões e Hipóteses

**Questão Principal:**
> É possível utilizar modelos de linguagem generativos para extrair, auditar e estruturar automaticamente documentos técnicos de construção com grau de precisão e confiabilidade adequados para aplicação em contexto profissional?

**Hipóteses Específicas:**

- **H1**: Modelos GPT treinados com prompts detalhados e regras de contexto conseguem extrair 85%+ das especificações técnicas relevantes sem omissões.
- **H2**: Auditorias cruzadas automáticas identificam corretamente 90%+ das inconsistências entre SPECS e BOQ comparadas manualmente por especialistas.
- **H3**: A deduplicação automática elimina 95%+ das duplicações cross-categoria mantendo rastreabilidade de origem.
- **H4**: O formato pivotado em Trade Packages é adequado para suportar decisões de orçamentação com margem de segurança apropriada.

---

## 4. Métodos e Técnicas Utilizados

### 4.1 Arquitetura Técnica

O projeto implementa uma arquitetura baseada em **componentes multi-camada**:

#### Camada 1: Leitura e Parsing de Documentos
- **PDF**: Utiliza `pdfplumber` para extração de texto com preservação de estrutura
- **DOCX**: Utiliza `python-docx` para leitura de documentos Word
- **CSV**: Implementa detecção automática de separadores (`,`, `;`, `\t`, `|`)
- **Auto-detecção**: Sistema identifica automaticamente tipo de ficheiro e aplica parser apropriado

#### Camada 2: Processamento com LLMs (Modelos de Linguagem)
- **Modelo Principal**: OpenAI GPT-5.1 (com fallback para GPT-4o para operações complexas)
- **Temperatura**: 0.0 para tarefas de extração (determinístico); 0.1 para auditoria (criativo mas consistente)
- **Retry com Exponential Backoff**: Implementado com `tenacity` para lidar com rate limits e timeouts da API

#### Camada 3: Orquestração com LangGraph
O projeto estrutura o processamento em **4 agentes especializados**:

**AGT-01 – Extrator de Especificações (SPECS Structurer)**
- Entrada: Documento de Especificações Técnicas
- Processo: Extrai seções, normas aplicáveis (EN/ISO/NBN), materiais e grades, acabamentos e proteções, tolerâncias/classes de execução, requisitos QA/submittals
- Saída: JSON estruturado com schema predefinido
- Regras Críticas: Filtra completamente informação relacionada com betão (out of scope)

**AGT-02 – Extrator de BOQ (BOQ Hunter + Structurer)**
- Entrada: Documento de Orçamento (PDF/DOCX ou CSV)
- Processo (para CSV): Extração estruturada de Fases → Zonas → Subzonas com dependências
- Processo (para texto): Extração narrativa mantendo contexto Phase/Zone/Subzone
- Saída: Texto estruturado ou JSON com mapeamento Phase→Zone completo
- Regras Críticas: Descartar quantidades e dados comerciais; focar apenas em requisitos técnicos

**AGT-03 – Deduplicador (Cross-Category Deduplication)**
- Entrada: Auditoria cruzada bruta (BOQ vs SPECS)
- Processo: 
  - Aplica regras de propriedade canonical para cada categoria
  - Atribui cada requisito a UMA só categoria (ex: um requirement de DFT é propriedade de Corrosão Protection)
  - Elimina duplicações mantendo rastreabilidade
- Saída: Auditoria normalizada sem redundâncias
- Regras: 5 categorias canonicais (Steel / Deck / Fire / Corrosion / Metal Fab)

**AGT-04 – Apresentador (Estimating Pivot)**
- Entrada: Auditoria normalizada
- Processo: Transforma formato Location-based (Phase→Zone) em formato Trade-Package-based
- Saída: Relatório Markdown com tabelas de Trade Package, Baseline Scope, Variations
- Objetivo: Estruturar dados para suporte a decisões de orçamentação

#### Camada 4: Interface de Utilizador
- **Framework**: Streamlit (aplicação web reativa)
- **Componentes**: Upload de ficheiros, preview de extrações, edição manual de contextos, visualização de resultados
- **Persistência**: Histórico de auditorias guardado com timestamp em `historico_auditorias/`

### 4.2 Técnicas Específicas

#### T1: Prompt Engineering Avançado
- Prompts detalhados com "persona" clara (ex: "Senior Construction Specifications Analyst")
- Definição explícita de regras ABSOLUTE (o que incluir/descartar)
- Schema de saída JSON bem definido com exemplos
- Instruções multi-passo (7-Step Extraction Strategy)
- Contexto injected (REGRAS_EXTRACAO carregadas de JSON externo)

#### T2: Context Windows Eficientes
- Processamento de documentos inteiros como single chunk (sem fragmentação)
- Injeção de contexto cross-document (SPECS como referência para BOQ extraction)
- Manutenção de state global (AuditoriaState TypedDict)

#### T3: Gestão de Erros e Reliability
- Retry automático com exponential backoff (max 4 tentativas)
- Tratamento de exceções API (RateLimitError, APITimeoutError, APIConnectionError)
- Logging estruturado com `logging` module
- Persistência de erros em lista acumulada

#### T4: Validação de Dados
- Regras explícitas de output (JSON válido, sem markdown, campos obrigatórios)
- RUIDO filtering: Descartar valores vazios, "N/A", "#N/A", "TBD", etc.
- Anti-hallucination rules: "Use NOT FOUND only if genuinely absent"
- EMPTY ZONE RULE: Se Subzone sem dados relevantes, marcar como [OUT OF SCOPE]

#### T5: Iteração e Refinamento
- Grafo de execução com retry condicional (até 2 tentativas de auditoria se comprimento insuficiente)
- Feedback loops: Output de um agente → input do próximo
- Checkpoint intermediário: Possibilidade de edição manual de contextos entre AGT-01/02 e AGT-03/04

### 4.3 Tecnologias Específicas

| Componente | Tecnologia | Versão/Detalhes |
|-----------|-----------|---|
| Orquestração | LangGraph | De LangChain ecosystem |
| LLMs | OpenAI API | GPT-5.1 (primário), GPT-4o (complexo) |
| Parsing PDF | pdfplumber | Preserva layout e estrutura |
| Parsing DOCX | python-docx | Leitura de estrutura Word |
| Parsing CSV | pandas + custom | Auto-detecção de separadores |
| Interface | Streamlit | Aplicação reativa web |
| Retry Logic | tenacity | Exponential backoff, logging |
| Estrutura Dados | TypedDict | Type hints para state management |
| Persistência | Filesystem | Histórico em .txt com timestamp |

---

## 5. Estrutura do Trabalho

### 5.1 Organização de Ficheiros

```
BlocoApps/
├── app.py                          # Ponto de entrada Streamlit
├── RegrasMekkin.json              # Regras de extração (injetadas em prompts)
├── core/
│   ├── __init__.py
│   ├── document_reader.py         # Parsers: PDF, DOCX, CSV
│   ├── langgraph_engine.py        # Lógica dos 4 agentes + grafo
│   └── orchestrator.py            # Orquestração de pipeline
└── ui/
    ├── __init__.py
    ├── components.py              # Componentes Streamlit reutilizáveis
    └── styles.py                  # CSS e styling global
```

### 5.2 Fluxo de Execução

```
Fase 1: Ingestion
  ├─ Upload de ficheiros (SPECS + BOQ)
  ├─ Auto-detecção de formato
  └─ Carregamento em memória

Fase 2: Extraction (AGT-01 + AGT-02)
  ├─ AGT-01: SPECS → JSON estruturado
  └─ AGT-02: BOQ → Estrutura Phase/Zone/Subzone

Fase 3: Manual Review (Opcional)
  ├─ Edição de contextos extraídos
  ├─ Validação manual
  └─ Ajustes antes de auditoria

Fase 4: Audit + Normalization (AGT-03 + AGT-03)
  ├─ AGT-02B: Auditoria cruzada BOQ vs SPECS
  ├─ AGT-03: Deduplicação cross-categoria
  └─ Retry automático se resultado insuficiente

Fase 5: Formatting (AGT-04)
  ├─ Pivot: Location-based → Trade-Package-based
  ├─ Geração de tabelas de variações
  └─ Relatório Markdown executivo

Fase 6: Persistence
  └─ Guardar relatório em historico_auditorias/ com timestamp
```

### 5.3 Componentes Principais

#### 5.3.1 Módulo `langgraph_engine.py`
Define os 4 agentes (nós do grafo), a AuditoriaState (schema de dados) e os grafos de execução:
- `construir_grafo_extracao()`: Grafo curto (apenas AGT-01/02)
- `construir_grafo_auditoria()`: Grafo completo (AGT-02B → AGT-03 → AGT-04)

#### 5.3.2 Módulo `document_reader.py`
Implementa parsers para múltiplos formatos:
- `read_document(file, tipo)`: Router principal
- Parser PDF (pdfplumber)
- Parser DOCX (python-docx)
- Parser CSV com auto-detecção de separador

#### 5.3.3 Módulo `orchestrator.py`
Funções de orquestração high-level:
- `processar_extracao_contextos()`: Executa AGT-01/02
- `processar_auditoria_com_contextos_editados()`: Executa AGT-02B/03/04

#### 5.3.4 Módulo `ui/components.py`
Componentes reutilizáveis Streamlit:
- `render_upload_section()`: Upload de ficheiros
- `render_results()`: Visualização de resultados
- `render_context_upload_section()`: Upload de contextos editados

### 5.4 Dados e Estruturas

#### AuditoriaState
Dicionário tipado que mantém estado durante toda a pipeline:
```python
{
    "texto_boq": str,                    # Conteúdo BOQ
    "texto_specs": str,                  # Conteúdo SPECS
    "resumo_boq": str,                   # Output AGT-02
    "resumo_specs": str,                 # Output AGT-01
    "auditoria_bruta": str,              # Output AGT-02B
    "auditoria_normalizada": str,        # Output AGT-03
    "relatorio_final": str,              # Output AGT-04
    "modo": str,                         # "SINGLE" ou "CROSS"
    "tentativas": int,                   # Contador de retry
    "erros": list,                       # Acumulação de erros
    ...
}
```

#### RegrasMekkin.json
Ficheiro externo contendo regras de extração:
- Definições de categorias canonical
- Regras de propriedade (ownership rules)
- Palavras-chave para cada disciplina
- Padrões de busca (regex)

### 5.5 Fases Cronológicas do Projeto

**Sprint 1**: Setup técnico
- Configuração de LangGraph e OpenAI API
- Implementação de document readers (PDF/DOCX/CSV)

**Sprint 2**: Agentes básicos
- AGT-01: Extrator SPECS
- AGT-02: Extrator BOQ

**Sprint 3**: Auditoria e normalização
- AGT-02B: Auditoria cruzada
- AGT-03: Deduplicador

**Sprint 4**: Pivot e relatório
- AGT-04: Trade Package formatter
- Estruturação de saída executiva

**Sprint 5**: UI e integração
- Interface Streamlit
- Persistência de histórico
- Testes end-to-end

**Sprint 6**: Validação e deployment
- Testes com documentos reais
- Refinamento de prompts
- Documentação final

---

## 6. Conclusão Introdutória

Este projeto representa uma aplicação inovadora de tecnologias de **Inteligência Artificial** e **engenharia de software** ao domínio da **gestão de construção**. Através de uma arquitetura modular, baseada em agentes especializados orquestrados por grafos de execução, BlocoAI demonstra como processos complexos e críticos podem ser automatizados, mantendo rastreabilidade, precisão e conformidade com regras de negócio específicas do sector.

Os resultados esperados contribuem para a **validação de hipóteses** sobre a viabilidade de aplicar LLMs em contextos de alta precisão exigida, enquanto estabelecem um **precedente metodológico** para automação inteligente em construção.
