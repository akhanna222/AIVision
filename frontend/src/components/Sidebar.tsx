import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Layers,
  FolderOpen,
  Tags as TagsIcon,
  BarChart3,
  FileInput,
  Package,
  Settings,
  Activity,
  LogOut,
} from 'lucide-react';

/**
 * Navigation Sidebar Component
 *
 * Provides seamless navigation across all AIVision features:
 * - Dashboard and analytics
 * - Document extraction (single and batch)
 * - Template management
 * - Category and tag organization
 * - API logs monitoring
 * - Settings
 *
 * Features:
 * - Active link highlighting
 * - Responsive design
 * - Icon-based navigation
 * - Collapsible sidebar
 */

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: LayoutDashboard,
    description: 'Overview and analytics',
  },
  {
    name: 'Extract',
    path: '/extract',
    icon: FileInput,
    description: 'Single document extraction',
  },
  {
    name: 'Batch Extract',
    path: '/batch',
    icon: Package,
    description: 'Process multiple documents',
  },
  {
    name: 'Templates',
    path: '/templates',
    icon: FileText,
    description: 'Manage extraction templates',
  },
  {
    name: 'Categories',
    path: '/categories',
    icon: FolderOpen,
    description: 'Organize document types',
  },
  {
    name: 'Tags',
    path: '/tags',
    icon: TagsIcon,
    description: 'Manage document tags',
  },
  {
    name: 'Analytics',
    path: '/analytics',
    icon: BarChart3,
    description: 'Usage and performance',
  },
  {
    name: 'API Logs',
    path: '/logs',
    icon: Activity,
    description: 'Monitor API calls',
  },
  {
    name: 'Settings',
    path: '/settings',
    icon: Settings,
    description: 'Account and preferences',
  },
];

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  return (
    <div
      className={`
        fixed left-0 top-0 h-full bg-white border-r border-gray-200 shadow-lg
        transition-transform duration-300 ease-in-out z-40
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        w-64
      `}
    >
      {/* Header */}
      <div className="h-16 flex items-center justify-between px-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">AIVision</h1>
            <p className="text-xs text-gray-500">OCR Service</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="lg:hidden text-gray-500 hover:text-gray-700"
          >
            ×
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-3">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `
                    flex items-center px-3 py-2.5 rounded-lg text-sm font-medium
                    transition-colors duration-150 group
                    ${
                      isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={`
                        w-5 h-5 mr-3 transition-colors
                        ${isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'}
                      `}
                    />
                    <div className="flex-1">
                      <div>{item.name}</div>
                      <div className="text-xs text-gray-500 group-hover:text-gray-600">
                        {item.description}
                      </div>
                    </div>
                  </>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Divider */}
        <div className="my-6 border-t border-gray-200"></div>

        {/* Account Info */}
        <div className="px-3">
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4">
            <div className="text-sm font-medium text-gray-900 mb-1">
              Free Plan
            </div>
            <div className="text-xs text-gray-600 mb-3">
              100 extractions/month
            </div>
            <button className="w-full px-3 py-1.5 bg-white text-blue-600 text-xs font-medium rounded-md hover:bg-blue-50 transition-colors">
              Upgrade Plan
            </button>
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-200 p-4">
        <button className="flex items-center w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors">
          <LogOut className="w-4 h-4 mr-3 text-gray-400" />
          Sign Out
        </button>
      </div>
    </div>
  );
}

/**
 * Layout wrapper with sidebar
 */
interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content */}
      <div
        className={`
          transition-all duration-300
          ${sidebarOpen ? 'lg:ml-64' : 'ml-0'}
        `}
      >
        {/* Top bar */}
        <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-500 hover:text-gray-700 lg:hidden"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          {/* Search bar */}
          <div className="flex-1 max-w-2xl mx-auto px-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search documents, templates, tags..."
                className="w-full px-4 py-2 pl-10 pr-4 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg
                className="absolute left-3 top-2.5 w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-4">
            <button className="text-gray-500 hover:text-gray-700 relative">
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
              <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
              TA
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">{children}</main>
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}
    </div>
  );
}
