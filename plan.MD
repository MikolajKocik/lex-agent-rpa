# Project Roadmap & Implementation Plan: Lex Agent RPA

Projekt bezpiecznego asystenta AI dla domeny prawnej z automatyzacją procesów (RPA), hybrydowym wyszukiwaniem RAG oraz integracją chmurową.

---

## 🏗️ Faza 1: Środowisko bazowe, Infrastruktura i Konteneryzacja

- [x] **Zarządzanie infrastrukturą jako kod (IaC - Terraform):**
  - [x] Utworzenie konfiguracji Terraform w `src/infrastructure/templates/`.
  - [x] Wdrożenie Azure Key Vault (`lex-rpa-keyvault`) do przechowywania sekretów.
  - [x] Wdrożenie Azure Storage Account (`lexrpaagentstorage`) wraz z kontenerem Blob na dokumenty prawne.
  - [x] Dodanie procedury bezpiecznego usuwania zasobów (`terraform destroy`).
- [x] **Bezpieczeństwo sekretów i rejestru:**
  - [x] Skrypt `setup-docker-pass.sh` do szyfrowania poświadczeń Dockera przez GPG/pass.
  - [x] Skrypty `nvidia-secret-export.sh` oraz `postgres-secret-export.sh` do eksportu kluczy z Azure Key Vault.
  - [x] Konfiguracja `.dockerignore` chroniąca przed wyciekiem sekretów do obrazów kontenerów.
- [x] **Konteneryzacja (Docker & Docker Compose):**
  - [x] Produkcyjny `Dockerfile` (Python 3 slim, non-root user `appuser`, healthcheck).
  - [x] Konfiguracja `docker-compose.yml` oraz `docker-compose.override.yml`.
  - [x] Integracja bazy danych PostgreSQL 17 (`postgres:17-trixie`) z wolumenem `postgres-data`.
  - [x] Serwis testowy (`tests`) z profilem uruchomieniowym `test`.
- [x] **CI/CD Pipeline (GitHub Actions):**
  - [x] Linter kodu (Ruff) i walidacja formatowania.
  - [x] Zautomatyzowane testy (Pytest) z testową instancją bazy PostgreSQL.
  - [x] Automatyczne budowanie i wypychanie obrazu do Docker Hub po merge do `main`.

---

## 🧠 Faza 2: Agent Orkiestrator (LangGraph) & Guardrails

- [ ] **Struktura agenta (LangGraph):**
  - [x] Utworzenie szablonów promptów (`src/agent/prompts/`).
  - [ ] Implementacja grafu decyzyjnego w `src/agent/graph/graph_workflow.py` (węzły i krawędzie).
  - [ ] Wdrożenie routerów przepływu w `src/agent/graph/route_nodes.py`.
  - [x] Integracja z NVIDIA Cloud API (`meta/llama-3.1-8b-instruct`) i structured output (Pydantic).
- [x] **Bezpieczeństwo i Guardrails (NVIDIA NeMo Guardrails):**
  - [x] Szkic konfiguracji w `src/agent/guardrails/config.yaml`.
  - [x] Definicja przepływów Colang w `src/agent/guardrails/flows/main_flow.co`.
  - [x] Wymuszenie zakazu porad medycznych / finansowych (Input Rails).
  - [x] Wymuszenie języka polskiego i weryfikacja halucynacji (Output Rails).
  - [x] Implementacja PII Scrubbing (anonimizacja danych wejściowych i wyjściowych).
  - [x] Zabezpieczenie przed Prompt Injection (Jailbreak check na wejściu).
- [ ] **Rejestracja narzędzi agenta (`src/agent/tools/`):**
  - [ ] Implementacja narzędzi RPA (np. pobieranie umów, powiadomienia Slack).
  - [ ] Implementacja narzędzi Krytyka (np. wyszukiwanie DuckDuckGo w `critical_reviewer_tools.py`).
  - [ ] Narzędzie odpytywania bazy aktów prawnych (po zrobieniu RAG).

---

## 📚 Faza 3: Moduł Hybrid RAG (Domena Prawna)

- [ ] **Przygotowanie bazy danych wektorowej:**
  - [ ] Włączenie rozszerzenia `pgvector` w PostgreSQL.
  - [ ] Przygotowanie modeli SQLAlchemy / SQLModel dla aktów prawnych i chunków wektorowych.
- [ ] **Parser aktów prawnych (ISAP) (`src/rag/parsers/`):**
  - [ ] Opracowanie parsera dzielącego ustawy i rozporządzenia na jednostki redakcyjne (Dział, Rozdział, Artykuł, Paragraf, Ustęp).
  - [ ] Ekstrakcja metadanych: numer artykułu, data publikacji, status prawny, sygnatura.
- [ ] **Silnik wektorowy i leksykalny (`src/rag/`):**
  - [ ] Generowanie embeddingów dla chunków prawnych (`src/rag/embeddings/`).
  - [ ] Implementacja wyszukiwania semantycznego (podobieństwo cosinusowe w pgvector).
  - [ ] Implementacja wyszukiwania leksykalnego (BM25 / Full-Text Search PostgreSQL).
  - [ ] Hybrydowy Retriever (`src/rag/retrievers/`) łączący wyniki obu metod (Reciprocal Rank Fusion - RRF).

---

## 🤖 Faza 4: Automatyzacja RPA (Playwright + 2FA)

- [ ] **Moduł uwierzytelniania 2FA (`src/rpa/auth/`):**
  - [ ] Implementacja generatora kodów TOTP w oparciu o `pyotp`.
  - [ ] Bezpieczne pobieranie sekretu 2FA z Azure Key Vault.
- [ ] **Automatyzacja portalu prawnego / sądowego (`src/rpa/browser/`):**
  - [ ] Skrypt Playwright w trybie headless.
  - [ ] Automatyczne logowanie do portalu (wypełnienie formularza + wstrzyknięcie kodu 2FA).
  - [ ] Pobieranie dokumentów / spraw i przekazywanie ich do Azure Blob Storage.
  - [ ] Obsługa błędów, captcha i mechanizmy ponawiania (retry policies).

---

## 🌐 Faza 5: API, Interfejs i Bezpieczny Dostęp

- [ ] **Warstwa API (FastAPI) (`src/api/`):**
  - [x] Podstawowe schematy Pydantic (`schemas.py`).
  - [x] Endpoint weryfikacji zdrowia (`/health`).
  - [ ] Główny endpoint agenta (`POST /task`) z obsługą kolejkowania i zadań w tle (Background Tasks / Celery / ARQ).
- [ ] **Integracja z magazynem Azure Blob Storage (`src/infrastructure/storage/`):**
  - [ ] Klient do bezpiecznego uploadu wygenerowanych pism procesowych i załączników.
- [ ] **UI i Zdalny dostęp:**
  - [ ] Podpięcie interfejsu użytkownika (np. Open WebUI lub lekki dedykowany dashboard).
  - [ ] Konfiguracja bezpiecznego tunelu Cloudflare Zero Trust (Tunnels) lub Tailscale do dostępu zdalnego bez publicznego IP.
