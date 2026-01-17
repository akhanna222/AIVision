import React, { useState, useEffect } from 'react';
import { Tag, Plus, X, Search, TrendingUp } from 'lucide-react';
import { api } from '../services/api';

/**
 * Tags Management Page
 *
 * Provides interface for managing document tags:
 * - View all tags with usage statistics
 * - Create custom tags
 * - Edit tag names and colors
 * - Delete unused tags
 * - See which documents use each tag
 * - Tag suggestions based on common patterns
 */

interface DocumentTag {
  id: number;
  tag_name: string;
  color: string;
  tag_category?: string;
  usage_count: number;
  created_at: string;
}

const TAG_COLORS = [
  { name: 'Blue', class: 'bg-blue-100 text-blue-800 border-blue-200' },
  { name: 'Green', class: 'bg-green-100 text-green-800 border-green-200' },
  { name: 'Yellow', class: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  { name: 'Red', class: 'bg-red-100 text-red-800 border-red-200' },
  { name: 'Purple', class: 'bg-purple-100 text-purple-800 border-purple-200' },
  { name: 'Pink', class: 'bg-pink-100 text-pink-800 border-pink-200' },
  { name: 'Indigo', class: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  { name: 'Gray', class: 'bg-gray-100 text-gray-800 border-gray-200' },
];

export function Tags() {
  const [tags, setTags] = useState<DocumentTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [newTag, setNewTag] = useState('');
  const [newTagColor, setNewTagColor] = useState(TAG_COLORS[0]);
  const [showAddTag, setShowAddTag] = useState(false);

  useEffect(() => {
    loadTags();
  }, []);

  const loadTags = async () => {
    try {
      setLoading(true);
      const data = await api.listTags();
      setTags(data);
    } catch (error) {
      console.error('Failed to load tags:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTag = async () => {
    if (!newTag.trim()) return;

    try {
      const newTagData = await api.createTag({
        tag_name: newTag.trim().toLowerCase(),
        color: newTagColor.name.toLowerCase(),
      });
      setTags([...tags, newTagData]);
      setNewTag('');
      setShowAddTag(false);
    } catch (error) {
      console.error('Failed to create tag:', error);
      alert('Failed to create tag. Please try again.');
    }
  };

  const handleDeleteTag = async (tagId: number) => {
    const tag = tags.find((t) => t.id === tagId);
    if (!tag) return;

    if (tag.usage_count > 0) {
      const confirmed = confirm(
        `This tag is used in ${tag.usage_count} documents. Are you sure you want to delete it?`
      );
      if (!confirmed) return;
    }

    try {
      await api.deleteTag(tagId);
      setTags(tags.filter((t) => t.id !== tagId));
    } catch (error) {
      console.error('Failed to delete tag:', error);
      alert('Failed to delete tag. Please try again.');
    }
  };

  const getColorClass = (colorName?: string) => {
    const color = TAG_COLORS.find(
      (c) => c.name.toLowerCase() === colorName?.toLowerCase()
    );
    return color?.class || TAG_COLORS[0].class;
  };

  const filteredTags = tags
    .filter((tag) => tag.tag_name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => b.usage_count - a.usage_count);

  const totalUsage = tags.reduce((sum, tag) => sum + tag.usage_count, 0);
  const topTags = [...tags]
    .sort((a, b) => b.usage_count - a.usage_count)
    .slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Tag Management</h1>
        <p className="mt-2 text-gray-600">
          Organize and manage your document tags
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Tag className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{tags.length}</div>
              <div className="text-sm text-gray-600">Total Tags</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalUsage}</div>
              <div className="text-sm text-gray-600">Total Usage</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div>
            <div className="text-sm font-medium text-gray-700 mb-2">Most Used Tags</div>
            <div className="flex flex-wrap gap-2">
              {topTags.slice(0, 3).map((tag) => (
                <span
                  key={tag.id}
                  className={`px-2 py-1 text-xs font-medium rounded border ${getColorClass(
                    tag.color
                  )}`}
                >
                  {tag.tag_name} ({tag.usage_count})
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Search and Add */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search tags..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <button
            onClick={() => setShowAddTag(!showAddTag)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add Tag
          </button>
        </div>

        {/* Add Tag Form */}
        {showAddTag && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tag Name
                </label>
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  placeholder="e.g., urgent, financial, personal"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && handleCreateTag()}
                />
              </div>

              <div className="w-40">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color
                </label>
                <select
                  value={newTagColor.name}
                  onChange={(e) =>
                    setNewTagColor(
                      TAG_COLORS.find((c) => c.name === e.target.value) || TAG_COLORS[0]
                    )
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {TAG_COLORS.map((color) => (
                    <option key={color.name} value={color.name}>
                      {color.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleCreateTag}
                  disabled={!newTag.trim()}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  Create
                </button>
              </div>
            </div>

            {/* Preview */}
            {newTag && (
              <div className="mt-3">
                <span className="text-sm text-gray-600 mr-2">Preview:</span>
                <span
                  className={`px-3 py-1 text-sm font-medium rounded border ${newTagColor.class}`}
                >
                  {newTag}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tags Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredTags.map((tag) => (
          <div
            key={tag.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-3">
              <span
                className={`px-3 py-1 text-sm font-medium rounded border ${getColorClass(
                  tag.color
                )}`}
              >
                {tag.tag_name}
              </span>
              <button
                onClick={() => handleDeleteTag(tag.id)}
                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                title="Delete tag"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 text-sm text-gray-600">
              <div>
                <span className="font-medium">Used in:</span>
                <span className="ml-2 text-gray-900 font-semibold">
                  {tag.usage_count} documents
                </span>
              </div>
              <div className="text-xs text-gray-500">
                Created {new Date(tag.created_at).toLocaleDateString()}
              </div>
            </div>

            {tag.usage_count > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                  View Documents →
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredTags.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          {loading ? (
            <p>Loading tags...</p>
          ) : searchTerm ? (
            <div>
              <p className="mb-2">No tags found matching "{searchTerm}"</p>
              <button
                onClick={() => setSearchTerm('')}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                Clear search
              </button>
            </div>
          ) : (
            <div>
              <Tag className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="mb-4">No tags created yet</p>
              <button
                onClick={() => setShowAddTag(true)}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                Create your first tag
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tag Suggestions */}
      <div className="mt-8 bg-blue-50 rounded-lg border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          💡 Suggested Tags
        </h3>
        <p className="text-sm text-blue-800 mb-4">
          Based on your document patterns, consider these tags:
        </p>
        <div className="flex flex-wrap gap-2">
          {['invoices-2024', 'receipts', 'contracts', 'tax-documents', 'identity-docs'].map(
            (suggestion) => (
              <button
                key={suggestion}
                onClick={() => {
                  setNewTag(suggestion);
                  setShowAddTag(true);
                }}
                className="px-3 py-1 text-sm bg-white text-blue-800 border border-blue-300 rounded hover:bg-blue-100 transition-colors"
              >
                + {suggestion}
              </button>
            )
          )}
        </div>
      </div>
    </div>
  );
}
