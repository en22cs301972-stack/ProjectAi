import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authAPI } from '../services/api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (credentials) => {
        set({ isLoading: true })
        try {
          const response = await authAPI.login(credentials)
          const { access_token, user } = response.data
          localStorage.setItem('access_token', access_token)
          set({ user, token: access_token, isAuthenticated: true, isLoading: false })
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          return { success: false, error: error.response?.data?.detail || 'Login failed' }
        }
      },

      register: async (userData) => {
        set({ isLoading: true })
        try {
          const response = await authAPI.register(userData)
          set({ isLoading: false })
          return { success: true, user: response.data }
        } catch (error) {
          set({ isLoading: false })
          return { success: false, error: error.response?.data?.detail || 'Registration failed' }
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({ user: null, token: null, isAuthenticated: false })
      },

      updateUser: (user) => set({ user }),
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated }),
    }
  )
)

export default useAuthStore
