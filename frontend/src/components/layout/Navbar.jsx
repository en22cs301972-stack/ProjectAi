import { Bars3Icon, BellIcon, SunIcon } from '@heroicons/react/24/outline'
import { UserCircleIcon } from '@heroicons/react/24/solid'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    toast.success('Logged out successfully')
    navigate('/login')
  }

  return (
    <header className="h-16 bg-[#11111b] border-b border-[#313244] flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="p-2 rounded-lg text-[#a6adc8] hover:bg-[#1e1e2e] hover:text-white transition-colors"
        >
          <Bars3Icon className="w-5 h-5" />
        </button>
        <div className="hidden sm:flex items-center gap-2 bg-[#1e1e2e] rounded-lg px-3 py-2">
          <span className="text-xs text-[#585b70]">Ctrl+K</span>
          <span className="text-xs text-[#585b70]">to search</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="p-2 rounded-lg text-[#a6adc8] hover:bg-[#1e1e2e] hover:text-white transition-colors">
          <BellIcon className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-white">{user?.full_name || user?.username}</p>
            <p className="text-xs text-[#585b70]">{user?.email}</p>
          </div>
          <div className="relative group">
            <button className="flex items-center gap-2 p-1 rounded-lg hover:bg-[#1e1e2e] transition-colors">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt={user.username} className="w-8 h-8 rounded-full" />
              ) : (
                <UserCircleIcon className="w-8 h-8 text-primary-400" />
              )}
            </button>
            {/* Dropdown */}
            <div className="absolute right-0 top-full mt-2 w-48 bg-[#1e1e2e] border border-[#313244] rounded-xl shadow-xl z-50 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200">
              <div className="p-2">
                <button
                  onClick={() => navigate('/profile')}
                  className="w-full text-left px-3 py-2 text-sm text-[#a6adc8] hover:bg-[#313244] hover:text-white rounded-lg transition-colors"
                >
                  Profile Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
