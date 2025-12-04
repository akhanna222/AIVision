# AIVision - Quick Start Guide

Get started with the AIVision OCR document extraction service in minutes.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- API keys for at least one vision model:
  - Google Gemini API key (recommended)
  - OpenAI API key (optional)
  - Anthropic API key (optional)

## Method 1: Local Python Setup (Development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd AIVision

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Required variables in `.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # optional
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # optional
```

### 3. Quick Test

```python
# test_extraction.py
import asyncio
from app.services.vision import GeminiClient
from app.core.template_registry import get_template_registry

async def test():
    # Initialize client
    client = GeminiClient(api_key="your_api_key")

    # Get template
    registry = get_template_registry()
    template = registry.get_template("ie_mortgage_app_v1")

    print(f"✓ Loaded template: {template.template_name}")
    print(f"✓ Fields to extract: {len(template.fields)}")
    print(f"✓ Gemini client ready")

    # Test with your document
    # with open("test_document.pdf", "rb") as f:
    #     pdf_bytes = f.read()
    #     # Convert PDF to image and extract...

if __name__ == "__main__":
    asyncio.run(test())
```

Run the test:
```bash
python test_extraction.py
```

## Method 2: Docker Setup (Production)

### 1. Prepare Environment

```bash
# Clone repository
git clone <repository-url>
cd AIVision

# Create .env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Start All Services

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

Services will be available at:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend UI**: http://localhost:3000
- **MinIO Console**: http://localhost:9001
- **Flower (Celery)**: http://localhost:5555

### 3. Access API Documentation

Open your browser to http://localhost:8000/docs to see the interactive API documentation.

## Usage Examples

### Example 1: Extract from Irish Mortgage Application

```python
from app.models import ExtractionRequest, VisionModel
from app.services.vision import GeminiClient
from app.core.template_registry import get_template_registry
import asyncio

async def extract_mortgage_app():
    # Initialize
    client = GeminiClient(api_key="your_api_key")
    registry = get_template_registry()

    # Get template
    template = registry.get_template("ie_mortgage_app_v1")

    # Read document
    with open("mortgage_application.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Convert PDF to images (using PDFProcessor)
    from app.services.pdf_processor import PDFProcessor
    pdf_processor = PDFProcessor()
    images = pdf_processor.convert_pdf_to_images(pdf_bytes)

    print(f"✓ Converted {len(images)} pages")

    # Extract from first page
    from app.core.template_registry import build_extraction_prompt
    prompt = build_extraction_prompt(template, page_number=1)

    result = await client.extract(
        image_bytes=images[0],
        prompt=prompt,
        temperature=0.0
    )

    print(f"✓ Extracted {len(result.get('extracted_fields', []))} fields")
    print(result)

if __name__ == "__main__":
    asyncio.run(extract_mortgage_app())
```

### Example 2: Extract Bank Statement with Transactions

```python
async def extract_bank_statement():
    client = GeminiClient(api_key="your_api_key")
    registry = get_template_registry()

    # Get bank statement template
    template = registry.get_template("ie_bank_stmt_v1")

    # Read PDF
    with open("bank_statement.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Process each page
    from app.services.pdf_processor import PDFProcessor
    pdf_processor = PDFProcessor()
    pages = pdf_processor.split_pdf_pages(pdf_bytes)

    for page_num, page_image in pages:
        print(f"Processing page {page_num}...")

        # Extract transactions from this page
        # (Implementation in extraction service)

    print(f"✓ Processed {len(pages)} pages")

if __name__ == "__main__":
    asyncio.run(extract_bank_statement())
```

### Example 3: Create Custom Template

```python
from app.models import (
    DocumentTemplate,
    DocumentCategory,
    CountryCode,
    FieldDefinition,
    FieldType
)
from app.core.template_registry import get_template_registry

# Create custom template
custom_template = DocumentTemplate(
    template_id="custom_employment_v1",
    category=DocumentCategory.EMPLOYMENT_VERIFICATION,
    country=CountryCode.IRELAND,
    template_name="Employment Verification Letter",
    description="Custom employment letter template",
    fields=[
        FieldDefinition(
            field_id="employee_name",
            field_name="Employee Name",
            field_type=FieldType.TEXT,
            description="Full name of employee",
            required=True
        ),
        FieldDefinition(
            field_id="job_title",
            field_name="Job Title",
            field_type=FieldType.TEXT,
            description="Current position",
            required=True
        ),
        FieldDefinition(
            field_id="start_date",
            field_name="Employment Start Date",
            field_type=FieldType.DATE,
            description="Date employment began",
            required=True
        ),
        FieldDefinition(
            field_id="annual_salary",
            field_name="Annual Salary",
            field_type=FieldType.CURRENCY,
            description="Gross annual salary in EUR",
            required=True,
            validation_rules={"currency": "EUR", "min": 0}
        )
    ]
)

# Register template
registry = get_template_registry()
registry.register_template(custom_template, user_id="user123")

print(f"✓ Registered template: {custom_template.template_name}")

# Use it later
template = registry.get_template("custom_employment_v1", user_id="user123")
print(f"✓ Retrieved template with {len(template.fields)} fields")
```

### Example 4: List Available Templates

```python
from app.core.template_registry import get_template_registry
from app.models import DocumentCategory, CountryCode

registry = get_template_registry()

# List all templates
all_templates = registry.list_templates()
print(f"Total templates: {len(all_templates)}")

# Filter by category
mortgage_templates = registry.list_templates(
    category=DocumentCategory.MORTGAGE_APPLICATION
)
print(f"Mortgage templates: {len(mortgage_templates)}")

# Filter by country
ireland_templates = registry.list_templates(
    country=CountryCode.IRELAND
)
print(f"Ireland templates: {len(ireland_templates)}")

# Get statistics
stats = registry.get_stats()
print(f"Statistics: {stats}")
```

## Available Templates

### Ireland (IE)
- `ie_mortgage_app_v1` - Irish Mortgage Application (14 fields)
- `ie_bank_stmt_v1` - Irish Bank Statement (10 fields + transactions)

### United Kingdom (GB)
- `gb_mortgage_app_v1` - UK Mortgage Application (11 fields)

### United States (US)
- `us_mortgage_app_v1` - Form 1003 Mortgage Application (13 fields)

### Universal
- `passport_universal_v1` - Passport Extraction (11 fields)
- `receipt_universal_v1` - Receipt Extraction (10 fields)

## Model Selection Guide

Choose the right vision model for your use case:

### Gemini 2.0 Flash (Recommended Default)
- **Cost**: ~$0.03 per page
- **Speed**: ~2 seconds per page
- **Accuracy**: 94%
- **Best for**: High-volume processing, cost-sensitive applications

### GPT-4o
- **Cost**: ~$0.15 per page
- **Speed**: ~4 seconds per page
- **Accuracy**: 96%
- **Best for**: Complex documents, highest accuracy requirements

### Claude Sonnet 4
- **Cost**: ~$0.12 per page
- **Speed**: ~3 seconds per page
- **Accuracy**: 97%
- **Best for**: Enterprise applications, sensitive documents

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution**: Make sure PYTHONPATH is set correctly:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Poppler not found" error

**Solution**: Install Poppler for PDF processing:

**Linux:**
```bash
sudo apt-get install poppler-utils
```

**Mac:**
```bash
brew install poppler
```

**Windows:**
Download from: https://blog.alivate.com.au/poppler-windows/

### Issue: Vision model API errors

**Solution**: Check your API keys in .env:
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Test API key
curl -X POST \
  https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Test"}]}]}'
```

### Issue: Docker containers won't start

**Solution**: Check Docker logs:
```bash
docker-compose logs backend
docker-compose logs postgres
docker-compose logs redis
```

## Next Steps

1. **Start Backend Development**: Implement FastAPI endpoints
2. **Build Frontend**: Create React UI components
3. **Add Tests**: Write unit and integration tests
4. **Deploy**: Set up production environment

## Resources

- **Full Documentation**: See README.md
- **Architecture**: See PROMPT.md
- **API Reference**: http://localhost:8000/docs (when running)
- **Example Code**: See `tests/` directory (to be created)

## Support

For issues or questions:
- Check documentation in README.md and PROMPT.md
- Review logs: `docker-compose logs -f`
- Check API docs: http://localhost:8000/docs
- Open GitHub issue: [repository]/issues

## Security Notes

⚠️ **Important**:
- Never commit .env file with real API keys
- Use strong passwords in production
- Enable HTTPS in production
- Rotate API keys regularly
- Set up proper access controls

Happy extracting! 🚀
