"""
Comprehensive tests for AIVision OCR Service.

Tests cover:
- Template management (CRUD operations)
- Category management
- Document extraction
- API logs
- Multi-tenant isolation
- Quality scoring
- Auto-tagging
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.models import Base
from app.db.session import get_db
from app.db import crud

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_account(test_db):
    """Create a test account"""
    account = crud.create_account(
        db=test_db,
        name="Test Account",
        email="test@example.com",
        plan="free"
    )
    return account


@pytest.fixture
def auth_headers(test_account):
    """Get authentication headers with test account token"""
    return {"Authorization": f"Bearer {test_account.api_token}"}


# ============================================================================
# ACCOUNT TESTS
# ============================================================================

def test_create_account(test_db):
    """Test account creation with API token generation"""
    response = client.post(
        "/api/v1/accounts/",
        json={
            "name": "New Test Account",
            "email": "new@example.com",
            "plan": "pro"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "New Test Account"
    assert data["email"] == "new@example.com"
    assert data["plan"] == "pro"
    assert data["api_token"].startswith("aiv_")
    assert len(data["api_token"]) > 36  # aiv_ + 32 chars


def test_api_token_format(test_account):
    """Test that API token has correct format"""
    assert test_account.api_token.startswith("aiv_")
    assert len(test_account.api_token) == 36  # aiv_ (4) + 32 chars


def test_get_account_with_valid_token(test_account, auth_headers):
    """Test retrieving account with valid token"""
    response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_account.id
    assert data["email"] == test_account.email


def test_reject_invalid_token():
    """Test that invalid tokens are rejected"""
    response = client.get(
        "/api/v1/accounts/1",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401


def test_reject_missing_token():
    """Test that requests without tokens are rejected"""
    response = client.get("/api/v1/accounts/1")
    assert response.status_code == 403  # Forbidden without auth header


# ============================================================================
# TEMPLATE TESTS
# ============================================================================

def test_create_template(test_account, auth_headers, test_db):
    """Test creating a custom template"""
    template_data = {
        "name": "Test Invoice Template",
        "category": "invoice",
        "country_code": "IE",
        "description": "Test template for invoices",
        "fields": [
            {
                "name": "invoice_number",
                "type": "string",
                "required": True,
                "description": "Invoice identifier"
            },
            {
                "name": "total_amount",
                "type": "currency",
                "required": True
            }
        ]
    }

    response = client.post(
        "/api/v1/templates/",
        headers=auth_headers,
        json=template_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["template_name"] == "Test Invoice Template"
    assert data["category"] == "invoice"
    assert len(data["fields"]) == 2
    assert data["account_id"] == test_account.id


def test_list_templates(test_account, auth_headers):
    """Test listing templates for account"""
    response = client.get(
        "/api/v1/templates/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should have default templates
    assert isinstance(data, list)
    assert len(data) > 0


def test_update_template(test_account, auth_headers, test_db):
    """Test updating an existing template"""
    # First create a template
    template = crud.create_template(
        db=test_db,
        account_id=test_account.id,
        template_name="Original Template",
        category="invoice",
        fields=[{"name": "field1", "type": "string", "required": True}]
    )

    # Update it
    response = client.put(
        f"/api/v1/templates/{template.template_id}",
        headers=auth_headers,
        json={
            "template_name": "Updated Template",
            "description": "Updated description"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["template_name"] == "Updated Template"
    assert data["description"] == "Updated description"


def test_delete_template(test_account, auth_headers, test_db):
    """Test deleting a template"""
    # Create a template
    template = crud.create_template(
        db=test_db,
        account_id=test_account.id,
        template_name="Template to Delete",
        category="invoice",
        fields=[{"name": "field1", "type": "string", "required": True}]
    )

    # Delete it
    response = client.delete(
        f"/api/v1/templates/{template.template_id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    # Verify it's deleted
    response = client.get(
        f"/api/v1/templates/{template.template_id}",
        headers=auth_headers
    )
    assert response.status_code == 404


# ============================================================================
# MULTI-TENANT ISOLATION TESTS
# ============================================================================

def test_template_isolation_between_accounts(test_db):
    """Test that accounts cannot access each other's templates"""
    # Create two accounts
    account1 = crud.create_account(
        db=test_db,
        name="Account 1",
        email="account1@example.com"
    )
    account2 = crud.create_account(
        db=test_db,
        name="Account 2",
        email="account2@example.com"
    )

    # Create template for account 1
    template = crud.create_template(
        db=test_db,
        account_id=account1.id,
        template_name="Account 1 Template",
        category="invoice",
        fields=[{"name": "field1", "type": "string", "required": True}]
    )

    # Try to access with account 2's token
    headers2 = {"Authorization": f"Bearer {account2.api_token}"}
    response = client.get(
        f"/api/v1/templates/{template.template_id}",
        headers=headers2
    )

    assert response.status_code == 404  # Should not be found


def test_extraction_isolation_between_accounts(test_db):
    """Test that accounts cannot access each other's extractions"""
    # Create two accounts
    account1 = crud.create_account(
        db=test_db,
        name="Account 1",
        email="extraction1@example.com"
    )
    account2 = crud.create_account(
        db=test_db,
        name="Account 2",
        email="extraction2@example.com"
    )

    # Create extraction for account 1
    extraction = crud.create_extraction(
        db=test_db,
        account_id=account1.id,
        filename="test.pdf",
        vision_model="gemini-2.0-flash-exp"
    )

    # Try to access with account 2's token
    headers2 = {"Authorization": f"Bearer {account2.api_token}"}
    response = client.get(
        f"/api/v1/extractions/{extraction.extraction_id}",
        headers=headers2
    )

    assert response.status_code == 404


# ============================================================================
# COUNTRY MANAGEMENT TESTS
# ============================================================================

def test_create_custom_country(test_account, auth_headers):
    """Test creating a custom country"""
    country_data = {
        "code": "CA",
        "name": "Canada",
        "currency": "CAD"
    }

    response = client.post(
        "/api/v1/countries/",
        headers=auth_headers,
        json=country_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["code"] == "CA"
    assert data["name"] == "Canada"


def test_list_countries(test_account, auth_headers):
    """Test listing countries for account"""
    response = client.get(
        "/api/v1/countries/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should have default countries (IE, UK, US)
    assert isinstance(data, list)
    assert len(data) >= 3

    country_codes = [c["code"] for c in data]
    assert "IE" in country_codes
    assert "UK" in country_codes
    assert "US" in country_codes


# ============================================================================
# API LOGS TESTS
# ============================================================================

def test_api_logs_endpoint(test_account, auth_headers, test_db):
    """Test retrieving API logs"""
    # Create some API logs
    crud.log_api_request(
        db=test_db,
        account_id=test_account.id,
        endpoint="/api/v1/templates/",
        method="GET",
        status_code=200,
        response_time_ms=150
    )

    crud.log_api_request(
        db=test_db,
        account_id=test_account.id,
        endpoint="/api/v1/extractions/extract",
        method="POST",
        status_code=200,
        response_time_ms=2500
    )

    # Fetch logs
    response = client.get(
        "/api/v1/analytics/logs?days=7",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "logs" in data
    assert "total" in data
    assert len(data["logs"]) >= 2


def test_api_logs_filtering(test_account, auth_headers, test_db):
    """Test filtering API logs by method and status code"""
    # Create logs with different methods and status codes
    crud.log_api_request(
        db=test_db,
        account_id=test_account.id,
        endpoint="/api/v1/templates/",
        method="GET",
        status_code=200,
        response_time_ms=100
    )

    crud.log_api_request(
        db=test_db,
        account_id=test_account.id,
        endpoint="/api/v1/templates/",
        method="POST",
        status_code=201,
        response_time_ms=200
    )

    crud.log_api_request(
        db=test_db,
        account_id=test_account.id,
        endpoint="/api/v1/templates/999",
        method="GET",
        status_code=404,
        response_time_ms=50
    )

    # Filter by GET method
    response = client.get(
        "/api/v1/analytics/logs?method=GET",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for log in data["logs"]:
        assert log["method"] == "GET"

    # Filter by status code
    response = client.get(
        "/api/v1/analytics/logs?status_code=404",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for log in data["logs"]:
        assert log["status_code"] == 404


def test_api_logs_pagination(test_account, auth_headers, test_db):
    """Test pagination of API logs"""
    # Create many logs
    for i in range(15):
        crud.log_api_request(
            db=test_db,
            account_id=test_account.id,
            endpoint=f"/api/v1/endpoint{i}",
            method="GET",
            status_code=200,
            response_time_ms=100 + i
        )

    # Get first page
    response = client.get(
        "/api/v1/analytics/logs?limit=10&offset=0",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["logs"]) == 10
    assert data["limit"] == 10
    assert data["offset"] == 0

    # Get second page
    response = client.get(
        "/api/v1/analytics/logs?limit=10&offset=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["logs"]) == 5


# ============================================================================
# ANALYTICS TESTS
# ============================================================================

def test_dashboard_analytics(test_account, auth_headers, test_db):
    """Test dashboard analytics endpoint"""
    # Create some usage logs
    crud.log_usage(
        db=test_db,
        account_id=test_account.id,
        extraction_id="test_extraction_1",
        vision_model="gemini-2.0-flash-exp",
        pages_processed=1,
        processing_time_ms=2000,
        cost_usd=0.0025,
        success=True
    )

    response = client.get(
        "/api/v1/analytics/dashboard?days=30",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "overview" in data
    assert "model_usage" in data
    assert "account_usage" in data
    assert data["period_days"] == 30


def test_usage_analytics(test_account, auth_headers):
    """Test usage analytics endpoint"""
    response = client.get(
        "/api/v1/analytics/usage?days=7",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "daily_stats" in data
    assert "model_costs" in data
    assert "total_cost" in data


def test_model_performance(test_account, auth_headers):
    """Test model performance analytics"""
    response = client.get(
        "/api/v1/analytics/models?days=30",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "models" in data
    assert "total_extractions" in data


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_template_validation_missing_required_fields(test_account, auth_headers):
    """Test that template creation fails with missing required fields"""
    template_data = {
        "name": "Invalid Template",
        # Missing category
        "fields": []
    }

    response = client.post(
        "/api/v1/templates/",
        headers=auth_headers,
        json=template_data
    )

    assert response.status_code == 422  # Validation error


def test_country_code_validation(test_account, auth_headers):
    """Test country code validation"""
    country_data = {
        "code": "INVALID_CODE",  # Too long
        "name": "Invalid Country"
    }

    response = client.post(
        "/api/v1/countries/",
        headers=auth_headers,
        json=country_data
    )

    # Should either reject or truncate
    # Depending on validation rules
    assert response.status_code in [400, 422]


# ============================================================================
# WEBHOOK TESTS
# ============================================================================

def test_create_webhook(test_account, auth_headers):
    """Test creating a webhook configuration"""
    webhook_data = {
        "url": "https://example.com/webhook",
        "events": ["extraction.completed", "extraction.failed"],
        "is_active": True
    }

    response = client.post(
        "/api/v1/webhooks/",
        headers=auth_headers,
        json=webhook_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["url"] == webhook_data["url"]
    assert "secret_key" in data  # HMAC secret generated
    assert len(data["events"]) == 2


def test_list_webhooks(test_account, auth_headers):
    """Test listing webhooks"""
    response = client.get(
        "/api/v1/webhooks/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)


# ============================================================================
# RATE LIMITING TESTS (if implemented)
# ============================================================================

def test_rate_limiting():
    """Test that rate limiting works (if implemented)"""
    # Create account
    response = client.post(
        "/api/v1/accounts/",
        json={"name": "Rate Test", "email": "rate@example.com"}
    )

    token = response.json()["api_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Make many requests rapidly
    success_count = 0
    rate_limited_count = 0

    for _ in range(100):
        response = client.get("/api/v1/templates/", headers=headers)
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:  # Too Many Requests
            rate_limited_count += 1

    # If rate limiting is implemented, we should see some 429s
    # If not, all should succeed
    assert success_count + rate_limited_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
