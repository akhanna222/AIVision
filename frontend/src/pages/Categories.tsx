import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Save, X, FolderOpen } from 'lucide-react';
import { api } from '../services/api';

interface Category {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  icon: string;
  color: string;
  template_count: number;
  extraction_count: number;
  is_default: boolean;
  created_at: string;
}

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

interface EditingCategory {
  id?: number;
  name: string;
  display_name: string;
  description: string;
  icon: string;
  color: string;
}

export function Categories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingCategory, setEditingCategory] = useState<EditingCategory | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await api.listCategories();
      setCategories(data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCategory = () => {
    setIsCreating(true);
    setEditingCategory({
      name: '',
      display_name: '',
      description: '',
      icon: '📁',
      color: 'blue',
    });
  };

  const handleEditCategory = (category: Category) => {
    if (category.is_default) {
      alert('Default categories cannot be edited.');
      return;
    }
    setEditingCategory({
      id: category.id,
      name: category.name,
      display_name: category.display_name,
      description: category.description || '',
      icon: category.icon,
      color: category.color,
    });
    setIsCreating(false);
  };

  const handleSaveCategory = async () => {
    if (!editingCategory) return;

    if (!editingCategory.display_name.trim()) {
      alert('Please enter a category name');
      return;
    }

    try {
      if (isCreating) {
        const newCategory = await api.createCategory({
          name: editingCategory.display_name.toLowerCase().replace(/\s+/g, '_'),
          display_name: editingCategory.display_name,
          description: editingCategory.description || undefined,
          icon: editingCategory.icon,
          color: editingCategory.color,
        });
        setCategories([...categories, newCategory]);
      } else if (editingCategory.id) {
        const updated = await api.updateCategory(editingCategory.id, {
          display_name: editingCategory.display_name,
          description: editingCategory.description || undefined,
          icon: editingCategory.icon,
          color: editingCategory.color,
        });
        setCategories(categories.map((cat) => (cat.id === updated.id ? updated : cat)));
      }
      setEditingCategory(null);
      setIsCreating(false);
    } catch (error) {
      console.error('Failed to save category:', error);
      alert('Failed to save category. Please try again.');
    }
  };

  const handleDeleteCategory = async (categoryId: number) => {
    const category = categories.find((c) => c.id === categoryId);
    if (!category) return;

    if (category.is_default) {
      alert('Default categories cannot be deleted.');
      return;
    }

    if (category.template_count > 0 || category.extraction_count > 0) {
      const confirmed = confirm(
        `This category has ${category.template_count} templates and ${category.extraction_count} extractions. Are you sure you want to delete it?`
      );
      if (!confirmed) return;
    }

    try {
      await api.deleteCategory(categoryId);
      setCategories(categories.filter((c) => c.id !== categoryId));
    } catch (error) {
      console.error('Failed to delete category:', error);
      alert('Failed to delete category. Please try again.');
    }
  };

  const getColorClass = (colorValue: string) => {
    const color = COLORS.find((c) => c.value === colorValue);
    return color?.class || COLORS[0].class;
  };

  const totalTemplates = categories.reduce((sum, cat) => sum + cat.template_count, 0);
  const totalExtractions = categories.reduce((sum, cat) => sum + cat.extraction_count, 0);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center text-gray-500">Loading categories...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Categories</h1>
          <p className="mt-2 text-gray-600">Customize document categories for better organization</p>
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
                  onClick={() => { setEditingCategory(null); setIsCreating(false); }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category Name *</label>
                  <input
                    type="text"
                    value={editingCategory.display_name}
                    onChange={(e) => setEditingCategory({ ...editingCategory, display_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Purchase Order"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={editingCategory.description}
                    onChange={(e) => setEditingCategory({ ...editingCategory, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Brief description..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Icon (Emoji)</label>
                    <input
                      type="text"
                      value={editingCategory.icon}
                      onChange={(e) => setEditingCategory({ ...editingCategory, icon: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="📁"
                      maxLength={2}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                    <select
                      value={editingCategory.color}
                      onChange={(e) => setEditingCategory({ ...editingCategory, color: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      {COLORS.map((color) => (
                        <option key={color.value} value={color.value}>{color.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {editingCategory.display_name && (
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="text-sm text-gray-600 mb-2">Preview:</div>
                    <div className={`inline-flex items-center px-3 py-2 rounded-lg border ${getColorClass(editingCategory.color)}`}>
                      <span className="text-xl mr-2">{editingCategory.icon}</span>
                      <span className="font-medium">{editingCategory.display_name}</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => { setEditingCategory(null); setIsCreating(false); }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveCategory}
                  disabled={!editingCategory.display_name.trim()}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
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
          <div key={category.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center">
                <span className="text-3xl mr-3">{category.icon}</span>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{category.display_name}</h3>
                  <span className={`inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded border ${getColorClass(category.color)}`}>
                    {category.name}
                  </span>
                </div>
              </div>
              {!category.is_default && (
                <div className="flex space-x-1">
                  <button
                    onClick={() => handleEditCategory(category)}
                    className="p-1.5 text-gray-600 hover:bg-gray-100 rounded"
                    title="Edit"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteCategory(category.id)}
                    className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                    title="Delete"
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
                <span className="font-semibold text-gray-900">{category.template_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Extractions:</span>
                <span className="font-semibold text-gray-900">{category.extraction_count}</span>
              </div>
            </div>

            {category.is_default && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <span className="text-xs text-blue-600 font-medium">Default Category</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
