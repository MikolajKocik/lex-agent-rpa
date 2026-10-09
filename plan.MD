# Project Roadmap & Implementation Plan: Lex Agent RPA

Agentic legal assistant system powered by autonomous graph orchestration, RPA browser automation, Hybrid RAG legal retrieval, and enterprise Azure cloud integrations.

---

## Phase 1: Core Environment, Infrastructure & Containerization

- [x] **Infrastructure as Code (IaC - Terraform):**
  - [x] Terraform templates in `src/infrastructure/templates/`.
  - [x] Provisioned Azure Key Vault (`lex-rpa-keyvault`) for secret management.
  - [x] Provisioned Azure Storage Account (`lexrpaagentstorage`) with document Blob containers.
  - [x] Controlled resource teardown workflow (`terraform destroy`).
- [x] **Secrets & Container Registry Security:**
  - [x] Secure credential store helper script `scripts/setup-docker-pass.sh` using GPG/pass.
  - [x] Environment variable extraction scripts from Azure Key Vault (`scripts/*-secret-export.sh`).
  - [x] Configured `.dockerignore` rules preventing credential leaks into container layers.
- [x] **Containerization (Docker & Docker Compose):**
  - [x] Production-ready `Dockerfile` (Python 3 slim, unprivileged user `appuser`, built-in healthcheck).
  - [x] Multi-container orchestration in `docker-compose.yml` and `docker-compose.override.yml`.
  - [x] PostgreSQL service integration backed by persistent volume `postgres-data`.
  - [x] Isolated test runner service configured under the `test` profile.
- [x] **CI/CD Automation (GitHub Actions):**
  - [x] Static code analysis and linting verification via Ruff.
  - [x] Automated unit test suite execution (Pytest) with an isolated PostgreSQL service container.
  - [x] Automated container build and registry publication to Docker Hub upon merge to `main`.

---

## Phase 2: Agent Orchestration (LangGraph) & Safety Guardrails

- [x] **Agent Architecture (LangGraph):**
  - [x] Markdown prompt templates located in `src/agent/prompts/`.
  - [x] Decision graph implementation in `src/agent/graph/graph_workflow.py` (nodes and edges).
  - [x] State flow routing logic in `src/agent/graph/route_nodes.py` (conditional edges).
  - [x] NVIDIA Cloud API integration (`meta/llama-3.1-8b-instruct`) with Pydantic structured output models.
- [x] **Safety & Governance Rails (NVIDIA NeMo Guardrails):**
  - [x] Core guardrails configuration in `src/agent/guardrails/config.yaml`.
  - [x] Colang conversational policy definitions in `src/agent/guardrails/flows/main_flow.co`.
  - [x] Input query validation (blocking unauthorized medical and financial advice).
  - [x] Polish language enforcement and output hallucination verification actions.
  - [x] Sensitive PII scrubbing and data redaction.
  - [x] Prompt injection and jailbreak mitigation mechanisms.
- [x] **Agent Tools & Integrations (`src/agent/tools/`):**
  - [x] Integration tools (Microsoft Graph API for attachments, Slack incoming webhooks for alerts).
  - [x] Azure Blob Storage integration for document archiving and legal opinions.
  - [x] Web research tool powered by Tavily Search API (`search_web_tool`).
  - [x] Database search integration with PostgreSQL (`search_postgres_database_tool`).
  - [x] Dependency Injection architecture and tool factories in `agent_tools.py` and `dependencies.py`.

---

## Phase 3: Hybrid RAG Engine (Legal Domain)

- [x] **Vector Database Architecture:**
  - [x] Enabled `pgvector` extension in PostgreSQL with schema migrations in `template.sql`.
  - [x] Pydantic domain models for legal acts and text chunks (`src/rag/models.py`).
  - [x] End-to-end ingestion pipeline bridging Azure Blob Storage and PostgreSQL (`src/rag/ingestion.py`).
- [x] **Statutory Legal Parser (ISAP) (`src/rag/parsers/`):**
  - [x] Structural parser decomposing Polish legal acts into editorial units (Sections, Chapters, Articles, Paragraphs) (`isap_parser.py`).
  - [x] Metadata extraction: article numbers, publication dates, legal status, and official act signatures.
  - [x] Raw PDF document text extraction service (`pdf_extractor.py`).
- [x] **Hybrid Retrieval Engine (`src/rag/`):**
  - [x] Batch embedding generation for legal chunks (`src/rag/embeddings/legal_embedder.py`).
  - [x] Dense semantic retrieval using cosine distance over pgvector HNSW index.
  - [x] Sparse lexical retrieval using Full-Text Search and Trigram GIN index in PostgreSQL.
  - [x] Hybrid retriever (`src/rag/retrievers/hybrid_retriever.py`) fusing rankings via Reciprocal Rank Fusion (RRF).

---

## Phase 4: RPA Browser Automation (Playwright & 2FA Auth)

- [x] **2FA Authentication Module (`src/rpa/auth/`):**
  - [x] Time-based One-Time Password (TOTP) generator service using `pyotp` (`totp_service.py`).
  - [x] Secure 2FA secret retrieval from Azure Key Vault with environment variable fallback.
- [x] **Legal Court Portal Automation (`src/rpa/browser/`):**
  - [x] Headless asynchronous Playwright browser automation (`portal_automation.py`).
  - [x] Automated portal login with credential filling and TOTP 2FA code injection.
  - [x] Court case document docket discovery, download, and direct Azure Blob archiving (`download_court_case_document_tool`).
  - [x] CAPTCHA challenge detection, error handling, and robust retry strategies.

---

## Phase 5: API Layer & Zero Trust Remote Access

- [x] **FastAPI Service Layer (`src/api/`):**
  - [x] Pydantic request and response schemas (`schemas.py`).
  - [x] Health monitoring endpoint (`GET /health`).
  - [x] Primary agent task endpoint (`POST /task`) with background asynchronous execution (`POST /task/async` and `GET /task/{task_id}`).
  - [x] Interactive OpenAPI / Swagger UI documentation (`/docs`).
- [x] **Azure Blob Storage Client (`src/infrastructure/blob/`):**
  - [x] Asynchronous client for secure file upload and retrieval (`upload_document_to_blob`, `download_document_from_blob`).
- [x] **Secure Remote Access:**
  - [x] Cloudflare Zero Trust tunnel setup script without exposing public IPs (`scripts/setup-cloudflare-tunnel.sh`).

---

## Phase 6: QA Testing, Evaluation & Benchmarks

- [x] **Unit Testing Suite (Pytest):**
  - [x] Search service and webhook integration unit tests (`tests/unit/test_web_search_service.py`).
  - [x] Legal RAG parser and extractor unit tests (`tests/unit/test_rag_pipeline.py`).
  - [x] Isolated LangGraph node tests utilizing mocked LLM endpoints (`tests/unit/test_graph_nodes.py`).
  - [x] 2FA TOTP generator unit tests for the RPA module (`tests/unit/test_rpa_auth.py`).
  - [x] FastAPI endpoint unit tests (`tests/unit/test_api_endpoints.py`).
- [x] **Integration Testing Suite:**
  - [x] External service integration tests (`tests/integration/test_web_search_service_integration.py`).
  - [x] Full operational chain validation: RPA -> Blob Storage -> Postgres Vectorization -> LangGraph -> FastAPI (`tests/integration/test_guardrails_and_pipeline.py`).
  - [x] NeMo Guardrails verification for PII leak prevention and hallucination rejection (`test_guardrails_and_pipeline.py`).
- [x] **Quality Evaluation Benchmarks (LLM-as-a-judge):**
  - [x] Curated statutory evaluation benchmark dataset (`tests/evaluation/eval_dataset.json`).
  - [x] Legal retrieval benchmark measuring Hit-Rate@K and Mean Reciprocal Rank (MRR) (`tests/evaluation/test_rag_eval.py`).
