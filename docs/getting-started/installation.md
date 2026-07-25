# Instalação

## Requisitos

- Python 3.9 ou superior
- pip 21+

## Instalação via pip

```bash
pip install guimitestai
```

## Instalação com extras

```bash
# Com suporte a LangFuse
pip install "guimitestai[langfuse]"

# Com suporte a LangSmith
pip install "guimitestai[langsmith]"

# Tudo incluído
pip install "guimitestai[all]"
```

## Verificar instalação

```bash
guimi --version
# guimitestai 0.1.0

guimi health
# ✅ SDK OK
# ✅ Conexão com API OK
# ✅ Módulos carregados: evaluation, observability, security, compliance
```

## Variáveis de ambiente

```bash
# Obrigatório
export GUIMI_API_KEY="sua-chave"

# Opcional — para integrações
export LANGFUSE_SECRET_KEY="..."
export LANGFUSE_PUBLIC_KEY="..."
export LANGSMITH_API_KEY="..."
```

## Instalação para desenvolvimento

```bash
git clone https://github.com/guimitestai/sdk.git
cd sdk
pip install -e ".[dev]"
```
