# DIAGRAMAS TÉCNICOS - BlocoAI
## 13 Visualizações Mermaid para Relatório Académico

**Objetivo:** Inserir diagrama por diagrama no seu relatório académico. Cada diagrama é exportável como PNG via mermaid.live

---

## INSTRUÇÕES DE USO

Para cada diagrama que quiser incluir no seu relatório:

```
1. Copie o código Mermaid (entre ```mermaid e ```)
2. Vá para: https://mermaid.live
3. Cole o código no editor
4. Click direito → Download as PNG (ou SVG)
5. Insira no seu documento Word/PDF
6. Adicione legenda: "Figura X: [Título e Descrição]"
```

---

## DIAGRAMA 1: Arquitetura em 5 Camadas

**Uso:** Secção 3 (Arquitetura) - explicar pilares do sistema

**Descrição:** Mostra as 5 camadas horizontais de BlocoAI, desde UI até persistência de dados.

```mermaid
graph TB
    subgraph UI["CAMADA 1: Interface (Streamlit)"]
        UI1["Header + Status"]
        UI2["Upload Documentos"]
        UI3["Project Context JSON"]
        UI4["Filtering Guide"]
        UI5["Results Display"]
    end

    subgraph ORQ["CAMADA 2: Orquestração (Orchestrator)"]
        ORQ1["carregar_env_local()"]
        ORQ2["executar_pipeline_completo()"]
        ORQ3["State Management"]
        ORQ4["Error Handling"]
    end

    subgraph ENG["CAMADA 3: Engines (LangGraph)"]
        ENG1["AGT-01: SPECS"]
        ENG2["AGT-02: BOQ"]
        ENG3["AGT-03: Audit"]
        ENG4["Retry Logic"]
    end

    subgraph PROC["CAMADA 4: Processing"]
        PROC1["Document Reader"]
        PROC2["Text Extraction"]
        PROC3["JSON Parsing"]
        PROC4["Noise Filtering"]
    end

    subgraph PERS["CAMADA 5: Persistence"]
        PERS1["Histórico Auditorias"]
        PERS2["Session State"]
        PERS3["Log Files"]
        PERS4["Report Storage"]
    end

    UI --> ORQ
    ORQ --> ENG
    ENG --> PROC
    PROC --> PERS

    style UI fill:#e1f5ff
    style ORQ fill:#fff3e0
    style ENG fill:#f3e5f5
    style PROC fill:#e8f5e9
    style PERS fill:#fce4ec
```

---

## DIAGRAMA 2: Fluxo de Dados (DFD - Nível 0)

**Uso:** Secção 5 (Implementação) - explicar pipeline de processamento

**Descrição:** Mostra entrada do utilizador → processamento através de 3 agentes → saída final.

```mermaid
graph LR
    USER["Utilizador"]
    UPLOAD["Upload<br/>Documentos"]
    
    subgraph "PROCESSAMENTO INTERNO"
        AGT1["AGT-01<br/>SPECS"]
        AGT2["AGT-02<br/>BOQ"]
        AGT3["AGT-03<br/>Audit"]
    end
    
    VALIDATE["Validacao"]
    REPORT["Relatório"]
    HISTORY["Histórico"]
    OUTPUT["Saída"]
    
    USER -->|Input JSON| VALIDATE
    VALIDATE -->|BOQ + SPECS| UPLOAD
    UPLOAD -->|Documentos| AGT1
    AGT1 -->|Specs JSON| AGT2
    AGT2 -->|BOQ JSON| AGT3
    AGT3 -->|Audit| REPORT
    REPORT -->|Persistir| HISTORY
    REPORT -->|Display| OUTPUT
    
    style USER fill:#e3f2fd
    style UPLOAD fill:#fff9c4
    style VALIDATE fill:#fff9c4
    style AGT1 fill:#f3e5f5
    style AGT2 fill:#f3e5f5
    style AGT3 fill:#f3e5f5
    style REPORT fill:#c8e6c9
    style HISTORY fill:#fce4ec
    style OUTPUT fill:#b2dfdb
```

---

## DIAGRAMA 3: Estado através das 3 Fases de Processamento

**Uso:** Secção 6 (Exemplos Práticos) - mostrar evolução do estado

**Descrição:** Mostra como o estado evolui conforme passa por cada fase.

```mermaid
sequenceDiagram
    participant USER as Utilizador
    participant APP as App.py
    participant ORCH as Orchestrator
    participant ENG as LangGraph Engines
    participant PERSIST as Persistence

    USER->>APP: Click "Iniciar Pipeline"
    APP->>ORCH: executar_pipeline_completo()
    
    Note over ORCH: FASE 1: Document Reading
    ORCH->>ENG: state = {texto_boq: "", texto_specs: "", ...}
    ORCH->>ENG: read_document(arquivo)
    ENG-->>ORCH: (texto, paginas_sem_texto)
    ORCH->>ORCH: state["texto_boq"] ← texto

    Note over ORCH: FASE 2: Extraction Graph
    ORCH->>ENG: stream extraction_graph
    ENG->>ENG: AGT-01 (SPECS)
    ENG->>ENG: AGT-02 (BOQ)
    ENG-->>ORCH: state["resumo_specs"] + state["resumo_boq"]
    ORCH->>ORCH: Atualizar Progress

    Note over ORCH: FASE 3: Audit Graph
    ORCH->>ENG: stream audit_graph
    ENG->>ENG: AGT-03 (Audit)
    ENG-->>ORCH: state["auditoria_final"]
    ORCH->>ORCH: Formatar Relatório

    Note over ORCH: FASE 4: Persistência
    ORCH->>PERSIST: _persistir_relatorio()
    PERSIST->>PERSIST: Salvar em historico_auditorias/
    PERSIST-->>ORCH: Relativo criado em [timestamp]
    
    ORCH-->>APP: relatorio_final
    APP-->>USER: Exibir Relatório
```

---

## DIAGRAMA 4: Sequência de Invocação LLM com Retry

**Uso:** Secção 5 (Implementação) - explicar resilência e retry

**Descrição:** Mostra como o retry exponencial trata falhas de API.

```mermaid
graph TD
    START["Iniciar Chamada LLM"]
    ATTEMPT1["Tentativa 1"]
    CHECK1{API OK?}
    SUCCESS["Sucesso"]
    WAIT1["Esperar 2s<br/>exponential backoff"]
    
    ATTEMPT2["Tentativa 2"]
    CHECK2{API OK?}
    WAIT2["Esperar 4s"]
    
    ATTEMPT3["Tentativa 3"]
    CHECK3{API OK?}
    WAIT3["Esperar 8s"]
    
    ATTEMPT4["Tentativa 4"]
    CHECK4{API OK?}
    
    FAIL["Falha<br/>Max Tentativas"]
    ERROR["Registar Erro"]
    
    START --> ATTEMPT1
    ATTEMPT1 --> CHECK1
    CHECK1 -->|Sim| SUCCESS
    CHECK1 -->|Nao| WAIT1
    WAIT1 --> ATTEMPT2
    ATTEMPT2 --> CHECK2
    CHECK2 -->|Sim| SUCCESS
    CHECK2 -->|Nao| WAIT2
    WAIT2 --> ATTEMPT3
    ATTEMPT3 --> CHECK3
    CHECK3 -->|Sim| SUCCESS
    CHECK3 -->|Nao| WAIT3
    WAIT3 --> ATTEMPT4
    ATTEMPT4 --> CHECK4
    CHECK4 -->|Sim| SUCCESS
    CHECK4 -->|Nao| FAIL
    
    FAIL --> ERROR
    ERROR --> END["Fim (com erro)"]
    SUCCESS --> END
    
    style START fill:#e3f2fd
    style SUCCESS fill:#c8e6c9
    style FAIL fill:#ffcdd2
    style ERROR fill:#ffcdd2
    style ATTEMPT1 fill:#fff9c4
    style ATTEMPT2 fill:#fff9c4
    style ATTEMPT3 fill:#fff9c4
    style ATTEMPT4 fill:#fff9c4
```

---

## DIAGRAMA 5: Grafo de Extração (AGT-01 + AGT-02)

**Uso:** Secção 3 (Arquitetura) - explicar fluxo interno dos agentes

**Descrição:** LangGraph state machine para extração de SPECS e BOQ.

```mermaid
graph TB
    START["Início"]
    
    READ["Ler Documentos<br/>estado: texto_boq, texto_specs"]
    
    EXTRACT_SPECS["AGT-01: Extrair SPECS<br/>sistema: extrair especificações técnicas<br/>output: resumo_specs JSON"]
    
    EXTRACT_BOQ["AGT-02: Extrair BOQ<br/>sistema: extrair quantidades com fases/zonas<br/>usando RegrasMekkin.json<br/>output: resumo_boq JSON"]
    
    VALIDATE["Validar JSONs<br/>Verificar: keys, tipos, completude"]
    
    CHECK_VALID{JSON<br/>Válido?}
    
    RETRY["Retry (máx 4x)<br/>wait exponential: 2-30s"]
    
    END["Fim<br/>estado: resumo_specs + resumo_boq"]
    
    START --> READ
    READ --> EXTRACT_SPECS
    EXTRACT_SPECS --> EXTRACT_BOQ
    EXTRACT_BOQ --> VALIDATE
    VALIDATE --> CHECK_VALID
    CHECK_VALID -->|Sim| END
    CHECK_VALID -->|Nao| RETRY
    RETRY --> EXTRACT_SPECS
    
    style START fill:#c8e6c9
    style END fill:#c8e6c9
    style READ fill:#e3f2fd
    style EXTRACT_SPECS fill:#f3e5f5
    style EXTRACT_BOQ fill:#f3e5f5
    style VALIDATE fill:#fff9c4
    style RETRY fill:#ffcdd2
```

---

## DIAGRAMA 6: Grafo de Auditoria (AGT-03)

**Uso:** Secção 3 (Arquitetura) - explicar auditoria cruzada SPECS vs BOQ

**Descrição:** Estado machine para validação cruzada e geração de relatório final.

```mermaid
graph TB
    INPUT["Input<br/>resumo_specs + resumo_boq"]
    
    AUDIT["AGT-03: Auditar<br/>Comparar SPECS vs BOQ<br/>Identificar: alignments, conflicts, gaps"]
    
    ANALYSIS["Análise de Resultados<br/>Alignments: O que coincide<br/>Conflicts: O que diverge<br/>Gaps: O que falta"]
    
    FORMAT["Formatar Relatório<br/>estrutura: markdown com tabelas"]
    
    QUALITY_CHECK["Verificação Qualidade<br/>Sanity checks"]
    
    PERSIST["Persistir<br/>historico_auditorias/"]
    
    OUTPUT["Saída Final"]
    
    INPUT --> AUDIT
    AUDIT --> ANALYSIS
    ANALYSIS --> FORMAT
    FORMAT --> QUALITY_CHECK
    QUALITY_CHECK --> PERSIST
    PERSIST --> OUTPUT
    
    style INPUT fill:#e3f2fd
    style AUDIT fill:#f3e5f5
    style ANALYSIS fill:#fff9c4
    style FORMAT fill:#c8e6c9
    style OUTPUT fill:#c8e6c9
    style QUALITY_CHECK fill:#fff9c4
    style PERSIST fill:#fce4ec
```

---

## DIAGRAMA 7: Padrão de Retry com Exponential Backoff

**Uso:** Secção 5 (Implementação) - detalhe técnico de resilência

**Descrição:** Visualização detalhada do padrão tenacity utilizado.

```mermaid
graph LR
    ATTEMPT["attempt = 1"]
    CALL["Chamar API"]
    
    EXCEPTION{Exceção<br/>capturada?}
    
    SUCCESS["Sem erro"]
    RATELIMIT["RateLimit"]
    TIMEOUT["Timeout"]
    CONNECTION["Connection"]
    
    CHECK_ATTEMPTS{Tentativas<br/>≤ 4?}
    
    WAIT["Wait =<br/>2^attempt * 1000ms<br/>max 30s"]
    
    INCREMENT["Próxima tentativa"]
    
    FINAL_FAIL["Levanter exceção"]
    
    ATTEMPT --> CALL
    CALL --> EXCEPTION
    
    EXCEPTION -->|Sim| SUCCESS
    EXCEPTION -->|RateLimit| RATELIMIT
    EXCEPTION -->|Timeout| TIMEOUT
    EXCEPTION -->|Connection| CONNECTION
    
    RATELIMIT --> CHECK_ATTEMPTS
    TIMEOUT --> CHECK_ATTEMPTS
    CONNECTION --> CHECK_ATTEMPTS
    
    CHECK_ATTEMPTS -->|Sim| WAIT
    CHECK_ATTEMPTS -->|Não| FINAL_FAIL
    
    WAIT --> INCREMENT
    INCREMENT --> CALL
    
    SUCCESS --> END["Return result"]
    FINAL_FAIL --> END
    
    style CALL fill:#ffcdd2
    style SUCCESS fill:#c8e6c9
    style FINAL_FAIL fill:#ffcdd2
    style WAIT fill:#fff9c4
    style RATELIMIT fill:#ffe0b2
    style TIMEOUT fill:#ffe0b2
    style CONNECTION fill:#ffe0b2
```

---

## DIAGRAMA 8: Validação de Input (UI)

**Uso:** Secção 6 (Exemplos) - mostrar validações antes processamento

**Descrição:** Fluxo de validação que usuário passa antes "Iniciar Pipeline".

```mermaid
graph TD
    USER["Utilizador clica 'Iniciar'"]
    
    CHECK1{"API Key<br/>presente?"}
    ERR1["Erro: Configure API Key<br/>na sidebar"]
    
    CHECK2{"Ficheiros<br/>uploaded?"}
    ERR2["Erro: Upload pelo menos<br/>BOQ ou SPECS"]
    
    CHECK3{"Project Context<br/>JSON válido?"}
    ERR3["Erro: JSON inválido<br/>Verifique sintaxe"]
    
    CHECK4{"Contexto JSON<br/>tem keys mínimas?"}
    ERR4["Erro: JSON deve ter<br/>projeto_nome, cliente"]
    
    VALID["Todas validações OK"]
    
    EXECUTE["Executar Pipeline"]
    
    USER --> CHECK1
    CHECK1 -->|Não| ERR1
    CHECK1 -->|Sim| CHECK2
    
    CHECK2 -->|Não| ERR2
    CHECK2 -->|Sim| CHECK3
    
    CHECK3 -->|Não| ERR3
    CHECK3 -->|Sim| CHECK4
    
    CHECK4 -->|Não| ERR4
    CHECK4 -->|Sim| VALID
    
    VALID --> EXECUTE
    
    ERR1 --> END["Abort"]
    ERR2 --> END
    ERR3 --> END
    ERR4 --> END
    
    EXECUTE --> PROC["Processing..."]
    
    style USER fill:#e3f2fd
    style CHECK1 fill:#fff9c4
    style CHECK2 fill:#fff9c4
    style CHECK3 fill:#fff9c4
    style CHECK4 fill:#fff9c4
    style VALID fill:#c8e6c9
    style EXECUTE fill:#c8e6c9
    style ERR1 fill:#ffcdd2
    style ERR2 fill:#ffcdd2
    style ERR3 fill:#ffcdd2
    style ERR4 fill:#ffcdd2
    style PROC fill:#fff9c4
```

---

## DIAGRAMA 9: Árvore de Componentes UI (Streamlit)

**Uso:** Secção 3 (Arquitetura) - estrutura hierárquica da UI

**Descrição:** Hierarquia de componentes Streamlit chamados em ordem.

```mermaid
graph TB
    ROOT["App.py<br/>main()"]
    
    ENV["carregar_env_local()"]
    
    SIDEBAR["Sidebar<br/>setup_sidebar()"]
    API["API Key Input"]
    STATUS["Status Badge"]
    
    HEADER["render_header()"]
    TITLE["Title Band"]
    
    CONTEXT["render_project_context_section()"]
    CONTEXT_FILE["File Upload / Paste"]
    CONTEXT_JSON["Project Baseline JSON"]
    
    UPLOAD["render_upload_section()"]
    UPLOAD_BOQ["BOQ Uploader"]
    UPLOAD_SPECS["SPECS Uploader"]
    
    FOCUS["render_focus_section()"]
    FOCUS_GUIDE["Filtering Guide (TextArea)"]
    
    RESULTS_SECTION["render_results()"]
    RESULTS_TEXT["Final Report Display"]
    RESULTS_DOWNLOAD["Download Button"]
    
    STATE["ensure_session_defaults()"]
    
    ROOT --> ENV
    ROOT --> STATE
    ROOT --> SIDEBAR
    ROOT --> HEADER
    ROOT --> CONTEXT
    ROOT --> UPLOAD
    ROOT --> FOCUS
    ROOT --> RESULTS_SECTION
    
    SIDEBAR --> API
    SIDEBAR --> STATUS
    
    HEADER --> TITLE
    
    CONTEXT --> CONTEXT_FILE
    CONTEXT --> CONTEXT_JSON
    
    UPLOAD --> UPLOAD_BOQ
    UPLOAD --> UPLOAD_SPECS
    
    FOCUS --> FOCUS_GUIDE
    
    RESULTS_SECTION --> RESULTS_TEXT
    RESULTS_SECTION --> RESULTS_DOWNLOAD
    
    style ROOT fill:#e3f2fd
    style ENV fill:#fff9c4
    style STATE fill:#fff9c4
    style SIDEBAR fill:#f3e5f5
    style HEADER fill:#e1f5ff
    style CONTEXT fill:#c8e6c9
    style UPLOAD fill:#c8e6c9
    style FOCUS fill:#c8e6c9
    style RESULTS_SECTION fill:#f8bbd0
```

---

## DIAGRAMA 10: Ciclo de Vida do Estado (SessionState)

**Uso:** Secção 5 (Implementação) - explicar session state management

**Descrição:** Como estado persiste e evolui através de reruns Streamlit.

```mermaid
graph TB
    INIT["Início Sessão<br/>st.session_state vazio"]
    
    DEFAULTS["ensure_session_defaults()<br/>Inicializar 20+ keys"]
    
    UI["Renderizar UI<br/>User interage"]
    
    UPLOAD_EVENT["User Upload<br/>atualizar state[files]"]
    
    JSON_INPUT["User Input JSON<br/>atualizar state[contexto_projeto]"]
    
    BUTTON_CLICK["User Click 'Iniciar'<br/>state[processado] = True"]
    
    EXECUTE_PIPELINE["Executar Pipeline<br/>Atualizar: pipeline_state,<br/>relatorio_final, erros_sessao"]
    
    DISPLAY_RESULTS["Streamlit re-render<br/>Mostrar resultados"]
    
    PERSIST["SessionState persiste<br/>até logout"]
    
    INIT --> DEFAULTS
    DEFAULTS --> UI
    UI --> UPLOAD_EVENT
    UPLOAD_EVENT --> JSON_INPUT
    JSON_INPUT --> BUTTON_CLICK
    BUTTON_CLICK --> EXECUTE_PIPELINE
    EXECUTE_PIPELINE --> DISPLAY_RESULTS
    DISPLAY_RESULTS --> PERSIST
    PERSIST -->|Usuário faz nova ação| UI
    
    style INIT fill:#e3f2fd
    style DEFAULTS fill:#fff9c4
    style UI fill:#c8e6c9
    style UPLOAD_EVENT fill:#fff9c4
    style JSON_INPUT fill:#fff9c4
    style BUTTON_CLICK fill:#fff9c4
    style EXECUTE_PIPELINE fill:#f3e5f5
    style DISPLAY_RESULTS fill:#c8e6c9
    style PERSIST fill:#fce4ec
```

---

## DIAGRAMA 11: Matriz RACI de Responsabilidades

**Uso:** Secção 4 (Design) - clarificar responsabilidades entre componentes

**Descrição:** Matriz de quem faz o quê (Responsible, Accountable, Consulted, Informed).

```mermaid
graph TB
    subgraph TASKS["TAREFAS CHAVE"]
        T1["1. Parse Documentos"]
        T2["2. Estruturar SPECS"]
        T3["3. Estruturar BOQ"]
        T4["4. Auditar"]
        T5["5. Gerar Relatório"]
        T6["6. Persistir"]
        T7["7. Exibir UI"]
    end
    
    subgraph COMPONENTS["COMPONENTES"]
        C1["document_reader.py"]
        C2["AGT-01 Agent"]
        C3["AGT-02 Agent"]
        C4["AGT-03 Agent"]
        C5["orchestrator.py"]
        C6["persistence"]
        C7["app.py + components.py"]
    end
    
    T1 -.-> C1
    T2 -.-> C2
    T3 -.-> C3
    T4 -.-> C4
    T5 -.-> C5
    T6 -.-> C6
    T7 -.-> C7
    
    style T1 fill:#fff9c4
    style T2 fill:#fff9c4
    style T3 fill:#fff9c4
    style T4 fill:#fff9c4
    style T5 fill:#fff9c4
    style T6 fill:#fff9c4
    style T7 fill:#fff9c4
    
    style C1 fill:#e8f5e9
    style C2 fill:#f3e5f5
    style C3 fill:#f3e5f5
    style C4 fill:#f3e5f5
    style C5 fill:#fff3e0
    style C6 fill:#fce4ec
    style C7 fill:#e1f5ff
```

---

## DIAGRAMA 12: Timeline de ADRs (Decisões Arquiteturais)

**Uso:** Secção 4 (Design) - mostrar evolução de decisões

**Descrição:** Cronologia das 5 decisões técnicas principais e suas razões.

```mermaid
timeline
    title ADRs Timeline - BlocoAI Decisões Arquitetturais
    
    ADR-001 : LangGraph State Machine
              : Razão: Fluxo determinístico, Fácil debug
              : Tradeoff: Menos flexível que OpenAI Swarm
    
    ADR-002 : Structured Output (JSON Forcing)
              : Razão: Reduzir LLM hallucinations
              : Tradeoff: Mais prompt engineering
    
    ADR-003 : Retry Pattern + Exponential Backoff
              : Razão: 99% success rate em API calls
              : Tradeoff: Latência aumenta em picos
    
    ADR-004 : Document Reader Polymorphic
              : Razão: Suportar PDF + DOCX + CSV + Excel
              : Tradeoff: Código mais complexo
    
    ADR-005 : Streamlit para UI
              : Razão: Prototipagem rápida, Deployment fácil
              : Tradeoff: Menos controlo sobre UX
```

---

## DIAGRAMA 13: Fluxo de Tratamento de Erros

**Uso:** Secção 8 (Desafios) - explicar como erros são capturados e reportados

**Descrição:** End-to-end error handling com tracking e feedback.

```mermaid
graph TD
    ERROR["Erro Capturado<br/>em qualquer ponto"]
    
    CLASSIFY{"Tipo de erro?"}
    
    API_ERROR["API Error<br/>RateLimit/Timeout"]
    JSON_ERROR["JSON Parse Error"]
    FILE_ERROR["File Read Error"]
    VALIDATION_ERROR["Validation Error"]
    OTHER_ERROR["Other Error"]
    
    RETRY["Retry?<br/>Tenacity logic"]
    COLLECT["Coletar info<br/>traceback, timestamp"]
    
    APPEND_STATE["Append to<br/>state[erros]"]
    APPEND_SESSION["Append to<br/>st.session_state.erros_sessao"]
    
    DISPLAY["Exibir ao User<br/>Expander: 'Ver detalhes'"]
    
    LOG_FILE["Log em<br/>historico_auditorias/"]
    
    GRACEFUL["Continue ou Abort<br/>conforme gravidade"]
    
    ERROR --> CLASSIFY
    CLASSIFY -->|API| API_ERROR
    CLASSIFY -->|JSON| JSON_ERROR
    CLASSIFY -->|File| FILE_ERROR
    CLASSIFY -->|Validation| VALIDATION_ERROR
    CLASSIFY -->|Outro| OTHER_ERROR
    
    API_ERROR --> RETRY
    RETRY -->|Sim| ERROR
    RETRY -->|Não| COLLECT
    
    JSON_ERROR --> COLLECT
    FILE_ERROR --> COLLECT
    VALIDATION_ERROR --> COLLECT
    OTHER_ERROR --> COLLECT
    
    COLLECT --> APPEND_STATE
    APPEND_STATE --> APPEND_SESSION
    APPEND_SESSION --> DISPLAY
    DISPLAY --> LOG_FILE
    LOG_FILE --> GRACEFUL
    
    style ERROR fill:#ffcdd2
    style COLLECT fill:#fff9c4
    style APPEND_STATE fill:#fff9c4
    style DISPLAY fill:#ffe0b2
    style LOG_FILE fill:#fce4ec
    style GRACEFUL fill:#c8e6c9
    style RETRY fill:#fff9c4
```

---

## CHECKLIST DE DIAGRAMAS

Utilize este checklist para inserir os diagramas no seu relatório:

- [ ] **DIAGRAMA 1** - Arquitetura 5 Camadas → Secção 3 (Arquitetura)
- [ ] **DIAGRAMA 2** - Fluxo de Dados → Secção 5 (Implementação)
- [ ] **DIAGRAMA 3** - Estado através Fases → Secção 6 (Exemplos Práticos)
- [ ] **DIAGRAMA 4** - Sequência LLM + Retry → Secção 5 (Implementação)
- [ ] **DIAGRAMA 5** - Grafo Extração → Secção 3 (Arquitetura)
- [ ] **DIAGRAMA 6** - Grafo Auditoria → Secção 3 (Arquitetura)
- [ ] **DIAGRAMA 7** - Retry Exponential → Secção 5 (Implementação)
- [ ] **DIAGRAMA 8** - Validação Input → Secção 6 (Exemplos)
- [ ] **DIAGRAMA 9** - Árvore UI → Secção 3 (Arquitetura)
- [ ] **DIAGRAMA 10** - Ciclo SessionState → Secção 5 (Implementação)
- [ ] **DIAGRAMA 11** - Matriz RACI → Secção 4 (Design)
- [ ] **DIAGRAMA 12** - Timeline ADRs → Secção 4 (Design)
- [ ] **DIAGRAMA 13** - Fluxo Erros → Secção 8 (Desafios)

**Mínimo recomendado para relatório:** Inserir pelo menos 8-10 diagramas

---

## 🔗 LINKS E RECURSOS

### Como Exportar Diagrama:

1. Copie uma secção inteira (```mermaid ... ```)
2. Vá para [Mermaid Live](https://mermaid.live)
3. Cole no editor
4. Click direito na imagem → Download as PNG/SVG
5. Salve com nome: `Figura_X_Descricao.png`
6. Insira em Word: Insert → Pictures → This Device
7. Adicione legenda: "Figura X: [Título e Descrição breve]"

### Alternativa: Extensão Mermaid4Word

Se usar Microsoft Word:
- Instale [Mermaid4Word](https://appsource.microsoft.com/en-us/product/office/WA200002467)
- Copie código Mermaid directamente no Word
- Renderiza automaticamente
- Mais profissional e dinâmico

---

## 📐 DICAS DE FORMATAÇÃO

### No seu relatório académico:

```markdown
## Secção 3: Arquitetura

A arquitetura de BlocoAI segue um padrão de 5 camadas...

[Insira Figura 1 aqui: Arquitetura em 5 Camadas]

**Figura 1:** Arquitetura de BlocoAI com as 5 camadas: Interface (Streamlit),
Orquestração (Python), Engines (LangGraph), Processamento (Parsing), e Persistência
(Ficheiros + Session). Cada camada tem responsabilidades bem definidas.

O fluxo de dados segue...

[Insira Figura 2 aqui: Fluxo de Dados]

**Figura 2:** Fluxo de dados do sistema: Utilizador → Upload → AGT-01 (SPECS) →
AGT-02 (BOQ) → AGT-03 (Auditoria) → Relatório → Histórico.
```

---

## RESUMO

Você tem 13 diagramas Mermaid prontos para inserir no seu relatório académico:

| # | Diagrama | Localização no Relatório |
|---|----------|--------------------------|
| 1 | Arquitetura 5 Camadas | Secção 3 - Arquitetura |
| 2 | Fluxo de Dados | Secção 5 - Implementação |
| 3 | Estado através Fases | Secção 6 - Exemplos |
| 4 | Sequência LLM + Retry | Secção 5 - Implementação |
| 5 | Grafo Extração | Secção 3 - Arquitetura |
| 6 | Grafo Auditoria | Secção 3 - Arquitetura |
| 7 | Retry Exponential Backoff | Secção 5 - Implementação |
| 8 | Validação Input | Secção 6 - Exemplos |
| 9 | Árvore UI | Secção 3 - Arquitetura |
| 10 | Ciclo SessionState | Secção 5 - Implementação |
| 11 | Matriz RACI | Secção 4 - Design |
| 12 | Timeline ADRs | Secção 4 - Design |
| 13 | Fluxo de Erros | Secção 8 - Desafios |

---

**Todos os diagramas estão prontos. Bom trabalho no seu relatório!** 🚀
