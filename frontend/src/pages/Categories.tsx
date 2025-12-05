import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Save, X, FolderOpen } from 'lucide-react';

/**
 * Categories Management Page
 *
 * Allows users to customize document categories for classification:
 * - View all available categories
 * - Create custom categories
 * - Edit category names and descriptions
 * - Set category-specific extraction rules
 * - Delete unused categories
 * - View category usage statistics
 */

interface Category {
  id: string;
  name: string;
  displayName: string;
  description: string;
  icon?: string;
  color: string;
  templateCount: number;
  extractionCount: number;
  isDefault: boolean;
}

const DEFAULT_CATEGORIES: Category[] = [
  {
    id: 'invoice',
    name: 'invoice',
    displayName: 'Invoice',
    description: 'Commercial invoices and billing documents',
    icon: '📄',
    color: 'blue',
    templateCount: 3,
    extractionCount: 145,
    isDefault: true,
  },
  {
    id: 'receipt',
    name: 'receipt',
    displayName: 'Receipt',
    description: 'Purchase receipts and transaction records',
    icon: '🧾',
    color: 'green',
    templateCount: 2,
    extractionCount: 89,
    isDefault: true,
  },
  {
    id: 'mortgage_application',
    name: 'mortgage_application',
    displayName: 'Mortgage Application',
    description: 'Mortgage and loan application forms',
    icon: '🏠',
    color: 'purple',
    templateCount: 4,
    extractionCount: 56,
    isDefault: true,
  },
  {
    id: 'bank_statement',
    name: 'bank_statement',
    displayName: 'Bank Statement',
    description: 'Bank account statements with transactions',
    icon: '🏦',
    color: 'indigo',
    templateCount: 3,
    extractionCount: 123,
    isDefault: true,
  },
  {
    id: 'passport',
    name: 'passport',
    displayName: 'Passport',
    description: 'Passport and travel documents',
    icon: '🛂',
    color: 'red',
    templateCount: 1,
    extractionCount: 34,
    isDefault: true,
  },
  {
    id: 'drivers_license',
    name: 'drivers_license',
    displayName: "Driver's License",
    description: "Driver's licenses and ID cards",
    icon: '🪪',
    color: 'yellow',
    templateCount: 1,
    extractionCount: 45,
    isDefault: true,
  },
  {
    id: 'utility_bill',
    name: 'utility_bill',
    displayName: 'Utility Bill',
    description: 'Electricity, gas, water, and internet bills',
    icon: '⚡',
    color: 'orange',
    templateCount: 2,
    extractionCount: 67,
    isDefault: true,
  },
  {
    id: 'tax_document',
    name: 'tax_document',
    displayName: 'Tax Document',
    description: 'Tax forms and related documents',
    icon: '💼',
    color: 'pink',
    templateCount: 2,
    extractionCount: 78,
    isDefault: true,
  },
];

const COLORS = [
  { name: 'Blue', value: 'blue', class: 'bg-blue-100 text-blue-800 border-blue-200' },
  { name: 'Green', value: 'green', class: 'bg-green-100 text-green-800 border-green-200' },
  { name: 'Purple', value: 'purple', class: 'bg-purple-100 text-purple-800 border-purple-200' },
  { name: 'Red', value: 'red', class: 'bg-red-100 text-red-800 border-red-200' },
  { name: 'Yellow', value: 'yellow', class: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  { name: 'Indigo', value: 'indigo', class: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  { name: 'Orange', value: 'orange', class: 'bg-orange-100 text-orange-800 border-orange-200' },
  { name: 'Pink', value: 'pink', class: 'bg-pink-100 text-pink-800 border-pink-200' },
];

export function Categories() {
  const [categories, setCategories] = useState<Category[]>(DEFAULT_CATEGORIES);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateCategory = () => {
    setIsCreating(true);
    setEditingCategory({
      id: '',
      name: '',
      displayName: '',
      description: '',
      icon: '📁',
      color: 'blue',
      templateCount: 0,
      extractionCount: 0,
      isDefault: false,
    });
  };

  const handleEditCategory = (category: Category) => {
    if (category.isDefault) {
      alert('Default categories cannot be edited. Create a custom category instead.');
      return;
    }
    setEditingCategory({ ...category });
    setIsCreating(false);
  };

  const handleSaveCategory = () => {
    if (!editingCategory) return;

    if (!editingCategory.displayName.trim()) {
      alert('Please enter a category name');
      return;
    }

    if (isCreating) {
      const newCategory = {
        ...editingCategory,
        id: editingCategory.displayName.toLowerCase().replace(/\s+/g, '_'),
        name: editingCategory.displayName.toLowerCase().replace(/\s+/g, '_'),
      };
      setCategories([...categories, newCategory]);
    } else {
      setCategories(
        categories.map((cat) =>
          cat.id === editingCategory.id ? editingCategory : cat
        )
      );
    }

    setEditingCategory(null);
    setIsCreating(false);
  };

  const handleDeleteCategory = (categoryId: string) => {
    const category = categories.find((c) => c.id === categoryId);
    if (!category) return;

    if (category.isDefault) {
      alert('Default categories cannot be deleted.');
      return;
    }

    if (category.templateCount > 0 || category.extractionCount > 0) {
      const confirmed = confirm(
        `This category has ${category.templateCount} templates and ${category.extractionCount} extractions. Are you sure you want to delete it?`
      );
      if (!confirmed) return;
    }

    setCategories(categories.filter((c) => c.id !== categoryId));
  };

  const getColorClass = (colorValue: string) => {
    const color = COLORS.find((c) => c.value === colorValue);
    return color?.class || COLORS[0].class;
  };

  const totalTemplates = categories.reduce((sum, cat) => sum + cat.templateCount, 0);
  const totalExtractions = categories.reduce(
    (sum, cat) => sum + cat.extractionCount,
    0
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Categories</h1>
          <p className="mt-2 text-gray-600">
            Customize document categories for better organization
          </p>
        </div>
        <button
          onClick={handleCreateCategory}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          New Category
        </button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <FolderOpen className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{categories.length}</div>
              <div className="text-sm text-gray-600">Total Categories</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-8 h-8 text-2xl mr-3">📋</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalTemplates}</div>
              <div className="text-sm text-gray-600">Total Templates</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="w-8 h-8 text-2xl mr-3">🔍</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalExtractions}</div>
              <div className="text-sm text-gray-600">Total Extractions</div>
            </div>
          </div>
        </div>
      </div>

      {/* Category Editor Modal */}
      {editingCategory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {isCreating ? 'Create Category' : 'Edit Category'}
                </h2>
                <button
                  onClick={() => {
                    setEditingCategory(null);
                    setIsCreating(false);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category Name *
                  </label>
                  <input
                    type="text"
                    value={editingCategory.displayName}
                    onChange={(e) =>
                      setEditingCategory({
                        ...editingCategory,
                        displayName: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Purchase Order"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={editingCategory.description}
                    onChange={(e) =>
                      setEditingCategory({
                        ...editingCategory,
                        description: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="Brief description of this category..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Icon (Emoji)
                    </label>
                    <input
                      type="text"
                      value={editingCategory.icon || ''}
                      onChange={(e) =>
                        setEditingCategory({ ...editingCategory, icon: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="📁"
                      maxLength={2}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Color
                    </label>
                    <select
                      value={editingCategory.color}
                      onChange={(e) =>
                        setEditingCategory({ ...editingCategory, color: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      {COLORS.map((color) => (
                        <option key={color.value} value={color.value}>
                          {color.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Preview */}
                {editingCategory.displayName && (
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="text-sm text-gray-600 mb-2">Preview:</div>
                    <div
                      className={`inline-flex items-center px-3 py-2 rounded-lg border ${getColorClass(
                        editingCategory.color
                      )}`}
                    >
                      {editingCategory.icon && (
                        <span className="text-xl mr-2">{editingCategory.icon}</span>
                      )}
                      <span className="font-medium">{editingCategory.displayName}</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setEditingCategory(null);
                    setIsCreating(false);
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveCategory}
                  disabled={!editingCategory.displayName.trim()}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save Category
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Categories Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {categories.map((category) => (
          <div
            key={category.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center">
                {category.icon && (
                  <span className="text-3xl mr-3">{category.icon}</span>
                )}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {category.displayName}
                  </h3>
                  <span
                    className={`inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded border ${getColorClass(
                      category.color
                    )}`}
                  >
                    {category.name}
                  </span>
                </div>
              </div>
              {!category.isDefault && (
                <div className="flex space-x-1">
                  <button
                    onClick={() => handleEditCategory(category)}
                    className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                    title="Edit category"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteCategory(category.id)}
                    className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete category"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {category.description && (
              <p className="text-sm text-gray-600 mb-4">{category.description}</p>
            )}

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Templates:</span>
                <span className="font-semibold text-gray-900">
                  {category.templateCount}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Extractions:</span>
                <span className="font-semibold text-gray-900">
                  {category.extractionCount}
                </span>
              </div>
            </div>

            {category.isDefault && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <span className="text-xs text-blue-600 font-medium">
                  ✓ Default Category
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
