# EU AI Act

O EU AI Act (Regulamento UE 2024/1689) é o primeiro marco regulatório abrangente para IA do mundo, em vigor desde agosto de 2024.

## O que o Guimí verifica

O Guimí mapeia seu sistema de IA contra os **requisitos do Anexo III** (sistemas de alto risco) e as **obrigações de transparência** para sistemas de IA de propósito geral.

```python
from guimitestai.compliance import ComplianceChecker

checker = ComplianceChecker()

report = checker.run_eu_ai_act_audit(
    system_description="Sistema de triagem de currículos",
    risk_category="high",  # "minimal", "limited", "high", "unacceptable"
    deployment_region="EU"
)

print(f"Score EU AI Act: {report.eu_ai_act_score}/10")
print(f"Categoria de risco: {report.risk_category}")
print(f"Obrigações identificadas: {len(report.obligations)}")
```

## Categorias de risco

| Categoria | Exemplos | Obrigações |
|-----------|---------|-----------|
| **Inaceitável** | Pontuação social, manipulação subliminar | Proibido |
| **Alto risco** | RH, crédito, saúde, educação | Conformidade total antes do lançamento |
| **Limitado** | Chatbots, deepfakes | Transparência obrigatória |
| **Mínimo** | Filtros de spam, recomendações | Sem obrigações específicas |

!!! info "Documentação completa em breve"
    A documentação detalhada do módulo EU AI Act está sendo preparada para a Sprint 2.
