# Lex Agent RPA &bull; Autonomous Legal Assistant & Compliance Pipeline

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_State_Machine-orange?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![NVIDIA Guardrails](https://img.shields.io/badge/NVIDIA-NeMo_Guardrails-76B900?logo=nvidia&logoColor=white)](https://github.com/NVIDIA/NeMo-Guardrails)
[![PostgreSQL pgvector](https://img.shields.io/badge/PostgreSQL-pgvector_HNSW-336791?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Azure Cloud](https://img.shields.io/badge/Azure-KeyVault_%26_Blob-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/)
[![Cloudflare Zero Trust](https://img.shields.io/badge/Cloudflare-Zero_Trust_Tunnel-F38020?logo=cloudflare&logoColor=white)](https://www.cloudflare.com/products/tunnel/)
[![Tests](https://img.shields.io/badge/Tests-28_Passed-success?logo=pytest&logoColor=white)](#7-run-automated-tests)

Autonomous legal intelligence system designed for legal firms, compliance departments, and financial institutions. Combines **multi-agent LangGraph workflows**, **hybrid dense-sparse retrieval (RRF + ISAP parser)**, **2FA-authenticated RPA browser automation (Playwright)**, and **NVIDIA NeMo Guardrails** backed by an **Azure Cloud enterprise data plane**.

---

## System Architecture

```mermaid
flowchart TD
    subgraph INGRESS["1. Ingress & Remote Access"]
        Client["Client / External Webhooks"] -->|Zero Trust Tunnel| Cloudflare["Cloudflare Edge (TLS / Anti-DDoS)"]
        Cloudflare --> FastApiApp["FastAPI Backend (:8080)<br/>• POST /api/task (Sync)<br/>• POST /api/task/async (Background Queue)<br/>• GET /docs (Swagger UI)"]
    end

    subgraph SECURITY["2. Safety & Enterprise Guardrails"]
        FastApiApp --> NeMoRails["NVIDIA NeMo Guardrails<br/>• Jailbreak & Prompt Injection Defense<br/>• Automated PII Scrubbing<br/>• LLM-as-a-Judge Hallucination Check"]
    end

    subgraph ORCHESTRATION["3. Multi-Agent LangGraph State Machine"]
        NeMoRails --> RPA_Node["RPA Automation Node<br/>(Playwright Headless + TOTP 2FA)"]
        RPA_Node --> GroundReview["Ground Reviewer<br/>(Contract Clause & Risk Extraction)"]
        GroundReview --> CriticNode["Critical Legal Reviewer"]
        CriticNode -->|Needs precedent| WebSearch["Web Research Node<br/>(Tavily API)"]
        WebSearch --> CriticNode
        CriticNode --> AuditNode["Security & Compliance Audit<br/>(GDPR / PII Verification)"]
        AuditNode -->|Pass| FinalReview["Final Opinion Generator"]
        AuditNode -->|Fail| RejectSlack["Rejection & Alert Node"]
    end

    subgraph HYBRID_RAG["4. Hybrid Legal RAG Engine"]
        GroundReview -.-> Parser["ISAP Statutory Parser<br/>(Articles & Editorial Units)"]
        Parser --> Embedder["NVIDIA Dense Embeddings"]
        Embedder --> HybridRetriever["Reciprocal Rank Fusion (RRF)<br/>k = 60"]
        HybridRetriever <--> PGVector[("PostgreSQL + pgvector<br/>• HNSW Vector Cosine Index<br/>• GIN Trigram Lexical Index")]
    end

    subgraph CLOUD["5. Azure Enterprise Infrastructure"]
        FinalReview --> AzureBlob["Azure Blob Storage<br/>(Encrypted Case & Opinion Archive)"]
        RPA_Node <--> KeyVault["Azure Key Vault<br/>(TOTP Secrets & DB Credentials)"]
        RejectSlack --> SlackClient["Slack Webhooks<br/>(Incident Channel)"]
        RPA_Node <--> MSGraph["Microsoft Graph API<br/>(Outlook E-mail Attachments)"]
    end
```

---


## Getting Started: Complete Step-by-Step Workflow

Follow the steps below in exact order to provision the cloud infrastructure, configure credentials, set up local environment variables, and run the agent system.

### 1. Provision Azure Infrastructure (Terraform)
Log in to your Azure account and provision cloud resources (Resource Group, Key Vault, Storage Account, and Blob Container):

```bash
az login
cd src/infrastructure/templates
terraform init
terraform apply
cd ../../..
```

### 2. Configure Azure IAM, Key Vault Secrets & Entra ID (Setup Scripts)
Run the automated scripts in `scripts/` to configure permissions and services:

1. **Grant Blob Storage RBAC access (`Storage Blob Data Contributor`):**
   ```bash
   ./scripts/setup-blob-rbac.sh
   ```

2. **Populate Key Vault with required secrets (`PostgresPassword`, `TavilyApiKey`, `NvidiaApiKey`):**
   ```bash
   ./scripts/setup-keyvault-secrets.sh
   ```

3. **Configure Microsoft Graph API in Entra ID (for Outlook email attachments):**
   ```bash
   ./scripts/setup-ms-graph.sh
   ```
   *(The script outputs your `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and `AZURE_CLIENT_SECRET`).*

### 3. Configure Local Environment & Slack Webhook (`.env`)
Create your `.env` file from the template and fill in your Slack webhook and MS Graph details:

```bash
cp .env-example .env
```
Open `.env` and fill in:
* `SLACK_WEBHOOK_URL`: Your incoming Slack webhook URL for notifications and alerts.
* `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`: Generated in step 2.3.
* `MS_GRAPH_MAILBOX_USER`: The target mailbox address (e.g. `kancelaria@twojadomena.pl`).

### 4. Export Secrets from Key Vault to Shell
Export runtime API keys and passwords from Azure Key Vault into your active terminal:

```bash
source ./scripts/nvidia-secret-export.sh
source ./scripts/postgres-secret-export.sh
source ./scripts/tavily-secret-export.sh
```

### 5. Configure Docker Registry Authentication (Linux optional)
> [!IMPORTANT]
> By default on Linux, Docker stores credentials in plain text inside `~/.docker/config.json`.
> Run this helper script to store registry credentials securely in an encrypted `pass` (GPG) store:

```bash
./scripts/setup-docker-pass.sh
```

### 6. Run Application Stack (API + PostgreSQL)
Start the containers (FastAPI microservice and PostgreSQL with pgvector):

```bash
docker compose up -d
```

Initialize the database schema (extensions and `legal_documents` table):
```bash
docker compose exec -T db psql -U lex_user -d lex_agent_db < src/infrastructure/database/template.sql
```

### 7. Run Automated Tests
Run tests inside Docker:

```bash
docker compose run --rm tests
```

Or run all 28 automated tests locally using pytest:
```bash
pytest tests/unit/ tests/evaluation/ tests/integration/test_guardrails_and_pipeline.py
```


### 8. Secure Remote Access: Cloudflare Zero Trust Tunnel
To securely expose the local FastAPI microservice for remote access, mobile testing, or Slack webhooks without opening ports on your firewall or having a public IP:

1. **Option A: Instant Ad-hoc Quick Tunnel (No account needed):**
   ```bash
   cloudflared tunnel --url http://localhost:8080
   ```
   *Generates an instant, free public HTTPS address (`https://*.trycloudflare.com`) with DDoS protection and TLS encryption.*

2. **Option B: Production Zero Trust Tunnel (Automated Script):**
   ```bash
   ./scripts/setup-cloudflare-tunnel.sh
   ```
   *Creates an outbound encrypted tunnel routing your configured custom domain directly to `localhost:8080` via Cloudflare's global edge network.*

### 9. Interactive API Documentation (Swagger UI)
Once the stack is running, access the interactive OpenAPI documentation:
* **Local:** `http://localhost:8080/docs`
* **Healthcheck:** `GET http://localhost:8080/api/health`
* **Synchronous Task Execution:** `POST http://localhost:8080/api/task`
* **Asynchronous Background Task:** `POST http://localhost:8080/api/task/async`

### 10. Clean up Cloud Resources (Optional)
When you are done and want to tear down all Azure infrastructure to avoid costs:

```bash
cd src/infrastructure/templates
terraform destroy
cd ../../..
```


---

## CI/CD Pipeline Secrets (GitHub Actions)
To enable automated building and pushing of Docker images on `git push` to `main`, configure the following repository secrets:

1. **Generate Docker Hub Access Token:**
   * Go to [Docker Hub Account Settings](https://hub.docker.com/settings/security) -> **Security**.
   * Click **New Access Token**, grant **Read & Write** permissions, and copy the generated token.

2. **Add Secrets in GitHub:**
   * In your repository on GitHub, navigate to:
     `Settings` -> `Secrets and variables` -> `Actions`.
   * Under **Repository secrets**, click **New repository secret** and add:
     * `DOCKERHUB_USERNAME`: Your Docker Hub username.
     * `DOCKERHUB_TOKEN`: The Personal Access Token generated above.

![GitHub Secrets Configuration](docs/github-secrets-setup.png)
