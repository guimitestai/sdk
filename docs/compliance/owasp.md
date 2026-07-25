# OWASP LLM Top 10

O OWASP LLM Top 10 lista as 10 vulnerabilidades mais críticas em aplicações baseadas em Large Language Models.

## Vulnerabilidades cobertas pelo Guimí

| # | Vulnerabilidade | Teste automático |
|---|----------------|-----------------|
| LLM01 | Prompt Injection | ✅ |
| LLM02 | Insecure Output Handling | ✅ |
| LLM03 | Training Data Poisoning | 🔜 |
| LLM04 | Model Denial of Service | ✅ |
| LLM05 | Supply Chain Vulnerabilities | 🔜 |
| LLM06 | Sensitive Information Disclosure | ✅ |
| LLM07 | Insecure Plugin Design | 🔜 |
| LLM08 | Excessive Agency | ✅ |
| LLM09 | Overreliance | ✅ |
| LLM10 | Model Theft | 🔜 |

```python
from guimitestai.security import RedTeamer

red_team = RedTeamer(target_url="https://sua-api.com/chat")
report = red_team.run_owasp_scan(language="pt-BR")

print(f"Score OWASP: {report.owasp_score}/10")
```
