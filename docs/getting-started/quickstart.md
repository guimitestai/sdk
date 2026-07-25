# Quickstart — 5 minutos

Este guia coloca o Guimí funcionando no seu projeto em menos de 5 minutos.

## 1. Instalar

```bash
pip install guimitestai
```

Requer Python 3.9 ou superior.

## 2. Configurar

```bash
export GUIMI_API_KEY="sua-chave-aqui"
```

Ainda não tem uma chave? [Crie sua conta gratuita →](https://app.guimitestai.com)

## 3. Primeiro teste de avaliação

```python
from guimitestai import GuimiClient

client = GuimiClient()  # lê GUIMI_API_KEY do ambiente

# Avaliar uma resposta do seu LLM
result = client.evaluate(
    model_response="O prazo de entrega é 5 dias úteis a partir da confirmação do pagamento.",
    expected="O prazo é de 5 dias úteis.",
    context="Política de entrega da empresa XYZ"
)

print(f"Score: {result.score:.2f}")        # 0.94
print(f"Passou: {result.passed}")          # True
print(f"Motivo: {result.reason}")          # "Resposta correta e completa..."
```

## 4. Primeiro trace de observabilidade

```python
import asyncio
from guimitestai.observability import GuimiTracer

tracer = GuimiTracer()

async def main():
    async with tracer.span("minha-chamada-llm") as span:
        # Simule sua chamada LLM aqui
        response = "Resposta do modelo"
        span.set_output(response)
        span.set_metadata({"model": "gpt-4o", "tokens": 150})

asyncio.run(main())

# Ver resumo
summary = tracer.summary()
print(f"Total de traces: {summary['total']}")
print(f"Custo estimado: R$ {summary['estimated_cost_brl']:.4f}")
```

## 5. Primeiro scan de segurança

```python
from guimitestai.security import RedTeamer

red_team = RedTeamer(target_url="http://localhost:8000/chat")

report = red_team.run(
    attacks=["prompt_injection", "pii_extraction"],
    language="pt-BR",
    max_attempts=10
)

print(f"Vulnerabilidades críticas: {report.critical_count}")
print(f"Score de segurança: {report.security_score}/10")
```

## 6. Verificação de compliance LGPD

```python
from guimitestai.compliance import ComplianceChecker

checker = ComplianceChecker()

report = checker.run_lgpd_audit(
    system_description="Chatbot de atendimento ao cliente para e-commerce",
    sample_interactions=[
        {"user": "Qual meu CPF cadastrado?", "assistant": "Seu CPF é 123.456.789-00"},
        {"user": "Me dê meu endereço", "assistant": "Rua das Flores, 123..."}
    ]
)

print(f"Score LGPD: {report.lgpd_score}/10")
print(f"Violações encontradas: {len(report.violations)}")
for v in report.violations:
    print(f"  ⚠️  {v.article}: {v.description}")
```

## Próximos passos

- [Configuração avançada →](configuration.md)
- [Integrar com LangFuse →](../integrations/langfuse.md)
- [Configurar CI/CD →](../guides/cicd.md)
- [Compliance LGPD completo →](../compliance/lgpd.md)
