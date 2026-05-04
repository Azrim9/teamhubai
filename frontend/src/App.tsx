import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { AuthGuard } from './components/AuthGuard';
import Login from './pages/Login';

// Placeholder components for routes
const Register = () => <div>Register Page</div>;
const Dashboard = () => <div>Dashboard</div>;
const Agents = () => <div>Agents</div>;
const Jobs = () => <div>Jobs</div>;
const Matches = () => <div>Matches</div>;

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          <Route path="/" element={
            <AuthGuard>
              <Dashboard />
            </AuthGuard>
          } />
          
          <Route path="/agents" element={
            <AuthGuard>
              <Agents />
            </AuthGuard>
          } />
          
          <Route path="/jobs" element={
            <AuthGuard>
              <Jobs />
            </AuthGuard>
          } />

          <Route path="/matches" element={
            <AuthGuard>
              <Matches />
            </AuthGuard>
          } />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
