from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import stripe
from app.database import get_db
from app.auth import get_optional_user, require_user
from app.config import settings
from app.models.subscription import Subscription, PlanType, SubscriptionStatus
from app.models.user import User

router = APIRouter(tags=["Billing & Stripe"])

# Initialize Stripe key if present
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

@router.get("/customer")
@router.get("/status")
def get_customer_info(
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if not user:
        # Check default subscription in db if any
        sub = db.query(Subscription).first()
        if sub:
            return {
                "plan_type": sub.plan_type.value if hasattr(sub.plan_type, "value") else str(sub.plan_type),
                "status": sub.status.value if hasattr(sub.status, "value") else str(sub.status),
                "current_period_end": sub.current_period_end,
                "is_pro": sub.plan_type in [PlanType.PRO, "pro"] and sub.status in [SubscriptionStatus.ACTIVE, "active"]
            }
        return {"plan_type": "free", "status": "none", "is_pro": False}

    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not sub:
        return {"plan_type": "free", "status": "none", "is_pro": False}
    
    is_pro_active = sub.plan_type in [PlanType.PRO, "pro"] and sub.status in [SubscriptionStatus.ACTIVE, "active"]
    return {
        "plan_type": sub.plan_type.value if hasattr(sub.plan_type, "value") else str(sub.plan_type),
        "status": sub.status.value if hasattr(sub.status, "value") else str(sub.status),
        "current_period_end": sub.current_period_end,
        "is_pro": is_pro_active
    }

@router.get("/usage")
def get_usage_stats(
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    from app.models.document import Document
    from app.models.chat import ChatMessage
    
    docs_count = db.query(Document).count()
    queries_count = db.query(ChatMessage).filter(ChatMessage.role == "user").count()

    # Determine if active Pro
    is_pro_active = False
    if user:
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if sub and sub.plan_type in [PlanType.PRO, "pro"] and sub.status in [SubscriptionStatus.ACTIVE, "active"]:
            is_pro_active = True
    else:
        sub = db.query(Subscription).first()
        if sub and sub.plan_type in [PlanType.PRO, "pro"] and sub.status in [SubscriptionStatus.ACTIVE, "active"]:
            is_pro_active = True

    return {
        "docs_count": docs_count,
        "queries_this_month": queries_count,
        "queries_limit": 10000 if is_pro_active else 100,
        "max_documents": 999999 if is_pro_active else settings.FREE_PLAN_DOC_LIMIT,
        "is_pro": is_pro_active,
        "free_limit": settings.FREE_PLAN_DOC_LIMIT
    }

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    user_id = user.id if user else "demo_user"
    user_email = user.email if user else (body.get("email") or "customer@knowly.ai")
    price_id = settings.effective_stripe_price_id

    # If live Stripe secret key is present and configured, create live Stripe Checkout Session
    if settings.STRIPE_SECRET_KEY and settings.STRIPE_SECRET_KEY.startswith("sk_"):
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='http://localhost:3000/billing?success=1',
                cancel_url='http://localhost:3000/pricing?canceled=1',
                client_reference_id=user_id,
                customer_email=user_email,
                metadata={"user_id": user_id, "plan": "pro"}
            )
            return {"url": checkout_session.url, "session_id": checkout_session.id}
        except Exception as e:
            # Fall back gracefully to mock redirect with error message
            raise HTTPException(status_code=400, detail=f"Stripe Error: {str(e)}")

    # Local development / Zero-key fallback simulation
    if user:
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if not sub:
            sub = Subscription(user_id=user.id, plan_type=PlanType.PRO, status=SubscriptionStatus.ACTIVE)
            db.add(sub)
        else:
            sub.plan_type = PlanType.PRO
            sub.status = SubscriptionStatus.ACTIVE
        db.commit()

    return {
        "url": "http://localhost:3000/billing?success=1",
        "mock": True,
        "message": "Local simulation mode: Subscription activated"
    }

@router.post("/portal")
async def create_portal_session(
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if settings.STRIPE_SECRET_KEY and settings.STRIPE_SECRET_KEY.startswith("sk_"):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        customer_id = None
        if user:
            sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
            if sub:
                customer_id = sub.stripe_customer_id
        
        if customer_id:
            try:
                portal_session = stripe.billing_portal.Session.create(
                    customer=customer_id,
                    return_url='http://localhost:3000/billing',
                )
                return {"url": portal_session.url}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Portal Error: {str(e)}")

    return {"url": "http://localhost:3000/billing", "mock": True}

@router.post("/update-plan")
async def update_plan(
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    data = await request.json()
    target_plan = data.get("plan", "free")
    new_plan = PlanType.PRO if target_plan == "pro" else PlanType.FREE

    if user:
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if not sub:
            sub = Subscription(
                user_id=user.id,
                plan_type=new_plan,
                status=SubscriptionStatus.ACTIVE if new_plan == PlanType.PRO else SubscriptionStatus.CANCELLED
            )
            db.add(sub)
        else:
            sub.plan_type = new_plan
            sub.status = SubscriptionStatus.ACTIVE if new_plan == PlanType.PRO else SubscriptionStatus.CANCELLED
        db.commit()
    return {"status": "success", "plan": target_plan}

@router.post("/webhook")
@router.post("/webhook/")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    event = None

    # Verify webhook signature if secret key is present
    if settings.STRIPE_WEBHOOK_SECRET and sig_header:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Parse JSON payload directly (useful for local CLI testing without verification or mock tests)
        try:
            import json
            event = json.loads(payload.decode('utf-8'))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

    event_type = event.get('type')
    event_data = event.get('data', {}).get('object', {})

    # 1. Checkout Session Completed
    if event_type == 'checkout.session.completed':
        user_id = event_data.get('client_reference_id') or event_data.get('metadata', {}).get('user_id')
        customer_id = event_data.get('customer')
        subscription_id = event_data.get('subscription')
        customer_email = event_data.get('customer_email') or event_data.get('customer_details', {}).get('email')

        # Find user by ID or Email
        user = None
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
        if not user and customer_email:
            user = db.query(User).filter(User.email == customer_email).first()

        target_user_id = user.id if user else (user_id or "default_user")

        sub = db.query(Subscription).filter(
            (Subscription.user_id == target_user_id) | 
            (Subscription.stripe_customer_id == customer_id)
        ).first()

        if not sub:
            sub = Subscription(
                user_id=target_user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan_type=PlanType.PRO,
                status=SubscriptionStatus.ACTIVE
            )
            db.add(sub)
        else:
            sub.stripe_customer_id = customer_id
            sub.stripe_subscription_id = subscription_id
            sub.plan_type = PlanType.PRO
            sub.status = SubscriptionStatus.ACTIVE
        db.commit()

    # 2. Subscription Created / Updated
    elif event_type in ['customer.subscription.created', 'customer.subscription.updated']:
        sub_id = event_data.get('id')
        customer_id = event_data.get('customer')
        stripe_status = event_data.get('status')
        period_end = event_data.get('current_period_end')

        mapped_status = SubscriptionStatus.ACTIVE
        if stripe_status in ['past_due', 'unpaid']:
            mapped_status = SubscriptionStatus.PAST_DUE
        elif stripe_status == 'canceled':
            mapped_status = SubscriptionStatus.CANCELLED
        elif stripe_status == 'trialing':
            mapped_status = SubscriptionStatus.TRIALING

        sub = db.query(Subscription).filter(
            (Subscription.stripe_subscription_id == sub_id) | 
            (Subscription.stripe_customer_id == customer_id)
        ).first()

        if sub:
            sub.status = mapped_status
            if period_end:
                sub.current_period_end = datetime.fromtimestamp(period_end)
            if mapped_status == SubscriptionStatus.ACTIVE:
                sub.plan_type = PlanType.PRO
            db.commit()

    # 3. Subscription Deleted / Cancelled
    elif event_type == 'customer.subscription.deleted':
        sub_id = event_data.get('id')
        customer_id = event_data.get('customer')
        sub = db.query(Subscription).filter(
            (Subscription.stripe_subscription_id == sub_id) | 
            (Subscription.stripe_customer_id == customer_id)
        ).first()
        if sub:
            sub.plan_type = PlanType.FREE
            sub.status = SubscriptionStatus.CANCELLED
            db.commit()

    # 4. Invoice Payment Succeeded
    elif event_type == 'invoice.payment_succeeded':
        customer_id = event_data.get('customer')
        sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
        if sub:
            sub.status = SubscriptionStatus.ACTIVE
            sub.plan_type = PlanType.PRO
            db.commit()

    # 5. Invoice Payment Failed
    elif event_type == 'invoice.payment_failed':
        customer_id = event_data.get('customer')
        sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
        if sub:
            sub.status = SubscriptionStatus.PAST_DUE
            db.commit()

    return {"status": "success", "event_type": event_type}
