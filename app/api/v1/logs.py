"""
API logs endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.core.auth import get_current_account
from app.db.models import Account
from app.db import crud

router = APIRouter()


class APILogResponse(BaseModel):
    id: int
    endpoint: str
    method: str
    status_code: int
    response_time_ms: Optional[int]
    ip_address: Optional[str]
    timestamp: str

    class Config:
        from_attributes = True


class LogsListResponse(BaseModel):
    logs: List[APILogResponse]
    total: int
    limit: int
    offset: int


@router.get("/", response_model=LogsListResponse)
async def list_logs(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    List API logs for account.

    - **days**: Number of days to look back (1-90)
    - **limit**: Max logs to return (1-500)
    - **offset**: Pagination offset
    - **method**: Filter by HTTP method (GET, POST, etc.)
    - **status_code**: Filter by status code (200, 404, etc.)
    """
    logs = crud.get_api_logs(
        db,
        account_id=account.id,
        days=days,
        limit=limit,
        offset=offset,
        method=method,
        status_code=status_code
    )

    return LogsListResponse(
        logs=[
            APILogResponse(
                id=log.id,
                endpoint=log.endpoint,
                method=log.method,
                status_code=log.status_code or 0,
                response_time_ms=log.response_time_ms,
                ip_address=log.ip_address,
                timestamp=log.timestamp.isoformat() if log.timestamp else ""
            )
            for log in logs
        ],
        total=len(logs),
        limit=limit,
        offset=offset
    )
