# CONTRIBUTING — Processo Standard de Alterações ao BlocoAI

Este documento define o processo obrigatório para qualquer alteração ao projecto,
seja feita por humano ou por IA. O objectivo é garantir rastreabilidade total,
evitar regressões silenciosas e manter o projecto compreensível no futuro.

---

## 1. Antes de qualquer alteração

### 1.1 Classifica a alteração

Toda a alteração tem um tipo:

| Tipo | Quando usar |
|---|---|
| `[FEAT]` | Nova funcionalidade que não existia |
| `[FIX]` | Correcção de bug ou comportamento errado |
| `[REFAC]` | Mudança interna sem impacto visível no comportamento |
| `[PERF]` | Melhoria de performance (velocidade, custo, tokens) |
| `[UI]` | Alteração visual na interface |
| `[DOC]` | Documentação apenas (sem código) |

Uma alteração pode ter mais de um tipo: `[FEAT] + [PERF]`.

### 1.2 Identifica o impacto

Antes de escrever uma linha de código, responde a estas três perguntas:

1. **O que está errado ou em falta?** — descreve o problema concreto,
   não a solução.
2. **O que vai mudar?** — lista os ficheiros e funções afectadas.
3. **O que pode quebrar?** — identifica dependências e efeitos secundários.

Se a alteração muda comportamento visível para o utilizador (output diferente,
novo campo, nova mensagem, novo fluxo), **confirma com o utilizador antes
de implementar**.

---

## 2. Durante a implementação

### 2.1 Regras de código

- **Uma alteração de cada vez.** Não mistures um FEAT com um REFAC
  no mesmo commit/sessão sem documentar ambos separadamente.
- **Não apagues código que funciona** sem perceber primeiro porque existe.
  Código "estranho" tem frequentemente uma razão de ser.
- **Preserva toda a funcionalidade existente** salvo instrução explícita
  em contrário.
- **Testa mentalmente o caminho de erro**: o que acontece se o utilizador
  não tiver internet? Se o ficheiro estiver vazio? Se a API Key for inválida?

### 2.2 Commits atómicos

Cada alteração distinta deve ser identificável. Se fizeres 3 melhorias,
documenta as 3 separadamente no CHANGELOG — não as mistures numa entrada.

---

## 3. Após a implementação — OBRIGATÓRIO

### 3.1 Actualizar o CHANGELOG.md

**Toda a alteração, sem excepção, é registada no `CHANGELOG.md`.**

Formato obrigatório de cada entrada:

```markdown
## [TIPO] Título curto e descritivo — YYYY-MM-DD
**Ficheiro(s):** `caminho/para/ficheiro.py` — função ou secção afectada

**Motivação:**
Porque é que esta alteração foi necessária? Que problema resolve?
Descreve o problema, não a solução.

**O que foi feito:**
- Lista concisa das mudanças técnicas efectuadas.
- Uma linha por mudança.

**Comportamento anterior vs. novo:** (quando relevante)

| Situação | Antes | Depois |
|---|---|---|
| ... | ... | ... |

**Dependência nova:** (se aplicável)
`nome-pacote` (`pip install nome-pacote`)
```

### 3.2 Verifica os ficheiros de documentação existentes

Após qualquer alteração relevante, verifica se é necessário actualizar:

| Ficheiro | Quando actualizar |
|---|---|
| `CHANGELOG.md` | **Sempre** — toda a alteração |
| `RELATORIO_DESENVOLVIMENTO_BlocoAI.txt` | Quando a arquitectura mudar |
| `RESPOSTAS_CRITICAS_BlocoAI.txt` | Quando uma limitação for resolvida |

---

## 4. Checklist de validação

Antes de considerar uma alteração concluída, valida:

```
[ ] O CHANGELOG.md foi actualizado com entrada completa
[ ] A funcionalidade existente não foi alterada (salvo instrução)
[ ] O código novo não introduz imports desnecessários
[ ] Erros são tratados explicitamente (não silenciados com pass)
[ ] Mensagens de erro são informativas (indicam o tipo e contexto do erro)
[ ] Se foi adicionada dependência nova → está documentada no CHANGELOG
[ ] Se o comportamento visível mudou → foi confirmado com o utilizador
```

---

## 5. Dependências do projecto

Sempre que uma nova dependência for adicionada, regista aqui:

| Pacote | Versão mínima | Usado em | Adicionado em |
|---|---|---|---|
| `streamlit` | ≥ 1.30 | Interface web | v1.0 |
| `pandas` | ≥ 2.0 | Leitura de Excel | v1.0 |
| `pdfplumber` | ≥ 0.10 | Leitura de PDFs | v1.0 |
| `langchain-core` | ≥ 0.2 | SystemMessage, HumanMessage | v1.0 |
| `langchain-openai` | ≥ 0.1 | ChatOpenAI wrapper | v1.0 |
| `openai` | ≥ 1.0 | Tipos de erro (RateLimitError, etc.) | v3.0 |
| `langgraph` | ≥ 0.1 | Orquestração por grafo de estado | v3.0 |
| `tenacity` | ≥ 8.0 | Retry com backoff exponencial | v3.0 |
| `openpyxl` | ≥ 3.1 | Exportação Excel (`excel_export.py`) | v1.0 |

Comando de instalação completo:
```bash
pip install streamlit pandas pdfplumber langchain-core langchain-openai \
            openai langgraph tenacity openpyxl
```

---

## 6. Estrutura de ficheiros do projecto

```
LangGraph-test/
├── BlocoApps/
│   ├── BlocoAI.py          ← Aplicação principal (versão activa)
│   ├── BlocoAI_pdf.py      ← Protótipo PDF com Ollama (arquivo)
│   ├── BlocoAI_steel.py    ← Protótipo Aço multi-motor (arquivo)
│   └── excel_export.py     ← Exportador JSON → Excel (CLI standalone)
├── historico_auditorias/   ← Criado automaticamente; relatórios persistidos
├── app.py                  ← Protótipo inicial Ollama (arquivo)
├── app2.py                 ← Utilitário de diagnóstico Ollama (arquivo)
├── CHANGELOG.md            ← Este ficheiro de alterações
├── CONTRIBUTING.md         ← Este processo standard
├── RELATORIO_DESENVOLVIMENTO_BlocoAI.txt
└── RESPOSTAS_CRITICAS_BlocoAI.txt
```

---

## 7. Convenções de código

### Nomes de funções
- Funções internas (não são nós do grafo): `_minuscula_com_underscore()`
- Nós do grafo LangGraph: `nó_nome_do_nó()`
- Funções de leitura: `read_*`
- Funções de renderização UI: `render_*`

### Comentários de secção
Usar a convenção de separadores já estabelecida:
```python
# ─────────────────────────────────────────────
# N. TÍTULO DA SECÇÃO
# ─────────────────────────────────────────────
```

### Constantes globais
Em maiúsculas no topo do ficheiro, após os imports:
```python
RUIDO = {'nan', 'none', ...}
STEPS = [("AGT-01", ...), ...]
```

### Mensagens de erro
Sempre incluir: qual agente, qual tipo de erro, contexto relevante.
```python
# Bom
erros.append(f"AGT-02 tentativa {tentativas} ({type(e).__name__}): {e}")

# Mau
erros.append(f"Erro: {e}")
```

---

## 8. O que confirmar com o utilizador antes de implementar

**Confirmar sempre** quando a alteração:
- Muda o output visível (novo campo, nova secção, formato diferente)
- Adiciona um novo passo ao fluxo do utilizador
- Remove uma funcionalidade existente
- Altera o comportamento por defeito de qualquer parâmetro
- Adiciona uma dependência externa nova

**Não é necessário confirmar** quando a alteração:
- É puramente interna (refactoring sem impacto visível)
- Corrige um bug com comportamento claramente errado
- Melhora mensagens de erro
- Actualiza documentação

---

*Última actualização: 2026-04-16 · v3.0*
