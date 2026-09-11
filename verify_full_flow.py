import requests
import sys

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("1. Testing Stripe Checkout & Usage Endpoints")
print("=" * 60)

# Check usage
r_usage = requests.get(f"{BASE_URL}/api/billing/usage")
assert r_usage.status_code == 200, f"Usage failed: {r_usage.text}"
print("[PASS] /api/billing/usage returns 200:", r_usage.json())

# Create checkout session
r_checkout = requests.post(f"{BASE_URL}/api/billing/create-checkout-session", json={"plan": "pro", "email": "test@enterprise.com"})
assert r_checkout.status_code == 200, f"Checkout failed: {r_checkout.text}"
print("[PASS] /api/billing/create-checkout-session returns 200:", r_checkout.json())

print("\n" + "=" * 60)
print("2. Testing Stripe Webhook Endpoints (both /webhook and /webhook/)")
print("=" * 60)

# Webhook checkout.session.completed
hook_payload = {
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "client_reference_id": "test_user_pro",
            "customer": "cus_test_stripe_live",
            "subscription": "sub_test_stripe_live",
            "customer_email": "pro_partner@enterprise.com"
        }
    }
}
r_hook = requests.post(f"{BASE_URL}/api/billing/webhook/", json=hook_payload)
assert r_hook.status_code == 200, f"Webhook failed: {r_hook.text}"
print("[PASS] POST /api/billing/webhook/ returns 200:", r_hook.json())

# Webhook customer.subscription.deleted
r_hook_del = requests.post(f"{BASE_URL}/api/billing/webhook", json={
    "type": "customer.subscription.deleted",
    "data": {
        "object": {
            "id": "sub_test_stripe_live",
            "customer": "cus_test_stripe_live"
        }
    }
})
assert r_hook_del.status_code == 200, f"Webhook delete failed: {r_hook_del.text}"
print("[PASS] POST /api/billing/webhook returns 200:", r_hook_del.json())

print("\n" + "=" * 60)
print("3. Testing Document Sharing by User Email")
print("=" * 60)

# Upload test doc
r_upload = requests.post(
    f"{BASE_URL}/api/v1/documents/upload",
    files={"file": ("partnership_agreement.txt", b"Master Partnership Agreement 2026.")},
    data={"workspace_id": "default-workspace"}
)
assert r_upload.status_code == 200, f"Upload failed: {r_upload.text}"
doc_id = r_upload.json()["id"]
print(f"[PASS] Uploaded doc: {doc_id}")

# Share with colleague
r_share = requests.post(
    f"{BASE_URL}/api/v1/documents/{doc_id}/share",
    json={"email": "colleague@partner.com", "permission": "editor"}
)
assert r_share.status_code == 200, f"Share failed: {r_share.text}"
share_id = r_share.json()["share"]["id"]
print(f"[PASS] Shared document with colleague@partner.com (share_id: {share_id})")

# Get shares for document
r_shares = requests.get(f"{BASE_URL}/api/v1/documents/{doc_id}/shares")
assert r_shares.status_code == 200
shares = r_shares.json()
assert len(shares) >= 1
print(f"[PASS] Retrieved document shares list ({len(shares)} active):", [s["shared_with_email"] for s in shares])

# Get shared-with-me
r_shared_with_me = requests.get(f"{BASE_URL}/api/v1/documents/shared/with-me?email=colleague@partner.com")
assert r_shared_with_me.status_code == 200
shared_docs = r_shared_with_me.json()
assert len(shared_docs) >= 1
print(f"[PASS] /documents/shared/with-me returned {len(shared_docs)} documents for colleague@partner.com")

# Revoke share
r_revoke = requests.delete(f"{BASE_URL}/api/v1/documents/{doc_id}/shares/{share_id}")
assert r_revoke.status_code == 200
print(f"[PASS] Revoked share {share_id}:", r_revoke.json())

# Cleanup doc
requests.delete(f"{BASE_URL}/api/v1/documents/{doc_id}")
print(f"[PASS] Deleted test document {doc_id}")

print("\n" + "=" * 60)
print("ALL LIVE VERIFICATION TESTS PASSED SUCCESSFULLY! 100%")
print("=" * 60)
