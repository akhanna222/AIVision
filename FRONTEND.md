# AIVision Frontend - React Implementation Guide

## ✅ Completed Frontend Setup

### Project Structure
```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── UploadZone.tsx           ✓ (Drag & drop upload)
│   │   ├── Dashboard/               (To implement)
│   │   ├── ResultsViewer/           (To implement)
│   │   ├── TemplateBuilder/         (To implement)
│   │   ├── Analytics/               (To implement)
│   │   └── BatchProcessor/          (To implement)
│   ├── pages/            # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Extract.tsx
│   │   ├── BatchExtract.tsx
│   │   ├── Results.tsx
│   │   ├── Templates.tsx
│   │   ├── Analytics.tsx
│   │   └── Settings.tsx
│   ├── services/         # API services
│   │   └── api.ts                   ✓ (Complete API client)
│   ├── types/            # TypeScript definitions
│   │   └── index.ts                 ✓ (All types defined)
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Utility functions
│   │   └── cn.ts                    ✓ (className helper)
│   ├── App.tsx                      ✓ (Main app with routing)
│   ├── main.tsx                     ✓ (Entry point)
│   └── index.css                    ✓ (Tailwind CSS)
├── package.json                      ✓
├── vite.config.ts                    ✓
├── tailwind.config.js                ✓
├── tsconfig.json                     ✓
└── index.html                        ✓
```

## 🚀 Quick Start

### Install Dependencies
```bash
cd frontend
npm install
```

### Configure Environment
Create `.env.local`:
```bash
VITE_API_URL=http://localhost:8000
```

### Start Development Server
```bash
npm run dev
```

Visit: http://localhost:3000

## 📦 Installed Packages

- **react** & **react-dom**: Core React
- **react-router-dom**: Routing
- **axios**: HTTP client
- **@tanstack/react-query**: Data fetching & caching
- **zustand**: State management
- **react-dropzone**: Drag & drop files
- **recharts**: Charts & analytics
- **lucide-react**: Icons
- **react-hot-toast**: Notifications
- **tailwindcss**: Styling
- **vite**: Build tool

## 🎨 Component Implementations

### 1. UploadZone Component ✓

**File: `src/components/UploadZone.tsx`**

Features:
- ✅ Drag & drop file upload
- ✅ Click to browse files
- ✅ Multiple file selection
- ✅ File size validation
- ✅ File type validation
- ✅ Selected files preview
- ✅ Remove individual files
- ✅ Clear all files

Usage:
```tsx
import { UploadZone } from '@/components/UploadZone';

function MyPage() {
  const handleFiles = (files: File[]) => {
    console.log('Selected files:', files);
  };

  return (
    <UploadZone
      onFilesSelected={handleFiles}
      maxFiles={10}
      maxSize={50}
      accept={['pdf', 'jpg', 'png']}
    />
  );
}
```

### 2. Dashboard Page (To Implement)

**File: `src/pages/Dashboard.tsx`**

```tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import {
  BarChart3,
  FileText,
  CheckCircle,
  DollarSign,
  TrendingUp
} from 'lucide-react';

export default function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.getDashboard(30),
  });

  const { data: account } = useQuery({
    queryKey: ['account'],
    queryFn: () => api.getCurrentAccount(),
  });

  if (!stats || !account) return <div>Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Extractions"
          value={stats.overview.total_extractions}
          icon={<FileText />}
          color="blue"
        />
        <StatCard
          title="Success Rate"
          value={`${stats.overview.success_rate.toFixed(1)}%`}
          icon={<CheckCircle />}
          color="green"
        />
        <StatCard
          title="Avg Confidence"
          value={`${(stats.overview.avg_confidence * 100).toFixed(1)}%`}
          icon={<TrendingUp />}
          color="purple"
        />
        <StatCard
          title="Total Cost"
          value={`$${stats.overview.total_cost_usd.toFixed(2)}`}
          icon={<DollarSign />}
          color="yellow"
        />
      </div>

      {/* Usage Progress */}
      <div className="card p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Monthly Usage</h2>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>{account.monthly_extractions} / {account.monthly_limit} extractions</span>
            <span>{stats.account_usage.remaining} remaining</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all"
              style={{
                width: `${(account.monthly_extractions / account.monthly_limit) * 100}%`
              }}
            />
          </div>
        </div>
      </div>

      {/* Recent Extractions */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Extractions</h2>
        <div className="space-y-3">
          {stats.recent_extractions.map((extraction) => (
            <div
              key={extraction.extraction_id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <p className="font-medium">{extraction.filename}</p>
                <p className="text-sm text-gray-500">
                  {new Date(extraction.created_at).toLocaleString()}
                </p>
              </div>
              <span className={`badge badge-${
                extraction.quality_grade === 'A' ? 'success' :
                extraction.quality_grade === 'B' ? 'info' :
                extraction.quality_grade === 'C' ? 'warning' : 'error'
              }`}>
                Grade {extraction.quality_grade}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Model Usage Chart */}
      <div className="card p-6 mt-8">
        <h2 className="text-lg font-semibold mb-4">Model Usage</h2>
        {/* Add Recharts BarChart here */}
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }: any) {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
        <div className={`p-3 bg-${color}-100 rounded-lg`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
```

### 3. Extract Page (Single Document)

**File: `src/pages/Extract.tsx`**

```tsx
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';
import { UploadZone } from '@/components/UploadZone';
import toast from 'react-hot-toast';

export default function Extract() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [visionModel, setVisionModel] = useState('gemini-2.0-flash-exp');
  const [autoDetect, setAutoDetect] = useState(true);

  const { data: templates } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.listTemplates(),
  });

  const extractMutation = useMutation({
    mutationFn: (file: File) =>
      api.extractDocument(file, {
        template_id: autoDetect ? undefined : selectedTemplate,
        vision_model: visionModel,
        auto_detect: autoDetect,
        confidence_threshold: 0.7,
      }),
    onSuccess: (data) => {
      toast.success('Extraction completed!');
      navigate(`/results/${data.extraction_id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Extraction failed');
    },
  });

  const handleExtract = () => {
    if (files.length === 0) {
      toast.error('Please select a file');
      return;
    }

    extractMutation.mutate(files[0]);
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Extract Document</h1>

      {/* Upload Section */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">1. Upload Document</h2>
        <UploadZone
          onFilesSelected={setFiles}
          maxFiles={1}
          maxSize={50}
        />
      </div>

      {/* Configuration */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">2. Configure Extraction</h2>

        <div className="space-y-4">
          {/* Auto-detect toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="autoDetect"
              checked={autoDetect}
              onChange={(e) => setAutoDetect(e.target.checked)}
              className="h-4 w-4 text-primary-600 rounded"
            />
            <label htmlFor="autoDetect" className="text-sm font-medium">
              Auto-detect document type and generate tags
            </label>
          </div>

          {/* Template selection */}
          {!autoDetect && (
            <div>
              <label className="label">Template</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="input"
              >
                <option value="">Select template...</option>
                {templates?.map((t) => (
                  <option key={t.template_id} value={t.template_id}>
                    {t.template_name} ({t.country_id})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Vision model */}
          <div>
            <label className="label">Vision Model</label>
            <select
              value={visionModel}
              onChange={(e) => setVisionModel(e.target.value)}
              className="input"
            >
              <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Recommended)</option>
              <option value="gpt-4o">GPT-4o (High Accuracy)</option>
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4 (Enterprise)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Extract Button */}
      <button
        onClick={handleExtract}
        disabled={files.length === 0 || extractMutation.isPending}
        className="btn btn-primary w-full text-lg py-3"
      >
        {extractMutation.isPending ? 'Extracting...' : 'Extract Document'}
      </button>
    </div>
  );
}
```

### 4. Batch Extract Page

**File: `src/pages/BatchExtract.tsx`**

```tsx
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';
import { UploadZone } from '@/components/UploadZone';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import toast from 'react-hot-toast';

export default function BatchExtract() {
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<any[]>([]);

  const batchMutation = useMutation({
    mutationFn: (files: File[]) =>
      api.batchExtract(files, {
        vision_model: 'gemini-2.0-flash-exp',
        auto_detect: true,
        confidence_threshold: 0.7,
      }),
    onSuccess: (data) => {
      toast.success(`Batch completed: ${data.completed}/${data.total_documents} successful`);
      setResults(data.extractions);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Batch extraction failed');
    },
  });

  const handleBatchExtract = () => {
    if (files.length === 0) {
      toast.error('Please select files');
      return;
    }

    batchMutation.mutate(files);
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Batch Extract</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div>
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Upload Documents</h2>
            <UploadZone
              onFilesSelected={setFiles}
              maxFiles={100}
              maxSize={50}
            />
          </div>

          <button
            onClick={handleBatchExtract}
            disabled={files.length === 0 || batchMutation.isPending}
            className="btn btn-primary w-full text-lg py-3"
          >
            {batchMutation.isPending ? 'Processing...' : `Extract ${files.length} Documents`}
          </button>
        </div>

        {/* Results Section */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">
            Results {results.length > 0 && `(${results.length})`}
          </h2>

          {batchMutation.isPending && (
            <div className="text-center py-12">
              <Loader className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-4" />
              <p className="text-gray-600">Processing documents...</p>
            </div>
          )}

          <div className="space-y-3">
            {results.map((result, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  {result.status === 'completed' ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                  <div>
                    <p className="font-medium">{result.filename}</p>
                    <p className="text-sm text-gray-500">
                      Grade {result.validation.quality_grade} · {result.total_pages} pages
                    </p>
                  </div>
                </div>
                <span className="text-sm text-gray-500">
                  ${result.processing.cost_usd.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

## 🔔 Webhook Backend Implementation

Add to backend: `app/api/v1/webhooks.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List

from app.db.session import get_db
from app.core.auth import get_current_account
from app.db.models import Account

router = APIRouter()

# Add Webhook model to app/db/models.py
"""
class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    url = Column(String(500), nullable=False)
    events = Column(JSON, default=list)  # ["extraction.completed", "extraction.failed"]
    is_active = Column(Boolean, default=True)
    secret = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account")
"""

class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    is_active: bool = True
    secret: str | None = None

@router.post("/")
async def create_webhook(
    webhook: WebhookCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Create webhook"""
    # Implementation
    pass

@router.get("/")
async def list_webhooks(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """List webhooks"""
    pass

@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Test webhook with sample payload"""
    pass
```

## 📱 Additional Components Needed

1. **Results Viewer** - Display extraction results with field highlighting
2. **Template Builder** - Visual template creation interface
3. **Analytics Dashboard** - Charts and metrics (use Recharts)
4. **Settings Page** - Account settings, API token management
5. **Navigation** - Sidebar or header navigation
6. **Loading States** - Skeleton loaders
7. **Error Boundaries** - Error handling

## 🚀 Next Steps

1. **Complete Page Components**: Implement all pages in `src/pages/`
2. **Add Webhook Backend**: Complete webhook implementation
3. **Add Real-time Updates**: WebSocket for live processing status
4. **Testing**: Unit tests with Vitest
5. **Build & Deploy**: Production build optimization

## 📦 Build for Production

```bash
npm run build
```

Output in `dist/` directory, ready to deploy.

## 🎨 UI Design System

Colors:
- Primary: Blue (#0ea5e9)
- Success: Green (#10b981)
- Warning: Yellow (#f59e0b)
- Error: Red (#ef4444)
- Gray scale: 50-900

Components follow Tailwind utility-first approach.

---

**Status**: Frontend setup 80% complete. Core components ready. Remaining: page implementations and webhook backend.
