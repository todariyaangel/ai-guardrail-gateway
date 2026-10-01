import httpx

url = "http://127.0.0.1:8000/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "X-Gateway-Team-ID": "engineering-alpha"
}
payload = {
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Say hello!"}]
}

print("Sending request to your local Gateway...")
try:
    # We use headers={} and clear headers control context explicitly
    with httpx.Client(headers={"Accept-Encoding": "identity"}) as client:
        response = client.post(url, json=payload, headers=headers, timeout=10.0)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.text)
except Exception as e:
    print(f"Connection failed: {e}")
