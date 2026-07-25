# CI/CD — Testes de IA no Pipeline

Integre o Guimí no seu pipeline de CI/CD para garantir que nenhuma regressão de qualidade, segurança ou compliance chegue à produção.

## GitHub Actions

```yaml
# .github/workflows/ai-quality-gate.yml
name: AI Quality Gate

on: [push, pull_request]

jobs:
  ai-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Instalar Guimí
        run: pip install guimitestai

      - name: Rodar testes de avaliação
        env:
          GUIMI_API_KEY: ${{ secrets.GUIMI_API_KEY }}
        run: guimi run --config guimi.yml --fail-on-score-below 0.8

      - name: Verificar compliance LGPD
        run: guimi compliance lgpd --fail-on-violations critical

      - name: Scan de segurança
        run: guimi security scan --attacks prompt_injection,pii_extraction
```

## Arquivo de configuração `guimi.yml`

```yaml
version: 1
project: meu-llm-app

evaluation:
  threshold: 0.80
  metrics:
    - correctness
    - faithfulness
    - answer_relevancy

compliance:
  frameworks:
    - lgpd
    - owasp_llm_top10
  fail_on: critical

security:
  attacks:
    - prompt_injection
    - jailbreak
    - pii_extraction
  language: pt-BR
```

## Templates prontos

O Guimí CLI inclui templates para os principais sistemas de CI/CD:

```bash
# GitHub Actions
guimi template cicd github-actions > .github/workflows/ai-quality-gate.yml

# GitLab CI
guimi template cicd gitlab > .gitlab-ci.yml

# Azure DevOps
guimi template cicd azure > azure-pipelines.yml

# Jenkins
guimi template cicd jenkins > Jenkinsfile

# AWS CodeBuild
guimi template cicd codebuild > buildspec.yml
```
