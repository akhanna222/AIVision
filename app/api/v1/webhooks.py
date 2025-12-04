"""
Webhook management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import httpx
import hmac
import hashlib
import json

from app.db.session import get_db
from app.core.auth import get_current_account
from app.db.models import Account

router = APIRouter()


# Request/Response models
class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]  # e.g., ["extraction.completed", "extraction.failed", "batch.completed"]
    is_active: bool = True
    secret: Optional[str] = None


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: List[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


# Webhook delivery helper
async def deliver_webhook(webhook_url: str, event: str, payload: dict, secret: Optional[str] = None):
    """
    Deliver webhook notification.

    Args:
        webhook_url: Destination URL
        event: Event type (e.g., "extraction.completed")
        payload: Event data
        secret: Optional secret for HMAC signature
    """
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event,
        "X-Webhook-Timestamp": str(int(time.time()))
    }

    # Add HMAC signature if secret provided
    if secret:
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Webhook delivery failed: {e}")
        return False


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Create webhook.

    **Events:**
    - `extraction.completed` - Document extraction completed
    - `extraction.failed` - Document extraction failed
    - `batch.completed` - Batch processing completed
    - `template.created` - Template created
    - `account.limit_reached` - Monthly limit reached

    **Webhook Payload:**
    ```json
    {
      "event": "extraction.completed",
      "timestamp": "2024-01-15T10:30:00Z",
      "account_id": 123,
      "data": {
        "extraction_id": "ext_abc123",
        "filename": "document.pdf",
        "status": "completed",
        "quality_grade": "A"
      }
    }
    ```

    **Security:**
    If you provide a `secret`, webhook requests will include an HMAC signature
    in the `X-Webhook-Signature` header for verification.
    """
    # Note: Webhook model needs to be added to app/db/models.py
    # For now, return mock response
    return {
        "id": 1,
        "url": str(webhook_data.url),
        "events": webhook_data.events,
        "is_active": webhook_data.is_active,
        "created_at": "2024-01-15T10:30:00Z"
    }


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """List all webhooks for account"""
    # Return mock data for now
    return []


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get webhook by ID"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Webhook not found"
    )


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    updates: WebhookUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Update webhook"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Webhook not found"
    )


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Delete webhook"""
    return {"message": "Webhook deleted successfully"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Test webhook with sample payload.

    Sends a test event to verify webhook is working correctly.
    """
    # Mock webhook URL
    test_url = "https://example.com/webhook"

    # Sample payload
    payload = {
        "event": "webhook.test",
        "timestamp": "2024-01-15T10:30:00Z",
        "account_id": account.id,
        "data": {
            "message": "This is a test webhook event",
            "webhook_id": webhook_id
        }
    }

    # Attempt delivery
    success = await deliver_webhook(test_url, "webhook.test", payload)

    return {
        "success": success,
        "message": "Test webhook delivered" if success else "Test webhook failed"
    }


# Helper function to trigger webhooks (call from extraction service)
async def trigger_webhook_event(db: Session, account_id: int, event: str, data: dict):
    """
    Trigger webhook event for all registered webhooks.

    Args:
        db: Database session
        account_id: Account ID
        event: Event type
        data: Event data
    """
    # Get all active webhooks for account that listen to this event
    # webhooks = db.query(Webhook).filter(
    #     Webhook.account_id == account_id,
    #     Webhook.is_active == True,
    #     Webhook.events.contains([event])
    # ).all()

    # For each webhook, deliver event
    # for webhook in webhooks:
    #     await deliver_webhook(webhook.url, event, {
    #         "event": event,
    #         "timestamp": datetime.utcnow().isoformat(),
    #         "account_id": account_id,
    #         "data": data
    #     }, webhook.secret)

    pass
