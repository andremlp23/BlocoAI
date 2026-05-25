# 5. Visão Geral da Arquitetura

## 5.1 Introdução Arquitetónica

O sistema BlocoAI é concebido segundo o paradigma de **computação orientada a grafos com agentes autónomos**, implementado através da plataforma LangGraph. Esta abordagem permite a orquestração estruturada de processos de análise documental complexos, onde múltiplos agentes especializados operam em sequência coordenada, comunicando através de estruturas de estado bem definidas. A arquitetura resulta de um compromisso deliberado entre simplicidade operacional e flexibilidade extensível, priorizando a rastreabilidade completa de processos e a tolerância a falhas transientes.

## 5.2 Objetivo do Sistema

O sistema BlocoAI resolve um problema específico de engenharia de documentação em projetos de construção civil, particularmente em estruturas metálicas: **validar consistência técnica entre documentos heterogéneos** (Especificações Técnicas e Bill of Quantities), segregando conteúdo técnico relevante de informação comercial (quantidades, preços, fornecedores) que frequentemente mascara ou conflitua com requisitos de engenharia. O objetivo operacional é reduzir o ruído informativo, rastrear alinhamentos e lacunas entre contextos documentais, e gerar relatórios estruturados de auditoria técnica que suportem decisão de engenharia e revisão académica.

## 5.3 Arquitetura Modular

O sistema organiza-se em **cinco módulos especializados e desacoplados**:

1. **Módulo de Interface (Streamlit)**: Camada de apresentação responsável pela interação utilizador, recolha de inputs (documentos, contexto de projeto, guias de filtragem) e exibição estruturada de resultados.

2. **Módulo de Orquestração (orchestrator.py)**: Coordena o fluxo completo de processamento, gerindo sequência de leitura de documentos, invocação de grafos de extração e auditoria, normalização de saídas e persistência de histórico.

3. **Módulo de Motor de Agentes (langgraph_engine.py)**: Define grafos orientados a nós, onde cada nó representa um agente especializado com responsabilidade bem delimitada (extração de SPECS, extração de BOQ, auditoria cruzada).

4. **Módulo de Processamento de Dados (document_reader.py)**: Responsável pela ingestão multi-formato (PDF, DOCX, CSV) com detecção automática de encoding, extração de texto com preservação de layout e filtro de ruído comercial.

5. **Módulo de Apresentação Funcional (components.py, styles.py)**: Agrupa componentes UI reutilizáveis e estilos globais, facilitando manutenção e evolução de interface.

Esta modularização permite que cada componente seja desenvolvido, testado e evoluído de forma relativamente independente, respeitando interfaces bem definidas entre módulos.

## 5.4 Paradigma Multi-Agente

O sistema implementa um arquitetura multi-agente composta por **três agentes especializados**:

- **AGT-01 (Extrator SPECS)**: Recebe o texto completo de Especificações Técnicas e estrutura-o em JSON, executando análise semântica para identificar requisitos técnicos, normas, padrões de execução e constraints de engenharia, eliminando conteúdo comercial e relacionado com betão (fora do escopo).

- **AGT-02 (Extrator BOQ)**: Processa documentos de Bill of Quantities, extraindo estrutura de trabalhos, items técnicos e especificidades de construção relevantes, com ênfase em segregação de conteúdo técnico.

- **AGT-03 (Auditor Cruzado)**: Executa análise cruzada dos JSONs estruturados produzidos por AGT-01 e AGT-02, identificando alinhamentos, conflitos, lacunas e recomendações, gerando relatório consolidado de auditoria.

Cada agente é invocado através de um **modelo de linguagem grande (LLM)** com instruções especializadas e contexto relevante. A comunicação entre agentes é intermediada por estruturas de estado imutáveis (TypedDict), garantindo visibilidade total de alterações e facilitando debugging.

## 5.5 Organização em Camadas

A arquitetura segue um modelo de **cinco camadas horizontais**:

```
┌───────────────────────────────────────────┐
│    CAMADA 1: Apresentação (Streamlit)     │
│  ↕ Interface utilizador, recolha inputs   │
├───────────────────────────────────────────┤
│   CAMADA 2: Orquestração (Orchestrator)   │
│  ↕ Coordenação pipeline, fluxo de controlo│
├───────────────────────────────────────────┤
│   CAMADA 3: Motor (LangGraph Engines)     │
│  ↕ Grafos de agentes, invocação LLM       │
├───────────────────────────────────────────┤
│  CAMADA 4: Processamento (Document Reader)│
│  ↕ Transformação multi-formato, filtragem │
├───────────────────────────────────────────┤
│ CAMADA 5: Persistência (Storage / Logging)│
│  ↕ Histórico auditorias, estado sessão    │
└───────────────────────────────────────────┘
```

Cada camada possui responsabilidades bem definidas e comunica com adjacentes através de interfaces especializadas, permitindo evolução sem propagação de impacto.

---

## 5.6 Fluxo Principal de Execução

O pipeline de processamento segue uma sequência linear mas parametrizável:

1. **Inicialização**: Carregamento de variáveis de ambiente, autenticação de API, construção de grafos LangGraph.

2. **Recolha de Inputs**: Utilizador fornece documento BOQ, ficheiros SPECS, baseline de projeto (JSON) e guia de filtragem (opcional).

3. **Leitura de Documentos**: Módulo document_reader processa cada ficheiro, detectando formato, encoding e estrutura, gerando texto contínuo com rastreabilidade de página.

4. **Extração (Grafo EXTRAÇÃO)**:
   - Nó AGT-01: Estrutura SPECS em JSON {secções, requisitos, padrões, normas}
   - Nó AGT-02: Estrutura BOQ em JSON {items, categorias, especificações}
   - Estado intermediário persiste resumos para contexto subsequente

5. **Auditoria (Grafo AUDITORIA)**:
   - Nó AGT-03: Compara JSONs estruturados + contexto de projeto
   - Identifica alinhamentos, conflitos, lacunas
   - Gera relatório técnico consolidado

6. **Normalização de Saída**: Formatação final de relatório, aplicação de estilos, geração de download `.txt`.

7. **Persistência**: Gravação de histórico com timestamp em `historico_auditorias/`, retenção de session state para rastreabilidade.

O fluxo implementa **retry automático com backoff exponencial** para erros transientes (timeout, rate limit), e captura completa de stack trace para debugging de falhas.

---

## 5.7 Diagrama Geral da Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                   INTERFACE STREAMLIT                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Recolha: BOQ, SPECS, JSON Contexto, Guia Filtragem        │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────────┘
                       │ executar_pipeline_completo()
┌──────────────────────▼───────────────────────────────────────────┐
│              ORQUESTRAÇÃO (orchestrator.py)                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ read_document(files) → (texto, metadados)                  │ │
│  │ Inicializa estado completo (AuditoriaState)                │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼ GRAFO EXTRAÇÃO             ▼ GRAFO AUDITORIA
┌──────────────────────────┐  ┌──────────────────────────┐
│  langgraph_engine.py     │  │  langgraph_engine.py     │
├──────────────────────────┤  ├──────────────────────────┤
│ AGT-01: Extrai SPECS     │  │ AGT-03: Audita Cruzado   │
│ AGT-02: Extrai BOQ       │  │ (Usa JSONs + Contexto)   │
│                          │  │                          │
│ Output: JSONs estruturado│  │ Output: Relatório Audit  │
└──────────────────────────┘  └──────────────────────────┘
        │                              │
        └──────────────┬───────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│           FORMATAÇÃO & APRESENTAÇÃO (components.py)              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Normaliza relatório, aplica estilos CSS, gera download    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│            PERSISTÊNCIA (historico_auditorias/ + session)         │
│  Grava: Auditoria_[timestamp].txt, state em memória sessão      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5.8 Justificação Arquitetónica

### 5.8.1 Modularidade

A segregação em cinco camadas e três módulos especializados permite que alterações num componente não se propaguem para os restantes. Por exemplo, substituir o parser de PDF (document_reader.py) não requer alterações em grafos ou interface. Esta propriedade decorre de duas decisões:

1. **Interfaces bem definidas**: Cada módulo comunica apenas através de tipos de dados explícitos (AuditoriaState, tuplos de saída).
2. **Separação de responsabilidades (SRP)**: Nenhum módulo combina múltiplas razões para mudar; a orquestração não conhece detalhes de parsing, nem a UI conhece lógica de agentes.

**Consequência prática**: Tempo de desenvolvimento para novos agentes reduz-se significativamente, pois a infraestrutura de orquestração reutiliza-se sem modificação.

### 5.8.2 Escalabilidade

A arquitetura facilita expansão em dois eixos:

**Escalabilidade Horizontal (mais agentes)**:
- Novos agentes podem ser adicionados ao grafo de extração ou auditoria sem alterar código existente.
- Cada agente é um nó independente; a topologia do grafo determina sequência.
- Exemplo: Adicionar AGT-04 (Validador de Conformidade) requer apenas inscrição de novo nó, não refatoração.

**Escalabilidade Vertical (processamento maior)**:
- Documentos maiores são processados como chunks contínuos, permitindo LLMs com context windows alargados.
- Implementação de batch processing para múltiplos projetos simultâneos é viável sem alteração arquitetural (via threading ou async).

**Proteção contra falhas transientes**:
- Retry automático com backoff exponencial absorve picos de latência de API e rate limiting.
- Estado persiste entre tentativas, eliminando reprocessamento desnecessário.

### 5.8.3 Extensibilidade

A arquitetura permite adição de funcionalidades sem comprometer estabilidade:

1. **Novos formatos de documento**: Estender document_reader.py com nova função `parsear_xlsx()` sem modificar orchestrator ou grafos.

2. **Novas regras de negócio**: Contexto de projeto é parametrizável (JSON carregável); novos requisitos de auditoria integram-se alterando apenas prompt de AGT-03.

3. **Novos LLMs**: Interface abstrata do LangGraph permite trocar `ChatOpenAI` por `ChatAnthropic` ou `ChatOllama` alterando uma linha de configuração.

4. **Novas camadas de análise**: Adicionar grafo de "Pós-Auditoria" após grafo de auditoria requer apenas orquestração adicional, sem alteração de módulos existentes.

### 5.8.4 Manutenção

A rastreabilidade e diagnóstico são facilitados por:

1. **State Immutability**: Cada alteração ao estado é um novo snapshot, permitindo auditoria completa de evolução. Debug é determinístico: repetir com mesma entrada produz idêntica saída.

2. **Structured Logging**: Cada nó regista entrada/saída, permitindo diagnóstico granular de falhas. Histórico de auditorias persiste com timestamp, facilitando investigação post-mortem.

3. **Type Safety**: TypedDict do AuditoriaState obriga explicitação de contrato entre módulos, reduzindo bugs de interface.

4. **Separação de Ambientes**: Modo debug ativa verbose logging sem afetar produção. Contextos editáveis (JSON) permitem ajuste de regras sem redeployment.

**Custo de manutenção reduz-se porque**:
- Bugs localizam-se rapidamente (qual nó/camada falhou?)
- Regressões evitam-se (contrato de interface é verificado)
- Evolução é orientada (novos requisitos integram-se em camadas específicas)

---

## 5.9 Resumo Arquitectónico

BlocoAI implementa uma **arquitetura multi-camadas orientada a agentes**, onde modularidade, escalabilidade, extensibilidade e manutenção são conseguidas através de:

- Separação clara de responsabilidades em cinco camadas
- Computação orientada a grafos (LangGraph) para orquestração explícita
- Paradigma multi-agente onde cada agente é um nó especializado
- Estado imutável e rastreável para determinismo e debugging
- Interfaces bem definidas que permitem evolução independente de componentes

Este desenho deliberadamente complexo (vs. pipeline linear simples) é justificado pela necessidade de **análise técnica robusta, extensível e auditável** em contexto académico e de engenharia profissional.
