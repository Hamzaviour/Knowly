import requests

BASE_URL = "http://localhost:8000"

queries = [
    "plain",
    "explain",
    "tell me what is in it",
    "what is the cgpa and degree progress in the transcript?",
    "what grades were achieved in Big Data and Database Systems?"
]

for q in queries:
    print("=" * 60)
    print(f"QUERY: '{q}'")
    print("=" * 60)
    r = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={"workspace_id": "default-workspace", "query": q, "mode": "standard"}
    )
    if r.status_code == 200:
        data = r.json()
        print("ANSWER:\n" + data["answer"].encode("ascii", "replace").decode("ascii"))
        print("\nCITATIONS COUNT:", len(data.get("citations", [])))
    else:
        print(f"FAILED (Status {r.status_code}): {r.text}")
    print("\n")
