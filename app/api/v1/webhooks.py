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
import time
import logging

from app.db.session import get_db
from app.core.auth import get_current_account
from app.db.models import Account
from app.db import crud

router = APIRouter()
logger = logging.getLogger(__name__)


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    is_active: bool = True


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: List[str]
    is_active: bool
    success_count: int
    failure_count: int
    last_triggered: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


async def deliver_webhook(
    webhook_url: str,
    event: str,
    payload: dict,
    secret: Optional[str] = None
) -> bool:
    """Deliver webhook notification with optional HMAC signature."""
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event,
        "X-Webhook-Timestamp": str(int(time.time()))
    }

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
            response = await client.post(webhook_url, json=payload, headers=headers)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Webhook delivery failed: {e}")
        return False


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """List all webhooks for account."""
    webhooks = crud.get_webhooks(db, account.id)
    return [
        WebhookResponse(
            id=w.id,
            url=w.url,
            events=w.events or [],
            is_active=w.is_active,
            success_count=w.success_count,
            failure_count=w.failure_count,
            last_triggered=w.last_triggered.isoformat() if w.last_triggered else None,
            created_at=w.created_at.isoformat() if w.created_at else ""
        )
        for w in webhooks
    ]


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Create a new webhook."""
    webhook = crud.create_webhook(
        db,
        account_id=account.id,
        url=str(data.url),
        events=data.events,
        secret=data.secret,
        is_active=data.is_active
    )
    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        success_count=webhook.success_count,
        failure_count=webhook.failure_count,
        last_triggered=None,
        created_at=webhook.created_at.isoformat() if webhook.created_at else ""
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get webhook by ID."""
    webhook = crud.get_webhook_by_id(db, account.id, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        success_count=webhook.success_count,
        failure_count=webhook.failure_count,
        last_triggered=webhook.last_triggered.isoformat() if webhook.last_triggered else None,
        created_at=webhook.created_at.isoformat() if webhook.created_at else ""
    )


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    updates: WebhookUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Update webhook."""
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])

    webhook = crud.update_webhook(db, account.id, webhook_id, update_data)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        success_count=webhook.success_count,
        failure_count=webhook.failure_count,
        last_triggered=webhook.last_triggered.isoformat() if webhook.last_triggered else None,
        created_at=webhook.created_at.isoformat() if webhook.created_at else ""
    )


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Delete webhook."""
    if not crud.delete_webhook(db, account.id, webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Test webhook with sample payload."""
    webhook = crud.get_webhook_by_id(db, account.id, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    payload = {
        "event": "webhook.test",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "account_id": account.id,
        "data": {"message": "Test webhook event", "webhook_id": webhook_id}
    }

    success = await deliver_webhook(webhook.url, "webhook.test", payload, webhook.secret)
    crud.record_webhook_result(db, webhook_id, success)

    return {
        "success": success,
        "message": "Test delivered" if success else "Test failed"
    }
