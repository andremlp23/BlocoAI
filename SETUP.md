# 📋 Instruções de Instalação e Configuração - BlocoAI

## Índice

1. [Requisitos do Sistema](#requisitos-do-sistema)
2. [Instalação Passo a Passo](#instalação-passo-a-passo)
3. [Configuração do Ambiente](#configuração-do-ambiente)
4. [Primeiro Uso](#primeiro-uso)
5. [Troubleshooting](#troubleshooting)

---

## Requisitos do Sistema

### Obrigatórios
- **Python**: 3.9 ou superior
- **pip**: 21.0 ou superior
- **Git**: (opcional, para clonar o repositório)

### Recomendado
- **RAM**: Mínimo 4GB (8GB ideal)
- **Disco**: 2GB de espaço livre
- **Conexão Internet**: Necessária para chamadas à API OpenAI

### Compatibilidade de SO
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 18.04+, CentOS 7+)
- ✅ Windows 10/11

---

## Instalação Passo a Passo

### 1️⃣ Clonar ou Descarregar o Projeto

#### Opção A: Via Git (recomendado)
```bash
git clone <url-do-repositorio>
cd BlocoAI
```

#### Opção B: Download Manual
1. Descarregue o arquivo ZIP
2. Descompacte na pasta desejada
3. Abra terminal na pasta raiz

### 2️⃣ Criar Ambiente Virtual

#### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Windows (CMD)
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### 3️⃣ Instalar Dependências

```bash
# Navegue para pasta com requirements.txt
cd src

# Instale as dependências
pip install --upgrade pip
pip install -r requirements.txt
```

**Tempo estimado**: 2-5 minutos (varia conforme conexão)

### 4️⃣ Configurar Variáveis de Ambiente

#### Criar Ficheiro `.env`

```bash
# Linux / macOS
cp .env.example .env
nano .env

# Windows
copy .env.example .env
notepad .env
```

#### Conteúdo do `.env`

```env
# ===== OPENAI CONFIGURATION =====
OPENAI_API_KEY=sk_your_key_here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4000

# ===== STREAMLIT CONFIGURATION =====
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost

# ===== DEBUG & LOGGING =====
DEBUG_MODE=false
LOG_LEVEL=INFO

# ===== PATHS CONFIGURATION =====
CONTEXT_SPECS_PATH=../data/contexts/AGT01_Specs_Context_Latest.json
CONTEXT_BOQ_PATH=../data/contexts/AGT02_BOQ_Context_Latest.json
RULES_PATH=../data/rules/RegrasMekkin.json
AUDIT_LOG_PATH=../audit/historico_auditorias/

# ===== PROCESSING CONFIGURATION =====
MAX_DOCUMENT_SIZE_MB=50
SUPPORTED_FORMATS=pdf,docx,txt
TIMEOUT_SECONDS=300
```

### 5️⃣ Obter Chave API OpenAI

1. Aceda a [platform.openai.com](https://platform.openai.com)
2. Crie uma conta ou faça login
3. Navegue para **API Keys**
4. Clique **Create new secret key**
5. Copie a chave e **guarde num local seguro**
6. Adicione ao `.env`:
   ```env
   OPENAI_API_KEY=sk_your_key_here
   ```

⚠️ **Segurança**: Nunca commit o `.env` ao repositório. Está listado em `.gitignore`.

---

## Configuração do Ambiente

### Estrutura de Pastas

Certifique-se que a estrutura está correta:

```
BlocoAI/
├── src/
│   ├── app.py
│   ├── requirements.txt
│   ├── core/
│   ├── ui/
│   └── .env                  # Crie este ficheiro!
├── data/
│   ├── contexts/
│   ├── rules/
│   └── uploads/
├── docs/
├── audit/
└── README.md
```

### Verificar Instalação

```bash
# Verifique se Python está correto
python --version
# Esperado: Python 3.9+

# Verifique ambiente virtual ativo (deve ter "venv" no prompt)
which python
# macOS/Linux: /path/to/venv/bin/python

# Verifique pacotes instalados
pip list
# Deve incluir: streamlit, langchain, pandas, etc.
```

### Testar Configuração de API

```bash
# Crie ficheiro test_api.py
cat > test_api.py << 'EOF'
import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ ERRO: OPENAI_API_KEY não encontrada")
    exit(1)

client = OpenAI(api_key=api_key)
try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Olá!"}],
        max_tokens=10
    )
    print("✅ API OpenAI funcionando corretamente!")
    print(f"Modelo: {response.model}")
except Exception as e:
    print(f"❌ Erro na API: {e}")
EOF

python test_api.py
```

---

## Primeiro Uso

### 1️⃣ Inicie a Aplicação

```bash
# Certifique-se que está na pasta src/
cd src

# Inicie Streamlit
streamlit run app.py
```

**Esperado**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

### 2️⃣ Abra no Navegador

Aceda a `http://localhost:8501` no seu navegador

### 3️⃣ Primeiro Teste

1. Vá para **"📤 Upload de Documentos"** (barra lateral)
2. Carregue um documento de teste (PDF ou DOCX)
3. Clique em **"Processar Documentos"**
4. Veja os resultados em tempo real

### 4️⃣ Explorar Funcionalidades

- **📊 Dashboard**: Visão geral do sistema
- **⚙️ Configurações**: Ajuste contextos e regras
- **📈 Histórico**: Veja auditorias anteriores
- **💾 Exportar**: Descarregue resultados

---

## Troubleshooting

### ❌ Erro: "ModuleNotFoundError: No module named 'streamlit'"

**Solução**:
```bash
# Verifique se o venv está ativo
which python

# Se não estiver, ative:
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows

# Reinstale:
pip install -r requirements.txt
```

### ❌ Erro: "OPENAI_API_KEY not found"

**Solução**:
1. Verifique se `.env` existe na pasta `src/`
2. Verifique se tem a linha: `OPENAI_API_KEY=sk_...`
3. Reinicie a aplicação: `streamlit run app.py`

### ❌ Erro: "Invalid API key"

**Solução**:
1. Verifique se a chave é válida em [platform.openai.com](https://platform.openai.com)
2. Verifique se não tem caracteres extra (espaços)
3. Tente gerar uma nova chave
4. Adicione ao `.env` e reinicie

### ❌ Erro: "SSL: CERTIFICATE_VERIFY_FAILED"

**Solução** (macOS):
```bash
# Instale os certificados SSL do Python
/Applications/Python\ 3.x/Install\ Certificates.command
```

### ⚠️ Erro: "TimeoutError" ao processar documento

**Solução**:
1. Tente documento mais pequeno
2. Aumente `TIMEOUT_SECONDS` no `.env`
3. Verifique conexão à internet
4. Reinicie a aplicação

### ⚠️ Aplicação muito lenta

**Solução**:
1. Verifique RAM disponível: `free -h` (Linux) ou Task Manager (Windows)
2. Feche outras aplicações
3. Reduza tamanho dos documentos
4. Considere usar modelo mais rápido: `OPENAI_MODEL=gpt-3.5-turbo`

### ⚠️ Porta 8501 já em uso

**Solução**:
```bash
# Mude a porta no .env
STREAMLIT_SERVER_PORT=8502

# Ou via linha de comando
streamlit run app.py --server.port 8502
```

---

## Atualizações e Manutenção

### Atualizar Dependências

```bash
# Verifique versões disponíveis
pip list --outdated

# Atualize tudo
pip install --upgrade -r requirements.txt

# Ou atualize pacote específico
pip install --upgrade streamlit
```

### Limpar Cache

```bash
# Streamlit cache
rm -rf ~/.streamlit/cache/

# Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Resetar Configurações

```bash
# Voltar ao .env padrão
rm src/.env
cp src/.env.example src/.env

# Edite .env conforme necessário
```

---

## Dicas de Produção

### 1️⃣ Usar Chave API Dedicada (não pessoal)

- Crie chave API específica para BlocoAI
- Defina permissões e limites de utilização
- Monitore gastos em OpenAI dashboard

### 2️⃣ Backup de Dados

```bash
# Backup regular
tar -czf backup_$(date +%Y%m%d).tar.gz data/ audit/

# Ou com script automático (cron job)
0 2 * * * cd /path/to/BlocoAI && tar -czf backups/backup_$(date +\%Y\%m\%d).tar.gz data/ audit/
```

### 3️⃣ Monitoramento

```bash
# Ver logs em tempo real
tail -f audit/historico_auditorias/latest.txt

# Com timestamps
tail -f audit/historico_auditorias/latest.txt | while IFS= read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done
```

### 4️⃣ Otimização de Custos

- Use `gpt-3.5-turbo` para tarefas simples (mais barato)
- Implemente caching de resultados
- Processe documentos em batch (fora de pico)

---

## Proximos Passos

Após instalação bem-sucedida:

1. ✅ Leia o [README.md](README.md)
2. ✅ Explore exemplos em `examples/`
3. ✅ Personalize contextos em `data/contexts/`
4. ✅ Consulte documentação em `docs/`
5. ✅ Teste com seus próprios documentos

---

## 📞 Suporte Técnico

### Verificação de Saúde do Sistema

```bash
# Crie script diagnostics.py
python << 'EOF'
import sys
import os
import importlib

print("=== DIAGNÓSTICO DO SISTEMA ===\n")

# Python
print(f"✓ Python: {sys.version}")

# Ambiente
print(f"✓ Virtual Env: {sys.prefix}")

# Pacotes críticos
packages = ['streamlit', 'langchain', 'pandas', 'openai', 'langgraph']
for pkg in packages:
    try:
        mod = importlib.import_module(pkg)
        version = getattr(mod, '__version__', 'N/A')
        print(f"✓ {pkg}: {version}")
    except ImportError:
        print(f"✗ {pkg}: NÃO INSTALADO")

# Variáveis de ambiente
env_vars = ['OPENAI_API_KEY', 'OPENAI_MODEL', 'DEBUG_MODE']
print("\n=== VARIÁVEIS DE AMBIENTE ===")
for var in env_vars:
    value = os.getenv(var, "NÃO DEFINIDO")
    if var == 'OPENAI_API_KEY':
        value = "***" + value[-5:] if value != "NÃO DEFINIDO" else value
    print(f"{var}: {value}")

print("\n✅ Diagnóstico completo!")
EOF
```

---

**Última Atualização**: 22 de Junho de 2026
