import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import LearningPage from './pages/LearningPage'
import CoursesPage from './pages/CoursesPage'
import CourseDetailPage from './pages/CourseDetailPage'
import TutorPage from './pages/TutorPage'
import AgentsPage from './pages/AgentsPage'
import ProfilePage from './pages/ProfilePage'
import useAuthStore from './store/authStore'

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function PublicRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e1e2e',
            color: '#cdd6f4',
            border: '1px solid #313244',
          },
          success: { iconTheme: { primary: '#a6e3a1', secondary: '#1e1e2e' } },
          error: { iconTheme: { primary: '#f38ba8', secondary: '#1e1e2e' } },
        }}
      />
      <Routes>
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="learning" element={<LearningPage />} />
          <Route path="courses" element={<CoursesPage />} />
          <Route path="courses/:id" element={<CourseDetailPage />} />
          <Route path="tutor" element={<TutorPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
