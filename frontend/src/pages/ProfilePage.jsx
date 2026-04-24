import { useState } from 'react'
import { authAPI } from '../services/api'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import { UserCircleIcon, KeyIcon, GlobeAltIcon } from '@heroicons/react/24/outline'

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    preferred_language: user?.preferred_language || 'en',
    response_language: user?.response_language || 'en',
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authAPI.updateMe(formData)
      updateUser(res.data)
      toast.success('Profile updated!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-white">Profile Settings</h1>

      {/* Avatar */}
      <div className="card flex items-center gap-4">
        {user?.avatar_url ? (
          <img src={user.avatar_url} alt={user.username} className="w-20 h-20 rounded-full" />
        ) : (
          <UserCircleIcon className="w-20 h-20 text-primary-400" />
        )}
        <div>
          <h2 className="text-xl font-bold text-white">{user?.full_name || user?.username}</h2>
          <p className="text-[#a6adc8]">{user?.email}</p>
          <div className="flex items-center gap-2 mt-1">
            {user?.is_verified && (
              <span className="badge badge-success text-xs">Verified</span>
            )}
            {user?.is_admin && (
              <span className="badge badge-warning text-xs">Admin</span>
            )}
          </div>
        </div>
      </div>

      {/* Edit Form */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <KeyIcon className="w-5 h-5 text-primary-400" />
          Edit Profile
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Full Name</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={e => setFormData(p => ({ ...p, full_name: e.target.value }))}
              className="input"
              placeholder="Your full name"
            />
          </div>

          <div>
            <label className="label flex items-center gap-1">
              <GlobeAltIcon className="w-4 h-4" />
              AI Tutor Response Language
            </label>
            <select
              value={formData.response_language}
              onChange={e => setFormData(p => ({ ...p, response_language: e.target.value }))}
              className="input"
            >
              <option value="en">English</option>
              <option value="hinglish">Hinglish (Hindi + English)</option>
            </select>
            <p className="text-xs text-[#585b70] mt-1">
              The AI Tutor will respond in your selected language
            </p>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Account Info */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Account Information</h2>
        <div className="space-y-3">
          {[
            { label: 'Username', value: user?.username },
            { label: 'Email', value: user?.email },
            { label: 'Member Since', value: user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A' },
          ].map(({ label, value }) => (
            <div key={label} className="flex justify-between items-center py-2 border-b border-[#313244]">
              <span className="text-sm text-[#585b70]">{label}</span>
              <span className="text-sm text-white">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
