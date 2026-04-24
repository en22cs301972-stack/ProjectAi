import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  CodeBracketIcon, AcademicCapIcon, ChatBubbleLeftRightIcon,
  CpuChipIcon, TrophyIcon, ClockIcon, FireIcon, CheckCircleIcon,
} from '@heroicons/react/24/outline'
import { learningAPI, coursesAPI, agentsAPI } from '../services/api'
import useAuthStore from '../store/authStore'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const activityData = [
  { day: 'Mon', problems: 2, time: 45 },
  { day: 'Tue', problems: 5, time: 120 },
  { day: 'Wed', problems: 3, time: 80 },
  { day: 'Thu', problems: 7, time: 150 },
  { day: 'Fri', problems: 4, time: 90 },
  { day: 'Sat', problems: 8, time: 200 },
  { day: 'Sun', problems: 6, time: 130 },
]

export default function Dashboard() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState({ submissions: 0, courses: 0, agents: 0, certificates: 0 })
  const [enrollments, setEnrollments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [subRes, enrollRes, agentRes, certRes] = await Promise.allSettled([
          learningAPI.getSubmissions(),
          coursesAPI.getEnrollments(),
          agentsAPI.list(),
          coursesAPI.getCertificates(),
        ])

        setStats({
          submissions: subRes.status === 'fulfilled' ? subRes.value.data.length : 0,
          courses: enrollRes.status === 'fulfilled' ? enrollRes.value.data.length : 0,
          agents: agentRes.status === 'fulfilled' ? agentRes.value.data.length : 0,
          certificates: certRes.status === 'fulfilled' ? certRes.value.data.length : 0,
        })

        if (enrollRes.status === 'fulfilled') {
          setEnrollments(enrollRes.value.data.slice(0, 3))
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const statCards = [
    { label: 'Problems Solved', value: stats.submissions, icon: CodeBracketIcon, color: 'text-blue-400', bg: 'bg-blue-900/20', border: 'border-blue-800/30' },
    { label: 'Courses Enrolled', value: stats.courses, icon: AcademicCapIcon, color: 'text-green-400', bg: 'bg-green-900/20', border: 'border-green-800/30' },
    { label: 'Active Agents', value: stats.agents, icon: CpuChipIcon, color: 'text-purple-400', bg: 'bg-purple-900/20', border: 'border-purple-800/30' },
    { label: 'Certificates', value: stats.certificates, icon: TrophyIcon, color: 'text-yellow-400', bg: 'bg-yellow-900/20', border: 'border-yellow-800/30' },
  ]

  const quickActions = [
    { to: '/learning', icon: CodeBracketIcon, label: 'Code Editor', desc: 'Practice & solve problems', color: 'from-blue-600 to-blue-700' },
    { to: '/courses', icon: AcademicCapIcon, label: 'Courses', desc: 'Structured learning paths', color: 'from-green-600 to-green-700' },
    { to: '/tutor', icon: ChatBubbleLeftRightIcon, label: 'AI Tutor', desc: 'Get instant help', color: 'from-purple-600 to-purple-700' },
    { to: '/agents', icon: CpuChipIcon, label: 'AI Agents', desc: 'Automate your tasks', color: 'from-orange-600 to-orange-700' },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Welcome */}
      <div className="card bg-gradient-to-r from-primary-900/50 to-purple-900/30 border-primary-800/30">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              Welcome back, {user?.full_name?.split(' ')[0] || user?.username}! 👋
            </h1>
            <p className="text-[#a6adc8] mt-1">
              Ready to level up your coding skills today?
            </p>
          </div>
          <div className="hidden md:flex items-center gap-2">
            <FireIcon className="w-8 h-8 text-orange-400" />
            <div>
              <p className="text-2xl font-bold text-white">7</p>
              <p className="text-xs text-[#a6adc8]">Day streak</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color, bg, border }) => (
          <div key={label} className={`card ${bg} border ${border}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#a6adc8]">{label}</p>
                <p className="text-3xl font-bold text-white mt-1">{value}</p>
              </div>
              <div className={`p-3 rounded-xl ${bg}`}>
                <Icon className={`w-6 h-6 ${color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Chart */}
        <div className="card lg:col-span-2">
          <h2 className="text-lg font-semibold text-white mb-4">Weekly Activity</h2>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={activityData}>
              <defs>
                <linearGradient id="colorProblems" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" tick={{ fill: '#585b70', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#585b70', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#1e1e2e', border: '1px solid #313244', borderRadius: 8 }}
                labelStyle={{ color: '#cdd6f4' }}
                itemStyle={{ color: '#a6adc8' }}
              />
              <Area type="monotone" dataKey="problems" stroke="#6366f1" fill="url(#colorProblems)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Course Progress */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Course Progress</h2>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-[#1e1e2e] rounded-lg animate-pulse" />
              ))}
            </div>
          ) : enrollments.length > 0 ? (
            <div className="space-y-3">
              {enrollments.map((enrollment) => (
                <div key={enrollment.id} className="bg-[#1e1e2e] rounded-lg p-3">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-sm font-medium text-white truncate">Course</p>
                    <span className="text-xs text-[#585b70]">{Math.round(enrollment.progress)}%</span>
                  </div>
                  <div className="w-full bg-[#313244] rounded-full h-1.5">
                    <div
                      className="bg-primary-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${enrollment.progress}%` }}
                    />
                  </div>
                  {enrollment.is_completed && (
                    <div className="flex items-center gap-1 mt-1">
                      <CheckCircleIcon className="w-3 h-3 text-green-400" />
                      <span className="text-xs text-green-400">Completed</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <AcademicCapIcon className="w-10 h-10 text-[#313244] mx-auto mb-2" />
              <p className="text-sm text-[#585b70]">No courses enrolled yet</p>
              <Link to="/courses" className="text-xs text-primary-400 hover:underline mt-1 block">
                Browse Courses →
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map(({ to, icon: Icon, label, desc, color }) => (
            <Link
              key={to}
              to={to}
              className={`card bg-gradient-to-br ${color} border-transparent hover:scale-105 transition-transform duration-200 cursor-pointer group`}
            >
              <Icon className="w-8 h-8 text-white mb-3" />
              <h3 className="font-semibold text-white">{label}</h3>
              <p className="text-xs text-white/70 mt-1">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
