import requests

for url in [
    'http://localhost:8000/api/v1/stripe/usage',
    'http://localhost:8000/api/v1/billing/usage',
    'http://localhost:8000/api/billing/usage'
]:
    r = requests.get(url)
    print(f"{url} -> status: {r.status_code}, text: {r.text[:100]}")
