import React, { useState, useEffect } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Download, Loader2 } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Template {
  template_id: string;
  template_name: string;
  category: string;
  usage_count: number;
  api_endpoint: string;
}

interface ExtractionResult {
  extraction_id: string;
  template_name: string;
  status: string;
  extracted_fields: Array<{
    field_name: string;
    value: any;
    confidence?: number;
    extracted_by?: string;
  }>;
  multi_model_tracking?: {
    models_tried: string[];
    extraction_summary: string;
    completeness: number;
    confidence: number;
  };
}

export default function SimpleExtract() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [useMultiModel, setUseMultiModel] = useState(false);
  const [models, setModels] = useState('gemini-2.0-flash-exp');
  const [strategy, setStrategy] = useState('hybrid');

  const [extracting, setExtracting] = useState(false);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/public/templates`);
      setTemplates(response.data.templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
      setResult(null);
    }
  };

  const handleExtract = async () => {
    if (!selectedTemplate) {
      setError('Please select a template');
      return;
    }

    if (!file) {
      setError('Please select a file');
      return;
    }

    setExtracting(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('use_multi_model', useMultiModel.toString());

      if (useMultiModel) {
        formData.append('models', models);
        formData.append('strategy', strategy);
      }

      const response = await axios.post(
        `${API_URL}/api/v1/public/extract/${selectedTemplate}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setResult(response.data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Extraction failed');
    } finally {
      setExtracting(false);
    }
  };

  const downloadJSON = () => {
    if (!result) return;

    const dataStr = JSON.stringify(result, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

    const exportFileDefaultName = `extraction_${result.extraction_id}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Simple Document Extraction</h1>
        <p className="text-gray-600">
          Upload a document and extract data using your saved templates. No authentication required!
        </p>
      </div>

      <div className="space-y-6">
        {/* Template Selection */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">1. Select Template</h2>

          {templates.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText size={48} className="mx-auto mb-3 opacity-30" />
              <p>No templates available yet.</p>
              <p className="text-sm mt-1">
                <a href="/template-builder" className="text-blue-600 hover:underline">
                  Create a template first →
                </a>
              </p>
            </div>
          ) : (
            <select
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
            >
              <option value="">-- Choose a template --</option>
              {templates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.template_name} ({template.category})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* File Upload */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">2. Upload Document</h2>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
            <Upload size={48} className="mx-auto mb-4 text-gray-400" />

            <label className="cursor-pointer">
              <span className="text-blue-600 hover:text-blue-700 font-medium">
                Choose a file
              </span>
              <input
                type="file"
                className="hidden"
                accept=".pdf,.png,.jpg,.jpeg,.tiff"
                onChange={handleFileChange}
              />
            </label>

            {file && (
              <div className="mt-4 text-sm text-gray-600">
                Selected: <span className="font-medium">{file.name}</span> ({(file.size / 1024).toFixed(1)} KB)
              </div>
            )}

            <p className="text-xs text-gray-500 mt-4">
              Supports PDF, PNG, JPG, JPEG, TIFF (max 50MB)
            </p>
          </div>
        </div>

        {/* Multi-Model Options */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">3. Extraction Options</h2>

          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={useMultiModel}
                onChange={(e) => setUseMultiModel(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <span className="font-medium">Use Multi-Model Extraction</span>
                <p className="text-sm text-gray-500">
                  Try multiple AI models for better accuracy
                </p>
              </div>
            </label>

            {useMultiModel && (
              <div className="ml-7 space-y-3 border-l-2 border-blue-200 pl-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Models (comma-separated)
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="gemini-2.0-flash-exp,gpt-4o,claude-sonnet-4-20250514"
                    value={models}
                    onChange={(e) => setModels(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Strategy
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value)}
                  >
                    <option value="sequential">Sequential (cost-effective)</option>
                    <option value="parallel">Parallel (maximum accuracy)</option>
                    <option value="hybrid">Hybrid (balanced)</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Extract Button */}
        <button
          onClick={handleExtract}
          disabled={extracting || !selectedTemplate || !file}
          className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-lg font-medium"
        >
          {extracting ? (
            <>
              <Loader2 size={24} className="animate-spin" />
              Extracting...
            </>
          ) : (
            <>
              <FileText size={24} />
              Extract Document
            </>
          )}
        </button>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
              <div>
                <h3 className="font-medium text-red-900">Extraction Failed</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <CheckCircle className="text-green-600" size={24} />
                Extraction Results
              </h2>
              <button
                onClick={downloadJSON}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium"
              >
                <Download size={16} />
                Download JSON
              </button>
            </div>

            {/* Multi-Model Summary */}
            {result.multi_model_tracking && (
              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Multi-Model Extraction</h3>
                <p className="text-sm text-blue-800 mb-2">{result.multi_model_tracking.extraction_summary}</p>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Models Tried:</span>
                    <p className="font-medium">{result.multi_model_tracking.models_tried.join(', ')}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Completeness:</span>
                    <p className="font-medium">{(result.multi_model_tracking.completeness * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Confidence:</span>
                    <p className="font-medium">{(result.multi_model_tracking.confidence * 100).toFixed(0)}%</p>
                  </div>
                </div>
              </div>
            )}

            {/* Extracted Fields */}
            <div className="space-y-3">
              {result.extracted_fields.map((field, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="font-medium text-gray-900">{field.field_name}</h3>
                    {field.confidence !== undefined && (
                      <span className={`text-xs px-2 py-1 rounded ${
                        field.confidence > 0.9 ? 'bg-green-100 text-green-800' :
                        field.confidence > 0.7 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {(field.confidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>
                  <p className="text-lg text-gray-700">{field.value || '(not extracted)'}</p>
                  {field.extracted_by && (
                    <p className="text-xs text-gray-500 mt-2">
                      Extracted by: {field.extracted_by}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* Raw JSON */}
            <details className="mt-6">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                View Raw JSON
              </summary>
              <pre className="mt-2 bg-gray-50 p-4 rounded-lg overflow-x-auto text-xs">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}
