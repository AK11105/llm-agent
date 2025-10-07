# 🧪 LLM Deployment API — cURL Test Suite

## 1️⃣ Health Check

**Purpose:** Verify the server is running.

```bash
curl -X GET "http://127.0.0.1:8000/health"
```

**Expected Response:**

```json
{
  "status": "ok"
}
```

---

## 2️⃣ Build Endpoint (`/build`)

**Purpose:** Test round 1 build workflow.

### ✅ Valid Secret

```bash
curl -X POST "http://127.0.0.1:8000/build" \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "super_secret_token",
    "project_name": "phase6_test_app",
    "brief": {"goal": "Create a hello world app"}
  }'
```

**Expected Response:**

```json
{
  "status": "build_complete",
  "project": "phase6_test_app",
  "repo_url": "https://github.com/<username>/phase6_test_app.git",
  "pages_url": "https://<username>.github.io/phase6_test_app/",
  "files": [
    "workspace/phase6_test_app/main.py",
    "workspace/phase6_test_app/README.md",
    "workspace/phase6_test_app/index.html"
  ]
}
```

### ❌ Invalid Secret

```bash
curl -X POST "http://127.0.0.1:8000/build" \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "wrong_secret",
    "project_name": "phase6_test_invalid",
    "brief": {"goal": "Create a hello world app"}
  }'
```

**Expected Response:**

```json
{
  "detail": "Invalid secret"
}
```

---

## 3️⃣ Revise Endpoint (`/revise`)

**Purpose:** Test round 2 / revision workflow.

### ✅ Valid Secret & Revision List

```bash
curl -X POST "http://127.0.0.1:8000/revise" \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "super_secret_token",
    "project_name": "phase6_test_app",
    "brief": {"goal": "Add new SVG support and update README"},
    "repo_url": "https://github.com/<username>/phase6_test_app.git",
    "changes": [
        "add_svg_support",
        "update_readme"
    ]
  }'
```

**Expected Response:**

```json
{
  "status": "revision_complete",
  "project": "phase6_test_app",
  "repo_url": "https://github.com/<username>/phase6_test_app.git",
  "pages_url": "https://<username>.github.io/phase6_test_app/",
  "updated_files": [
    "workspace/phase6_test_app/main.py",
    "workspace/phase6_test_app/README.md",
    "workspace/phase6_test_app/index.html"
  ]
}
```

### ❌ Invalid Secret

```bash
curl -X POST "http://127.0.0.1:8000/revise" \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "wrong_secret",
    "project_name": "phase6_test_app",
    "brief": {"goal": "Add new SVG support"},
    "changes": ["add_svg_support"]
  }'
```

**Expected Response:**

```json
{
  "detail": "Invalid secret"
}
```

---