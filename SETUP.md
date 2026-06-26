# 📋 Instruções de Instalação e Configuração - BlocoAI
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

1. Vá para **"📤 Upload de Documentos"**
2. Carregue um documento de teste (PDF ou DOCX)
3. Clique em **"Processar Documentos"**
4. Veja os resultados em tempo real
---
