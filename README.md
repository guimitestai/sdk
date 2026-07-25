# 🐺 Guimí Test AI

> Plataforma unificada de testes, observabilidade e compliance para sistemas de IA.
> Inspirado no lobo-guará — espécie-chave do Cerrado que regula e protege o ecossistema.

[![PyPI version](https://badge.fury.io/py/guimitestai.svg)](https://pypi.org/project/guimitestai/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/EmersonGuilherme/guimitestai/actions/workflows/publish.yml/badge.svg)](https://github.com/EmersonGuilherme/guimitestai/actions)

---

## O que é?

O **Guimí Test AI** é um SDK Python que unifica em uma única biblioteca:

| Módulo | Função |
|---|---|
| 🧪 **Evaluation** | Avaliação LLM-as-Judge com múltiplos critérios |
| 🔭 **Observability** | Tracing de operações com latência, tokens e erros |
| 🛡️ **Security** | Red teaming automatizado baseado em OWASP LLM Top 10 |
| 📋 **Compliance** | Verificação de conformidade LGPD, EU AI Act, NIST, ISO 42001 |
| 🔗 **Integrations** | Conectores nativos para LangFuse e LangSmith |

---

## Instalação

```bash
# Instalação básica
pip install guimitestai

# Com suporte a LangFuse
pip install guimitestai[langfuse]

# Com suporte a LangSmith
pip install guimitestai[langsmith]

# Com suporte a OpenAI (para avaliação local)
pip install guimitestai[openai]

# Tudo incluído
pip install guimitestai[all]
```

---

## Uso Rápido

### Avaliação LLM-as-Judge

```python
from guimitestai import GuimiClient

async def main():
    async with GuimiClient(api_url="http://localhost:3000") as client:
        result = await client.evaluate(
            input="Qual é a capital do Brasil?",
            output="Brasília",
            expected="Brasília",
            criteria="correctness"
        )
        print(f"Score: {result.score:.2f} | Passou: {result.passed}")
        # Score: 1.00 | Passou: True
```

### Avaliação Local (sem servidor)

```python
from guimitestai.evaluation import Evaluator

evaluator = Evaluator(model="gpt-4o-mini", threshold=0.7)

result = await evaluator.evaluate(
    input="Explique machine learning em uma frase.",
    output="Machine learning é quando computadores aprendem com dados.",
    criteria="helpfulness"
)
print(f"Score: {result.score} | Raciocínio: {result.reasoning}")
```

### Observabilidade com Tracer

```python
from guimitestai.observability import Tracer

tracer = Tracer()

async with tracer.span("chat_completion", model="gpt-4o") as span:
    span.set_input("Olá, como você está?")
    response = await llm.invoke("Olá, como você está?")
    span.set_output(response.content)
    span.set_tokens(input_tokens=10, output_tokens=25)

print(tracer.summary())
# {'total': 1, 'errors': 0, 'avg_latency_ms': 342, ...}
```

### Red Teaming Automatizado

```python
from guimitestai.security import RedTeamer

async def my_llm(prompt: str) -> str:
    # Sua função de LLM
    return await llm.invoke(prompt)

red_teamer = RedTeamer()
alerts = await red_teamer.run(target=my_llm)

report = red_teamer.report(alerts)
print(f"Ataques: {report['total_attacks']}")
print(f"Vulnerabilidades: {report['vulnerabilities_found']}")
print(f"Taxa: {report['vulnerability_rate']:.1%}")
```

### Verificação de Compliance

```python
from guimitestai.compliance import ComplianceChecker
from guimitestai.core.models import ComplianceFramework

checker = ComplianceChecker()
report = checker.analyze(
    organization="Minha Empresa",
    metrics={
        "has_audit_trail": True,
        "has_human_oversight": False,
        "pii_detected_count": 0,
        "explainability_score": 0.7,
        "has_risk_assessment": True,
        "error_rate": 0.02,
    },
    frameworks=[ComplianceFramework.LGPD, ComplianceFramework.EU_AI_ACT]
)

print(f"Score de Conformidade: {report.overall_score:.1f}%")
print(f"Brechas Críticas: {report.critical_gaps}")
for gap in report.gaps:
    print(f"  [{gap.severity.value.upper()}] {gap.framework.value} {gap.article}: {gap.title}")
```

### Integração com LangFuse

```python
from guimitestai.integrations import LangFuseIntegration

lf = LangFuseIntegration(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
)

# Usar como callback em LangChain
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(callbacks=[lf.callback_handler])

# Registrar score de avaliação
lf.score(trace_id="trace-123", name="correctness", value=0.95)
lf.flush()
```

---

## Configuração via Variáveis de Ambiente

```bash
# API do Guimí Test AI
GUIMI_API_URL=http://localhost:3000
GUIMI_API_KEY=sk-guimi-...

# LangFuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# LangSmith
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=guimitestai
```

---

## Critérios de Avaliação Disponíveis

| Critério | Descrição |
|---|---|
| `correctness` | Precisão factual em relação ao ground truth |
| `helpfulness` | Utilidade e relevância para o usuário |
| `safety` | Ausência de conteúdo prejudicial ou discriminatório |
| `conciseness` | Objetividade e ausência de verbosidade |
| `faithfulness` | Fidelidade ao contexto (RAG), sem alucinações |
| `lgpd_compliance` | Conformidade com privacidade de dados (LGPD) |

---

## Frameworks de Compliance Suportados

| Framework | Cobertura |
|---|---|
| 🇧🇷 **LGPD** | Art. 6, 18, 20, 37, 46 |
| 🇪🇺 **EU AI Act** | Art. 9, 10, 12, 13, 14, 15, 17 |
| 🇺🇸 **NIST AI RMF** | GOVERN, MAP, MEASURE, MANAGE |
| 🔐 **OWASP LLM Top 10** | LLM01–LLM10 |
| 🌐 **ISO/IEC 42001** | Cláusulas 5–10 |

---

## Desenvolvimento

```bash
git clone https://github.com/EmersonGuilherme/guimitestai.git
cd guimitestai
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Licença

MIT © [Emerson Guilherme](https://github.com/EmersonGuilherme)

---

*🐺 Assim como o lobo-guará regula e protege o ecossistema do Cerrado,
o Guimí Test AI monitora, detecta anomalias e protege o ecossistema de IA da sua organização.*
