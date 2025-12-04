/**
 * Main App Component
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Pages (to be created)
import Dashboard from '@/pages/Dashboard';
import Extract from '@/pages/Extract';
import BatchExtract from '@/pages/BatchExtract';
import Results from '@/pages/Results';
import Templates from '@/pages/Templates';
import Analytics from '@/pages/Analytics';
import Settings from '@/pages/Settings';
import Login from '@/pages/Login';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Toaster position="top-right" />

          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/extract" element={<Extract />} />
            <Route path="/batch" element={<BatchExtract />} />
            <Route path="/results/:id" element={<Results />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
