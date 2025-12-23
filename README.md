# 🛡️ Mitigation Service

A lightweight, policy-driven HTTP service designed to redact PII (Personally Identifiable Information) and enforce security rules on text prompts before they reach downstream LLMs.

**Key Capabilities:**
-  **Blocking:** Automatically blocks prompts containing banned keywords (e.g., violence, self-harm).
-  **Redaction:** Detects and masks PII such as Emails, Phone Numbers, Secrets, and Credit Cards.
-  **Audit History:** Maintains a searchable history of recent requests and actions.
-  **Dockerized:** Ready to deploy in any containerized environment.

---

**Architecture**
- server.py (The Doorman): Handles HTTP requests, validation, and history logging.
- policy.py (The Brain): Loads rules and orchestrates the decision-making process.
- redactors.py (The Workers): Individual classes responsible for regex-based text replacement.

---

## ✨ Features

### 1. Robust PII Redaction
The service uses a modular `Redactor` architecture to sanitize inputs.

| Type | Pattern | Replacement |
|------|---------|-------------|
| **Email** | `user@example.com` | `<EMAIL>` |
| **Phone** | `123-456-7890` | `<PHONE>` |
| **Secrets** | `SECRET{...}` | `<SECRET>` |
| **Credit Cards** | `1234 5678...` | `<CARD>` |

### 2. Configurable Policy Engine
All rules are defined in a simple `policy.json` file. You can toggle specific redactors or add banned words without changing the code.

### 3. "Fail-Closed" Architecture
Designed for security first. If the policy rules cannot be loaded (missing or invalid JSON), the server refuses to start to prevent data leakage.

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
| **`run_demo.bat`** | **Demo Mode.** Starts the server *and* automatically fires 10 distinct test cases (Allow, Block, Redact) to verify all features. |
---

### Option A: Run with Docker (Recommended)
This ensures the environment matches exactly what was developed.
If you prefer running commands manually:

**1. Build the Image**
```bash
docker build -t mitigation-service .
```

**2. Run the Container**
```bash
docker run -p 8000:8000 mitigation-service
```

The server will start listening on port 8000.

### Option B: Run Locally (Python)
If you prefer to run it directly on your machine.
```bash
python server.py
```



## 🚀 Usage
**1. Mitigate a Prompt (POST)**
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

**2. Check History (GET)**
View the last 20 interactions (by default) for auditing purposes
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
  "redaction_rules": {
    "redact_emails": true,
    "redact_phone_numbers": true,
    "redact_secrets": true,
    "redact_credit_cards": true
}

```