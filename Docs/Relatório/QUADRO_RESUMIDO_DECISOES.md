# BlocoAI — Decisões em Quadro Resumido
## Referência Rápida para Apresentações

---

## 📑 Quadro Resumido: Decisões por Categoria

### 1. ARQUITETURA GLOBAL

| Aspecto | Decisão | Porquê | Alternativa |
|---------|---------|--------|-------------|
| **Padrão** | 3 Agentes Multi-Agente | Especialização → +15% qualidade | 1 Agente (simples mas fraco) |
| **Integração** | Pipeline sequencial (AGT-01→02→03) | Cada agente recebe output prévio | Paralelo (perda contexto) |
| **Formatação** | Pipe-separado (no meio) | Robusto vs. erros | JSON (10% fail rate) |
| **Persistência** | Streamlit session_state | Sessão do utilizador | Redis (overcomplicated) |
| **Storage Resultados** | Ficheiros .txt (historico_auditorias/) | Simples, auditável, versioning git | Base de dados (overshoot) |

---

### 2. MOTOR LLM & MODELOS

| Aspecto | Decisão | Porquê | Trade-off |
|---------|---------|--------|-----------|
| **Motor Produção** | OpenAI GPT-4o-mini | 85-90% acurácia; custo-benefício | Dados cloud (NDA) |
| **Motor Prototipagem** | Ollama Qwen 9B | Privacidade; sem custos | 65-70% acurácia |
| **Temperatura Extração** | 0.0 (determinismo máximo) | Queremos factualidade pura | 0.5-1.0 (criatividade indesejada) |
| **Temperatura Auditoria** | 0.1 (ligeiramente criativo) | Síntese permitida, mas ancorado | 0.0 (inflexível) |
| **Tamanho Contexto** | 128k tokens (GPT-4o-mini) | 15% utilização = seguro | 4k-8k tokens (Ollama, limitado) |

---

### 3. PROCESSAMENTO DE DADOS

| Aspecto | Decisão | Porquê | Custo |
|---------|---------|--------|-------|
| **Tamanho Chunk** | 75.000 caracteres (~18.75k tokens) | Eficiência (4 chamadas v.s. 20) | Risco "lost in middle" (mitigado) |
| **Tipo Chunking** | Por caracteres + limpeza regex | Simples de implementar | Não semântico (não-ideal) |
| **PDF Extração** | `layout=True` + espacos → 3 máx | Tabelas legíveis | Mais processamento |
| **Formatos Suportados** | Excel, CSV (auto-detect sep.), PDF, DOCX | Flexibilidade utilizador | Complexidade parser |
| **Limpeza Ruído** | Descartar células RUIDO set | Reduzir tokens inúteis | Risco omitir dados válidos |
| **Rastreabilidade** | [Pág: N] e [Linha: N] anotações | Auditabilidade relatório | Mais tokens por linha |

---

### 4. INTERFACE & UX

| Aspecto | Decisão | Porquê | Trade-off |
|---------|---------|--------|-----------|
| **Framework Web** | Streamlit | TTM 3 dias (vs. 2-4 semanas Flask) | CSS customização limitada |
| **Layout** | Sidebar (auth) + Main (workflow) | Padrão familiar apps internas | Menos flexible responsivo |
| **Tema** | Dark mode + laranja Blocotelha | Brand + menos fadiga ocular | Contraste accessibility review |
| **Session State** | Streamlit built-in (não Redis) | Simplicidade; suficiente para uso | Não escala multi-servidor |
| **Debug Mode** | Toggle checkbox (oculto) | Diagnóstico sem afectar utilizador | Info técnica visível se ativado |
| **Progressbar** | Simples (0% → 100%) | Visual feedback | Não mapeia fases reais |

---

### 5. SEGURANÇA & CONFIGURAÇÃO

| Aspecto | Decisão | Porquê | Risco |
|---------|---------|--------|-------|
| **API Key** | Input sidebar (text hidden) + .env fallback | Flexibilidade + segurança | Key visível em memória Streamlit |
| **Carregamento Config** | .env caseiro (não python-dotenv heavy) | Controle explícito | Não trata expansion variables |
| **Dados de Entrada** | BytesIO (em memória) | Não toca disco | Limitado a upload size Streamlit (~200MB) |
| **Relatórios** | .txt plain text (não Excel formatado) | Simples parser | Menos visuais que .xlsx |

---

### 6. ENGENHARIA DE PROMPTS

| Aspecto | Decisão | Porquê | Limitação |
|---------|---------|--------|-----------|
| **Regra EXACT STRINGS** | "Use exact names found in text" | Combater parafrase LLM | Modelo ainda ocasionalmente falha |
| **Filtro Concreto** | Regras JSON isoladas (RegrasMekkin.json) | Reutilizável; fácil manutenção | Requer atualização manual |
| **Formato Output AGT-01** | `[FILE: X\|DOMAIN: Y\|Phase: Z\|Spec: W` | Rastreabilidade completa | Mais verbose |
| **Modo Detectação** | AGT-02 detecta CROSS vs. SINGLE | Adaptável documentos | Heurística pode falhar |
| **Instrução Dedup** | "Do NOT omit items even if lack specs" | Capturar ambíguos | Pode gerar false positives |

---

## 📊 Quadro Comparativo: Versões do Projeto

```
EVOLUÇÃO v1 → v5 (Simplificado)

v1: app.py (Ollama local)
    · 1 Agente
    · Janela 4-8k tokens
    · Chunk 15k chars = 20 chamadas
    · Output: tabs (txt + JSON)
    ❌ Qualidade: 50-60%
    ✅ Privacidade total

v2: BlocoAI_pdf.py (Ollama)
    · 1 Agente especializado
    · layout=True (PDF crucial)
    · Ainda 15k chunks
    · Output: accumulating text_area
    ❌ Qualidade: 60-70%
    ❌ Sem cross-document

v3: BlocoAI_steel.py (Ollama + OpenAI híbrido)
    · 1 Agente Steel Engineer
    · Chunking por linhas completas
    · Multi-motor LLM (seleção UI)
    · Matriz editable + export DataFrame
    ⚠️ Qualidade: 70-75%
    ✅ Editável utilizador

v4: BlocoAI.py v1 (OpenAI GPT-4)
    · 3 Agentes (AGT-01/02/03)
    · Chunk 75k
    · Apenas GPT-4 (não Ollama)
    · Output: relatório estruturado
    ✅ Qualidade: 80-85%
    ✅ Cross-document
    ⚠️ Custo/token ↑

v5: BlocoAI.py v2 + LangGraph (ATUAL)
    · 3 Agentes + LangGraph engine
    · Chunk 75k otimizado
    · GPT-4o-mini (mais barato)
    · UI redesigned (Streamlit melhorado)
    · Multi-formato (Excel/CSV/PDF/DOCX)
    ✅ Qualidade: 85-90%
    ✅ Custo otimizado
    ✅ Produção-ready
```

---

## 🎯 Matriz de Decisão: Custo vs. Benefício

```
ALTO IMPACTO, BAIXO CUSTO:
┌──────────────────────────────────────────────────┐
│ · layout=True PDF                                │
│ · Pipe separator (robustez)                      │
│ · Lazy LLM init (responsiveness)                 │
│ · Anotação [Pág:N] (rastreabilidade)            │
└──────────────────────────────────────────────────┘

ALTO IMPACTO, CUSTO MODERADO:
┌──────────────────────────────────────────────────┐
│ · 3 Agentes (+1 chamada API; +15% qualidade)   │
│ · Chunk 75k (+5s latência; 5x menos chamadas)  │
│ · GPT-4o-mini (dados cloud; mas 85-90% qualid) │
└──────────────────────────────────────────────────┘

BAIXO IMPACTO, CUSTO BAIXO:
┌──────────────────────────────────────────────────┐
│ · Streamlit vs. Flask (TTM vs. flexibilidade)   │
│ · Session state (não Redis)                      │
│ · Dark theme UI                                  │
└──────────────────────────────────────────────────┘

EVITAR:
┌──────────────────────────────────────────────────┐
│ ✗ JSON estruturado (10% fail rate em outputs longos) │
│ ✗ Chunking semântico (complexity ROI negativo)  │
│ ✗ Fine-tuning modelo (dados insuficientes)      │
│ ✗ Multi-agent paralelo (perda contexto)         │
└──────────────────────────────────────────────────┘
```

---

## 🔑 10 Decisões Críticas (Resumo)

| # | Decisão | Porquê |
|---|---------|--------|
| 1 | **3 Agentes Multi-Agente** | Qualidade +15% vs. 1 agente |
| 2 | **GPT-4o-mini em Produção** | 85-90% acurácia (vs. 65-70% Ollama) |
| 3 | **layout=True em PDF** | Tabelas legíveis (diferença vida/morte) |
| 4 | **Chunk 75k** | 4 chamadas API v.s. 20; +5s latência aceitável |
| 5 | **Pipe Separator** | Robusto: JSON tem 10% fail rate |
| 6 | **Streamlit** | TTM 3 dias (vs. 2-4 sem Flask/Django) |
| 7 | **Lazy LLM Init** | Responsiveness; evita timeouts |
| 8 | **Dedup Cliente** | Determinístico; não consome tokens |
| 9 | **Session State** | Não precisa Redis; Streamlit suficiente |
| 10 | **Rastreabilidade [Pág:N]** | Auditabilidade relatório |

---

## 🚨 Top 5 Riscos & Mitigações

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| **Falsa Segurança**: BlocoAI omite inconsistência crítica | 🔴 ALTO | Comunicar que é "1º passe"; utilizador responsável |
| **Qualidade 80-85%**: 15-20% requer revisão | 🟠 MÉDIO | Documentação clara; alertas quando confiança baixa |
| **Lost in Middle**: Contexto 75k pode degrade atenção | 🟡 BAIXO | Teste empírico mostra negligível para extração |
| **Risco Parafrase LLM**: Não transceve exactamente | 🟡 BAIXO | Regra EXACT STRINGS + manual review sample |
| **Custo Cloud (OpenAI)**: Escalabilidade | 🟠 MÉDIO | Cache de extrações; fine-tuning futuro |

---

## ✅ Checklist de Alinhamento: "Porquê Esta Decisão?"

Usar este checklist quando questionar decisão X:

```
☐ Foi experiência empiricamente (testada em dados reais)?
☐ Tem trade-off explícito documentado?
☐ Alternativas foram consideradas (com razões rejeição)?
☐ Há compensação de custo vs. benefício?
☐ Riscos foram identificados & mitigados?
☐ Pode ser revertida em futuro sem rewrite?
☐ Team tem consensus ou razão técnica clara?
```

**Se resposta a tudo é SIM → Decisão é defensável**  
**Se resposta é NÃO → Revisitar decisão**

---

## 📈 Métricas de Sucesso Atual

```
ANTES (Manual):
· Tempo: 0.5-2 dias por projeto
· Custo: 1 engenheiro-dia × €80-100/hora = €640-1600
· Qualidade: 100% (humano) mas lento
· Escala: ~5 projetos/mês

DEPOIS (BlocoAI v3):
· Tempo: 15-30 minutos por projeto
· Custo: ~$0.002 (API) + 5min engenheiro revisão = €10-20
· Qualidade: 80-85% (LLM) + revisão → 95-98%
· Escala: ~50 projetos/mês (10x)

ROI:
· Redução tempo: 96%
· Redução custo: 98%
· Aumento escala: 10x
```

---

## 🔄 Processo de Iteração

**Como esta documentação é mantida?**

```
1. Decisão proposta → Discussão team
2. Teste empírico em dados reais
3. Documentação no RELATORIO_DECISOES_ARQUITETURAIS.md
4. Review por stakeholders (tech + negócio)
5. Implementação
6. Monitorização métricas em produção
7. Revisão trimestral (julgar se ainda válida)
```

**Próxima revisão**: Julho 2026 (pós-features Q2-Q3)

---

## 📚 Documentação Relacionada

- [RELATORIO_DECISOES_ARQUITETURAIS_2026.md](./RELATORIO_DECISOES_ARQUITETURAIS_2026.md) — **Profundo** (20+ páginas)
- [SUMARIO_EXECUTIVO_DECISOES.md](./SUMARIO_EXECUTIVO_DECISOES.md) — **Executivo** (2 páginas)
- [RELATORIO_DESENVOLVIMENTO_BlocoAI.txt](./RELATORIO_DESENVOLVIMENTO_BlocoAI.txt) — **Histórico** (evolução v1-v5)
- [RESPOSTAS_CRITICAS_BlocoAI.txt](./RESPOSTAS_CRITICAS_BlocoAI.txt) — **Q&A Detalhado** (todas as questões)
- [Código-Fonte](../BlocoApps/) — **Implementação**

---

**Compilado**: Abril 2026 | **Versão**: 3.0 | **Status**: Referência Atual
