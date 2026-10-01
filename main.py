import os
import json
import httpx
import redis
import tiktoken
from fastapi import FastAPI, Request, Response, HTTPException, status
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv()
app = FastAPI(title="AI Token and Rate Guardrail Gateway")

try:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )
except Exception as e:
    print(f"Could not connect to Redis: {e}")

PRICING = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000}
}

def calculate_prompt_tokens(payload: dict, model: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    token_count = 0
    if "messages" in payload:
        for msg in payload["messages"]:
            token_count += len(encoding.encode(msg.get("content", "")))
    return token_count

def extract_latest_prompt(payload: dict) -> str:
    if "messages" in payload and len(payload["messages"]) > 0:
        return payload["messages"][-1].get("content", "").strip()
    return ""

@app.post("/v1/chat/completions")
async def gateway_chat_completions(request: Request):
    team_id = request.headers.get("X-Gateway-Team-ID")
    if not team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required security header: X-Gateway-Team-ID"
        )
        
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    model = body.get("model", "gpt-4o")
    budget_key = f"budget:{team_id}:daily"
    history_key = f"history:{team_id}:prompts"
    
    current_spend = float(r.get(budget_key) or 0.0)
    max_budget = float(os.getenv("DAILY_BUDGET_USD", 5.00))
    
    if current_spend >= max_budget:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Blocked. Team '{team_id}' hit daily spending ceiling (${current_spend:.2f}/${max_budget:.2f})."
        )

    current_prompt = extract_latest_prompt(body)
    if current_prompt:
        past_prompts = r.lrange(history_key, 0, 2)
        
        if past_prompts:
            for past_prompt in past_prompts:
                similarity = SequenceMatcher(None, current_prompt, past_prompt).ratio()
                if similarity > 0.90:
                    raise HTTPException(
                        status_code=status.HTTP_408_REQUEST_TIMEOUT,
                        detail="Transaction Aborted. Autonomous Loop Detector triggered. Repeated execution behavior flagged."
                    )
        
        r.lpush(history_key, current_prompt)
        r.ltrim(history_key, 0, 4)
        r.expire(history_key, 3600)

    input_tokens = calculate_prompt_tokens(body, model)
    model_pricing = PRICING.get(model, PRICING["gpt-4o"])
    estimated_cost = input_tokens * model_pricing["input"]
    
    if (current_spend + estimated_cost) > max_budget:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Transaction blocked. Predicted token overhead exceeds remaining daily budget capacity."
        )

    openai_url = "https://openai.com"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
        "Accept-Encoding": "identity"
    }

    async with httpx.AsyncClient() as client:
        try:
            upstream_response = await client.post(openai_url, json=body, headers=headers, timeout=30.0)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Upstream host connection failure: {exc}")

    response_content = upstream_response.text

    if upstream_response.status_code != 200:
        return Response(content=response_content, status_code=upstream_response.status_code, media_type="application/json")

    response_data = json.loads(response_content)
    usage = response_data.get("usage", {})
    actual_input = usage.get("prompt_tokens", input_tokens)
    actual_output = usage.get("completion_tokens", 0)
    
    final_cost = (actual_input * model_pricing["input"]) + (actual_output * model_pricing["output"])
    
    r.incrbyfloat(budget_key, final_cost)
    if r.ttl(budget_key) == -1:
         r.expire(budget_key, 86400)

    return Response(
        content=response_content,
        status_code=200,
        media_type="application/json",
        headers={
            "X-Gateway-Calculated-Cost": f"{final_cost:.6f}",
            "X-Gateway-Remaining-Budget": f"{(max_budget - (current_spend + final_cost)):.4f}"
        }
    )
