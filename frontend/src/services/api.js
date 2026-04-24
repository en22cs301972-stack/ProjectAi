import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach auth token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
  googleAuth: () => api.get('/auth/google'),
}

// Learning
export const learningAPI = {
  executeCode: (data) => api.post('/learning/execute', data),
  debugCode: (data) => api.post('/learning/debug', data),
  suggestFix: (code, language, issue) =>
    api.post('/learning/suggest-fix', null, { params: { code, language, issue } }),
  getProblems: (params) => api.get('/learning/problems', { params }),
  getProblem: (id) => api.get(`/learning/problems/${id}`),
  getSubmissions: () => api.get('/learning/submissions'),
}

// Courses
export const coursesAPI = {
  list: (params) => api.get('/courses', { params }),
  get: (id) => api.get(`/courses/${id}`),
  enroll: (id) => api.post(`/courses/${id}/enroll`),
  updateProgress: (courseId, lessonId) =>
    api.put(`/courses/${courseId}/progress`, null, { params: { lesson_id: lessonId } }),
  getEnrollments: () => api.get('/courses/my/enrollments'),
  getCertificates: () => api.get('/courses/certificates/my'),
  downloadCertificate: (id) =>
    api.get(`/courses/certificates/${id}/download`, { responseType: 'blob' }),
}

// AI Tutor
export const tutorAPI = {
  chat: (data) => api.post('/tutor/chat', data),
  getSessions: () => api.get('/tutor/sessions'),
  getSessionMessages: (id) => api.get(`/tutor/sessions/${id}/messages`),
  deleteSession: (id) => api.delete(`/tutor/sessions/${id}`),
}

// Agents
export const agentsAPI = {
  list: () => api.get('/agents'),
  create: (data) => api.post('/agents', data),
  get: (id) => api.get(`/agents/${id}`),
  update: (id, data) => api.put(`/agents/${id}`, data),
  delete: (id) => api.delete(`/agents/${id}`),
  start: (id, data) => api.post(`/agents/${id}/start`, data),
  stop: (id) => api.post(`/agents/${id}/stop`),
  getLogs: (id) => api.get(`/agents/${id}/logs`),
  getAvailableTools: () => api.get('/agents/tools/available'),
}

export default api
