"""
CRUD operations for database models.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta

from app.db.models import (
    Account, Country, Template, DocumentTag,
    Extraction, UsageLog, APILog, DEFAULT_COUNTRIES
)


# ============================================================================
# ACCOUNT OPERATIONS
# ============================================================================

def create_account(
    db: Session,
    name: str,
    email: str,
    plan: str = "free"
) -> Account:
    """Create new account with default settings"""
    account = Account(
        name=name,
        email=email,
        plan=plan,
        api_token=Account.generate_api_token(),
        enabled_models=["gemini-2.0-flash-exp", "gpt-4o", "claude-sonnet-4-20250514"]
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    # Create default countries
    for country_data in DEFAULT_COUNTRIES:
        country = Country(
            account_id=account.id,
            **country_data
        )
        db.add(country)

    db.commit()
    return account


def get_account_by_id(db: Session, account_id: int) -> Optional[Account]:
    """Get account by ID"""
    return db.query(Account).filter(Account.id == account_id).first()


def get_account_by_email(db: Session, email: str) -> Optional[Account]:
    """Get account by email"""
    return db.query(Account).filter(Account.email == email).first()


def get_account_by_token(db: Session, api_token: str) -> Optional[Account]:
    """Get account by API token"""
    return db.query(Account).filter(
        and_(
            Account.api_token == api_token,
            Account.is_active == True
        )
    ).first()


def regenerate_api_token(db: Session, account_id: int) -> str:
    """Regenerate API token for account"""
    account = get_account_by_id(db, account_id)
    if account:
        account.api_token = Account.generate_api_token()
        db.commit()
        return account.api_token
    return None


def update_account_usage(
    db: Session,
    account_id: int,
    extractions: int = 1
):
    """Update account usage counters"""
    account = get_account_by_id(db, account_id)
    if account:
        account.total_extractions += extractions
        account.monthly_extractions += extractions
        db.commit()


def reset_monthly_usage(db: Session, account_id: int):
    """Reset monthly usage counter (run at start of month)"""
    account = get_account_by_id(db, account_id)
    if account:
        account.monthly_extractions = 0
        db.commit()


# ============================================================================
# COUNTRY OPERATIONS
# ============================================================================

def create_country(
    db: Session,
    account_id: int,
    code: str,
    name: str,
    is_active: bool = True
) -> Country:
    """Create custom country for account"""
    country = Country(
        account_id=account_id,
        code=code.upper(),
        name=name,
        is_active=is_active,
        is_default=False
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def get_countries(
    db: Session,
    account_id: int,
    active_only: bool = True
) -> List[Country]:
    """Get countries for account"""
    query = db.query(Country).filter(Country.account_id == account_id)
    if active_only:
        query = query.filter(Country.is_active == True)
    return query.all()


def get_country_by_code(
    db: Session,
    account_id: int,
    code: str
) -> Optional[Country]:
    """Get country by code"""
    return db.query(Country).filter(
        and_(
            Country.account_id == account_id,
            Country.code == code.upper()
        )
    ).first()


# ============================================================================
# TEMPLATE OPERATIONS
# ============================================================================

def create_template(
    db: Session,
    account_id: int,
    template_data: Dict[str, Any]
) -> Template:
    """Create new template"""
    template = Template(
        account_id=account_id,
        **template_data
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def get_templates(
    db: Session,
    account_id: int,
    category: Optional[str] = None,
    country_id: Optional[int] = None,
    active_only: bool = True
) -> List[Template]:
    """Get templates for account with optional filters"""
    query = db.query(Template).filter(Template.account_id == account_id)

    if active_only:
        query = query.filter(Template.is_active == True)
    if category:
        query = query.filter(Template.category == category)
    if country_id:
        query = query.filter(Template.country_id == country_id)

    return query.order_by(desc(Template.usage_count)).all()


def get_template_by_id(
    db: Session,
    account_id: int,
    template_id: str
) -> Optional[Template]:
    """Get template by template_id"""
    return db.query(Template).filter(
        and_(
            Template.account_id == account_id,
            Template.template_id == template_id,
            Template.is_active == True
        )
    ).first()


def update_template(
    db: Session,
    account_id: int,
    template_id: str,
    updates: Dict[str, Any]
) -> Optional[Template]:
    """Update template"""
    template = get_template_by_id(db, account_id, template_id)
    if template:
        for key, value in updates.items():
            setattr(template, key, value)
        db.commit()
        db.refresh(template)
    return template


def delete_template(
    db: Session,
    account_id: int,
    template_id: str
) -> bool:
    """Soft delete template"""
    template = get_template_by_id(db, account_id, template_id)
    if template:
        template.is_active = False
        db.commit()
        return True
    return False


def update_template_stats(
    db: Session,
    template_id: int,
    confidence: float,
    completeness: float
):
    """Update template usage statistics"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if template:
        template.usage_count += 1
        # Running average
        template.avg_confidence = (
            (template.avg_confidence * (template.usage_count - 1) + confidence) /
            template.usage_count
        )
        template.avg_completeness = (
            (template.avg_completeness * (template.usage_count - 1) + completeness) /
            template.usage_count
        )
        db.commit()


# ============================================================================
# DOCUMENT TAG OPERATIONS
# ============================================================================

def create_document_tag(
    db: Session,
    account_id: int,
    tag_name: str,
    tag_category: Optional[str] = None,
    auto_tag_rules: Optional[Dict] = None
) -> DocumentTag:
    """Create document tag"""
    tag = DocumentTag(
        account_id=account_id,
        tag_name=tag_name,
        tag_category=tag_category,
        auto_tag_rules=auto_tag_rules
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def get_document_tags(
    db: Session,
    account_id: int,
    category: Optional[str] = None
) -> List[DocumentTag]:
    """Get document tags for account"""
    query = db.query(DocumentTag).filter(DocumentTag.account_id == account_id)
    if category:
        query = query.filter(DocumentTag.tag_category == category)
    return query.order_by(desc(DocumentTag.usage_count)).all()


def increment_tag_usage(db: Session, tag_id: int):
    """Increment tag usage counter"""
    tag = db.query(DocumentTag).filter(DocumentTag.id == tag_id).first()
    if tag:
        tag.usage_count += 1
        db.commit()


# ============================================================================
# EXTRACTION OPERATIONS
# ============================================================================

def create_extraction(
    db: Session,
    extraction_data: Dict[str, Any]
) -> Extraction:
    """Create extraction record"""
    extraction = Extraction(**extraction_data)
    db.add(extraction)
    db.commit()
    db.refresh(extraction)
    return extraction


def get_extraction(
    db: Session,
    account_id: int,
    extraction_id: str
) -> Optional[Extraction]:
    """Get extraction by ID"""
    return db.query(Extraction).filter(
        and_(
            Extraction.account_id == account_id,
            Extraction.extraction_id == extraction_id
        )
    ).first()


def get_extractions(
    db: Session,
    account_id: int,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Extraction]:
    """Get extractions for account"""
    query = db.query(Extraction).filter(Extraction.account_id == account_id)

    if status:
        query = query.filter(Extraction.status == status)

    return query.order_by(desc(Extraction.created_at)).limit(limit).offset(offset).all()


def update_extraction(
    db: Session,
    extraction_id: str,
    updates: Dict[str, Any]
) -> Optional[Extraction]:
    """Update extraction record"""
    extraction = db.query(Extraction).filter(
        Extraction.extraction_id == extraction_id
    ).first()

    if extraction:
        for key, value in updates.items():
            setattr(extraction, key, value)
        db.commit()
        db.refresh(extraction)
    return extraction


def get_extraction_stats(
    db: Session,
    account_id: int,
    days: int = 30
) -> Dict[str, Any]:
    """Get extraction statistics for account"""
    since_date = datetime.utcnow() - timedelta(days=days)

    total = db.query(func.count(Extraction.id)).filter(
        and_(
            Extraction.account_id == account_id,
            Extraction.created_at >= since_date
        )
    ).scalar()

    completed = db.query(func.count(Extraction.id)).filter(
        and_(
            Extraction.account_id == account_id,
            Extraction.created_at >= since_date,
            Extraction.status == "completed"
        )
    ).scalar()

    avg_confidence = db.query(func.avg(Extraction.average_confidence)).filter(
        and_(
            Extraction.account_id == account_id,
            Extraction.created_at >= since_date,
            Extraction.status == "completed"
        )
    ).scalar() or 0.0

    total_cost = db.query(func.sum(Extraction.cost_usd)).filter(
        and_(
            Extraction.account_id == account_id,
            Extraction.created_at >= since_date
        )
    ).scalar() or 0.0

    return {
        "total_extractions": total,
        "completed": completed,
        "success_rate": (completed / total * 100) if total > 0 else 0,
        "avg_confidence": float(avg_confidence),
        "total_cost_usd": float(total_cost)
    }


# ============================================================================
# USAGE LOG OPERATIONS
# ============================================================================

def log_usage(
    db: Session,
    account_id: int,
    operation: str,
    vision_model: str,
    pages_processed: int,
    tokens_used: int,
    cost_usd: float,
    success: bool = True,
    processing_time_ms: int = 0,
    extraction_id: Optional[str] = None
):
    """Log usage for billing and analytics"""
    log = UsageLog(
        account_id=account_id,
        operation=operation,
        vision_model=vision_model,
        pages_processed=pages_processed,
        tokens_used=tokens_used,
        cost_usd=cost_usd,
        success=success,
        processing_time_ms=processing_time_ms,
        extraction_id=extraction_id
    )
    db.add(log)
    db.commit()


def get_usage_logs(
    db: Session,
    account_id: int,
    days: int = 30
) -> List[UsageLog]:
    """Get usage logs for account"""
    since_date = datetime.utcnow() - timedelta(days=days)
    return db.query(UsageLog).filter(
        and_(
            UsageLog.account_id == account_id,
            UsageLog.log_date >= since_date
        )
    ).order_by(desc(UsageLog.log_date)).all()


# ============================================================================
# API LOG OPERATIONS
# ============================================================================

def log_api_request(
    db: Session,
    endpoint: str,
    method: str,
    status_code: int,
    account_id: Optional[int] = None,
    api_token: Optional[str] = None,
    response_time_ms: int = 0,
    ip_address: Optional[str] = None
):
    """Log API request"""
    log = APILog(
        account_id=account_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        api_token=api_token,
        response_time_ms=response_time_ms,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()


def get_api_logs(
    db: Session,
    account_id: int,
    days: int = 7,
    limit: int = 100,
    offset: int = 0,
    method: Optional[str] = None,
    status_code: Optional[int] = None
) -> List[APILog]:
    """
    Get API logs for account with optional filters.

    Args:
        db: Database session
        account_id: Account ID to filter logs
        days: Number of days to look back
        limit: Maximum number of logs to return
        offset: Pagination offset
        method: Optional HTTP method filter
        status_code: Optional status code filter

    Returns:
        List of APILog objects
    """
    since_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(APILog).filter(
        and_(
            APILog.account_id == account_id,
            APILog.created_at >= since_date
        )
    )

    if method:
        query = query.filter(APILog.method == method.upper())

    if status_code:
        query = query.filter(APILog.status_code == status_code)

    return query.order_by(desc(APILog.created_at)).limit(limit).offset(offset).all()
