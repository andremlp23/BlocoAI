# CHANGELOG — BlocoAI Master Cross-Audit

Todas as alterações ao projecto são documentadas aqui por versão e data.
Formato: `[TIPO] Descrição — ficheiro(s) afectado(s)`

Tipos de alteração:
- `[FEAT]`  — nova funcionalidade
- `[FIX]`   — correcção de bug ou comportamento errado
- `[REFAC]` — refactoring sem alteração de comportamento visível
- `[PERF]`  — melhoria de performance
- `[UI]`    — alteração de interface visual
- `[DOC]`   — documentação

---

## v3.0 — 2026-04-16

### [FIX] Pipeline visual actualiza em tempo real durante execução do grafo — 2026-04-16
**Ficheiro:** `BlocoApps/BlocoAI.py` — bloco de processamento (secção 15)

**Motivação:**
O pipeline visual (AGT-01 / AGT-02 / AGT-03) existia mas não reflectia o estado real
da execução. `grafo_auditoria.invoke()` bloqueia até o grafo terminar, por isso o
utilizador via apenas dois estados: AGT-01 activo → tudo done (ou tudo error).
Os estados intermédios (`AGT-02 activo`, `retry` do AGT-02, `AGT-03 activo`) nunca
eram exibidos, tornando o pipeline visual decorativo em vez de informativo.

**O que foi feito:**
- Substituído `grafo_auditoria.invoke()` por `grafo_auditoria.stream(..., stream_mode="updates")`.
- O stream emite `{node_name: {campos alterados}}` após cada nó concluído.
- Para cada evento do stream, o pipeline visual é actualizado imediatamente via `pipeline_slot.markdown()`.
- Lógica de mapeamento nó → estado visual:
  - `extrair` concluído → `["done", "active", "idle"]`
  - `auditar` com output válido → `["done", "done", "active"]`
  - `auditar` com output fraco e tentativas < 2 → `["done", "retry", "idle"]` (estado âmbar visível)
  - `auditar` esgotou tentativas → `["done", "error", "idle"]`
  - `formatar` concluído → `["done", "done", "done"]`
  - `erro` → estado de erro no agente responsável (detectado por prefixo nas mensagens de erro)
- Estado final acumulado via `estado_final.update(updates)` a cada evento.

**Comportamento anterior vs. novo:**

| Situação | Antes | Depois |
|---|---|---|
| AGT-01 a correr | Pipeline mostra AGT-01 activo | Igual |
| AGT-01 termina, AGT-02 começa | Pipeline continua a mostrar AGT-01 activo | AGT-01 done, AGT-02 activo |
| AGT-02 faz retry | Estado `retry` nunca visível | Pipeline mostra âmbar/↺ durante retry |
| AGT-02 termina, AGT-03 começa | Pipeline continua a mostrar AGT-01 activo | AGT-02 done, AGT-03 activo |
| AGT-01 falha | Tudo error | Só AGT-01 error |
| AGT-02 falha após retries | Tudo error | AGT-01 done, AGT-02 error |

---

### [REFAC] Migração para LangGraph — orquestração por grafo de estado
**Ficheiro:** `BlocoApps/BlocoAI.py`

**Motivação:**
A versão anterior orquestrava os 3 agentes com código Python linear e variáveis
locais soltas. Não havia gestão de erros entre agentes, retry automático,
nem estado centralizado. Uma falha num agente propagava-se sem controlo.

**O que foi feito:**
- Introduzido `AuditoriaState` (TypedDict) como estado partilhado e tipado entre agentes.
- Cada agente passou a ser um nó independente (`nó_router`, `nó_extrator`,
  `nó_auditor`, `nó_apresentador`, `nó_erro`).
- Grafo compilado com `StateGraph` do LangGraph, substituindo a sequência manual.
- Adicionadas edges condicionais:
  - Após `nó_extrator`: se não há dados → `nó_erro`; se há dados → `nó_auditor`.
  - Após `nó_auditor`: se output válido → `nó_apresentador`; se fraco e tentativas < 2 → retry; se fraco e tentativas ≥ 2 → `nó_erro`.

**Comportamento anterior vs. novo:**

| Situação | Antes | Depois |
|---|---|---|
| AGT-02 falha com output vazio | crash ou resultado incompleto | retry automático até 2x |
| Falha num agente | excepção não tratada | capturada no `nó_erro`, pipeline termina com mensagem clara |
| Estado entre agentes | variáveis locais em Python | `AuditoriaState` centralizado e tipado |
| Fluxo | hardcoded sequencial | grafo com condicionais |

**Dependência nova:** `langgraph` (`pip install langgraph`)

---

### [FEAT] Chunking com sobreposição por linhas completas
**Ficheiro:** `BlocoApps/BlocoAI.py` — função `_chunkar()`

**Motivação:**
O chunking anterior dividia o texto a cada N caracteres, sem considerar
limites de linha. Especificações multi-linha na fronteira entre chunks
eram enviadas partidas ao AGT-01, resultando em extracção incompleta.

**O que foi feito:**
- `_chunkar()` reescrita para acumular linhas completas (não caracteres).
- Sobreposição de `overlap_linhas=8` linhas entre chunks consecutivos.
- As últimas 8 linhas de cada chunk repetem-se no início do seguinte,
  garantindo contexto completo para specs na fronteira.

**Comportamento anterior vs. novo:**

```
ANTES — corte por caracteres:
  chunk 1: "...Proteção ao Fogo | Intumescent Paint | 2 Hr R"
  chunk 2: "120 | Zones A3 + B2..."     ← spec partida ao meio

DEPOIS — corte por linha completa com overlap:
  chunk 1: "...Proteção ao Fogo | Intumescent Paint | 2 Hr R120 | Zones A3 + B2"
  chunk 2: "[últimas 8 linhas do chunk 1] ..."  ← contexto preservado
```

---

### [FIX] Filtragem de ruído no Excel mais completa
**Ficheiro:** `BlocoApps/BlocoAI.py` — constante `RUIDO` + `read_document()`

**Motivação:**
A lista anterior (`['nan','none','0.0','0','']`) não cobria valores comuns
em orçamentos reais como `N/A`, `TBD`, `TBC`, `-`, `#REF!`, `#VALUE!`.
Estes valores eram enviados ao LLM como conteúdo, desperdiçando tokens.

**O que foi feito:**
- Criada constante global `RUIDO` com lista expandida de valores a ignorar.
- Adicionado filtro de comprimento mínimo (`len(v.strip()) > 1`).

**Lista completa:**
```python
RUIDO = {'nan','none','0.0','0','','n/a','tbd','tbc','-','--',
         '---','#n/a','#ref!','#value!','#name?'}
```

---

### [FEAT] Aviso de páginas PDF sem texto detectável
**Ficheiro:** `BlocoApps/BlocoAI.py` — `read_document()` + UI

**Motivação:**
Quando o pdfplumber não conseguia extrair texto de uma página (digitalização
ou imagem embebida), o sistema continuava silenciosamente sem avisar o
utilizador. O relatório ficava incompleto sem explicação.

**O que foi feito:**
- `read_document()` passa a devolver `(texto, paginas_sem_texto)`.
- Lista de páginas sem texto acumulada durante a leitura de todos os ficheiros.
- Aviso visual em âmbar exibido na UI se alguma página for detectada.

**Formato do aviso:**
```
⚠ Páginas sem texto detectadas (possível digitalização):
  orcamento.pdf pág.12, caderno_encargos.pdf pág.3, pág.7 — conteúdo não foi analisado.
```

---

### [FEAT] Persistência automática de relatórios
**Ficheiro:** `BlocoApps/BlocoAI.py` — bloco de processamento

**Motivação:**
O `st.session_state` do Streamlit perde-se ao fechar o browser. O utilizador
perdia o relatório se não fizesse download imediatamente.

**O que foi feito:**
- Após cada auditoria concluída com sucesso, o relatório é guardado
  automaticamente em `historico_auditorias/Auditoria_YYYYMMDD_HHMM.txt`.
- Falha silenciosa se a pasta não puder ser criada (não bloqueia o utilizador).
- Pasta criada automaticamente se não existir.

---

### [UI] Estado `retry` no pipeline visual
**Ficheiro:** `BlocoApps/BlocoAI.py` — `render_pipeline()` + CSS

**Motivação:**
O pipeline visual tinha 4 estados (idle, active, done, error). Com o retry
do LangGraph para o AGT-02, era necessário um quinto estado visualmente
distinto para comunicar "a tentar de novo".

**O que foi feito:**
- Novo estado `retry` com cor âmbar (`#cc8800`) e animação `pulse-amber` (0.9s).
- Ícone `↺` para o estado retry.
- Diferenciado visualmente do `active` (azul) e do `error` (vermelho).

---

### [UI] Sidebar actualizada para v3.0 LangGraph
**Ficheiro:** `BlocoApps/BlocoAI.py` — sidebar

**O que foi feito:**
- Versão actualizada de `v2.0` para `v3.0 · LangGraph`.
- Painel de modelos actualizado para mostrar `retry×2` no AGT-02.

---

## [PERF] + [FIX] Retry com backoff exponencial via tenacity — 2026-04-16
**Ficheiro:** `BlocoApps/BlocoAI.py` — `_invocar_llm()` + todos os agentes

**Motivação:**
Todas as chamadas ao LLM usavam `llm.invoke()` directamente, sem qualquer
estratégia de retry. Uma falha de rede de 2 segundos ou um pico de rate
limit (429) resultava na perda definitiva do chunk sem nova tentativa.
Adicionalmente, a detecção de erros 429 era feita por `"429" in str(e)`,
frágil e dependente do formato da mensagem de erro.

**O que foi feito:**
- Criada função centralizada `_invocar_llm(llm, mensagens)` com decorator
  `@retry` do `tenacity`.
- Todos os agentes (AGT-01, AGT-02, AGT-03) passam a chamar `_invocar_llm`
  em vez de `llm.invoke` directamente.
- Erros capturados por tipo (não por string parsing):
  - `RateLimitError` — rate limit da API (429)
  - `APIConnectionError` — falha de rede
  - `APITimeoutError` — timeout da chamada
- Erros não-transitórios (`AuthenticationError`, `BadRequestError`, etc.)
  falham imediatamente sem retry — comportamento correcto.

**Comportamento do retry:**
```
Tentativa 1 falha → espera 2s  → tenta de novo
Tentativa 2 falha → espera 4s  → tenta de novo
Tentativa 3 falha → espera 8s  → tenta de novo
Tentativa 4 falha → lança excepção para o nó de erro do LangGraph
```

**Mensagem de erro melhorada:**
```
ANTES: "[Erro no bloco 7: HTTPStatusError: 429 Too Many Requests ...]"
DEPOIS: "[Bloco 7 não processado após retries: RateLimitError]"
```

**Dependência nova:** `tenacity` (`pip install tenacity`)

---

## v2.0 — 2026-04-16

### [UI] Redesign completo da interface — Dark + Azul Técnico
**Ficheiro:** `BlocoApps/BlocoAI.py`

**Motivação:**
A v1.0 usava a interface padrão branca do Streamlit, sem hierarquia visual
clara e sem feedback do estado dos agentes durante o processamento.

**O que foi feito:**
- Dark theme completo (`#0a0e1a`) com acentos azul técnico (`#3a8eff`).
- Tipografia: `Space Mono` (labels técnicos) + `DM Sans` (corpo).
- Header band com gradiente, logo e badge de estado da API.
- Pipeline visual de 3 etapas com estados idle/active/done/error.
- Section cards numerados (STEP 01/03, 02/03, 03/03).
- File chips com nome, extensão e tamanho após upload.
- Área de resultados com métricas (ficheiros, fases, status).
- CSS injectado via `st.markdown()` com seletores `data-testid` estáveis.

---

## v1.0 — 2026-04-15

### [FEAT] Sistema de 3 Agentes com OpenAI GPT-4o-mini
**Ficheiro:** `BlocoApps/BlocoAI.py` (versão inicial)

**Motivação:**
As versões anteriores (`BlocoAI_pdf.py`, `BlocoAI_steel.py`) usavam um único
agente Ollama. A qualidade de extracção era limitada e não havia lógica de
cross-document audit.

**O que foi feito:**
- AGT-01 Extrator (`gpt-4o-mini`, `temperature=0.0`) — extracção de specs por chunks.
- AGT-02 Auditor Sénior (`gpt-4o-mini`, `temperature=0.1`) — cross-audit e deduplicação.
- AGT-03 Apresentador (`gpt-4o-mini`, `temperature=0.1`) — formatação em Markdown.
- Detecção automática de modo CROSS-DOCUMENT vs. SINGLE-DOCUMENT.
- Rastreabilidade de ficheiro e linha em todos os extracts.
- Download do relatório em `.txt`.
- Migração de Ollama local para OpenAI cloud.

---

## Protótipos Experimentais

### BlocoAI_steel.py — Extractor especializado em estruturas metálicas
- Suporte multi-motor: Ollama local / remoto / OpenAI API Key.
- Chunking por linhas completas (primeira implementação).
- Matriz de auditoria editável pelo utilizador.
- Deduplicação em Python (não via LLM).
- Exportação para DataFrame / CSV.
- Gestão rudimentar de rate limits (sleep fixo de 25s).

### BlocoAI_pdf.py — Auditoria de conformidade em PDF (Modo Esponja)
- Primeira utilização de `pdfplumber` com `layout=True`.
- Actualização em tempo real via `st.empty()`.
- Expanders com texto cru de cada chunk para debugging.
- Modelo: Ollama (Qwen 3.5 9B / Llama 3.2 3B).

### app.py — Protótipo inicial
- Validação da hipótese central: LLM consegue extrair specs de orçamentos.
- Streamlit + Ollama. Loop simulado. Sem chunking real.
- 68 linhas. Output em tabs (Relatório + JSON).
