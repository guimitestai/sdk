# Guimí Test AI

<div class="hero" markdown>

## O nome parece brinquedo. O produto é cirurgia.

**Guimí Test AI** é a plataforma unificada de testes, observabilidade e compliance para LLMs e sistemas de IA — com suporte nativo a **LGPD**, **EU AI Act** e **OWASP LLM Top 10**.

[Começar em 5 minutos](getting-started/quickstart.md){ .md-button .md-button--primary }
[Ver no GitHub](https://github.com/guimitestai/sdk){ .md-button }

</div>

---

## Por que o Guimí?

Você subiu seu LLM em produção. Ele passa no demo. Mas você realmente sabe o que acontece quando um usuário tenta extrair dados pessoais? Quando o modelo alucina em um contexto crítico? Quando uma versão nova regride silenciosamente?

O Guimí fecha esse ciclo — da avaliação pré-produção até o monitoramento em produção, passando por red teaming adversarial e compliance regulatório — em uma única ferramenta, com uma única instalação.

```bash
pip install guimitestai
```

---

## O que o Guimí faz

=== "Avaliação"

    Avalie a qualidade do seu LLM com métricas verificáveis — não "vibe checks".

    ```python
    from guimitestai import GuimiClient

    client = GuimiClient(api_key="sua-chave")
    result = client.evaluate(
        model_response="O prazo de entrega é 5 dias úteis.",
        expected="O prazo é de 5 dias úteis.",
        context="Política de entrega da empresa"
    )
    print(result.score)  # 0.97
    ```

=== "Observabilidade"

    Trace cada chamada LLM em produção — custo, latência, qualidade, anomalias.

    ```python
    from guimitestai.observability import GuimiTracer

    tracer = GuimiTracer()
    async with tracer.span("resposta-usuario") as span:
        response = await seu_llm.generate(prompt)
        span.set_output(response)
    ```

=== "Red Teaming"

    Ataque seu próprio sistema antes que alguém o faça.

    ```python
    from guimitestai.security import RedTeamer

    red_team = RedTeamer(target_url="https://sua-api.com/chat")
    report = red_team.run(
        attacks=["prompt_injection", "jailbreak", "pii_extraction"],
        language="pt-BR"  # ataques em português
    )
    print(f"Vulnerabilidades encontradas: {report.critical_count}")
    ```

=== "Compliance LGPD"

    Verifique automaticamente se seu sistema de IA está em conformidade com a LGPD.

    ```python
    from guimitestai.compliance import ComplianceChecker

    checker = ComplianceChecker()
    report = checker.run_lgpd_audit(
        system_description="Chatbot de atendimento ao cliente",
        sample_interactions=interactions
    )
    print(report.lgpd_score)  # 8.4/10
    ```

---

## Diferenciais

| Capacidade | Guimí | Confident AI | Promptfoo | Giskard | Langfuse |
|-----------|:-----:|:------------:|:---------:|:-------:|:--------:|
| Testes autônomos por IA | ✅ | ❌ | Parcial | ❌ | ❌ |
| Red teaming em PT-BR | ✅ | ❌ | ❌ | ❌ | ❌ |
| Compliance LGPD nativo | ✅ | ❌ | ❌ | ❌ | ❌ |
| Integração LangFuse + LangSmith | ✅ | Parcial | ❌ | ❌ | ✅ |
| Ciclo fechado sem intervenção humana | ✅ | ❌ | ❌ | ❌ | ❌ |
| Interface em português | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Instalação rápida

```bash
# Instalar o SDK
pip install guimitestai

# Verificar instalação
guimi --version

# Inicializar projeto
guimi init meu-projeto
```

---

## Licença

O Guimí Test AI é distribuído sob a **Business Source License 1.1 (BSL 1.1)**. O código-fonte é aberto e auditável. Uso comercial como serviço (SaaS) requer licença comercial.

[Ver licença completa](license.md) · [Planos comerciais](https://guimitestai.com/pricing)
