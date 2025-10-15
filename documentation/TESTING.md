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
    "email": "23f2001251@ds.study.iitm.ac.in",
    "secret": "super_secret_token",
    "task": "Simple Calculator",
    "round": 1,
    "nonce": "abc123def456ghi789jkl0",
    "brief": "Create a simple calculator allowing simple BODMAS operations, taking 2 numbers and operation as input and giving result as output",
    "checks": [
      "Repo has MIT license",
      "README.md is professional",
      "Page displays 2 input boxes",
      "Page displays +, -, *, / operation buttons",
      "Page displays results immediately on the screen"
    ],
    "evaluation_url": "https://example.com/notify",
    "attachments": []
  }'

    # "attachments": [
    #   {
    #     "name": "logo.png",
    #     "url": "data:image/png;base64,iVBORw..."
    #   }
    # ]

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
$ curl -X POST "http://127.0.0.1:8000/build"   -H "Content-Type: application/json"   -d '{
    "email": "23f2001251@ds.study.iitm.ac.in",
    "secret": "super_secret_token",
    "task": "Simple Calculator",
    "round": 2,
    "nonce": "abc123def456ghi789jkl0",
    "brief": "Add another section where addition will be done based on the attachment provided it has 3 columns, output must be addition of three columns for each row",
    "checks": [
      "Repo has MIT license",
      "README.md is professional and updated based on refactoring",
      "Page displays another section for attachment output",
      "Page displays addition of all columns in a row and displays output",
      "Page displays results immediately on the screen"
    ],
    "evaluation_url": "https://example.com/notify",
    "attachments": [{
        "name": "data.csv",
        "url": "data:text/csv;base64,Y29sMSxjb2wyLGNvbDMKMSwyLDMKNiw3LDgK"
    }]
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