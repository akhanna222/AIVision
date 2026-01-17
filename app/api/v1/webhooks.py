"""
Webhook delivery utilities.
Note: CRUD endpoints are placeholder - webhook storage not yet implemented.
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

router = APIRouter()
logger = logging.getLogger(__name__)


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    is_active: bool = True
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: List[str]
    is_active: bool
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


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_webhook(
    webhook_data: WebhookCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Create webhook - not implemented."""
    raise HTTPException(status_code=501, detail="Webhook storage not implemented")


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """List webhooks - returns empty (not implemented)."""
    return []


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get webhook - not implemented."""
    raise HTTPException(status_code=404, detail="Webhook not found")


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Delete webhook - not implemented."""
    raise HTTPException(status_code=404, detail="Webhook not found")
