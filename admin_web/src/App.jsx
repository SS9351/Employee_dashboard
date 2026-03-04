import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import EmployeeDashboard from './pages/EmployeeDashboard';

function PrivateAdminRoute({ children }) {
  const token = localStorage.getItem('admin_token');
  const isAdmin = localStorage.getItem('is_admin') === 'true';
  return token && isAdmin ? children : <Navigate to="/employee-dashboard" />;
}

function PrivateEmployeeRoute({ children }) {
  const token = localStorage.getItem('admin_token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/admin-dashboard"
          element={
            <PrivateAdminRoute>
              <Dashboard />
            </PrivateAdminRoute>
          }
        />

        <Route
          path="/employee-dashboard"
          element={
            <PrivateEmployeeRoute>
              <EmployeeDashboard />
            </PrivateEmployeeRoute>
          }
        />

        <Route path="*" element={<Navigate to="/employee-dashboard" />} />
      </Routes>
    </Router>
  );
}

export default App;
