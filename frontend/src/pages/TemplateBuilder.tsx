import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save, FileText, CheckCircle, Copy, Sparkles, Wand2 } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TemplateField {
  name: string;
  type: string;
  description: string;
  required: boolean;
}

interface Template {
  template_id: string;
  template_name: string;
  category: string;
  description: string;
  fields: TemplateField[];
  usage_count?: number;
}

interface DefaultTemplate {
  template_id: string;
  template_name: string;
  category: string;
  description: string;
  field_count: number;
}

export default function TemplateBuilder() {
  const [templateName, setTemplateName] = useState('');
  const [category, setCategory] = useState('custom');
  const [description, setDescription] = useState('');
  const [fields, setFields] = useState<TemplateField[]>([
    { name: '', type: 'string', description: '', required: false }
  ]);

  const [savedTemplates, setSavedTemplates] = useState<Template[]>([]);
  const [defaultTemplates, setDefaultTemplates] = useState<DefaultTemplate[]>([]);
  const [selectedDefault, setSelectedDefault] = useState('');

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [apiEndpoint, setApiEndpoint] = useState('');

  useEffect(() => {
    loadSavedTemplates();
    loadDefaultTemplates();
  }, []);

  const loadDefaultTemplates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/public/templates/defaults`);
      setDefaultTemplates(response.data.templates);
    } catch (error) {
      console.error('Failed to load default templates:', error);
    }
  };

  const loadSavedTemplates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/public/templates/list`);
      setSavedTemplates(response.data);
    } catch (error) {
      console.error('Failed to load saved templates:', error);
    }
  };

  const loadDefaultTemplate = async (templateId: string) => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/public/templates/defaults/${templateId}`);
      const template = response.data;

      setTemplateName(template.template_name);
      setCategory(template.category);
      setDescription(template.description);
      setFields(template.fields);
      setSelectedDefault(templateId);
    } catch (error) {
      console.error('Failed to load default template:', error);
    }
  };

  const addField = () => {
    setFields([...fields, { name: '', type: 'string', description: '', required: false }]);
  };

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const updateField = (index: number, key: keyof TemplateField, value: string | boolean) => {
    const newFields = [...fields];
    newFields[index] = { ...newFields[index], [key]: value };
    setFields(newFields);
  };

  const saveTemplate = async () => {
    if (!templateName.trim()) {
      setSaveError('Template name is required');
      return;
    }

    const validFields = fields.filter(f => f.name.trim() !== '');
    if (validFields.length === 0) {
      setSaveError('At least one field is required');
      return;
    }

    setSaving(true);
    setSaveError('');
    setSaveSuccess(false);

    try {
      const response = await axios.post(`${API_URL}/api/v1/public/templates/create`, {
        template_name: templateName,
        category,
        description,
        fields: validFields
      });

      const savedTemplate = response.data;
      const endpoint = `${API_URL}/api/v1/public/extract/${savedTemplate.template_id}`;
      setApiEndpoint(endpoint);
      setSaveSuccess(true);
      loadSavedTemplates();

      setTimeout(() => {
        setTemplateName('');
        setCategory('custom');
        setDescription('');
        setFields([{ name: '', type: 'string', description: '', required: false }]);
        setSelectedDefault('');
      }, 3000);

    } catch (error: any) {
      setSaveError(error.response?.data?.detail || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-lg">
              <Wand2 className="text-white" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Template Builder
              </h1>
              <p className="text-gray-600 mt-1">Create custom OCR templates in seconds • No signup required</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Start */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-start gap-4">
                <Sparkles size={24} className="flex-shrink-0 mt-1" />
                <div>
                  <h2 className="text-xl font-bold mb-2">Quick Start</h2>
                  <p className="text-blue-100 text-sm leading-relaxed">
                    Choose from 5 pre-built templates or create your own from scratch.
                    Add fields, click save, and get your API endpoint instantly!
                  </p>
                </div>
              </div>
            </div>

            {/* Default Templates */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Start from a Default Template
              </label>
              <select
                className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                value={selectedDefault}
                onChange={(e) => loadDefaultTemplate(e.target.value)}
              >
                <option value="">Create from scratch →</option>
                {defaultTemplates.map((template) => (
                  <option key={template.template_id} value={template.template_id}>
                    {template.template_name} • {template.field_count} fields
                  </option>
                ))}
              </select>
            </div>

            {/* Template Details */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Template Details</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    placeholder="My Amazing Template"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                  >
                    <option value="custom">Custom</option>
                    <option value="financial">Financial</option>
                    <option value="employment">Employment</option>
                    <option value="identification">Identification</option>
                    <option value="legal">Legal</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                    rows={3}
                    placeholder="What kind of documents will this template extract?"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Fields */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex justify-between items-center mb-5">
                <h2 className="text-lg font-bold text-gray-900">Fields ({fields.length})</h2>
                <button
                  onClick={addField}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-lg transition-all transform hover:scale-105"
                >
                  <Plus size={18} />
                  Add Field
                </button>
              </div>

              <div className="space-y-4">
                {fields.map((field, index) => (
                  <div key={index} className="bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-gray-200 rounded-xl p-5">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-2">
                          Field Name *
                        </label>
                        <input
                          type="text"
                          className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="e.g., invoice_number"
                          value={field.name}
                          onChange={(e) => updateField(index, 'name', e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-2">
                          Type
                        </label>
                        <select
                          className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          value={field.type}
                          onChange={(e) => updateField(index, 'type', e.target.value)}
                        >
                          <option value="string">Text</option>
                          <option value="number">Number</option>
                          <option value="date">Date</option>
                          <option value="boolean">Yes/No</option>
                        </select>
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-xs font-semibold text-gray-600 mb-2">
                          Description
                        </label>
                        <input
                          type="text"
                          className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="What should be extracted from the document?"
                          value={field.description}
                          onChange={(e) => updateField(index, 'description', e.target.value)}
                        />
                      </div>

                      <div className="md:col-span-2 flex items-center justify-between pt-2">
                        <label className="flex items-center gap-2 cursor-pointer group">
                          <input
                            type="checkbox"
                            checked={field.required}
                            onChange={(e) => updateField(index, 'required', e.target.checked)}
                            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">Required field</span>
                        </label>

                        {fields.length > 1 && (
                          <button
                            onClick={() => removeField(index)}
                            className="text-red-600 hover:text-red-700 flex items-center gap-1 text-sm font-medium transition-colors"
                          >
                            <Trash2 size={16} />
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Save Button */}
            <button
              onClick={saveTemplate}
              disabled={saving}
              className="w-full flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-2xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 font-semibold text-lg"
            >
              {saving ? (
                <>Saving...</>
              ) : (
                <>
                  <Save size={24} />
                  Save Template & Get API Endpoint
                </>
              )}
            </button>

            {/* Success Message */}
            {saveSuccess && (
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-2xl p-6 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="p-2 bg-green-500 rounded-full">
                    <CheckCircle className="text-white" size={24} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-green-900 text-lg mb-2">Template Saved Successfully! 🎉</h3>
                    <p className="text-sm text-green-700 mb-3">Your API endpoint is ready to use:</p>
                    <div className="flex items-center gap-2 bg-white rounded-xl px-4 py-3 border-2 border-green-200">
                      <code className="flex-1 text-sm font-mono text-gray-800 break-all">{apiEndpoint}</code>
                      <button
                        onClick={() => copyToClipboard(apiEndpoint)}
                        className="flex-shrink-0 p-2 bg-green-100 hover:bg-green-200 rounded-lg transition-colors"
                        title="Copy to clipboard"
                      >
                        <Copy size={18} className="text-green-700" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Error Message */}
            {saveError && (
              <div className="bg-red-50 border-2 border-red-300 rounded-2xl p-6">
                <h3 className="font-bold text-red-900 mb-1">Error</h3>
                <p className="text-sm text-red-700">{saveError}</p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Saved Templates */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FileText size={20} className="text-blue-600" />
                Your Templates ({savedTemplates.length})
              </h2>

              {savedTemplates.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <FileText size={48} className="mx-auto opacity-20" />
                  </div>
                  <p className="text-gray-500 text-sm">No templates yet</p>
                  <p className="text-gray-400 text-xs mt-1">Create your first template!</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {savedTemplates.map((template) => (
                    <div
                      key={template.template_id}
                      className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 rounded-xl hover:shadow-md transition-shadow"
                    >
                      <h3 className="font-semibold text-sm text-gray-900">{template.template_name}</h3>
                      <div className="flex items-center gap-2 mt-2 text-xs text-gray-600">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full">{template.category}</span>
                        <span>{template.fields.length} fields</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-2 font-mono truncate">
                        {template.template_id}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Guide */}
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
              <h3 className="font-bold text-lg mb-3">Quick Guide</h3>
              <ol className="space-y-3 text-sm">
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-xs font-bold">1</span>
                  <span>Choose a default template or start fresh</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-xs font-bold">2</span>
                  <span>Add fields you want to extract</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-xs font-bold">3</span>
                  <span>Click save and get your API endpoint</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-xs font-bold">4</span>
                  <span>Start extracting documents!</span>
                </li>
              </ol>

              <div className="mt-6 pt-6 border-t border-white/20">
                <h4 className="font-semibold text-sm mb-2">Example API Call:</h4>
                <pre className="bg-black/20 p-3 rounded-lg text-xs overflow-x-auto">
{`curl -X POST \\
  "your-api-endpoint" \\
  -F "file=@document.pdf"`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
