import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save, FileText, AlertCircle, CheckCircle, Copy } from 'lucide-react';
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

  const updateField = (index: number, key: keyof TemplateField, value: any) => {
    const newFields = [...fields];
    newFields[index] = { ...newFields[index], [key]: value };
    setFields(newFields);
  };

  const saveTemplate = async () => {
    // Validation
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

      // Reset form
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
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Template Builder</h1>
        <p className="text-gray-600">
          Create custom OCR extraction templates without authentication. Save your template and use it via API.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Default Templates */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Start from Default Template</h2>
            <select
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={selectedDefault}
              onChange={(e) => loadDefaultTemplate(e.target.value)}
            >
              <option value="">-- Choose a default template --</option>
              {defaultTemplates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.template_name} ({template.field_count} fields)
                </option>
              ))}
            </select>
          </div>

          {/* Template Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Template Details</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Name *
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., My Invoice Template"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  placeholder="Describe what this template is for..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Fields */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Fields</h2>
              <button
                onClick={addField}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus size={16} />
                Add Field
              </button>
            </div>

            <div className="space-y-4">
              {fields.map((field, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Field Name *
                      </label>
                      <input
                        type="text"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        placeholder="e.g., invoice_number"
                        value={field.name}
                        onChange={(e) => updateField(index, 'name', e.target.value)}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Type
                      </label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
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
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <input
                        type="text"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        placeholder="What should be extracted..."
                        value={field.description}
                        onChange={(e) => updateField(index, 'description', e.target.value)}
                      />
                    </div>

                    <div className="md:col-span-2 flex items-center justify-between">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={field.required}
                          onChange={(e) => updateField(index, 'required', e.target.checked)}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm text-gray-700">Required field</span>
                      </label>

                      {fields.length > 1 && (
                        <button
                          onClick={() => removeField(index)}
                          className="text-red-600 hover:text-red-700 flex items-center gap-1"
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
          <div className="flex gap-4">
            <button
              onClick={saveTemplate}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <>Saving...</>
              ) : (
                <>
                  <Save size={20} />
                  Save Template
                </>
              )}
            </button>
          </div>

          {/* Success/Error Messages */}
          {saveSuccess && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="text-green-600 flex-shrink-0" size={20} />
                <div className="flex-1">
                  <h3 className="font-medium text-green-900">Template Saved Successfully!</h3>
                  <p className="text-sm text-green-700 mt-1">Your API endpoint:</p>
                  <div className="mt-2 flex items-center gap-2 bg-white rounded px-3 py-2 font-mono text-sm">
                    <code className="flex-1 break-all">{apiEndpoint}</code>
                    <button
                      onClick={() => copyToClipboard(apiEndpoint)}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      <Copy size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {saveError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-medium text-red-900">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{saveError}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Saved Templates */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FileText size={20} />
              Saved Templates ({savedTemplates.length})
            </h2>

            {savedTemplates.length === 0 ? (
              <p className="text-gray-500 text-sm">No templates saved yet</p>
            ) : (
              <div className="space-y-2">
                {savedTemplates.map((template) => (
                  <div
                    key={template.template_id}
                    className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <h3 className="font-medium text-sm">{template.template_name}</h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {template.fields.length} fields • {template.category}
                    </p>
                    <p className="text-xs text-gray-400 mt-1 font-mono break-all">
                      {template.template_id}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Usage Instructions */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-2">How to Use</h3>
            <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
              <li>Create your template above</li>
              <li>Click "Save Template"</li>
              <li>Copy the API endpoint</li>
              <li>Send documents to that endpoint!</li>
            </ol>

            <div className="mt-4 pt-4 border-t border-blue-200">
              <h4 className="font-medium text-blue-900 text-sm mb-2">Example cURL:</h4>
              <pre className="bg-blue-900 text-blue-100 p-3 rounded text-xs overflow-x-auto">
{`curl -X POST \\
  "http://yourserver/api/v1/public/extract/your_template_id" \\
  -F "file=@document.pdf"`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
