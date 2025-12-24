# 🛡️ Mitigation Service

A lightweight, policy-driven HTTP service designed to redact PII (Personally Identifiable Information) and enforce security rules on text prompts before they reach downstream LLMs.

**Key Capabilities:**
-  **Blocking:** Automatically blocks prompts containing banned keywords (e.g., violence, self-harm).
-  **Redaction:** Detects and masks PII such as Emails, Phone Numbers, Secrets, and Credit Cards.
-  **Semantic Analysis:** Uses an offline AI model to detect dangerous *intent* (e.g., "how to make a bomb") even if specific keywords are missing.
-  **Audit History:** Maintains a searchable history of recent requests and actions.
-  **Dockerized:** Ready to deploy in any containerized environment.

---

**Architecture**
- server.py (The Doorman): Handles HTTP requests, validation, and history logging.
- policy.py (The Brain): Loads rules and orchestrates the decision-making process.
- semantic.py (The Investigator): Uses a localized AI model (`sentence-transformers`) to analyze prompt intent.
- redactors.py (The Workers): Individual classes responsible for regex-based text replacement.

---

## ✨ Features

### 1. AI Semantic Blocking
Unlike simple keyword lists, the service uses a local AI model (`all-MiniLM-L6-v2`) to understand the **meaning** of a prompt.
* **How it works:** It calculates the semantic distance between the user's prompt and a list of "banned concepts" (e.g., "instructions for illegal acts").
* **Offline Capable:** The AI model is baked into the Docker image, so it runs 100% offline with no internet access required at runtime.
* **Example:**
    * *User Prompt:* "I want to end my life."
    * *Keyword Match:* Fails (if "kill" isn't used).
    * *Semantic Match:* **BLOCKS** (Similar to concept "suicide").

### 2. Robust PII Redaction
The service uses a modular `Redactor` architecture to sanitize inputs.

| Type | Pattern | Replacement |
|------|---------|-------------|
| **Email** | `user@example.com` | `<EMAIL>` |
| **Phone** | `123-456-7890` | `<PHONE>` |
| **Secrets** | `SECRET{...}` | `<SECRET>` |
| **Credit Cards** | `1234 5678...` | `<CARD>` |

### 3. Configurable Policy Engine
All rules are defined in a simple `policy.json` file. You can toggle specific redactors or add banned words without changing the code.

### 4. "Fail-Closed" Architecture
Designed for security first. If the policy rules cannot be loaded (missing or invalid JSON), the server refuses to start to prevent data leakage.

### 5. ICAP Adapter (Mock)
In addition to the HTTP API, the service exposes a TCP endpoint on **port 1344** that simulates an ICAP (Internet Content Adaptation Protocol) interface.
* **What is ICAP?** It is a standard protocol used by proxies and firewalls to offload content scanning (e.g., checking a file for viruses or a URL for safety).
* **Why this matters:** This adapter demonstrates **Logic Reuse**. By abstracting the `Policy` engine from the network layer, the exact same mitigation rules (Block/Redact/Semantic) are applied to both REST API traffic and raw TCP stream traffic without duplicating a single line of business logic.
* **Goal:** Demonstrate how the core `Policy` engine can be reused across different protocols (HTTP vs ICAP) without code duplication.
* **Usage:** Accepts raw `REQMOD ... PROMPT=...` packets.

---

## 🛠️ Installation & Setup

> **Note on Constraints & Dependencies:**
> 1. **Standard Library Only:** The core service strictly follows the assignment constraint to use **only Python's Standard Library** (no `Flask`, `FastAPI`, etc.).
> 2. **Offline Runtime:** As per requirements, the service is designed to **run without internet access** once built.
>    * ⚠️ The initial build may take **5-10 minutes** to complete.
>    * This is intentional: the Dockerfile is installing `torch` and **downloading the AI model** to "bake" it into the image.
>    * First build: Requires internet to download base images and dependencies (`docker compose build`)
>    * The `--pull=never` flag ensures Docker uses cached images instead of checking the registry
>    * The only external dependency is the **Bonus Semantic Feature** (`sentence-transformers`).
>    * To support offline execution, the AI model is pre-downloaded and baked into the Docker image during the build phase (`download_model.py`).
>    * **Benefit:** This ensures the service works **100% offline** and starts up instantly on subsequent runs.
>    * If the library is missing, the code degrades gracefully and starts with semantic blocking disabled.


**Prerequisites:**
* Docker Desktop installed and running.
* Ensure you are in the project root directory:
```bash
cd mitigation_service
```

### ⚡ Quick Start (Linux / macOS)
A `Makefile` is provided to simplify the workflow.

| Command | Description |
| :--- | :--- |
| **`make build`** | **Step 1.** Builds the Docker image. **Requires Internet** (downloads PyTorch & Models). |
| **`make run`** | **Step 2.** Starts the service using the local image. **Works Offline.** |
| **`make demo`** | **Step 3.** Runs the automated test script (`run_demo.sh`) against the running server. |
| **`make clean`** | Stops and removes all containers. |
```bash
# 1. First, build the image (do this while you have internet!)
make build

# 2. Start the application (safe to run without internet)
make run

# 3. (Optional) Run the automated demo suite
make demo
```

### ⚡ Quick Start (Windows)
I have provided batch scripts to automate the entire build and run process.

| File | Description |
| :--- | :--- |
| **`run_server.bat`** | **Start Here.** Builds the Docker image, handles port conflicts, and starts the server. |
| **`run_demo.bat`** | **Demo** Mode. Starts the server and automatically fires 13 distinct test cases (HTTP + ICAP) to verify all features. |
---

### Option A: Run with Docker (Recommended)
This ensures the environment matches exactly what was developed.
If you prefer running raw Docker commands:

```bash
docker compose up --build
```

The server will start listening on:\
HTTP: Port 8000\
ICAP: Port 1344

### Option B: Run Locally (Python)
If you prefer to run it directly on your machine.
```bash
python server.py
```



## 🚀 Usage (API examples)
**1. Mitigate a Prompt for HTTP server(POST)**
Send text to the /mitigate endpoint to sanitize it.

Request using CMD
```bash
curl -X POST http://localhost:8000/mitigate -H "Content-Type: application/json" -d "{\"prompt\":\"i want to change my phone number to 0548045004\",\"user_id\":123}"
```

Request using POWERSHELL
```bash
curl -METHOD POST -Uri "http://localhost:8000/mitigate" -ContentType "application/json" -Body '{"prompt": "i want to change my phone number to 0548045004", "user_id": 123}'
```

Response (Blocked Example)
```bash
{
  "action": "block",
  "prompt_out": "My email is test@example.com and I hate you",
  "reason": "Contains banned keyword: hate",
  "user_id": "123"
}
```

Request (Semantic Example)
```bash
curl -X POST http://localhost:8000/mitigate -H "Content-Type: application/json" -d "{\"prompt\":\"I want to make a bomb\",\"user_id\":123}"
```
\
Response (Semantic Example)
```bash
{
  "action": "block",
  "prompt_out": "I want to make a bomb",
  "reason": "Semantic Policy Violation (Similarity: 0.92)",
  "user_id": "123"
}
```

**2. Mitigate a Prompt for ICAP server(POST)**\
Since ICAP is a raw TCP protocol, we use a Python one-liner to simulate a client sending a REQMOD command.\
\
Request using CMD
```bash
python -c "import socket; s=socket.socket(); s.connect(('localhost', 1344)); s.sendall(b'REQMOD icap://server/mitigate PROMPT=I want to kill the process\n'); print(s.recv(1024).decode())"
```
\
Request using Powershell
```bash
python -c 'import socket; s=socket.socket(); s.connect(("localhost", 1344)); s.sendall(b"REQMOD icap://server/mitigate PROMPT=I want to kill the process\n"); print(s.recv(1024).decode())'
```

**3. Check History (GET)**
View the last 20 interactions (by default) for auditing purposes\
However, you can choose how many last requests you want to view by adding ?n=number to the end-point

Request using CMD
```bash
curl http://localhost:8000/history
```
Get specific number of recent requests (e.g., last 5)
```bash
curl http://localhost:8000/history?n=5
```

Request using POWERSHELL
```bash
Invoke-RestMethod -Uri "http://localhost:8000/history" -Method Get | Select-Object -ExpandProperty history | Format-Table
```
Get specific number of recent requests (e.g., last 5)
```bash
Invoke-RestMethod -Uri "http://localhost:8000/history?n=5" -Method Get | Select-Object -ExpandProperty history | Format-Table
```


Response Example
```bash
{
  "history": [
    {
      "timestamp": "2025-12-23 15:40:00",
      "user_id": "123",
      "prompt_in": "My secret is SECRET{123}",
      "action": "redact",
      "reason": "P.I.I detected and redacted: ['Secret']"
    }
  ]
}
```

**4. Reload Policy (POST)**
Updates the live policy configuration without restarting the server.
* **Purpose:** Allows admins to add banned words or toggle redactors instantly.
* **Behavior:** The server attempts to parse `policy.json`. If valid, the new rules take effect immediately. If invalid (e.g., bad JSON syntax), the server keeps the old policy active and returns a 500 error to prevent downtime.

Request using CMD
```bash
curl -X POST http://localhost:8000/reload
```

Request using Powershell
```bash
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/reload"
```

---
## ⚙️ Configuration
Modify **policy.json** to change the behavior of the service. You can add new banned words or toggle specific redaction rules on/off.

```bash
{
  "banned_keywords": ["kill", "violence"],
  "max_prompt_chars": 1000,
  "semantic_blocking": {
    "enabled": true,
    "threshold": 0.6,
    "banned_phrases": [
        "how to make a bomb",
        "instructions for illegal acts",
        "stealing credit cards",
        "I want to hurt you"
    ]
  },
  "redaction_rules": {
    "redact_emails": true,
    "redact_phone_numbers": true,
    "redact_secrets": true,
    "redact_credit_cards": true
  }
}

```

---

## ❓ Troubleshooting

**1. Docker "Permission Denied" on Linux/WSL**
If you see `permission denied while trying to connect to the Docker daemon socket`:
* **Cause:** Your Linux user is not in the `docker` group.
* **Fix:**
  ```bash
  sudo usermod -aG docker $USER
  # Then log out and log back in for changes to take effect.
  ```

**2. "Make" command not found**
* **Cause:** make is not installed by default on some minimal Linux distros (or WSL).
* **Fix:**
  ```bash
  sudo apt-get update && sudo apt-get install make -y
  ```

**3. "command not found" or "\r" errors when running demo on Linux**
* **Cause:** The `run_demo.sh` file may have been saved with Windows Line Endings (CRLF) instead of Linux (LF).
* **Fix:** Convert the file to LF using `dos2unix` or a text editor, or run:
  ```bash
  sed -i 's/\r$//' run_demo.sh

