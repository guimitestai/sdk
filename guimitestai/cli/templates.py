"""Gerador de templates CI/CD para integração com o Guimí Test AI."""

from __future__ import annotations

from pathlib import Path

TEMPLATES = {
    "github": {
        "path": ".github/workflows/guimi.yml",
        "content": """\
# Guimí Test AI — GitHub Actions
# Documentação: https://guimitestai.com/docs/ci-cd/github
name: Guimí AI Quality Gate

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 8 * * 1'  # Segunda-feira às 8h — auditoria semanal

jobs:
  guimi-scan:
    name: 🔴 Red Teaming & Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Guimí
        run: pip install guimitestai

      - name: Quick Security Scan (Free)
        run: |
          guimi scan \\
            --target ${{{{ vars.LLM_ENDPOINT_URL }}}} \\
            --profile quick \\
            --output scan-results.json

      - name: Full OWASP LLM Top 10 Scan (Premium)
        if: github.ref == 'refs/heads/main'
        env:
          GUIMI_API_KEY: ${{{{ secrets.GUIMI_API_KEY }}}}
        run: |
          guimi scan \\
            --target ${{{{ vars.LLM_ENDPOINT_URL }}}} \\
            --profile owasp_llm_top10 \\
            --output full-scan-results.json

      - name: Upload Scan Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: guimi-scan-results
          path: '*-scan-results.json'

  guimi-eval:
    name: ⚖️ LLM Evaluation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Guimí
        run: pip install guimitestai

      - name: Evaluate LLM Responses
        run: |
          guimi eval \\
            --dataset tests/llm-test-cases.csv \\
            --criteria correctness \\
            --output eval-results.json

      - name: Check Pass Rate
        run: |
          python3 -c "
          import json, sys
          results = json.load(open('eval-results.json'))
          passed = sum(1 for r in results if r.get('passed'))
          rate = passed / len(results) if results else 0
          print(f'Taxa de aprovação: {passed}/{len(results)} ({rate:.0%})')
          if rate < 0.8:
              print('FALHA: Taxa abaixo de 80%')
              sys.exit(1)
          "

  guimi-audit:
    name: 📋 Compliance Audit (Weekly)
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    env:
      GUIMI_API_KEY: ${{{{ secrets.GUIMI_API_KEY }}}}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Guimí
        run: pip install guimitestai

      - name: LGPD + EU AI Act Audit
        run: |
          guimi audit \\
            --framework lgpd \\
            --org "${{{{ vars.ORGANIZATION_NAME }}}}" \\
            --output lgpd-audit.json

      - name: Upload Compliance Report
        uses: actions/upload-artifact@v4
        with:
          name: compliance-reports
          path: '*-audit.json'
          retention-days: 90
""",
    },
    "gitlab": {
        "path": ".gitlab-ci.yml",
        "content": """\
# Guimí Test AI — GitLab CI/CD
# Documentação: https://guimitestai.com/docs/ci-cd/gitlab

image: python:3.11-slim

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  LLM_ENDPOINT_URL: "http://seu-llm-endpoint/chat"

cache:
  paths:
    - .cache/pip/

stages:
  - security
  - evaluation
  - compliance

# ─── Security Scan ───────────────────────────────────────────────────────────
guimi:quick-scan:
  stage: security
  script:
    - pip install guimitestai -q
    - guimi scan --target $LLM_ENDPOINT_URL --profile quick --output scan-results.json
  artifacts:
    paths:
      - scan-results.json
    expire_in: 30 days
  only:
    - merge_requests
    - main
    - develop

guimi:full-scan:
  stage: security
  script:
    - pip install guimitestai -q
    - guimi scan --target $LLM_ENDPOINT_URL --profile owasp_llm_top10 --output full-scan.json
  artifacts:
    paths:
      - full-scan.json
    expire_in: 90 days
  only:
    - main
  when: manual

# ─── LLM Evaluation ──────────────────────────────────────────────────────────
guimi:eval:
  stage: evaluation
  script:
    - pip install guimitestai -q
    - guimi eval --dataset tests/llm-test-cases.csv --criteria correctness --output eval-results.json
    - |
      python3 -c "
      import json, sys
      results = json.load(open('eval-results.json'))
      passed = sum(1 for r in results if r.get('passed'))
      rate = passed / len(results) if results else 0
      print(f'Taxa de aprovação: {passed}/{len(results)} ({rate:.0%})')
      sys.exit(0 if rate >= 0.8 else 1)
      "
  artifacts:
    paths:
      - eval-results.json
    expire_in: 30 days
  only:
    - merge_requests
    - main

# ─── Compliance Audit (Semanal) ───────────────────────────────────────────────
guimi:audit:
  stage: compliance
  script:
    - pip install guimitestai -q
    - guimi audit --framework lgpd --org "$ORGANIZATION_NAME" --output lgpd-audit.json
  artifacts:
    paths:
      - lgpd-audit.json
    expire_in: 365 days
  only:
    - schedules
  variables:
    GUIMI_API_KEY: $GUIMI_API_KEY
""",
    },
    "azure": {
        "path": "azure-pipelines.yml",
        "content": """\
# Guimí Test AI — Azure DevOps Pipelines
# Documentação: https://guimitestai.com/docs/ci-cd/azure

trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

schedules:
  - cron: '0 8 * * 1'
    displayName: 'Auditoria Semanal de Compliance'
    branches:
      include:
        - main
    always: true

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.11'
  LLM_ENDPOINT_URL: 'http://seu-llm-endpoint/chat'

stages:
  - stage: SecurityScan
    displayName: '🔴 Security Scan'
    jobs:
      - job: QuickScan
        displayName: 'Quick Red Teaming Scan'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - script: pip install guimitestai
            displayName: 'Install Guimí'

          - script: |
              guimi scan \
                --target $(LLM_ENDPOINT_URL) \
                --profile quick \
                --output $(Build.ArtifactStagingDirectory)/scan-results.json
            displayName: 'Run Quick Scan'

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)'
              artifactName: 'guimi-scan-results'

  - stage: Evaluation
    displayName: '⚖️ LLM Evaluation'
    dependsOn: SecurityScan
    jobs:
      - job: EvalLLM
        displayName: 'Evaluate LLM Responses'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - script: pip install guimitestai
            displayName: 'Install Guimí'

          - script: |
              guimi eval \
                --dataset tests/llm-test-cases.csv \
                --criteria correctness \
                --output $(Build.ArtifactStagingDirectory)/eval-results.json
            displayName: 'Evaluate LLM'

          - script: |
              python3 -c "
              import json, sys
              results = json.load(open('$(Build.ArtifactStagingDirectory)/eval-results.json'))
              passed = sum(1 for r in results if r.get('passed'))
              rate = passed / len(results) if results else 0
              print(f'Taxa: {rate:.0%}')
              sys.exit(0 if rate >= 0.8 else 1)
              "
            displayName: 'Check Pass Rate (min 80%)'

  - stage: ComplianceAudit
    displayName: '📋 Compliance Audit'
    condition: and(succeeded(), eq(variables['Build.Reason'], 'Schedule'))
    jobs:
      - job: AuditLGPD
        displayName: 'LGPD Audit'
        variables:
          GUIMI_API_KEY: $(GUIMI_API_KEY)
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - script: pip install guimitestai
            displayName: 'Install Guimí'

          - script: |
              guimi audit \
                --framework lgpd \
                --org "$(ORGANIZATION_NAME)" \
                --output $(Build.ArtifactStagingDirectory)/lgpd-audit.json
            displayName: 'Run LGPD Audit'
            env:
              GUIMI_API_KEY: $(GUIMI_API_KEY)

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)'
              artifactName: 'compliance-reports'
""",
    },
    "jenkins": {
        "path": "Jenkinsfile",
        "content": """\
// Guimí Test AI — Jenkinsfile
// Documentação: https://guimitestai.com/docs/ci-cd/jenkins

pipeline {
    agent any

    environment {
        GUIMI_API_KEY = credentials('guimi-api-key')
        LLM_ENDPOINT_URL = 'http://seu-llm-endpoint/chat'
        ORGANIZATION_NAME = 'Minha Empresa'
    }

    triggers {
        // Auditoria semanal toda segunda-feira às 8h
        cron('0 8 * * 1')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install guimitestai -q'
                sh 'guimi --version'
            }
        }

        stage('Quick Security Scan') {
            steps {
                sh '''
                    guimi scan \\
                        --target ${LLM_ENDPOINT_URL} \\
                        --profile quick \\
                        --output scan-results.json
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'scan-results.json', allowEmptyArchive: true
                }
            }
        }

        stage('LLM Evaluation') {
            steps {
                sh '''
                    guimi eval \\
                        --dataset tests/llm-test-cases.csv \\
                        --criteria correctness \\
                        --output eval-results.json
                '''
                script {
                    def result = sh(
                        script: '''python3 -c "
import json, sys
results = json.load(open('eval-results.json'))
passed = sum(1 for r in results if r.get('passed'))
rate = passed / len(results) if results else 0
print(f'Taxa: {rate:.0%}')
sys.exit(0 if rate >= 0.8 else 1)
"''',
                        returnStatus: true
                    )
                    if (result != 0) {
                        error('Taxa de aprovação abaixo de 80%')
                    }
                }
            }
        }

        stage('Full OWASP Scan') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    guimi scan \\
                        --target ${LLM_ENDPOINT_URL} \\
                        --profile owasp_llm_top10 \\
                        --api-key ${GUIMI_API_KEY} \\
                        --output full-scan.json
                '''
            }
        }

        stage('Compliance Audit') {
            when {
                triggeredBy 'TimerTrigger'
            }
            steps {
                sh '''
                    guimi audit \\
                        --framework lgpd \\
                        --org "${ORGANIZATION_NAME}" \\
                        --api-key ${GUIMI_API_KEY} \\
                        --output lgpd-audit.json
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'lgpd-audit.json', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        failure {
            echo '❌ Pipeline falhou — verifique os resultados do Guimí'
        }
        success {
            echo '✅ Todos os gates de qualidade passaram!'
        }
    }
}
""",
    },
    "aws": {
        "path": "buildspec.yml",
        "content": """\
# Guimí Test AI — AWS CodeBuild buildspec.yml
# Documentação: https://guimitestai.com/docs/ci-cd/aws
# Configure GUIMI_API_KEY como variável de ambiente no CodeBuild

version: 0.2

env:
  variables:
    LLM_ENDPOINT_URL: "http://seu-llm-endpoint/chat"
    ORGANIZATION_NAME: "Minha Empresa"
  parameter-store:
    GUIMI_API_KEY: "/guimitestai/api-key"

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - echo "Instalando Guimí Test AI..."
      - pip install guimitestai -q
      - guimi --version

  pre_build:
    commands:
      - echo "Executando Quick Security Scan..."
      - |
        guimi scan \
          --target $LLM_ENDPOINT_URL \
          --profile quick \
          --output scan-results.json
      - echo "Quick scan concluído"

  build:
    commands:
      - echo "Avaliando respostas do LLM..."
      - |
        guimi eval \
          --dataset tests/llm-test-cases.csv \
          --criteria correctness \
          --output eval-results.json
      - |
        python3 -c "
        import json, sys
        results = json.load(open('eval-results.json'))
        passed = sum(1 for r in results if r.get('passed'))
        rate = passed / len(results) if results else 0
        print(f'Taxa de aprovação: {passed}/{len(results)} ({rate:.0%})')
        sys.exit(0 if rate >= 0.8 else 1)
        "

  post_build:
    commands:
      - echo "Executando auditoria de compliance LGPD..."
      - |
        guimi audit \
          --framework lgpd \
          --org "$ORGANIZATION_NAME" \
          --api-key $GUIMI_API_KEY \
          --output lgpd-audit.json || echo "Auditoria concluída com avisos"
      - echo "Pipeline Guimí concluído!"

artifacts:
  files:
    - scan-results.json
    - eval-results.json
    - lgpd-audit.json
  name: guimi-results-$(date +%Y%m%d)

reports:
  guimi-eval-report:
    files:
      - eval-results.json
    file-format: JUNITXML
""",
    },
}


def generate_ci_template(provider: str, output_dir: str = ".") -> str:
    """Gera um template CI/CD para o provider especificado.

    Args:
        provider: Nome do provider (github, gitlab, azure, jenkins, aws).
        output_dir: Diretório de saída.

    Returns:
        Caminho do arquivo gerado.

    Raises:
        ValueError: Se o provider não for suportado.
    """
    if provider not in TEMPLATES:
        supported = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Provider '{provider}' não suportado. Use: {supported}")

    template = TEMPLATES[provider]
    output_path = Path(output_dir) / template["path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template["content"])
    return str(output_path)
