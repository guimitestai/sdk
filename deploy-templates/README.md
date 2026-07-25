# Templates de Deploy — Guimí Test AI

Templates prontos de CI/CD para fazer deploy da **plataforma/engine do Guimí** em produção.

> **Nota:** Estes templates são para a **engine FastAPI** (repositório `guimitestai/platform`),
> não para o SDK Python. O SDK é publicado no PyPI via `publish.yml`.

## Como usar

1. Copie o arquivo correspondente à sua plataforma para `.github/workflows/` no seu repositório
2. Substitua os valores marcados com `← substituir` ou `SEU_*`
3. Configure os secrets no GitHub (Settings → Secrets → Actions)
4. Faça push na branch `main` — o deploy acontece automaticamente

## Templates disponíveis

| Arquivo | Plataforma | Autenticação | Secrets necessários |
|---------|-----------|-------------|---------------------|
| `deploy-aws.yml` | AWS ECS/Fargate | OIDC | ARN da IAM Role |
| `deploy-azure.yml` | Azure Container Apps | Workload Identity | `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` |
| `deploy-gcp.yml` | Google Cloud Run | Workload Identity | `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT` |
| `deploy-kubernetes.yml` | Kubernetes (EKS/AKS/GKE/on-premise) | kubeconfig | `KUBE_CONFIG`, `REGISTRY_URL`, `REGISTRY_USER`, `REGISTRY_TOKEN` |
| `deploy-docker-compose.yml` | VPS / Self-Hosted | SSH | `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY` |

## Todos os templates incluem

- ✅ Testes obrigatórios antes do deploy (falhou = para tudo)
- ✅ Sem senhas nos secrets (OIDC/Workload Identity onde disponível)
- ✅ Rollback automático se o deploy falhar
- ✅ Health check pós-deploy

## Documentação completa

Veja [docs.guimitestai.com/guides/deploy](https://guimitestai.github.io/sdk/guides/deploy/) para instruções detalhadas de cada plataforma.
