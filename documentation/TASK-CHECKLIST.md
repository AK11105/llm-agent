# 📋 TASK_CHECKLIST.md

### *Student-Side LLM Build-and-Deploy Agent*

---

## 🟢 Phase 0 — Environment Setup

* [ ] Install Python 3.10+
* [ ] Create virtual environment (`python -m venv venv`)
* [ ] Install core dependencies:

  * FastAPI, Uvicorn
  * Pydantic, python-dotenv
  * httpx
  * PyGithub
  * OpenAI / LiteLLM
  * pytest, pytest-asyncio
* [ ] Initialize git and create `.gitignore`
* [ ] Create `.env` with:

  ```
  GITHUB_TOKEN=
  LLM_API_KEY=
  STUDENT_SECRET=
  EVALUATOR_URL=
  APP_ENV=
  PORT=
  ```
* [ ] Add `requirements.txt` / `pyproject.toml`

---

## ⚙️ Phase 1 — Application Skeleton

* [ ] `main.py`:

  * [ ] Initialize FastAPI app
  * [ ] Include routers
  * [ ] Register startup/shutdown events
  * [ ] Add `/health` endpoint
* [ ] `api/endpoints.py`:

  * [ ] Create `/build` route placeholder
  * [ ] Create `/revise` route placeholder
* [ ] `utils/config.py`:

  * [ ] Load `.env` values
* [ ] `utils/logger.py`:

  * [ ] Configure structured logging
* [ ] Test server runs and `/health` responds 200 OK

---

## 🧠 Phase 2 — Request Verification

* [ ] `models/request_models.py`:

  * [ ] Define `BuildRequest` and `ReviseRequest` schemas
* [ ] `core/verifier.py`:

  * [ ] Implement secret verification logic
* [ ] `api/endpoints.py`:

  * [ ] Verify secret for all incoming requests
* [ ] Test invalid secrets are rejected (HTTP 403)

---

## 🧩 Phase 3 — Code Generation

* [ ] `services/llm_service.py`:

  * [ ] Wrap LLM calls
  * [ ] Generate code scaffold from brief
* [ ] `core/generator.py`:

  * [ ] Orchestrate build request → code output
* [ ] `templates/prompts/`:

  * [ ] Store reusable LLM prompts
* [ ] Test LLM output saved locally or logged

---

## 🚀 Phase 4 — GitHub Deployment

* [ ] `services/github_service.py`:

  * [ ] Create repo dynamically
  * [ ] Add MIT LICENSE
  * [ ] Commit generated code
  * [ ] Enable GitHub Pages
* [ ] `core/deployer.py`:

  * [ ] Orchestrate code → repo → Pages URL
* [ ] `core/builder.py`:

  * [ ] Full “Build → Deploy → Notify” workflow
* [ ] Test full round 1 manually:

  * [ ] Repo created
  * [ ] Pages live
  * [ ] Evaluator notified

---

## 🔁 Phase 5 — Revision Flow

* [ ] `core/reviser.py`:

  * [ ] Accept round 2 JSON request
  * [ ] Modify existing repo based on brief
* [ ] `services/llm_service.py`:

  * [ ] Add refactoring prompt handling
* [ ] `core/deployer.py`:

  * [ ] Push changes and redeploy Pages
* [ ] `core/builder.py`:

  * [ ] Update pipeline for round 2
* [ ] Test revision flow manually:

  * [ ] Repo updated
  * [ ] Pages redeployed
  * [ ] Evaluator notified

---

## 🧾 Phase 6 — Logging, Testing & Documentation

* [ ] `tests/test_api.py`:

  * [ ] Test `/build` and `/revise` endpoints
  * [ ] Test secret validation
* [ ] `tests/test_services.py`:

  * [ ] Mock LLM + GitHub API
* [ ] `DOCUMENTATION.md`:

  * [ ] Implementation checklist for all modules
* [ ] `TECH_STACK.md`:

  * [ ] Stack explanation and rationale
* [ ] `README.md`:

  * [ ] Usage instructions
  * [ ] Architecture summary

---

## 🔹 Notes

* This checklist is **progressive**: complete earlier phases before moving to later ones.
* Tick each item as it is **implemented and verified**.
* Optional: link `TASK_CHECKLIST.md` to your PR or CI workflow for visibility.

---

