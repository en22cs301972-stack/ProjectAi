import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  CodeBracketIcon,
  AcademicCapIcon,
  ChatBubbleLeftRightIcon,
  CpuChipIcon,
  UserIcon,
  SparklesIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

const navItems = [
  { to: '/dashboard', icon: HomeIcon, label: 'Dashboard' },
  { to: '/learning', icon: CodeBracketIcon, label: 'Code Editor' },
  { to: '/courses', icon: AcademicCapIcon, label: 'Courses' },
  { to: '/tutor', icon: ChatBubbleLeftRightIcon, label: 'AI Tutor' },
  { to: '/agents', icon: CpuChipIcon, label: 'AI Agents' },
  { to: '/profile', icon: UserIcon, label: 'Profile' },
]

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed lg:relative z-50 lg:z-auto
          flex flex-col h-full
          bg-[#11111b] border-r border-[#313244]
          transition-all duration-300 ease-in-out
          ${open ? 'w-64 translate-x-0' : 'w-0 lg:w-16 -translate-x-full lg:translate-x-0'}
          overflow-hidden
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-[#313244] min-h-[64px]">
          {open && (
            <div className="flex items-center gap-2">
              <SparklesIcon className="w-7 h-7 text-primary-400" />
              <span className="font-bold text-lg text-white whitespace-nowrap">AI Platform</span>
            </div>
          )}
          {!open && (
            <SparklesIcon className="w-7 h-7 text-primary-400 mx-auto" />
          )}
          <button
            onClick={onClose}
            className="lg:hidden text-[#585b70] hover:text-white"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg transition-all duration-200
                ${isActive
                  ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30'
                  : 'text-[#a6adc8] hover:bg-[#1e1e2e] hover:text-white'
                }`
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {open && <span className="text-sm font-medium whitespace-nowrap">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-[#313244]">
          {open && (
            <p className="text-xs text-[#585b70] text-center">
              AI Learning Platform v1.0
            </p>
          )}
        </div>
      </aside>
    </>
  )
}
