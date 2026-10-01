# AI Token & Budget Guardrail Gateway

This is a lightweight API proxy built with FastAPI and Redis to control LLM costs and stop runaway AI agent loops. 

Instead of your apps hitting OpenAI directly, they talk to this gateway. The gateway intercepts the requests, checks if the team is within budget, checks if the agent is stuck repeating itself, and then safely forwards the request.

## What it does
* **Cost Controls:** Real-time ledger tracking in Redis that blocks requests once a team hits their dynamic daily spending limit.
* **Infinite Loop Killswitch:** Uses standard string pattern matching to catch rogue agents sending duplicate prompts back-to-back, dropping the connection before it burns tokens.
* **Resilient Routing:** Asynchronous proxying that handles bad API responses or upstream errors gracefully without crashing your client app.

## The Stack
* **FastAPI** (Async routing engine)
* **Redis** (Fast in-memory cache database)
* **HTTPX** (Async network requests client)
* **Tiktoken** (OpenAI token counting utility)

## How It Processes Requests
1. Validates the incoming header `X-Gateway-Team-ID`.
2. Pulls the team's current spend from Redis. If they are over budget, it throws a `429 Too Many Requests`.
3. Runs a similarity score comparison against the last 3 prompts. If it is a >90% match, it assumes an infinite loop and stops execution with a `408 Timeout`.
4. Routes clean text data to the target endpoint securely.
5. Measures exact tokens used, increments the financial spend ledger in Redis, and passes response data back to the app.

## How to Set Up and Run Locally

### Prerequisites
Make sure you have Python 3.10+ installed and a Redis database running locally (you can spin up Redis inside Docker Desktop with `docker run -d --name redis-gateway -p 6379:6379 redis`).

### 1. Install dependencies
```bash
pip install fastapi uvicorn httpx redis tiktoken python-dotenv
```

### 2. Configure variables
Create a `.env` file in your root folder:
```env
OPENAI_API_KEY=your_actual_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
DAILY_BUDGET_USD=5.00
```

### 3. Launch the server
```bash
python -m uvicorn main:app --reload --port 8000
```

### 4. Test it out
Open a separate terminal window and execute the verification script to simulate traffic and watch the loop detector trigger on consecutive attempts:
```bash
python test_gateway.py
```
