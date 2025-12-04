"""
Database models for AIVision OCR service.
Multi-tenant architecture with account-specific templates and extractions.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import secrets

Base = declarative_base()


class Account(Base):
    """Account/Organization model - multi-tenant support"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Subscription details
    plan = Column(String(50), default="free")  # free, starter, professional, enterprise
    is_active = Column(Boolean, default=True)

    # API tokens
    api_token = Column(String(255), unique=True, nullable=False, index=True)
    api_token_expires = Column(DateTime, nullable=True)

    # Usage tracking
    total_extractions = Column(Integer, default=0)
    monthly_extractions = Column(Integer, default=0)
    monthly_limit = Column(Integer, default=100)  # Based on plan

    # Vision model preferences
    default_vision_model = Column(String(50), default="gemini-2.0-flash-exp")
    enabled_models = Column(JSON, default=list)  # List of enabled models

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    templates = relationship("Template", back_populates="account", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="account", cascade="all, delete-orphan")
    countries = relationship("Country", back_populates="account", cascade="all, delete-orphan")
    document_tags = relationship("DocumentTag", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, plan={self.plan})>"

    @staticmethod
    def generate_api_token():
        """Generate secure API token"""
        return f"aiv_{secrets.token_urlsafe(32)}"


class Country(Base):
    """Dynamic country management - accounts can add custom countries"""
    __tablename__ = "countries"
    __table_args__ = (
        UniqueConstraint('account_id', 'code', name='uix_account_country_code'),
        Index('ix_countries_account_code', 'account_id', 'code'),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Country details
    code = Column(String(3), nullable=False)  # ISO 3166-1 alpha-2/3
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Pre-configured countries

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    account = relationship("Account", back_populates="countries")
    templates = relationship("Template", back_populates="country")

    def __repr__(self):
        return f"<Country(code={self.code}, name={self.name})>"


class Template(Base):
    """Document template model - account-specific"""
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint('account_id', 'template_id', name='uix_account_template_id'),
        Index('ix_templates_account_category', 'account_id', 'category'),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)

    # Template identification
    template_id = Column(String(255), nullable=False, index=True)  # e.g., ie_mortgage_app_v1
    template_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)

    # Template details
    description = Column(Text)
    version = Column(String(20), default="1.0.0")
    fields = Column(JSON, nullable=False)  # List of field definitions
    page_structure = Column(JSON, nullable=True)  # Expected page layout

    # Template metadata
    tags = Column(JSON, default=list)
    is_custom = Column(Boolean, default=True)  # Custom vs default template
    is_active = Column(Boolean, default=True)

    # Usage statistics
    usage_count = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    avg_completeness = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account", back_populates="templates")
    country = relationship("Country", back_populates="templates")
    extractions = relationship("Extraction", back_populates="template")

    def __repr__(self):
        return f"<Template(id={self.template_id}, name={self.template_name})>"


class DocumentTag(Base):
    """Auto-generated document tags for classification"""
    __tablename__ = "document_tags"
    __table_args__ = (
        UniqueConstraint('account_id', 'tag_name', name='uix_account_tag_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Tag details
    tag_name = Column(String(100), nullable=False, index=True)
    tag_category = Column(String(50), nullable=True)  # document_type, entity, date_range, etc.
    confidence_threshold = Column(Float, default=0.7)

    # Auto-tagging rules
    auto_tag_rules = Column(JSON, nullable=True)  # Rules for automatic tagging

    # Statistics
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    account = relationship("Account", back_populates="document_tags")

    def __repr__(self):
        return f"<DocumentTag(name={self.tag_name}, category={self.tag_category})>"


class Extraction(Base):
    """Extraction job model"""
    __tablename__ = "extractions"
    __table_args__ = (
        Index('ix_extractions_account_status', 'account_id', 'status'),
        Index('ix_extractions_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    extraction_id = Column(String(255), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)

    # Document information
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer)
    file_path = Column(String(500))  # Storage path
    total_pages = Column(Integer)

    # Extraction configuration
    vision_model = Column(String(50), nullable=False)
    fallback_models = Column(JSON, default=list)
    confidence_threshold = Column(Float, default=0.7)

    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed, partial

    # Results
    extracted_fields = Column(JSON, default=list)  # List of extracted fields
    bank_statement_pages = Column(JSON, nullable=True)  # Bank statement transactions
    raw_text = Column(Text, nullable=True)

    # Validation results
    completeness_score = Column(Float, default=0.0)
    average_confidence = Column(Float, default=0.0)
    quality_grade = Column(String(2), nullable=True)  # A, B, C, D, F
    missing_required_fields = Column(JSON, default=list)
    low_confidence_fields = Column(JSON, default=list)
    validation_errors = Column(JSON, default=list)

    # Processing metadata
    processing_time_ms = Column(Integer)
    cost_usd = Column(Float, default=0.0)
    fallback_used = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)

    # Auto-generated tags
    auto_tags = Column(JSON, default=list)
    detected_category = Column(String(100), nullable=True)
    detected_country = Column(String(3), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("Account", back_populates="extractions")
    template = relationship("Template", back_populates="extractions")

    def __repr__(self):
        return f"<Extraction(id={self.extraction_id}, status={self.status})>"


class UsageLog(Base):
    """Usage tracking for billing and analytics"""
    __tablename__ = "usage_logs"
    __table_args__ = (
        Index('ix_usage_logs_account_date', 'account_id', 'log_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Usage details
    log_date = Column(DateTime(timezone=True), server_default=func.now())
    operation = Column(String(50), nullable=False)  # extract, classify, validate

    # Cost tracking
    vision_model = Column(String(50))
    pages_processed = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    # Success metrics
    success = Column(Boolean, default=True)
    processing_time_ms = Column(Integer)

    # Reference
    extraction_id = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<UsageLog(account_id={self.account_id}, operation={self.operation}, cost=${self.cost_usd})>"


class APILog(Base):
    """API request logging"""
    __tablename__ = "api_logs"
    __table_args__ = (
        Index('ix_api_logs_account_timestamp', 'account_id', 'timestamp'),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    # Request details
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)

    # Authentication
    api_token = Column(String(255), nullable=True)

    # Request/Response
    request_body = Column(JSON, nullable=True)
    response_body = Column(JSON, nullable=True)

    # Performance
    response_time_ms = Column(Integer)

    # IP and User Agent
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<APILog(endpoint={self.endpoint}, status={self.status_code})>"


# Initialize default countries for new accounts
DEFAULT_COUNTRIES = [
    {"code": "IE", "name": "Ireland", "is_default": True},
    {"code": "GB", "name": "United Kingdom", "is_default": True},
    {"code": "US", "name": "United States", "is_default": True},
    {"code": "CA", "name": "Canada", "is_default": True},
    {"code": "AU", "name": "Australia", "is_default": True},
    {"code": "DE", "name": "Germany", "is_default": True},
    {"code": "FR", "name": "France", "is_default": True},
    {"code": "ES", "name": "Spain", "is_default": True},
    {"code": "IT", "name": "Italy", "is_default": True},
    {"code": "NL", "name": "Netherlands", "is_default": True},
]
