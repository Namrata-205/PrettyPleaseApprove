# 🤖 prettypleaseapprove

> Automated PR Review Bot — AI (Groq) + SonarQube + Trivy security scanning

---

## Architecture

```
GitHub PR opened/updated
        │
        ▼
GitHub Webhook ──────────────────────► Bot Backend (FastAPI :8000)
                                               │
                                    ┌──────────┼──────────┐
                                    ▼          ▼          ▼
                              Trigger      Groq AI    Fetch PR diff
                              Jenkins      review     from GitHub API
                                 │
                     ┌───────────┼───────────┐
                     ▼           ▼           ▼
                  SonarQube   Trivy FS    Jenkins
                  analysis    scan       build log
                     │           │
                     └─────┬─────┘
                           ▼
                   Jenkins callback ──► Bot Backend
                                              │
                                              ▼
                                   Aggregate scores + AI review
                                              │
                                              ▼
                                   Post comment on GitHub PR
                                   (APPROVED ✅ or BLOCKED ❌)
```

---

## Repository Structure

```
├── ci/
│   ├── Jenkinsfile              ← Pipeline definition
│   ├── sonar-project.properties ← SonarQube config
│   └── trivy-config.yaml        ← Trivy scan settings
├── infra/
│   ├── terraform/               ← AWS infra (Jenkins + SonarQube + Bot VMs)
│   └── ansible/                 ← Install + configure all services
├── monitoring/
│   ├── prometheus.yml           ← Metrics scraping
│   ├── grafana-dashboard.json   ← Bot dashboard
│   └── alerts.yml               ← Alerting rules
├── docker-compose.yml           ← Local dev / staging stack
├── .env.example                 ← All required env vars
└── backend/                     ← FastAPI bot (teammate's code)
```

---

## Quick Start

### 1. Provision infrastructure

```bash
cd infra/terraform

# Copy and fill in your values
cp terraform.tfvars.example terraform.tfvars
# Edit: key_pair_name, admin_cidr, aws_region

terraform init
terraform plan
terraform apply

# Note the output IPs
terraform output ansible_inventory_hint
```

### 2. Configure services with Ansible

```bash
cd infra/ansible

# Paste IPs from terraform output into inventory.ini
nano inventory.ini

# Run full setup
ansible-playbook -i inventory.ini playbook.yml
```

This installs:
- **Jenkins** (with Docker, GitHub PR plugin, SonarQube plugin)
- **SonarQube** (via Docker, with PostgreSQL)
- **Trivy** (on the Jenkins host)

### 3. Configure credentials in Jenkins

Go to `http://JENKINS_IP:8080` → **Manage Jenkins → Credentials**

| ID | Type | Value |
|----|------|-------|
| `github-token` | Secret text | Your GitHub PAT |
| `sonar-token` | Secret text | SonarQube user token |

### 4. Create Jenkins pipeline

1. **New Item → Multibranch Pipeline**
2. Source: GitHub → your repo URL + `github-token`
3. Build Configuration: `Jenkinsfile path` = `ci/Jenkinsfile`
4. Scan triggers: every 1 minute or via webhook

### 5. Configure GitHub Webhook

Go to your repo → **Settings → Webhooks → Add webhook**

| Field | Value |
|-------|-------|
| Payload URL | `http://BOT_BACKEND_IP:8000/api/v1/webhook/github` |
| Content type | `application/json` |
| Secret | Value from `GITHUB_WEBHOOK_SECRET` in your `.env` |
| Events | Pull requests, Pull request reviews |

### 6. Start bot backend locally (dev)

```bash
cp .env.example .env
# Fill in all values

docker compose up --build
```

Bot backend: http://localhost:8000  
Grafana: http://localhost:3000  
Prometheus: http://localhost:9090

---

## Environment Variables

See [.env.example](.env.example) for the full list with descriptions.

Critical ones:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | PAT with `repo` + `pull_request` scopes |
| `GITHUB_WEBHOOK_SECRET` | Shared secret for webhook signature verification |
| `GROQ_API_KEY` | From console.groq.com |
| `JENKINS_URL` | Jenkins base URL reachable from bot backend |
| `SONAR_TOKEN` | SonarQube user token |
| `COVERAGE_THRESHOLD` | Minimum test coverage % (default: 80) |

---

## How the Verdict Works

| Condition | Verdict |
|-----------|---------|
| SonarQube quality gate = FAILED | ❌ BLOCKED |
| Coverage < threshold | ❌ BLOCKED |
| Trivy CRITICAL or HIGH CVE found | ❌ BLOCKED |
| Trivy secret detected | ❌ BLOCKED |
| AI review flags security issues | ⚠️ WARNING (bot comment, not blocked) |
| All checks pass | ✅ APPROVED |

---

## Monitoring

- **Grafana**: http://localhost:3000 — PRs reviewed, blocked/approved ratio, latency
- **Prometheus**: http://localhost:9090 — raw metrics
- **Alerts**: configured in `monitoring/alerts.yml`

---

## Troubleshooting

**Bot not posting comment on PR**
- Check bot backend logs: `docker compose logs bot-backend`
- Verify GitHub webhook delivery in repo Settings → Webhooks → Recent Deliveries
- Confirm `GITHUB_TOKEN` has `pull_requests:write` scope

**Jenkins pipeline not triggering**
- Check Jenkins webhook plugin configuration
- Verify the GitHub webhook URL points to Jenkins (`:8080`) not the bot backend (`:8000`) if using the GitHub PR Builder plugin approach

**SonarQube "quality gate not found"**
- The quality gate `prettypleaseapprove-gate` must exist in SonarQube
- Ansible creates it automatically, or create manually: Quality Gates → Create

**Trivy DB stale**
- SSH into Jenkins host: `trivy image --download-db-only`
