/**
 * Main App Component with Layout and Navigation
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { Layout } from '@/components/Sidebar';

// Pages
import Dashboard from '@/pages/Dashboard';
import Extract from '@/pages/Extract';
import BatchExtract from '@/pages/BatchExtract';
import Results from '@/pages/Results';
import { Templates } from '@/pages/Templates';
import Analytics from '@/pages/Analytics';
import Settings from '@/pages/Settings';
import Login from '@/pages/Login';
import { Categories } from '@/pages/Categories';
import { Tags } from '@/pages/Tags';
import { APILogs } from '@/pages/APILogs';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

/**
 * Authenticated layout wrapper
 */
function AuthenticatedRoute({ children }: { children: React.ReactNode }) {
  // TODO: Add authentication check
  // const isAuthenticated = useAuth();
  // if (!isAuthenticated) return <Navigate to="/login" replace />;

  return <Layout>{children}</Layout>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />

        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />

          {/* Authenticated routes with layout */}
          <Route
            path="/dashboard"
            element={
              <AuthenticatedRoute>
                <Dashboard />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/extract"
            element={
              <AuthenticatedRoute>
                <Extract />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/batch"
            element={
              <AuthenticatedRoute>
                <BatchExtract />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/results/:id"
            element={
              <AuthenticatedRoute>
                <Results />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/templates"
            element={
              <AuthenticatedRoute>
                <Templates />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/categories"
            element={
              <AuthenticatedRoute>
                <Categories />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/tags"
            element={
              <AuthenticatedRoute>
                <Tags />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <AuthenticatedRoute>
                <Analytics />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/logs"
            element={
              <AuthenticatedRoute>
                <APILogs />
              </AuthenticatedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <AuthenticatedRoute>
                <Settings />
              </AuthenticatedRoute>
            }
          />

          {/* Redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
