# Fluxo de Pipeline - Diagrama Mermaid

## Diagrama 1: Fluxo Sequencial Completo

```mermaid
graph TD
    START["🟢 INÍCIO<br/>Utilizador submete documentos"] --> READ["📖 LEITURA DE DOCUMENTOS<br/>━━━━━━━━━━━━━━━━━━━<br/>• Parse BOQ.csv<br/>• Parse SPECS.pdf/docx<br/>• Detecção encoding<br/>• Marcadores de origem<br/>• Aviso: páginas sem OCR"]
    
    READ --> POPULATE["🔨 POPULAÇÃO ESTADO INICIAL<br/>━━━━━━━━━━━━━━━━━━━<br/>texto_boq: str<br/>texto_specs: str<br/>contexto_projeto: dict<br/>guia_filtragem: str"]
    
    POPULATE --> ROUTER["🚦 ROUTER INICIAL<br/>━━━━━━━━━━━━━━━━━━━<br/>Determina modo:"]
    
    ROUTER -->|ambos BOQ+SPECS| CROSS["✓ CROSS<br/>Auditoria cruzada"]
    ROUTER -->|só um documento| SINGLE["⚠️ SINGLE<br/>Validação simples"]
    
    CROSS --> EXTRACT["🔷 EXTRAÇÃO DE SPECS E BOQ<br/>━━━━━━━━━━━━━━━━━━━<br/>Nó AGT-01 (SPECS):<br/>  • Estrutura em JSON<br/>  • Materiais, normas, tolerâncias<br/>  • Remove comercial + betão<br/><br/>Nó AGT-02 (BOQ):<br/>  • Detecta formato (CSV/PDF)<br/>  • Mapeia Phase/Zone/Subzone<br/>  • Contexto de SPECS injetado"]
    SINGLE --> EXTRACT
    
    EXTRACT --> EXTRACTOK{Extração<br/>bem-sucedida?}
    
    EXTRACTOK -->|ambos não-vazios| VALIDATE["✓ VALIDAÇÃO INTERMÉDIA<br/>━━━━━━━━━━━━━━━━━━━<br/>• Verifica tamanho mínimo<br/>• Detecta JSON inválido<br/>• Rastreia páginas sem texto<br/>• Acumula erros se houver"]
    EXTRACTOK -->|dados vazios| ERROR1["❌ Erro: Extração falhou<br/>Sem dados para prosseguir"]
    
    ERROR1 --> END_FAIL["🔴 CONCLUSÃO (Falha)<br/>Erros exibidos na UI"]
    
    VALIDATE --> VALIDATEOK{Estado<br/>válido?}
    VALIDATEOK -->|SIM| AUDIT["🔶 AUDITORIA CRUZADA<br/>━━━━━━━━━━━━━━━━━━━<br/>Nó AGT-03 (Auditor):<br/>  • Compara resumo_specs<br/>    vs resumo_boq<br/>  • Aplica contexto_projeto<br/>  • Identifica:<br/>    - Alinhamentos<br/>    - Conflitos<br/>    - Lacunas"]
    VALIDATEOK -->|NÃO| ERROR2["❌ Erro: Estado inválido<br/>Metadados inconsistentes"]
    
    ERROR2 --> END_FAIL
    
    AUDIT --> AUDITOK{Auditoria<br/>completa?<br/>len >= 100}
    
    AUDITOK -->|SIM| DEDUPE["🟡 DEDUPLICAÇÃO E NORMALIZAÇÃO<br/>━━━━━━━━━━━━━━━━━━━<br/>Nó Dedupe:<br/>  • Remove linhas duplicadas<br/>  • Normaliza formatação<br/>  • Agrupa por Phase/Zone<br/>  • Mantém rastreabilidade"]
    AUDITOK -->|NÃO| RETRY{Tentativas<br/>< 2?}
    
    RETRY -->|SIM| AUDIT
    RETRY -->|NÃO| ERROR3["❌ Erro: Auditoria falhou<br/>Output muito curto<br/>após 2 tentativas"]
    
    ERROR3 --> END_FAIL
    
    DEDUPE --> FORMAT["🎨 FORMATAÇÃO DO RELATÓRIO FINAL<br/>━━━━━━━━━━━━━━━━━━━<br/>Nó Apresentador:<br/>  • Cabeçalhos visuais<br/>  • Sumário executivo<br/>  • Separadores & estilos<br/>  • Rodapé com metadata<br/>  • Timestamps"]
    
    FORMAT --> PERSIST["💾 PERSISTÊNCIA<br/>━━━━━━━━━━━━━━━━━━━<br/>• Escreve relatório em<br/>  historico_auditorias/<br/>  Auditoria_[timestamp].txt<br/><br/>• Atualiza session state<br/>  st.session_state.relatorio_final<br/>  st.session_state.erros"]
    
    PERSIST --> SUCCESS["🟢 CONCLUSÃO (Sucesso)<br/>Relatório pronto para display<br/>e download"]
    
    SUCCESS --> END["Utilizador vê resultados<br/>na interface Streamlit"]
    END_FAIL --> END
    
    style START fill:#90caf9,stroke:#1976d2,stroke-width:2px
    style READ fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style POPULATE fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style ROUTER fill:#ffccbc,stroke:#ff6f00,stroke-width:2px
    style CROSS fill:#b3e5fc
    style SINGLE fill:#b3e5fc
    style EXTRACT fill:#ce93d8,stroke:#7b1fa2,stroke-width:2px
    style EXTRACTOK fill:#fff9c4,stroke:#fbc02d
    style VALIDATE fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style VALIDATEOK fill:#fff9c4,stroke:#fbc02d
    style AUDIT fill:#b2dfdb,stroke:#00796b,stroke-width:2px
    style AUDITOK fill:#fff9c4,stroke:#fbc02d
    style DEDUPE fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    style FORMAT fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px
    style PERSIST fill:#a5d6a7,stroke:#2e7d32,stroke-width:2px
    style SUCCESS fill:#90caf9,stroke:#1976d2,stroke-width:2px
    style END fill:#90caf9,stroke:#1976d2,stroke-width:2px
    style ERROR1 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style ERROR2 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style ERROR3 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style END_FAIL fill:#ef5350,stroke:#c62828,stroke-width:2px
```

---

## Diagrama 2: Fluxo Simplificado (Visão Executiva)

```mermaid
graph TD
    A["📥 ENTRADA<br/>Documentos + Contexto"] --> B["📖 LEITURA"]
    B --> C["🚦 ROUTER"]
    C --> D["🔷 EXTRAÇÃO<br/>AGT-01 + AGT-02"]
    D --> E["✓ VALIDAÇÃO"]
    E --> F["🔶 AUDITORIA<br/>AGT-03"]
    F --> G["🟡 DEDUPE"]
    G --> H["🎨 FORMATO"]
    H --> I["💾 PERSISTÊNCIA"]
    I --> J["📤 SAÍDA<br/>Relatório final"]
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style B fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style C fill:#ffccbc,stroke:#ff6f00,stroke-width:2px
    style D fill:#ce93d8,stroke:#7b1fa2,stroke-width:2px
    style E fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style F fill:#b2dfdb,stroke:#00796b,stroke-width:2px
    style G fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    style H fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px
    style I fill:#a5d6a7,stroke:#2e7d32,stroke-width:2px
    style J fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
```

---

## Diagrama 3: Fluxo com Nós LangGraph

```mermaid
graph TD
    START["INÍCIO"] --> READ["Leitura Documentos<br/>fora LangGraph"]
    
    READ --> INIT["Inicializa Estado<br/>AuditoriaState"]
    
    INIT --> GRAFO1["GRAFO EXTRAÇÃO"]
    
    GRAFO1 --> NODE_R["NÓ: router<br/>determina modo"]
    NODE_R --> NODE_E["NÓ: extrair<br/>AGT-01 + AGT-02<br/>popula resumo_specs<br/>e resumo_boq"]
    
    NODE_E --> COND_E{"Condição:<br/>decidir_apos_extracao<br/><br/>tem_dados?"}
    
    COND_E -->|SIM| END_E["✓ Sucesso<br/>passa estado"]
    COND_E -->|NÃO| NODE_ERR1["NÓ: erro"]
    NODE_ERR1 --> FAIL1["❌ Falha"]
    
    END_E --> GRAFO2["GRAFO AUDITORIA"]
    
    GRAFO2 --> NODE_A["NÓ: auditar<br/>AGT-03<br/>popula auditoria_bruta<br/>e incrementa tentativas"]
    
    NODE_A --> COND_A{"Condição:<br/>decidir_apos_auditoria<br/><br/>len >= 100?"}
    
    COND_A -->|SIM| NODE_D["NÓ: dedupe<br/>popula auditoria_normalizada"]
    COND_A -->|RETRY| NODE_A
    COND_A -->|MAX RETRIES| NODE_ERR2["NÓ: erro"]
    NODE_ERR2 --> FAIL2["❌ Falha"]
    
    NODE_D --> NODE_F["NÓ: formatar<br/>popula relatorio_final"]
    
    NODE_F --> END_OK["✓ Sucesso"]
    
    END_OK --> PERSIST["Persistência<br/>fora LangGraph<br/>histórico + session state"]
    
    PERSIST --> FINAL["🟢 Devolvido à UI"]
    
    FAIL1 --> FINAL
    FAIL2 --> FINAL
    
    style GRAFO1 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style GRAFO2 fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style NODE_R fill:#ce93d8
    style NODE_E fill:#ce93d8
    style NODE_A fill:#a5d6a7
    style NODE_D fill:#a5d6a7
    style NODE_F fill:#a5d6a7
    style COND_E fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style COND_A fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style FINAL fill:#90caf9,stroke:#1976d2,stroke-width:2px
```

---

## Diagrama 4: Ciclo de Transformação de Dados

```mermaid
graph LR
    TX1["texto_boq<br/>texto_specs"] -->|nó router| TX2["modo:<br/>CROSS/SINGLE"]
    
    TX2 -->|nó extrair| TX3["resumo_specs<br/>resumo_boq"]
    
    TX3 -->|decisão| TX4{validação<br/>OK?}
    
    TX4 -->|SIM| TX5["resumo_specs<br/>resumo_boq<br/>contexto_projeto"]
    
    TX5 -->|nó auditar| TX6["auditoria_bruta<br/>tentativas"]
    
    TX6 -->|decisão| TX7{tamanho<br/>OK?}
    
    TX7 -->|SIM| TX8["auditoria_bruta"]
    TX7 -->|RETRY| TX6
    
    TX8 -->|nó dedupe| TX9["auditoria_normalizada"]
    
    TX9 -->|nó formatar| TX10["relatorio_final<br/>com headers<br/>e footer"]
    
    TX10 -->|persistência| TX11["Ficheiro txt<br/>+ session state"]
    
    style TX1 fill:#e3f2fd
    style TX2 fill:#ffe0b2
    style TX3 fill:#ce93d8
    style TX4 fill:#fff9c4
    style TX5 fill:#c8e6c9
    style TX6 fill:#b2dfdb
    style TX7 fill:#fff9c4
    style TX8 fill:#f8bbd0
    style TX9 fill:#f8bbd0
    style TX10 fill:#e1bee7
    style TX11 fill:#a5d6a7
```

---

## Diagrama 5: Árvore de Decisão

```mermaid
graph TD
    A["Pipeline iniciado"] --> B{Documentos<br/>carregados?}
    
    B -->|NÃO| B_ERR["❌ Erro: Sem documentos"]
    B -->|SIM| C["Leitura realizada"]
    
    C --> D{Texto extraído<br/>não-vazio?}
    
    D -->|NÃO| D_ERR["❌ Erro: Sem conteúdo legível"]
    D -->|SIM| E["Extração iniciada"]
    
    E --> F{Ambos resumos<br/>populados?}
    
    F -->|NÃO| F_ERR["❌ Erro: Extração incompleta"]
    F -->|SIM| G["Validação OK"]
    
    G --> H["Auditoria iniciada"]
    
    H --> I{Output >= 100<br/>caracteres?}
    
    I -->|SIM| J["Normalização iniciada"]
    I -->|NÃO| K{Tentativas<br/>< 2?}
    
    K -->|SIM| H
    K -->|NÃO| K_ERR["❌ Erro: Auditoria inconclusiva"]
    
    J --> L["Formatação iniciada"]
    
    L --> M{Relatório<br/>final gerado?}
    
    M -->|SIM| N["✅ Sucesso"]
    M -->|NÃO| M_ERR["❌ Erro: Formatação falhou"]
    
    N --> O["Persistência"]
    O --> P["🟢 Conclusão"]
    
    B_ERR --> P
    D_ERR --> P
    F_ERR --> P
    K_ERR --> P
    M_ERR --> P
    
    style A fill:#e3f2fd
    style B fill:#fff9c4
    style D fill:#fff9c4
    style F fill:#fff9c4
    style I fill:#fff9c4
    style K fill:#fff9c4
    style M fill:#fff9c4
    style N fill:#c8e6c9
    style P fill:#90caf9
    style B_ERR fill:#ffcdd2
    style D_ERR fill:#ffcdd2
    style F_ERR fill:#ffcdd2
    style K_ERR fill:#ffcdd2
    style M_ERR fill:#ffcdd2
```
