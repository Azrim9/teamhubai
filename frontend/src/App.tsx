import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { AuthGuard } from './components/AuthGuard';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import Jobs from './pages/Jobs';
import Matches from './pages/Matches';

// Placeholder components for routes
const Settings = () => <div>Settings</div>;

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          <Route path="/" element={
            <AuthGuard>
              <Layout>
                <Dashboard />
              </Layout>
            </AuthGuard>
          } />
          
          <Route path="/agents" element={
            <AuthGuard>
              <Layout>
                <Agents />
              </Layout>
            </AuthGuard>
          } />
          
          <Route path="/jobs" element={
            <AuthGuard>
              <Layout>
                <Jobs />
              </Layout>
            </AuthGuard>
          } />

          <Route path="/matches" element={
            <AuthGuard>
              <Layout>
                <Matches />
              </Layout>
            </AuthGuard>
          } />

          <Route path="/settings" element={
            <AuthGuard>
              <Layout>
                <Settings />
              </Layout>
            </AuthGuard>
          } />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
