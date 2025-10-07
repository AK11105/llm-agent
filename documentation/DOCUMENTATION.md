# PROJECT PLAN (File-by-file breakdown)

## `main.py`

**Purpose:** application entrypoint and lifecycle manager.

**What to expect here**

* Load configuration (via `utils/config.py`) and initialize logging.
* Register and mount API routes from `api/endpoints.py`.
* Initialize optional services (DB connection, caches).
* Expose health/readiness endpoints (`/health`, `/metrics`).
* Start the ASGI server (uvicorn) or provide the WSGI entry used by your deploy system.
* Graceful shutdown hooks to flush logs, close DB connections, and clean temp files.

**Inputs / Outputs**

* Reads environment variables and config file.
* Starts HTTP server; returns non-zero process status on fatal startup errors.

**Behavioral notes**

* Fail fast if required secrets/keys are missing.
* Add an option for `DRY_RUN` to allow local testing without pushing to GitHub.

**Testing**

* Smoke tests should start `main.py` and confirm `/health` responds.

---

## `api/__init__.py`

**Purpose:** mark `api/` as a package and (optionally) export router objects.

**What to expect**

* Minimal content: package exports or helper to assemble routers.
* Keep small — actual request handling is in `endpoints.py`.

---

## `api/endpoints.py`

**Purpose:** define the HTTP endpoints your institution will POST to.

**What to expect**

* Endpoints:

  * `POST /build` — receives round 1 task JSON.
  * `POST /revise` — receives round ≥2 task JSON.
  * `GET /health` — returns basic status.
* Each endpoint:

  * Validates payload (via `api/validators.py`).
  * Verifies the secret (calls `services/secret_service`).
  * Records receipt (logs, optionally persist to local DB/cache).
  * Triggers the corresponding core flow (`core.build_flow` or `core.revise_flow`).
  * Returns a clear JSON response and HTTP code (200 on accepted; 4xx for validation/auth failure).
* Response detail:

  * The project spec requires you to *send a HTTP 200 JSON response* upon valid request receipt; implement that deterministically so the instructor system can proceed (do not hang until build finishes).
  * Include a short body like `{"status":"accepted","task":"<task>"}` for clarity.

**Error handling**

* Return 400 for malformed requests (with helpful error messages).
* Return 401/403 for secret/auth failures.
* Log and return 5xx for internal errors.

**Performance**

* Keep endpoint latency low — parse & validate quickly and hand off heavy work to core flows (background tasks or worker threads/processes).

**Testing**

* Unit tests cover validation failures, secret rejection, and that endpoint enqueues/starts the build flow.

---

## `api/validators.py`

**Purpose:** schema and content validation for incoming task requests.

**What to expect**

* Define the expected JSON shape (required fields: `email`, `task`, `round`, `nonce`, `brief`, `checks`, `evaluation_url`, `attachments`).
* Validate types & ranges:

  * `round` is integer ≥1.
  * `evaluation_url` is a valid URL and uses HTTPS (recommended).
  * `attachments` entries are well-formed (name + data URI).
  * `checks` is a non-empty list of strings.
* Sanity checks:

  * Reject overly large attachments (size limit).
  * Ensure `task` id length/allowed characters.
* Return detailed error objects highlighting which field failed.

**Testing**

* Tests should validate acceptance/rejection cases and edge-cases (missing fields, invalid data URIs).

---

## `core/__init__.py`

**Purpose:** package export for `core` flows.

**What to expect**

* Lightweight (exposes the build and revise entry points for import).

---

## `core/build_flow.py`

**Purpose:** full orchestration for **Round 1** builds — from task JSON to notifying the evaluator.

**High-level responsibilities**

1. Verify secret (call `services/secret_service`).
2. Decode & store attachments (via `utils/files.py` / `services/storage_service`).
3. Call LLM to generate a minimal app and README (`services/llm_service`), using `templates/app_prompt.txt`.
4. Produce an initial project structure (files + metadata). Ensure an MIT license is included (`templates/license.txt`).
5. Sanity-check generated code (basic lint/syntax check), and scan for accidental secrets.
6. Create a unique repo name (based on the provided `task` plus hash/timestamp) and push to GitHub (`services/github_service`).
7. Enable GitHub Pages and poll until the Pages URL responds 200 (with timeout).
8. POST metadata to `evaluation_url` (repo URL, commit SHA, pages URL) via `services/http_service` — follow the required retry backoff behavior if evaluator returns non-200.
9. Update local tracking (DB or `data/cache.json`) with results, timestamps and logs.
10. Clean up temporary files.

**Inputs / Outputs**

* Input: validated task JSON.
* Output: object/dict summarizing repo_url, commit_sha, pages_url, status and logs.

**Error handling & retries**

* Retry on transient network issues (GitHub, LLM, evaluation POST).
* If the build fails irrecoverably, log full error and POST a failure payload to the `evaluation_url` if appropriate (or follow the accepted instructor contract).
* Ensure you do **not** push if secrets are detected in files.

**Security**

* Do not embed tokens or secrets in generated files.
* Use secrets scanning (gitleaks/trufflehog integration or conservative regex checks).
* Ensure tokens are injected at runtime and never committed.

**Idempotency**

* Detect duplicate requests (same `task` + `nonce`) and avoid creating duplicate repos — either skip or attach a deterministic suffix.

**Testing**

* Unit-test orchestration with mocked LLM and GitHub services.
* Integration tests can exercise the full flow in a dev-mode with `DRY_RUN`.

---

## `core/revise_flow.py`

**Purpose:** orchestration for **Round 2+**: modify an existing repo in response to instructor changes, re-deploy and re-notify.

**High-level responsibilities**

1. Verify secret and identify the existing repo (from local DB or from request fields).
2. Clone/fetch current repository state (via `services/github_service`).
3. Provide repo context + new brief to the LLM and request a refactor/update (`services/llm_service`), using `templates/revise_prompt.txt`.
4. Validate changes (lint, tests if available), scan for secrets.
5. Commit changes and push (optionally on a branch and merge) via `services/github_service`.
6. Ensure GitHub Pages rebuilt and reachable.
7. POST updated metadata to `evaluation_url` (round number updated).
8. Log update to `data/models.py` / cache.

**Conflict & failure handling**

* If automatic refactor fails or would cause destructive changes, create a PR and notify (return an informative response / log).
* If LLM suggests large library additions, prefer explicit check/approval or fail-safe (instructors expect minimal, self-contained apps).

**Concurrency**

* Serialize revisions for the same repo/task to avoid race conditions.

**Testing**

* Simulate revise requests; ensure final repo contains expected modifications and that the pages URL is updated.

---

## `services/__init__.py`

**Purpose:** package initializer; optional convenience exports.

---

## `services/llm_service.py`

**Purpose:** single integration point to your chosen LLM for generation & refactor tasks.

**What to expect**

* Functions that:

  * Generate a new project given a brief + attachments + checks.
  * Produce README.md content from a template.
  * Produce refactor patches or updated file contents given a repo snapshot and new brief.
  * Produce a short, testable commit message & change summary for audit logs.
* Use the prompt templates from `templates/` and pass clear constraints (file size, dependencies, no external API keys).
* Provide token management and chunking for large inputs (attachments or long codebases).
* Post-process LLM output:

  * Convert from the LLM-delivered format into disk files.
  * Validate that files are syntactically correct (basic lint/parsing).
  * Sanitize anything that looks like a credential.

**Security & privacy**

* Do not send private secrets or personal tokens to a third-party LLM.
* Consider redacting any sensitive info before sending repo contents to LLM.

**Reliability**

* Retry transient LLM errors.
* Cache LLM responses for reproducibility and debugging.
* Validate that the LLM did not produce disallowed content.

**Testing**

* Provide deterministic prompts for unit tests and stubbed LLM responses.

---

## `services/github_service.py`

**Purpose:** all interactions with GitHub: repo creation, commits, pushes, Pages enabling, cloning.

**What to expect**

* Create repo (unique name), set visibility to public (per spec) and add license file.
* Create initial commit with generated files and README.
* Enable GitHub Pages (use the API to enable pages and compute pages_url).
* Return `repo_url`, `commit_sha`, and `pages_url`.
* Clone/pull a repo for revise flow and push changes.
* Provide utilities:

  * Check whether a repo already exists.
  * Add tags/releases if needed.
  * Check Pages build status and retrieve build logs (if available).
* Rate-limit & retry handling (respect GitHub API response headers).
* Secret scanning hooks (scan commit tree before push).

**Security**

* Keep `GITHUB_TOKEN` only in environment vars or secret manager; never commit it.
* Ensure minimum scopes for the token (repo, pages) and avoid broader rights.

**Testing**

* Mock GitHub API for unit tests; have integration tests for a sandbox org/account.

---

## `services/http_service.py`

**Purpose:** robust HTTP client for posting evaluation metadata and checking URLs.

**What to expect**

* Post evaluation payload to `evaluation_url` with required headers (Content-Type: application/json).
* Implement the required retry/backoff behavior (1,2,4,8… seconds) until a maximum attempt threshold or until HTTP 200 is received.
* Timeouts for each request and total time budget.
* Functions to perform GET checks (e.g., confirm Pages URL returns 200).
* Structured logging of responses and attempts.

**Reliability**

* Exponential backoff with jitter.
* Respect the spec: ensure you attempt reliable resubmission.

**Testing**

* Tests simulate evaluator returning 500 several times then 200 and assert backoff logic.

---

## `services/secret_service.py`

**Purpose:** validate incoming secrets and protect endpoints.

**What to expect**

* Read expected secret(s) from config or secure store (never from repo).
* Compare using constant-time comparison to mitigate timing attacks.
* Optionally support hashed secrets (store only hashes).
* Rate-limit authentication attempts.
* Log suspicious auth failures and optionally alert (or increment a mitigation counter).

**Testing**

* Tests for valid/invalid secrets and rate-limit behavior.

---

## `services/storage_service.py` (optional)

**Purpose:** handle temporary file storage (attachments, generated project files).

**What to expect**

* Create secure temporary directories for each task.
* Write decoded attachments to disk and verify MIME/type.
* Provide functions to archive project dir (zip) if needed.
* Clean-up function to remove temp data after success/failure.
* Optional persistence (local or cloud) for large attachments, with TTL.

**Security**

* Ensure temporary files are in private directories with proper permissions.
* Do not persist secrets.

---

## `templates/app_prompt.txt`

**Purpose:** canonical LLM prompt to instruct code generation for fresh apps.

**What to expect**

* A carefully crafted system / user prompt skeleton with placeholders:

  * `{{brief}}`, `{{attachments}}`, `{{checks}}`, `{{seed}}`
* Constraints:

  * "Produce a minimal single-page app using vanilla HTML/CSS/JS."
  * "Include README, MIT license, and a small testable script to satisfy checks."
  * Format expectations (e.g., produce a JSON list of files).
* A small example demonstrating expected outputs & formatting rules for the LLM.

**Maintenance**

* Keep prompts small, explicit and reproducible; version-control them.

---

## `templates/revise_prompt.txt`

**Purpose:** LLM prompt template for refactors / round 2 requests.

**What to expect**

* Guidelines to present the current repo state and the change request.
* Clear instructions on what may/should be changed and what must be preserved (LICENSE, README, tests).
* Required output format (e.g., files to replace with new contents, commit message).
* Constraints to avoid introducing external secrets, heavy dependencies or network calls.

---

## `templates/readme_prompt.txt`

**Purpose:** instruct the LLM to produce a high-quality README.md.

**What to expect**

* Specified README sections:

  * Short summary
  * Setup & run instructions
  * How to test locally
  * Explanation of file structure
  * License statement
* Example style and tone (concise, professional).
* Requirement that README mentions how to reproduce the evaluation checks.

---

## `templates/license.txt`

**Purpose:** MIT license boilerplate used when seeding each repo.

**What to expect**

* MIT license text with placeholders for year and author.
* A small helper in `core` to render year/author into the file.

---

## `utils/__init__.py`

**Purpose:** package initializer.

---

## `utils/logger.py`

**Purpose:** structured, centralized logging utilities.

**What to expect**

* Function to create/get a logger with appropriate formatting (JSON or readable).
* Add contextual fields to logs (task id, nonce, email).
* Options to log to console, rotating file handler, or external observability backend.
* Utility to mask secrets in logs (mask tokens and secrets).
* Standard levels and correlation-id support.

**Testing**

* Tests ensure sensitive tokens are never printed and logs include a task context.

---

## `utils/config.py`

**Purpose:** load typed configuration and environment variables.

**What to expect**

* Use a structured config loader (pydantic `BaseSettings` recommended) to expose:

  * `GITHUB_TOKEN`, `LLM_API_KEY`, `STUDENT_SECRET`, `PORT`, `DEFAULT_BRANCH`, `RETRY_MAX_ATTEMPTS`, etc.
* Validate required fields at startup and provide helpful error messages.
* Support config overrides (env vars > dev.env).
* Provide a `get_config()` helper.

**Security**

* Encourage use of secret managers in production; include guidance in README.

---

## `utils/files.py`

**Purpose:** file-system helpers for attachments, project dirs and safe IO.

**What to expect**

* Helpers to:

  * Decode data URIs and write safe files.
  * Create and clean temporary project directories.
  * Sanitize filenames to avoid path traversal.
  * Compute checksums/hashes for idempotency/uniqueness.
* Provide basic MIME sniffing and file-size checks.

**Testing**

* Test data URI decoding, file write/read and cleanup.

---

## `utils/retry.py`

**Purpose:** small, reusable retry/backoff utility.

**What to expect**

* Decorator or helper to perform exponential backoff with optional jitter.
* Configurable parameters: initial delay, max attempts, allowed exception types.
* Logging hooks for each retry attempt.

**Use**

* Wrap network calls (GitHub, LLM, evaluation POST) with this helper.

---

## `data/__init__.py`

**Purpose:** package initializer for data utilities.

---

## `data/db.py` (optional)

**Purpose:** local persistence (SQLite) for tracking tasks and deployments.

**What to expect**

* Provide a minimal persistent store to record:

  * Task receives, status, timestamps.
  * Repo metadata (`repo_url`, `commit_sha`, `pages_url`).
  * Revision attempts and outcomes.
* Connection management; ensure thread/process-safety.
* CRUD helper functions called by `core` flows to mark progress.

**Why useful**

* Enables idempotency (detect duplicate tasks).
* Helps debugging and recovery after crashes.

---

## `data/models.py`

**Purpose:** define the data model for the local DB or cache.

**What to expect**

* `Task` model: email, task id, round, nonce, brief, received_at, status.
* `Deployment` model: repo_url, commit_sha, pages_url, deployed_at, logs.
* `Revision` model: similar to deployment but references previous commit.
* Migration notes and reference schemas (if using Alembic).

---

## `data/cache.json`

**Purpose:** very small, optional on-disk cache for last-known state.

**What to expect**

* A JSON file mapping `task -> last successful repo metadata`.
* Use as a fallback if DB not present.
* Keep it small and rotate/expire entries.

**Security**

* Do not store secrets in cache files.

---

## `tests/__init__.py`

**Purpose:** mark tests package and provide test helpers.

---

## `tests/test_build_flow.py`

**Purpose:** unit & integration tests for the build orchestration.

**What to expect**

* Mock `services/llm_service` and `services/github_service` to simulate success/failure.
* Tests for:

  * Valid request flows lead to a `repo_url` and a POST to evaluator.
  * Attachments are decoded and passed correctly.
  * Error paths produce clear logs and do not leak secrets.

---

## `tests/test_revise_flow.py`

**Purpose:** tests for revise flow logic.

**What to expect**

* Simulate revise requests and validate that:

  * Repo is fetched and passed to LLM.
  * Changes are committed and pushed.
  * Conflicts or failures are handled properly (e.g., create PR or return error).

---

## `tests/test_http_service.py`

**Purpose:** exercises HTTP client and retry/backoff logic.

**What to expect**

* Simulate an evaluator endpoint that returns a sequence of statuses (e.g., 500,500,200) and verify backoff behavior.
* Confirm timeouts and exception handling.

---

## `configs/dev.env`

**Purpose:** example local environment variables — **do not commit to VCS**.

**What to expect**

* Example variables:

  * `GITHUB_TOKEN=...` (placeholder)
  * `LLM_API_KEY=...`
  * `STUDENT_SECRET=...`
  * `PORT=8080`
* Include comments describing recommended production practices (use secret manager).

---

## `configs/logging.yaml`

**Purpose:** logging configuration for different environments.

**What to expect**

* Console formatter, file handlers, and log levels for development vs production.
* Example of JSON output for ingestion into log aggregators.

---

## `.env`

**Purpose:** runtime environment file for local development (gitignored).

**What to expect**

* Actual secret values (used by `utils/config.py`).
* Make sure `.gitignore` includes `.env`.

---

## `requirements.txt`

**Purpose:** dependency manifest for the project.

**What to expect**

* Pin versions of framework & libs used (FastAPI/Flask, requests/httpx, python-dotenv, pydantic, PyGithub, testing libs).
* Separate dev/test dependencies (pytest, a mocking library).
* Add a small README note about pinning and reproducible installs.

---

## `README.md`

**Purpose:** developer documentation and quickstart.

**What to expect**

* Project purpose & scope (student-side agent).
* Quickstart: env setup, install deps, how to run locally (development server), how to run tests.
* API documentation with example payloads for `/build` and `/revise` (include required/optional fields).
* Operational notes: timeouts, expected behaviour, how to rotate tokens, how the evaluation POST works.
* Security & privacy guidance (never commit secrets; use secret manager).
* Troubleshooting (common failures, where logs live).
* Contributing and license.

---

## Additional considerations (cross-cutting)

**Secrets & keys**

* Never write tokens into repo or commit history.
* Prefer runtime environment variables or a secret manager (HashiCorp/AWS/GCP secret storage).
* When scanning for secrets, treat false positives carefully but err on the side of not pushing.

**Idempotency & deduplication**

* Use `task + nonce` to avoid re-processing the same request.
* Persist state (DB or `cache.json`) for recovery after crashes.

**Observability**

* Include structured logs with task-level correlation id.
* Expose `/health` and optionally `/metrics` for uptime and performance monitoring.

**Timeouts & budgets**

* The instructor evaluator expects a Pages POST within ~10 minutes; design flows to meet that window and surface progress.

**Security & privacy with LLM**

* Avoid sending private keys or personal tokens to the LLM.
* Use minimal context: send only parts of the repo necessary for refactor, not credentials.

**Testing**

* Unit test each service with mocks.
* Provide an integration/dev mode that runs with `DRY_RUN` and a sandbox GitHub account.
* Add CI (GitHub Actions) to run tests and static checks.

---