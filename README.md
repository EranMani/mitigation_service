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
* **Goal:** Demonstrate how the core `Policy` engine can be reused across different protocols (HTTP vs ICAP) without code duplication.
* **Usage:** Accepts raw `REQMOD ... PROMPT=...` packets.

---

## 🛠️ Installation & Setup

**Prerequisites:**
* Docker Desktop installed and running.
* Ensure you are in the project root directory:
```bash
cd mitigation_service
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
If you prefer running commands manually:

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

**3. Reload Policy (POST)**
Updates policy configuration without restarting the server

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