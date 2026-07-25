# NIST AI Risk Management Framework

O NIST AI RMF organiza a gestão de riscos de IA em 4 funções: **Govern**, **Map**, **Measure** e **Manage**.

```python
from guimitestai.compliance import ComplianceChecker

checker = ComplianceChecker()
report = checker.run_nist_audit(
    system_description="Modelo de análise de crédito",
    maturity_level="initial"  # "initial", "managed", "defined", "optimizing"
)

print(f"Score NIST AI RMF: {report.nist_score}/10")
```

!!! info "Documentação completa em breve"
    A documentação detalhada do módulo NIST AI RMF está sendo preparada para a Sprint 2.
