# 🛡️ AI Guardrail Gateway

An enterprise-grade, high-throughput LLM proxy control plane designed to sit between user-facing applications and Foundation Models. This system acts as an intelligent security firewall—intercepting, logging, and filtering out malicious inputs while validating structural prompt data in real-time.

---

## 🏗️ System Architecture

[ User / Client Application ]
            │
            ▼ (Secure HTTP Request)
┌────────────────────────────────────────┐
│      AI Guardrail Gateway Proxy        │
│  • FastAPI Server Layer                │
│  • X-Gateway-Team-ID Team Enforcement │
└───────────────────┬────────────────────┘
                    │
                    ├─► [ Input Defense: Prompt Injection Scanner ] ──► (Blocks Jailbreaks)
                    │
                    ├─► [ Privacy Guardrail: RegEx PII Redactor ]   ──► (Scrubs Emails/Phones)
                    │
                    ▼
[ Cleansed & Sanitized Payload Ready for LLM Ingestion ]

---

## 🚀 Core Capabilities

* **Security Header Verification:** Restricts access to internal team microservices by strictly validating required `X-Gateway-Team-ID` headers.
* **Input Injection Defense:** Real-time semantic analysis layer designed to catch and drop prompt jailbreak strings (e.g., *"ignore previous instructions"*).
* **Data Privacy Compliance:** Algorithmic regex extraction engine that automatically discovers and redacts sensitive PII (emails and phone numbers) to prevent training data leaks.
* **Automated MLOps Guardrails:** Integrated **Continuous Integration (CI/CD)** pipeline that executes test assertions inside an isolated cloud runner.

---

## 🛠️ Tech Stack & Skills Proven

* **Core Backend:** Python • FastAPI • Uvicorn • Pydantic
* **Testing Framework:** PyTest • HTTPX Mock Testing
* **Infrastructure & MLOps:** GitHub Actions CI/CD Workflows • Git/GitHub Hygiene • Data Privacy Controls

---

## 💻 Local Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com
cd ai-guardrail-gateway
```

### 2. Install Project Dependencies
```bash
pip install -r requirements.txt pytest httpx
```

### 3. Run the Microservice Locally
```bash
uvicorn main:app --reload
```

---

## 🧪 Automated Testing

This repository leverages an automated CI pipeline. Every single push or pull request automatically instantiates an isolated testing suite via GitHub Actions to assert boundary vulnerabilities before distribution.

To execute tests manually:
```bash
python -m pytest test_gateway.py
```
