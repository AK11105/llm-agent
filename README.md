# LLM Code Deployment

**Project Overview**
This project demonstrates a fully automated workflow where students build, deploy, update, and evaluate applications using LLM-assisted code generation, GitHub Pages, and automated evaluation pipelines.

The project simulates a real-world software lifecycle:

1. **Build** – Students receive a task brief, generate code using LLMs, deploy to GitHub Pages, and notify an evaluation API.
2. **Evaluate** – Instructors perform automated static, dynamic, and LLM-based checks on the submitted app.
3. **Revise** – Students apply requested revisions, re-deploy, and notify the evaluation API again.

---

## Features

### Build

* Accepts a JSON POST request with app brief, secret, and attachments.
* Verifies the secret against a known value.
* Generates application code using an LLM-assisted generator.
* Creates a GitHub repository with a unique name.
* Adds an MIT LICENSE, complete `README.md`, and pushes the code.
* Enables GitHub Pages and returns a deployable URL.
* Sends project metadata (`repo_url`, `pages_url`, `commit_sha`) to an evaluation API.

### Revise

* Accepts round 2 POST requests for code modifications.
* Verifies student secret.
* Updates the repository code according to the new brief.
* Updates `README.md` to reflect changes.
* Re-deploys GitHub Pages.
* Sends updated repo metadata back to evaluation API.

### Evaluate

* Instructors perform automated checks:

  * **Repo-level:** LICENSE, README, public repo.
  * **LLM-based:** Code and documentation quality.
  * **Dynamic:** Run Playwright scripts to validate functionality.
* Round 2 tasks are automatically generated based on round 1 submissions.

---

## Request Format

```json
{
  "email": "student@example.com",
  "secret": "student-secret",
  "task": "captcha-solver-xyz123",
  "round": 1,
  "nonce": "ab12-...",
  "brief": "Create a captcha solver that handles ?url=https://.../image.png.",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Page displays captcha URL passed at ?url=...",
    "Page displays solved captcha text within 15 seconds"
  ],
  "evaluation_url": "https://example.com/notify",
  "attachments": [
    {
      "name": "sample.png",
      "url": "data:image/png;base64,iVBORw..."
    }
  ]
}
```

---

## Endpoints

| Endpoint      | Method | Description                                                          |
| ------------- | ------ | -------------------------------------------------------------------- |
| `/build`      | POST   | Accepts a build request, generates and deploys an app.               |
| `/revise`     | POST   | Accepts a revision request, updates code, and re-deploys.            |
| `/evaluation` | POST   | Receives repo metadata and evaluation results (instructor endpoint). |

**Example build response:**

```json
{
  "status": "build_and_deploy_complete",
  "repo_url": "https://github.com/user/repo",
  "pages_url": "https://user.github.io/repo/",
  "commit_sha": "abc123"
}
```

---
