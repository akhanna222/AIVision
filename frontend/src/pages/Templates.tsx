import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Save, X, FileText } from 'lucide-react';
import { api } from '../services/api';
import { ErrorMessage, EmptyState, CardSkeleton } from '../components/Loading';
import toast from 'react-hot-toast';

interface TemplateField {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

interface EditableTemplate {
  id: number | string;
  name: string;
  template_name?: string;
  category: string;
  country_code: string;
  description: string;
  fields: TemplateField[];
  is_active: boolean;
  account_id?: string;
  created_at?: string;
  updated_at?: string;
}

export function Templates() {
  const [templates, setTemplates] = useState<EditableTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingTemplate, setEditingTemplate] = useState<EditableTemplate | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [saving, setSaving] = useState(false);

  // Field types available for customization
  const fieldTypes = [
    'string', 'number', 'currency', 'date', 'email', 'phone', 'address', 'boolean'
  ];

  // Document categories
  const categories = [
    'invoice', 'receipt', 'mortgage_application', 'bank_statement',
    'passport', 'drivers_license', 'utility_bill', 'tax_document', 'other'
  ];

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getTemplates();
      setTemplates(data);
    } catch (err: any) {
      console.error('Failed to load templates:', err);
      setError(err.response?.data?.detail || 'Failed to load templates. Please try again.');
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setIsCreating(true);
    setEditingTemplate({
      id: '',
      name: '',
      category: 'other',
      country_code: 'IE',
      description: '',
      fields: [],
      is_active: true,
      account_id: '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  };

  const handleEditTemplate = (template: EditableTemplate) => {
    setEditingTemplate({ ...template });
    setIsCreating(false);
  };

  const handleSaveTemplate = async () => {
    if (!editingTemplate) return;

    if (!editingTemplate.name?.trim()) {
      toast.error('Please enter a template name');
      return;
    }

    if (editingTemplate.fields.length === 0) {
      toast.error('Please add at least one field');
      return;
    }

    try {
      setSaving(true);
      if (isCreating) {
        await api.createTemplate(editingTemplate as any);
        toast.success('Template created successfully');
      } else {
        await api.updateTemplate(String(editingTemplate.id), editingTemplate as any);
        toast.success('Template updated successfully');
      }
      setEditingTemplate(null);
      setIsCreating(false);
      await loadTemplates();
    } catch (err: any) {
      console.error('Failed to save template:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to save template. Please try again.';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTemplate = async (templateId: number | string) => {
    if (!confirm('Are you sure you want to delete this template?')) return;

    try {
      await api.deleteTemplate(String(templateId));
      toast.success('Template deleted successfully');
      await loadTemplates();
    } catch (err: any) {
      console.error('Failed to delete template:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to delete template. Please try again.';
      toast.error(errorMessage);
    }
  };

  const handleAddField = () => {
    if (!editingTemplate) return;

    const newField: TemplateField = {
      name: '',
      type: 'string',
      required: false,
      description: '',
    };

    setEditingTemplate({
      ...editingTemplate,
      fields: [...editingTemplate.fields, newField],
    });
  };

  const handleUpdateField = (index: number, field: Partial<TemplateField>) => {
    if (!editingTemplate) return;

    const updatedFields = [...editingTemplate.fields];
    updatedFields[index] = { ...updatedFields[index], ...field };

    setEditingTemplate({
      ...editingTemplate,
      fields: updatedFields,
    });
  };

  const handleRemoveField = (index: number) => {
    if (!editingTemplate) return;

    setEditingTemplate({
      ...editingTemplate,
      fields: editingTemplate.fields.filter((_, i) => i !== index),
    });
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Templates</h1>
          <p className="mt-2 text-gray-600">
            Manage document extraction templates and customize fields
          </p>
        </div>
        <CardSkeleton count={6} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Templates</h1>
          <p className="mt-2 text-gray-600">
            Manage document extraction templates and customize fields
          </p>
        </div>
        <ErrorMessage
          title="Failed to Load Templates"
          message={error}
          onRetry={loadTemplates}
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Templates</h1>
          <p className="mt-2 text-gray-600">
            Manage document extraction templates and customize fields
          </p>
        </div>
        <button
          onClick={handleCreateTemplate}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          New Template
        </button>
      </div>

      {/* Template Editor Modal */}
      {editingTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {isCreating ? 'Create Template' : 'Edit Template'}
                </h2>
                <button
                  onClick={() => {
                    setEditingTemplate(null);
                    setIsCreating(false);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Template Basic Info */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    value={editingTemplate.name}
                    onChange={(e) =>
                      setEditingTemplate({ ...editingTemplate, name: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Irish Utility Bill"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category *
                    </label>
                    <select
                      value={editingTemplate.category}
                      onChange={(e) =>
                        setEditingTemplate({ ...editingTemplate, category: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      {categories.map((cat) => (
                        <option key={cat} value={cat}>
                          {cat.replace(/_/g, ' ').toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Country Code *
                    </label>
                    <input
                      type="text"
                      value={editingTemplate.country_code}
                      onChange={(e) =>
                        setEditingTemplate({
                          ...editingTemplate,
                          country_code: e.target.value.toUpperCase(),
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g., IE, UK, US"
                      maxLength={2}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={editingTemplate.description || ''}
                    onChange={(e) =>
                      setEditingTemplate({ ...editingTemplate, description: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={2}
                    placeholder="Brief description of this template..."
                  />
                </div>
              </div>

              {/* Fields Section */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Fields</h3>
                  <button
                    onClick={handleAddField}
                    className="flex items-center px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add Field
                  </button>
                </div>

                <div className="space-y-3">
                  {editingTemplate.fields.map((field, index) => (
                    <div
                      key={index}
                      className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <div className="grid grid-cols-12 gap-3">
                        <div className="col-span-4">
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Field Name *
                          </label>
                          <input
                            type="text"
                            value={field.name}
                            onChange={(e) =>
                              handleUpdateField(index, { name: e.target.value })
                            }
                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., total_amount"
                          />
                        </div>

                        <div className="col-span-3">
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Type *
                          </label>
                          <select
                            value={field.type}
                            onChange={(e) =>
                              handleUpdateField(index, { type: e.target.value })
                            }
                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            {fieldTypes.map((type) => (
                              <option key={type} value={type}>
                                {type}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="col-span-4">
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Description
                          </label>
                          <input
                            type="text"
                            value={field.description || ''}
                            onChange={(e) =>
                              handleUpdateField(index, { description: e.target.value })
                            }
                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Optional hint..."
                          />
                        </div>

                        <div className="col-span-1 flex items-end justify-end">
                          <button
                            onClick={() => handleRemoveField(index)}
                            className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                            title="Remove field"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      <div className="mt-2 flex items-center">
                        <label className="flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={field.required || false}
                            onChange={(e) =>
                              handleUpdateField(index, { required: e.target.checked })
                            }
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">Required field</span>
                        </label>
                      </div>
                    </div>
                  ))}

                  {editingTemplate.fields.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      No fields added yet. Click "Add Field" to get started.
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setEditingTemplate(null);
                    setIsCreating(false);
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveTemplate}
                  disabled={
                    saving ||
                    !editingTemplate.name ||
                    !editingTemplate.category ||
                    editingTemplate.fields.length === 0
                  }
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {saving ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Template
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Templates List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div
            key={template.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  {template.name}
                </h3>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                    {template.category.replace(/_/g, ' ')}
                  </span>
                  <span>{template.country_code}</span>
                </div>
              </div>
              <div className="flex space-x-1">
                <button
                  onClick={() => handleEditTemplate(template)}
                  className="p-2 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                  title="Edit template"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeleteTemplate(template.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Delete template"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {template.description && (
              <p className="text-sm text-gray-600 mb-4">{template.description}</p>
            )}

            <div className="space-y-2">
              <div className="text-sm">
                <span className="font-medium text-gray-700">Fields:</span>
                <span className="ml-2 text-gray-600">{template.fields.length}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {template.fields.slice(0, 5).map((field, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                  >
                    {field.name}
                  </span>
                ))}
                {template.fields.length > 5 && (
                  <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                    +{template.fields.length - 5} more
                  </span>
                )}
              </div>
            </div>

            {template.usage_count !== undefined && (
              <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
                Used {template.usage_count} times
              </div>
            )}
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <EmptyState
          icon={<FileText className="w-16 h-16 text-gray-300" />}
          title="No Templates Yet"
          message="Get started by creating your first extraction template to define what fields to extract from documents."
          action={{
            label: "Create Template",
            onClick: handleCreateTemplate,
          }}
        />
      )}
    </div>
  );
}
