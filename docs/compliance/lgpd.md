# Compliance LGPD para Sistemas de IA

O Guimí Test AI é a **única ferramenta do mundo** com suporte nativo à Lei Geral de Proteção de Dados (LGPD — Lei 13.709/2018) aplicada especificamente a sistemas de inteligência artificial.

!!! tip "Por que isso importa"
    A ANPD (Autoridade Nacional de Proteção de Dados) publicou a **Nota Técnica 12/2025**, que estabelece diretrizes específicas para o uso de IA no tratamento de dados pessoais no Brasil. Empresas que usam LLMs em produção sem auditoria de conformidade estão expostas a multas de até **R$ 50 milhões por infração**.

---

## O que o Guimí verifica automaticamente

O módulo de compliance LGPD do Guimí audita seu sistema de IA contra **23 artigos da LGPD** relevantes para sistemas de IA, organizados em 6 categorias:

### 1. Exposição de Dados Pessoais (Art. 5º, 6º)

O Guimí detecta se o seu LLM está expondo ou processando dados pessoais sem base legal adequada:

- CPF, RG, CNH, passaporte
- Endereços residenciais e comerciais
- Dados bancários e financeiros
- Dados de saúde e biométricos
- E-mail, telefone, IP

```python
from guimitestai.compliance import ComplianceChecker

checker = ComplianceChecker()

# Testar se o modelo expõe dados pessoais
result = checker.check_pii_exposure(
    interactions=suas_conversas,
    sensitivity_level="high"  # "low", "medium", "high"
)

print(result.pii_found)        # Lista de dados pessoais detectados
print(result.exposure_risk)    # "critical", "high", "medium", "low"
```

### 2. Decisões Automatizadas (Art. 20)

O Art. 20 da LGPD garante ao titular o direito de **revisão humana** de decisões tomadas exclusivamente por meios automatizados. O Guimí verifica se seu sistema:

- Toma decisões que afetam direitos do usuário sem revisão humana
- Fornece explicação adequada sobre os critérios da decisão
- Oferece canal para contestação

```python
# Auditar decisões automatizadas
result = checker.check_automated_decisions(
    system_description="Sistema de concessão de crédito por IA",
    decision_examples=exemplos_de_decisoes
)

print(result.requires_human_review)    # True/False
print(result.explainability_score)     # 0-10
print(result.art20_compliant)          # True/False
```

### 3. Finalidade e Minimização (Art. 6º, I e III)

Verifica se o LLM está usando dados além da finalidade declarada e se está coletando mais dados do que o necessário:

```python
result = checker.check_data_minimization(
    declared_purpose="Atendimento ao cliente",
    actual_data_collected=dados_coletados,
    interactions=conversas
)
```

### 4. Segurança e Prevenção (Art. 46)

Testa se o sistema tem medidas técnicas adequadas para proteger dados pessoais contra vazamentos via prompt injection, jailbreak e outras técnicas adversariais:

```python
result = checker.check_security_measures(
    target_url="https://sua-api.com/chat",
    test_pii_extraction=True,
    test_prompt_injection=True
)
```

### 5. Transparência (Art. 6º, VI)

Verifica se o sistema informa adequadamente ao usuário que está interagindo com IA e como seus dados são usados:

```python
result = checker.check_transparency(
    system_prompt=seu_system_prompt,
    user_interface_description="Chatbot de atendimento"
)
```

### 6. Direitos do Titular (Art. 17-22)

Verifica se o sistema respeita os direitos de acesso, correção, exclusão e portabilidade dos dados:

```python
result = checker.check_data_subject_rights(
    deletion_mechanism_exists=True,
    access_mechanism_exists=True,
    portability_mechanism_exists=False
)
```

---

## Auditoria Completa LGPD

Para uma auditoria completa em um único comando:

```python
from guimitestai.compliance import ComplianceChecker

checker = ComplianceChecker()

report = checker.run_lgpd_audit(
    system_description="Assistente virtual de RH para triagem de currículos",
    target_url="https://sua-api.com/chat",
    sample_interactions=suas_conversas,
    include_red_team=True  # testa ativamente tentativas de extração de dados
)

# Score geral
print(f"Score LGPD: {report.lgpd_score}/10")
print(f"Nível de risco: {report.risk_level}")  # "crítico", "alto", "médio", "baixo"

# Violações por artigo
for violation in report.violations:
    print(f"\n⚠️  Art. {violation.article} — {violation.title}")
    print(f"   Descrição: {violation.description}")
    print(f"   Recomendação: {violation.recommendation}")
    print(f"   Multa potencial: R$ {violation.potential_fine:,.0f}")

# Exportar relatório para auditoria
report.export_pdf("relatorio-lgpd-2025.pdf")
report.export_json("relatorio-lgpd-2025.json")
```

---

## Relatório de Conformidade

O Guimí gera relatórios prontos para apresentar ao DPO (Data Protection Officer), ao jurídico e à ANPD:

```
RELATÓRIO DE CONFORMIDADE LGPD — SISTEMAS DE IA
Gerado por: Guimí Test AI v0.1.0
Data: 25/07/2026
Sistema auditado: Assistente virtual de RH

SCORE GERAL: 7.2/10 — RISCO MÉDIO

CONFORMIDADES (14/23 artigos):
  ✅ Art. 5º  — Definição de dados pessoais tratados
  ✅ Art. 7º  — Base legal identificada (legítimo interesse)
  ✅ Art. 46  — Medidas de segurança implementadas
  ...

VIOLAÇÕES (9/23 artigos):
  ❌ Art. 20  — Decisões automatizadas sem revisão humana
     Risco: ALTO | Multa potencial: R$ 2.000.000
     Recomendação: Implementar fluxo de revisão humana para
     decisões de triagem que afetem candidatos.

  ❌ Art. 6º III — Dados coletados além da finalidade declarada
     Risco: MÉDIO | Multa potencial: R$ 500.000
     ...
```

---

## Mapeamento Regulatório Completo

O Guimí mapeia automaticamente as violações encontradas para múltiplos frameworks regulatórios:

| Framework | Cobertura | Relatório |
|-----------|-----------|-----------|
| **LGPD** (Brasil) | 23 artigos | ✅ Nativo |
| **EU AI Act** | Anexo III (alto risco) | ✅ Nativo |
| **OWASP LLM Top 10** | 10 categorias | ✅ Nativo |
| **NIST AI RMF** | 4 funções | ✅ Nativo |
| **ISO/IEC 42001** | Principais controles | 🔜 Sprint 2 |
| **CCPA** (Califórnia) | Principais direitos | 🔜 Sprint 2 |

---

## Por que nenhum concorrente tem isso

Ferramentas como Confident AI, Giskard e Promptfoo foram construídas para o mercado americano e europeu. A LGPD tem particularidades que não existem no GDPR nem no CCPA:

- **Art. 20** (decisões automatizadas) é mais amplo que o GDPR Art. 22 — cobre qualquer decisão automatizada, não só as "significativas"
- **Dados sensíveis** incluem categorias específicas do contexto brasileiro (origem racial, convicção religiosa, filiação sindical)
- **ANPD** tem interpretações próprias que divergem da EDPB europeia
- **Nota Técnica 12/2025** criou obrigações específicas para IA que não existem em nenhuma outra jurisdição

O Guimí foi construído no Brasil, por quem entende o contexto regulatório brasileiro. Não é uma tradução do GDPR — é LGPD nativa.

---

## Próximos passos

- [EU AI Act →](eu-ai-act.md)
- [OWASP LLM Top 10 →](owasp.md)
- [Configurar auditoria contínua em CI/CD →](../guides/cicd.md)
- [Planos premium com relatórios PDF →](https://guimitestai.com/pricing)
