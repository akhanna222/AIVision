"""
Analytics and reporting API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db import crud
from app.core.auth import get_current_account
from app.db.models import Account

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics.

    **Returns:**
    - Total extractions in period
    - Success rate
    - Average confidence
    - Total cost
    - Recent extractions
    - Model usage breakdown
    """
    # Get extraction stats
    stats = crud.get_extraction_stats(db, account.id, days=days)

    # Get recent extractions
    recent_extractions = crud.get_extractions(
        db,
        account.id,
        status=None,
        limit=10,
        offset=0
    )

    recent_list = [
        {
            "extraction_id": e.extraction_id,
            "filename": e.filename,
            "status": e.status,
            "quality_grade": e.quality_grade,
            "created_at": e.created_at.isoformat()
        }
        for e in recent_extractions
    ]

    # Get usage logs for model breakdown
    usage_logs = crud.get_usage_logs(db, account.id, days=days)

    model_usage = {}
    for log in usage_logs:
        model = log.vision_model
        if model not in model_usage:
            model_usage[model] = {
                "count": 0,
                "total_pages": 0,
                "total_cost": 0.0,
                "avg_time_ms": 0
            }

        model_usage[model]["count"] += 1
        model_usage[model]["total_pages"] += log.pages_processed
        model_usage[model]["total_cost"] += log.cost_usd
        model_usage[model]["avg_time_ms"] += log.processing_time_ms

    # Calculate averages
    for model, data in model_usage.items():
        if data["count"] > 0:
            data["avg_time_ms"] = int(data["avg_time_ms"] / data["count"])

    return {
        "period_days": days,
        "overview": stats,
        "recent_extractions": recent_list,
        "model_usage": model_usage,
        "account_usage": {
            "monthly_extractions": account.monthly_extractions,
            "monthly_limit": account.monthly_limit,
            "remaining": max(0, account.monthly_limit - account.monthly_extractions),
            "total_all_time": account.total_extractions
        }
    }


@router.get("/usage")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Get detailed usage analytics.

    **Returns:**
    - Daily extraction volume
    - Cost breakdown by model
    - Success rate trends
    - Peak usage times
    """
    usage_logs = crud.get_usage_logs(db, account.id, days=days)

    # Aggregate by date
    daily_stats = {}
    model_costs = {}

    for log in usage_logs:
        date = log.log_date.date().isoformat()

        if date not in daily_stats:
            daily_stats[date] = {
                "extractions": 0,
                "pages": 0,
                "cost": 0.0,
                "successes": 0
            }

        daily_stats[date]["extractions"] += 1
        daily_stats[date]["pages"] += log.pages_processed
        daily_stats[date]["cost"] += log.cost_usd
        if log.success:
            daily_stats[date]["successes"] += 1

        # Model costs
        model = log.vision_model
        if model not in model_costs:
            model_costs[model] = 0.0
        model_costs[model] += log.cost_usd

    return {
        "period_days": days,
        "daily_stats": daily_stats,
        "model_costs": model_costs,
        "total_cost": sum(model_costs.values()),
        "total_extractions": len(usage_logs),
        "avg_cost_per_extraction": sum(model_costs.values()) / len(usage_logs) if usage_logs else 0
    }


@router.get("/templates")
async def get_template_analytics(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Get template performance analytics.

    **Returns:**
    - Most used templates
    - Template success rates
    - Average confidence by template
    """
    templates = crud.get_templates(db, account.id, active_only=True)

    template_stats = [
        {
            "template_id": t.template_id,
            "template_name": t.template_name,
            "category": t.category,
            "usage_count": t.usage_count,
            "avg_confidence": round(t.avg_confidence, 3),
            "avg_completeness": round(t.avg_completeness, 3),
            "quality_grade": (
                "A" if t.avg_completeness >= 0.9 and t.avg_confidence >= 0.9
                else "B" if t.avg_completeness >= 0.8 and t.avg_confidence >= 0.8
                else "C" if t.avg_completeness >= 0.7 and t.avg_confidence >= 0.7
                else "D" if t.avg_completeness >= 0.6 and t.avg_confidence >= 0.6
                else "F"
            ) if t.usage_count > 0 else "N/A"
        }
        for t in templates
    ]

    # Sort by usage
    template_stats.sort(key=lambda x: x["usage_count"], reverse=True)

    return {
        "total_templates": len(template_stats),
        "templates": template_stats
    }


@router.get("/models")
async def get_model_performance(
    days: int = Query(30, ge=1, le=365),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Get vision model performance comparison.

    **Returns:**
    - Usage percentage by model
    - Average processing time
    - Cost per page
    - Success rate
    """
    usage_logs = crud.get_usage_logs(db, account.id, days=days)

    model_performance = {}

    for log in usage_logs:
        model = log.vision_model

        if model not in model_performance:
            model_performance[model] = {
                "usage_count": 0,
                "total_pages": 0,
                "total_cost": 0.0,
                "total_time_ms": 0,
                "successes": 0
            }

        model_performance[model]["usage_count"] += 1
        model_performance[model]["total_pages"] += log.pages_processed
        model_performance[model]["total_cost"] += log.cost_usd
        model_performance[model]["total_time_ms"] += log.processing_time_ms
        if log.success:
            model_performance[model]["successes"] += 1

    # Calculate metrics
    total_usage = sum(m["usage_count"] for m in model_performance.values())

    for model, data in model_performance.items():
        usage_count = data["usage_count"]
        data["usage_percentage"] = (usage_count / total_usage * 100) if total_usage > 0 else 0
        data["avg_time_seconds"] = round(data["total_time_ms"] / usage_count / 1000, 2) if usage_count > 0 else 0
        data["cost_per_page"] = round(data["total_cost"] / data["total_pages"], 3) if data["total_pages"] > 0 else 0
        data["success_rate"] = round((data["successes"] / usage_count * 100), 2) if usage_count > 0 else 0

        # Clean up intermediate fields
        del data["total_time_ms"]
        del data["successes"]

    return {
        "period_days": days,
        "total_extractions": total_usage,
        "models": model_performance
    }


@router.get("/logs")
async def get_api_logs(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Get API call logs for the account.

    **Query Parameters:**
    - days: Number of days to fetch logs (default: 7)
    - limit: Maximum number of logs to return (default: 100)
    - offset: Pagination offset (default: 0)
    - method: Filter by HTTP method (GET, POST, PUT, DELETE, etc.)
    - status_code: Filter by HTTP status code

    **Returns:**
    - List of API logs with:
      - Endpoint called
      - HTTP method
      - Status code
      - Response time
      - Timestamp
      - Request/response metadata
    """
    from datetime import datetime, timedelta

    # Fetch API logs from the database
    api_logs = crud.get_api_logs(
        db,
        account_id=account.id,
        days=days,
        limit=limit,
        offset=offset,
        method=method,
        status_code=status_code
    )

    logs_list = [
        {
            "id": log.id,
            "account_id": log.account_id,
            "endpoint": log.endpoint,
            "method": log.method,
            "status_code": log.status_code,
            "response_time_ms": log.response_time_ms,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat()
        }
        for log in api_logs
    ]

    return {
        "total": len(logs_list),
        "limit": limit,
        "offset": offset,
        "logs": logs_list
    }
