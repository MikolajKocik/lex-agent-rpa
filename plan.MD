# Project Roadmap & Implementation Plan: Lex Agent RPA

System asystenta prawnego oparty na architekturze agentowej, automatyzacji procesów RPA, hybrydowym wyszukiwaniu informacji (Hybrid RAG) oraz integracji z usługami chmurowymi Azure.

---

## Faza 1: Środowisko bazowe, Infrastruktura i Konteneryzacja

- [x] **Zarządzanie infrastrukturą jako kod (IaC - Terraform):**
  - [x] Konfiguracja Terraform w katalogu `src/infrastructure/templates/`.
  - [x] Wdrożenie usługi Azure Key Vault (`lex-rpa-keyvault`) do zarządzania sekretami.
  - [x] Wdrożenie Azure Storage Account (`lexrpaagentstorage`) oraz kontenera Blob na dokumenty.
  - [x] Procedura bezpiecznego niszczenia zasobów (`terraform destroy`).
- [x] **Bezpieczeństwo sekretów i rejestru:**
  - [x] Skrypt `scripts/setup-docker-pass.sh` konfigurujący bezpieczny magazyn poświadczeń GPG/pass.
  - [x] Skrypty eksportu zmiennych środowiskowych z Key Vault (`scripts/*-secret-export.sh`).
  - [x] Konfiguracja reguł `.dockerignore` zapobiegająca przenikaniu danych poufnych do obrazów.
- [x] **Konteneryzacja (Docker & Docker Compose):**
  - [x] Obraz produkcyjny `Dockerfile` (Python 3 slim, użytkownik nieuprzywilejowany `appuser`, healthcheck).
  - [x] Konfiguracja środowiska wielokontenerowego w `docker-compose.yml` oraz `docker-compose.override.yml`.
  - [x] Integracja bazy danych PostgreSQL z wolumenem trwałym `postgres-data`.
  - [x] Dedykowany serwis testowy z profilem `test`.
- [x] **Pipeline CI/CD (GitHub Actions):**
  - [x] Statyczna analiza kodu i weryfikacja formatowania (Ruff).
  - [x] Zautomatyzowane testy jednostkowe (Pytest) z instancją testową PostgreSQL.
  - [x] Automatyczne budowanie i publikacja obrazu w Docker Hub po scaleniu do gałęzi `main`.

---

## Faza 2: Agent Orkiestrator (LangGraph) i Bezpieczeństwo (Guardrails)

- [x] **Struktura agenta (LangGraph):**
  - [x] Szablony promptów w `src/agent/prompts/`.
  - [x] Implementacja grafu decyzyjnego w `src/agent/graph/graph_workflow.py` (węzły i krawędzie).
  - [x] Wdrożenie routerów przepływu w `src/agent/graph/route_nodes.py` (krawędzie warunkowe).
  - [x] Integracja z modelem NVIDIA Cloud API (`meta/llama-3.1-8b-instruct`) i formatem wyjściowym Pydantic.
- [x] **Bezpieczeństwo i mechanizmy ochronne (NVIDIA NeMo Guardrails):**
  - [x] Konfiguracja główna w `src/agent/guardrails/config.yaml`.
  - [x] Definicja reguł dialogowych Colang w `src/agent/guardrails/flows/main_flow.co`.
  - [x] Walidacja zapytań wejściowych (blokada porad medycznych i finansowych).
  - [x] Wymuszenie języka polskiego i weryfikacja halucynacji w odpowiedziach.
  - [x] Anonimizacja danych wrażliwych (PII Scrubbing).
  - [x] Ochrona przed atakami typu Prompt Injection i Jailbreak.
- [x] **Rejestracja i implementacja narzędzi agenta (`src/agent/tools/`):**
  - [x] Narzędzia integracyjne (Microsoft Graph API do pobierania załączników, Slack Webhook do alertów).
  - [x] Integracja z Azure Blob Storage do archiwizacji dokumentów i opinii.
  - [x] Wyszukiwanie sieciowe za pomocą Tavily Search API (`search_web_tool`).
  - [x] Wyszukiwanie wektorowe w bazie danych PostgreSQL (`search_postgres_database_tool`).
  - [x] Architektura Dependency Injection i fabryki narzędzi w `agent_tools.py` i `dependencies.py`.

---

## Faza 3: Moduł Hybrid RAG (Domena Prawna)

- [x] **Baza danych wektorowa:**
  - [x] Włączenie rozszerzenia `pgvector` w PostgreSQL oraz schemat `template.sql`.
  - [x] Modele danych Pydantic dla aktów prawnych i fragmentów tekstowych (chunków) (`src/rag/models.py`).
  - [x] Pipeline przetwarzania integrujący Azure Blob Storage z bazą danych (ekstrakcja tekstu i wektoryzacja) (`src/rag/ingestion.py`).
- [x] **Parser aktów prawnych (ISAP) (`src/rag/parsers/`):**
  - [x] Parser strukturalny dzielący akty prawne na jednostki redakcyjne (Dział, Rozdział, Artykuł, Paragraf, Ustęp) (`isap_parser.py`).
  - [x] Ekstrakcja metadanych: numer artykułu, data publikacji, status prawny, sygnatura aktu.
  - [x] Moduł ekstrakcji tekstu z plików PDF (`pdf_extractor.py`).
- [x] **Silnik hybrydowego wyszukiwania (`src/rag/`):**
  - [x] Generowanie embeddingów dla chunków prawnych (`src/rag/embeddings/legal_embedder.py`).
  - [x] Wyszukiwanie semantyczne (podobieństwo cosinusowe z indeksem HNSW w pgvector).
  - [x] Wyszukiwanie leksykalne (Full-Text Search / Trigram GIN w PostgreSQL).
  - [x] Hybrydowy retriever (`src/rag/retrievers/hybrid_retriever.py`) łączący wyniki za pomocą Reciprocal Rank Fusion (RRF).

---

## Faza 4: Automatyzacja RPA (Playwright i Uwierzytelnianie 2FA)

- [x] **Moduł uwierzytelniania 2FA (`src/rpa/auth/`):**
  - [x] Generator kodów jednorazowych TOTP z wykorzystaniem biblioteki `pyotp` (`totp_service.py`).
  - [x] Bezpieczny odczyt sekretu 2FA z Azure Key Vault z mechanizmem fallback.
- [x] **Automatyzacja portalu prawnego / sądowego (`src/rpa/browser/`):**
  - [x] Skrypty Playwright działające asynchronicznie w trybie headless (`portal_automation.py`).
  - [x] Logowanie do portalu z automatycznym wypełnianiem formularza i wstrzykiwaniem kodu 2FA.
  - [x] Pobieranie dokumentów spraw i przekazywanie ich do Azure Blob Storage (`download_court_case_document_tool`).
  - [x] Obsługa wyjątków, weryfikacja captcha oraz polityki ponawiania operacji.

---

## Faza 5: Warstwa API i Bezpieczny Dostęp Zdalny

- [x] **Warstwa API (FastAPI) (`src/api/`):**
  - [x] Modele żądań i odpowiedzi Pydantic (`schemas.py`).
  - [x] Endpoint monitorowania stanu usługi (`GET /health`).
  - [x] Główny endpoint orkiestratora (`POST /task`) z obsługą kolejkowania i zadań w tle (`POST /task/async` oraz `GET /task/{task_id}`).
  - [x] Interaktywna dokumentacja API w standardzie OpenAPI / Swagger UI (`/docs`).
- [x] **Integracja z Azure Blob Storage (`src/infrastructure/blob/`):**
  - [x] Asynchroniczny klient do bezpiecznego przesyłania i pobierania plików (`upload_document_to_blob`, `download_document_from_blob`).
- [x] **Bezpieczny dostęp zdalny:**
  - [x] Skrypt bezpiecznego tunelu Cloudflare Zero Trust bez publicznego adresu IP (`scripts/setup-cloudflare-tunnel.sh`).


---

## Faza 6: Testowanie, Ewaluacja i Zapewnienie Jakości (QA)

- [ ] **Testy jednostkowe (Pytest):**
  - [x] Testy jednostkowe usług wyszukiwania i integracji (`tests/unit/`).
  - [ ] Testy jednostkowe parserów strukturalnych RAG (`src/rag/parsers/`).
  - [ ] Izolowane testy węzłów grafu z wykorzystaniem mocków API LLM.
  - [ ] Testy generatora kodów 2FA dla modułu RPA.
- [ ] **Testy integracyjne:**
  - [x] Testy integracyjne serwisów zewnętrznych (`tests/integration/`).
  - [ ] Walidacja pełnego łańcucha operacyjnego: RPA -> Blob Storage -> Wektoryzacja Postgres -> Graf LangGraph -> Endpoint FastAPI.
  - [ ] Weryfikacja skuteczności NeMo Guardrails w blokowaniu wycieków PII oraz halucynacji.
- [ ] **Ewaluacja jakościowa (LLM-as-a-judge):**
  - [ ] Przygotowanie referencyjnego zbioru ewaluacyjnego (10-20 umów i spraw prawnych).
  - [ ] Ocena dokładności ekstrakcji klauzul i retrievalu (metryki Hit-Rate, MRR).
