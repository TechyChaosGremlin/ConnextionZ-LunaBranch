# Secrets Management — Setup Guide

> **Author:** Seth Nenninger (Lead Architect)
> **Last Updated:** 2026-07-08
> **Status:** Active

---

## Overview

ConnextionZ uses environment variables for all secrets and configuration. Secrets must **never** be committed to version control. This document explains how to set up secrets for local development, Docker Compose, and production deployment.

## Quick Start (Local Development)

```bash
# 1. Copy the template
cp .env.example .env

# 2. Generate secure random values for each CHANGE_ME entry
#    On Linux/macOS:
openssl rand -base64 32

#    On Windows (PowerShell):
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))

# 3. Edit .env and replace every CHANGE_ME_* value
```

## Environment Variable Inventory

| Variable | Scope | Sensitivity | Notes |
|----------|-------|-------------|-------|
| `POSTGRES_PASSWORD` | DB | **Secret** | PostgreSQL superuser password |
| `REDIS_PASSWORD` | Cache | **Secret** | Redis AUTH password |
| `RABBITMQ_PASSWORD` | Queue | **Secret** | RabbitMQ broker password |
| `REDIS_COMMANDER_HTTP_PASSWORD` | Admin UI | **Secret** | Redis Commander web UI password |
| `JWT_SECRET_KEY` | Auth | **Secret** | HMAC signing key for JWT tokens |
| `OPENAI_API_KEY` | LLM | **Secret** | OpenAI API key (if using cloud LLM) |
| `ANTHROPIC_API_KEY` | LLM | **Secret** | Anthropic API key (if using cloud LLM) |
| `AWS_ACCESS_KEY_ID` | Cloud | **Secret** | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Cloud | **Secret** | AWS IAM secret key |

## Docker Compose Integration

The `docker/docker-compose.yml` file references environment variables using `${VAR:-default}` syntax:

```yaml
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}
```

This means:
- If `POSTGRES_PASSWORD` is set in your `.env` file → uses that value.
- If not set → falls back to the default (`password`), which is **only safe for local dev**.

**For any shared or production-like environment, always set real values in `.env`.**

### docker-compose auto-loading

Docker Compose automatically reads `.env` from the project root. When you run:

```bash
docker compose -f docker/docker-compose.yml up
```

It will pick up all variables defined in your `.env` file.

## Production Secrets

In production (AWS), secrets are managed via **AWS Secrets Manager** and injected into containers through:

1. **EKS**: External Secrets Operator syncs AWS Secrets Manager → Kubernetes Secrets.
2. **ECS/Fargate**: Secrets are referenced directly in the task definition.
3. **Terraform**: Secrets are created via `aws_secretsmanager_secret_version` resources (values set manually or via CI).

### Terraform Example

```hcl
resource "aws_secretsmanager_secret" "jwt" {
  name        = "connextionz/${var.environment}/jwt-secret-key"
  description = "JWT signing key for ConnextionZ ${var.environment}"
}

resource "aws_secretsmanager_secret_version" "jwt" {
  secret_id     = aws_secretsmanager_secret.jwt.id
  secret_string = var.jwt_secret_key  # Set via CI variable, never in code
}
```

## Security Rules (Enforced)

1. **No secrets in code, config, or Dockerfiles** — checked by git-secrets + Checkov in CI.
2. **`.env` is git-ignored** — verified by `.gitignore` rules.
3. **`.env.example` IS committed** — serves as a template without real values.
4. **Default fallback values are dev-only** — never use defaults in staging/production.
5. **Rotate secrets on compromise** — JWT secret rotation invalidates all sessions; plan accordingly.

## LocalStack Notes

For local development, LocalStack accepts any AWS credentials. The defaults in `.env.example` (`test` / `test`) are fine for local use. Do NOT use real AWS credentials in local dev.

## Verifying Your Setup

```bash
# Check that .env is ignored
git status --ignored | grep .env

# Verify docker-compose resolves variables correctly
docker compose -f docker/docker-compose.yml config | grep -E "PASSWORD|SECRET|KEY"
```

The `config` command shows the resolved compose file — verify no hardcoded values appear.

---

*Update this document whenever new secrets are added to the platform.*
