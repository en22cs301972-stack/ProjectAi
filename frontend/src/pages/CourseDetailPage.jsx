import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { coursesAPI } from '../services/api'
import { AcademicCapIcon, TrophyIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function CourseDetailPage() {
  const { id } = useParams()
  const [course, setCourse] = useState(null)
  const [enrollment, setEnrollment] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCourse()
  }, [id])

  const fetchCourse = async () => {
    try {
      const [courseRes, enrollRes] = await Promise.all([
        coursesAPI.get(id),
        coursesAPI.getEnrollments(),
      ])
      setCourse(courseRes.data)
      const enroll = enrollRes.data.find(e => e.course_id === id)
      setEnrollment(enroll)
    } catch (err) {
      toast.error('Failed to load course')
    } finally {
      setLoading(false)
    }
  }

  const handleMarkComplete = async (lessonId) => {
    try {
      const res = await coursesAPI.updateProgress(id, lessonId)
      setEnrollment(prev => ({
        ...prev,
        ...res.data,
      }))
      toast.success('Lesson completed!')
      if (res.data.is_completed) {
        toast.success('🎉 Course completed! Certificate being generated...', { duration: 5000 })
      }
    } catch (err) {
      toast.error('Failed to update progress')
    }
  }

  const handleDownloadCert = async (certId) => {
    try {
      const res = await coursesAPI.downloadCertificate(certId)
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `certificate.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error('Failed to download certificate')
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!course) return (
    <div className="card text-center py-16">
      <p className="text-[#a6adc8]">Course not found</p>
    </div>
  )

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Header */}
      <div className="card bg-gradient-to-r from-primary-900/40 to-purple-900/20 border-primary-800/30">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="badge badge-info">{course.level}</span>
              <span className="badge badge-purple">{course.language}</span>
            </div>
            <h1 className="text-2xl font-bold text-white">{course.title}</h1>
            <p className="text-[#a6adc8] mt-2">{course.description}</p>
          </div>
          <AcademicCapIcon className="w-12 h-12 text-primary-400 flex-shrink-0" />
        </div>

        {enrollment && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-[#a6adc8] mb-2">
              <span>Progress</span>
              <span>{Math.round(enrollment.progress)}%</span>
            </div>
            <div className="w-full bg-[#313244] rounded-full h-2">
              <div
                className="bg-primary-500 h-2 rounded-full transition-all"
                style={{ width: `${enrollment.progress}%` }}
              />
            </div>
            {enrollment.is_completed && (
              <div className="flex items-center gap-2 mt-3">
                <TrophyIcon className="w-5 h-5 text-yellow-400" />
                <span className="text-yellow-400 font-medium">Course Completed!</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sample lesson list (since modules come from API) */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Course Content</h2>
        <div className="space-y-2">
          {['Introduction', 'Getting Started', 'Core Concepts', 'Advanced Topics', 'Final Project'].map((lesson, i) => {
            const lessonId = `lesson-${i}`
            const completed = enrollment?.completed_lessons?.includes(lessonId)
            return (
              <div
                key={lessonId}
                className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                  completed ? 'bg-green-900/20 border-green-800/30' : 'bg-[#1e1e2e] border-[#313244]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    completed ? 'bg-green-600 text-white' : 'bg-[#313244] text-[#585b70]'
                  }`}>
                    {completed ? '✓' : i + 1}
                  </div>
                  <span className={`font-medium ${completed ? 'text-green-400' : 'text-white'}`}>
                    {lesson}
                  </span>
                </div>
                {enrollment && !completed && (
                  <button
                    onClick={() => handleMarkComplete(lessonId)}
                    className="btn-primary text-xs py-1 px-3"
                  >
                    Mark Complete
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
