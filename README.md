
<div align="center">

[![CI Python](https://github.com/guimitestai/sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/guimitestai/sdk/actions/workflows/ci.yml)
[![CI TypeScript](https://github.com/guimitestai/sdk/actions/workflows/ci-typescript.yml/badge.svg)](https://github.com/guimitestai/sdk/actions/workflows/ci-typescript.yml)
[![PyPI version](https://badge.fury.io/py/guimitestai.svg)](https://badge.fury.io/py/guimitestai)
[![npm version](https://badge.fury.io/js/guimitestai.svg)](https://badge.fury.io/js/guimitestai)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License: BSL 1.1](https://img.shields.io/badge/license-BSL%201.1-orange.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-guimitestai.github.io-purple.svg)](https://guimitestai.github.io/sdk/)

**O nome parece brinquedo. O produto é cirurgia.**

Plataforma unificada de testes, observabilidade e compliance para LLMs e sistemas de IA.  
Com suporte nativo a **LGPD**, **EU AI Act** e **OWASP LLM Top 10**.

*Inspirado no lobo-guará — espécie-chave do Cerrado que regula e protege o ecossistema.*

[Documentação](https://guimitestai.github.io/sdk/) · [Quickstart Python](#-quickstart-python) · [Quickstart TypeScript](#-quickstart-typescript) · [Compliance LGPD](#-compliance-lgpd)

</div>

---

## ⚡ Quickstart Python

```bash
pip install guimitestai
guimi init meu-projeto
```

```python
from guimitestai import GuimiClient

client = GuimiClient(api_key="sua-chave")

result = client.evaluate(
    input="Qual é a capital do Brasil?",
    output="Brasília",
    expected="Brasília",
    criteria="correctness"
)
print(f"Score: {result.score:.2f} | Passou: {result.passed}")
# Score: 1.00 | Passou: True
```

---

## ⚡ Quickstart TypeScript

```bash
npm install guimitestai
# ou
pnpm add guimitestai
```

```typescript
import { GuimiClient } from 'guimitestai'

const guimi = new GuimiClient({ apiKey: 'sua-api-key' })

// Avaliar resposta de LLM
const result = await guimi.evaluate({
  input: "Qual a capital do Brasil?",
  output: "Brasília",
  criteria: ["accuracy", "safety"]
})
console.log(result.score)  // 0.95
console.log(result.passed) // true

// Compliance LGPD
const compliance = await guimi.compliance.lgpd("texto da resposta do LLM")
console.log(compliance.compliant) // true

// Red teaming autônomo
const report = await guimi.redTeam.run({
  target: async (prompt) => await meuLLM.chat(prompt)
})
console.log(report.summary.score) // 95 (0-100, 100 = seguro)

// Observabilidade
const trace = await guimi.tracer.trace({ name: "chat-completion", userId: "user-123" })
const span = trace.span({ name: "llm-call", input: prompt })
const response = await meuLLM.chat(prompt)
await span.end(response)
```

---

## 🎯 Por que o Guimí?

Você subiu seu LLM em produção. Ele passa no demo. Mas você sabe o que acontece quando um usuário tenta extrair dados pessoais? Quando o modelo alucina em contexto crítico? Quando uma versão nova regride silenciosamente?

O Guimí fecha esse ciclo — da avaliação pré-produção até o monitoramento em produção, passando por red teaming adversarial e compliance regulatório — **em uma única ferramenta**.

| Capacidade | Guimí | Confident AI | Promptfoo | Giskard | Langfuse |
|-----------|:-----:|:------------:|:---------:|:-------:|:--------:|
| Testes autônomos por IA | ✅ | ❌ | Parcial | ❌ | ❌ |
| Red teaming em PT-BR | ✅ | ❌ | ❌ | ❌ | ❌ |
| Compliance LGPD nativo | ✅ | ❌ | ❌ | ❌ | ❌ |
| SDK TypeScript + Python | ✅ | ❌ | Parcial | ❌ | Parcial |
| Integração LangFuse + LangSmith | ✅ | Parcial | ❌ | ❌ | ✅ |
| Ciclo fechado sem intervenção humana | ✅ | ❌ | ❌ | ❌ | ❌ |
| Interface em português | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 📦 Módulos

| Módulo | Python | TypeScript | Função |
|--------|:------:|:----------:|--------|
| 🧪 **Evaluation** | ✅ | ✅ | Avaliação LLM-as-Judge com múltiplos critérios |
| 🔭 **Observability** | ✅ | ✅ | Tracing com latência, custo por token e anomalias |
| 🛡️ **Security** | ✅ | ✅ | Red teaming automatizado em PT-BR (OWASP LLM Top 10) |
| 🤖 **Autonomous** | ✅ | 🔜 | Descoberta e geração de testes sem intervenção humana |
| 📋 **Compliance** | ✅ | ✅ | LGPD, EU AI Act, NIST AI RMF — relatório pronto para DPO |
| 🔗 **Integrations** | ✅ | 🔜 | LangFuse, LangSmith, Garak como cidadãos de primeira classe |

---

## 🧪 Avaliação (Python)

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

**Critérios disponíveis:** `correctness` · `helpfulness` · `safety` · `conciseness` · `faithfulness` · `lgpd_compliance`

---

## 🔭 Observabilidade (Python)

```python
from guimitestai.observability import Tracer

tracer = Tracer()

async with tracer.span("chat_completion", model="gpt-4o") as span:
    span.set_input("Olá, como você está?")
    response = await llm.invoke("Olá, como você está?")
    span.set_output(response.content)
    span.set_tokens(input_tokens=10, output_tokens=25)

summary = tracer.summary()
print(f"Traces: {summary['total']} | Latência média: {summary['avg_latency_ms']}ms")
```

---

## 🛡️ Red Teaming (Python)

```python
from guimitestai.security import RedTeamer

red_teamer = RedTeamer()
alerts = await red_teamer.run(target=meu_llm)

report = red_teamer.report(alerts)
print(f"Ataques: {report['total_attacks']} | Vulnerabilidades: {report['vulnerabilities_found']}")
print(f"Taxa de vulnerabilidade: {report['vulnerability_rate']:.1%}")
```

---

## 🤖 Testes Autônomos

O Guimí descobre, gera e executa testes sem intervenção humana — o único SDK do mercado com esse ciclo fechado.

```python
from guimitestai.autonomous import AutonomousRunner

runner = AutonomousRunner(target_url="https://sua-api.com/chat")
runner.discover()       # descobre comportamentos automaticamente
runner.generate()       # gera casos de teste com LLM
results = runner.run()  # executa e reporta
print(f"Testes gerados: {results.total} | Falhas: {results.failures}")
```

---

## 🛡️ Compliance LGPD

O Guimí é a **única ferramenta do mundo** com suporte nativo à LGPD aplicada a sistemas de IA, cobrindo os 23 artigos relevantes para IA — incluindo o Art. 20 (decisões automatizadas).

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

print(f"Score LGPD: {report.overall_score:.1f}%")
print(f"Brechas críticas: {report.critical_gaps}")
for gap in report.gaps:
    print(f"  [{gap.severity.value.upper()}] Art. {gap.article}: {gap.title}")
```

**Frameworks cobertos:** LGPD · EU AI Act · OWASP LLM Top 10 · NIST AI RMF · ISO/IEC 42001

[Ver documentação completa de compliance →](https://guimitestai.github.io/sdk/compliance/lgpd/)

---

## 🔌 Integrações

```python
# LangFuse
from guimitestai.integrations import LangFuseIntegration
lf = LangFuseIntegration(public_key="pk-lf-...", secret_key="sk-lf-...")
lf.score(trace_id="trace-123", name="correctness", value=0.95)

# LangSmith
from guimitestai.integrations import LangSmithIntegration
ls = LangSmithIntegration(api_key="ls__...")
```

---

## 🚀 CI/CD

```bash
# Gerar template para o seu sistema de CI/CD
guimi template cicd github-actions > .github/workflows/ai-quality-gate.yml
guimi template cicd gitlab
guimi template cicd jenkins
guimi template cicd azure
guimi template cicd codebuild
```

---

## 📥 Instalação

### Python

```bash
pip install guimitestai                    # básico
pip install "guimitestai[langfuse]"        # + LangFuse
pip install "guimitestai[langsmith]"       # + LangSmith
pip install "guimitestai[all]"             # tudo incluído
```

**Requisitos:** Python 3.9+

### TypeScript / JavaScript

```bash
npm install guimitestai
# ou
pnpm add guimitestai
# ou
yarn add guimitestai
```

**Requisitos:** Node.js 18+, TypeScript 5+ (opcional mas recomendado)

---

## 📚 Documentação

**[guimitestai.github.io/sdk](https://guimitestai.github.io/sdk/)**

- [Quickstart em 5 minutos](https://guimitestai.github.io/sdk/getting-started/quickstart/)
- [Compliance LGPD](https://guimitestai.github.io/sdk/compliance/lgpd/)
- [Guia de CI/CD](https://guimitestai.github.io/sdk/guides/cicd/)
- [Referência da API](https://guimitestai.github.io/sdk/reference/client/)

---

## 🤝 Contribuindo

```bash
# Python
git clone https://github.com/guimitestai/sdk.git
cd sdk
pip install -e ".[dev]"
pytest

# TypeScript
cd sdk-typescript
pnpm install
pnpm test
pnpm build
```

---

## 📄 Licença

Distribuído sob a [Business Source License 1.1](LICENSE). O código-fonte é aberto e auditável. Uso comercial como serviço requer licença comercial.

Em 1º de janeiro de 2028, converte automaticamente para **Apache 2.0**.

---

<div align="center">

Feito no Brasil 🇧🇷 por [Emerson Guilherme](https://github.com/EmersonGuilherme) e a comunidade Guimí.

*🐺 Assim como o lobo-guará regula e protege o ecossistema do Cerrado,
o Guimí Test AI monitora, detecta anomalias e protege o ecossistema de IA da sua organização.*

**[⭐ Star no GitHub](https://github.com/guimitestai/sdk)** · **[📦 PyPI](https://pypi.org/project/guimitestai)** · **[📦 npm](https://www.npmjs.com/package/guimitestai)** · **[📚 Docs](https://guimitestai.github.io/sdk/)**

</div>
