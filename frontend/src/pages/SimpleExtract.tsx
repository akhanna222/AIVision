import React, { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle, Download, Loader2, Zap, ChevronDown, ChevronUp } from 'lucide-react';
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
    value: string | number | boolean | null;
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
  const [showRawJson, setShowRawJson] = useState(false);

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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg">
              <Zap className="text-white" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Document Extraction
              </h1>
              <p className="text-gray-600 mt-1">Extract data instantly using your saved templates</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Quick Info */}
          <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-xl p-6 text-white">
            <div className="flex items-start gap-4">
              <Zap size={24} className="flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-xl font-bold mb-2">Fast & Easy Extraction</h2>
                <p className="text-green-100 text-sm leading-relaxed">
                  Select a template, upload your document, and get instant results.
                  Powered by AI vision models with optional multi-model support for maximum accuracy.
                </p>
              </div>
            </div>
          </div>

          {/* Template Selection */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-bold text-sm">
                1
              </span>
              <h2 className="text-lg font-bold text-gray-900">Select Template</h2>
            </div>

            {templates.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-xl">
                <FileText size={56} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-600 font-medium mb-2">No templates available yet</p>
                <p className="text-sm text-gray-500 mb-4">
                  Create your first template to start extracting documents
                </p>
                <a
                  href="/template-builder"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-lg transition-all transform hover:scale-105"
                >
                  Create Template
                </a>
              </div>
            ) : (
              <select
                className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-base font-medium"
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
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-bold text-sm">
                2
              </span>
              <h2 className="text-lg font-bold text-gray-900">Upload Document</h2>
            </div>

            <div className="border-3 border-dashed border-gray-300 rounded-2xl p-12 text-center bg-gradient-to-br from-gray-50 to-gray-100 hover:border-blue-400 transition-all cursor-pointer">
              <Upload size={56} className="mx-auto mb-4 text-gray-400" />

              <label className="cursor-pointer">
                <span className="text-blue-600 hover:text-blue-700 font-semibold text-lg">
                  Choose a file
                </span>
                {' or drag and drop'}
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf,.png,.jpg,.jpeg,.tiff"
                  onChange={handleFileChange}
                />
              </label>

              {file && (
                <div className="mt-6 p-4 bg-white rounded-xl border-2 border-blue-200 inline-block">
                  <div className="flex items-center gap-3">
                    <FileText className="text-blue-600" size={24} />
                    <div className="text-left">
                      <p className="font-semibold text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                </div>
              )}

              <p className="text-xs text-gray-500 mt-4">
                PDF, PNG, JPG, JPEG, TIFF • Max 50MB
              </p>
            </div>
          </div>

          {/* Options */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-bold text-sm">
                3
              </span>
              <h2 className="text-lg font-bold text-gray-900">Options</h2>
            </div>

            <div className="space-y-4">
              <label className="flex items-start gap-4 cursor-pointer p-4 rounded-xl border-2 border-gray-200 hover:border-blue-300 transition-all">
                <input
                  type="checkbox"
                  checked={useMultiModel}
                  onChange={(e) => setUseMultiModel(e.target.checked)}
                  className="mt-1 w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">Use Multi-Model Extraction</div>
                  <p className="text-sm text-gray-600 mt-1">
                    Try multiple AI models for better accuracy. Models vote on each field.
                  </p>
                </div>
              </label>

              {useMultiModel && (
                <div className="ml-12 space-y-4 p-4 bg-blue-50 rounded-xl border-2 border-blue-200">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Models (comma-separated)
                    </label>
                    <input
                      type="text"
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="gemini-2.0-flash-exp,gpt-4o"
                      value={models}
                      onChange={(e) => setModels(e.target.value)}
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Available: gemini-2.0-flash-exp (free), gpt-4o, claude-sonnet-4-20250514
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Strategy
                    </label>
                    <select
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
            className="w-full flex items-center justify-center gap-3 px-8 py-5 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-2xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 font-bold text-lg"
          >
            {extracting ? (
              <>
                <Loader2 size={28} className="animate-spin" />
                Extracting data...
              </>
            ) : (
              <>
                <Zap size={28} />
                Extract Document
              </>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border-2 border-red-300 rounded-2xl p-6">
              <h3 className="font-bold text-red-900 text-lg mb-1">Extraction Failed</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-500 rounded-full">
                    <CheckCircle className="text-white" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Extraction Complete!</h2>
                    <p className="text-sm text-gray-600">Template: {result.template_name}</p>
                  </div>
                </div>
                <button
                  onClick={downloadJSON}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors font-medium"
                >
                  <Download size={18} />
                  Download JSON
                </button>
              </div>

              {/* Multi-Model Summary */}
              {result.multi_model_tracking && (
                <div className="mb-6 p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-200">
                  <h3 className="font-bold text-blue-900 mb-3">Multi-Model Analysis</h3>
                  <p className="text-sm text-blue-800 mb-4">{result.multi_model_tracking.extraction_summary}</p>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white p-3 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Models Used</div>
                      <div className="font-bold text-blue-900">{result.multi_model_tracking.models_tried.join(', ')}</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Completeness</div>
                      <div className="font-bold text-green-600">{(result.multi_model_tracking.completeness * 100).toFixed(0)}%</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Confidence</div>
                      <div className="font-bold text-green-600">{(result.multi_model_tracking.confidence * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Extracted Fields */}
              <div className="space-y-3">
                <h3 className="font-bold text-gray-900 mb-4">Extracted Fields ({result.extracted_fields.length})</h3>
                {result.extracted_fields.map((field, index) => (
                  <div key={index} className="bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-gray-200 rounded-xl p-5">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-bold text-gray-900 text-lg">{field.field_name}</h4>
                      {field.confidence !== undefined && (
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          field.confidence > 0.9 ? 'bg-green-100 text-green-800' :
                          field.confidence > 0.7 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {(field.confidence * 100).toFixed(0)}% confident
                        </span>
                      )}
                    </div>
                    <div className="text-xl text-gray-900 font-medium mb-2">
                      {field.value || <span className="text-gray-400 italic">(not extracted)</span>}
                    </div>
                    {field.extracted_by && (
                      <p className="text-xs text-gray-600 bg-white px-3 py-1 rounded-full inline-block">
                        Extracted by: <span className="font-semibold">{field.extracted_by}</span>
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* Raw JSON Toggle */}
              <div className="mt-6">
                <button
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-gray-900 transition-colors"
                >
                  {showRawJson ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  {showRawJson ? 'Hide' : 'Show'} Raw JSON
                </button>

                {showRawJson && (
                  <pre className="mt-3 bg-gray-900 text-green-400 p-5 rounded-xl overflow-x-auto text-xs font-mono border-2 border-gray-700">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
