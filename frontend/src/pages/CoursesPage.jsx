import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { AcademicCapIcon, ClockIcon, ChevronRightIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { coursesAPI } from '../services/api'
import toast from 'react-hot-toast'

const LEVEL_COLORS = {
  beginner: 'badge-success',
  intermediate: 'badge-warning',
  advanced: 'badge-error',
}

const LANG_COLORS = {
  python: 'bg-blue-900/30 text-blue-400',
  java: 'bg-orange-900/30 text-orange-400',
  sql: 'bg-purple-900/30 text-purple-400',
}

export default function CoursesPage() {
  const [courses, setCourses] = useState([])
  const [enrollments, setEnrollments] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ level: '', language: '' })
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetchData()
  }, [filter])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [coursesRes, enrollRes] = await Promise.all([
        coursesAPI.list(filter),
        coursesAPI.getEnrollments(),
      ])
      setCourses(coursesRes.data)
      setEnrollments(enrollRes.data)
    } catch (err) {
      toast.error('Failed to load courses')
    } finally {
      setLoading(false)
    }
  }

  const handleEnroll = async (courseId) => {
    try {
      await coursesAPI.enroll(courseId)
      toast.success('Enrolled successfully!')
      fetchData()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to enroll')
    }
  }

  const getEnrollment = (courseId) =>
    enrollments.find(e => e.course_id === courseId)

  const filteredCourses = courses.filter(c =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.description.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-white">Courses</h1>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#585b70]" />
            <input
              type="text"
              placeholder="Search courses..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-9 w-48 text-sm py-2"
            />
          </div>
          {/* Level filter */}
          <select
            value={filter.level}
            onChange={e => setFilter(f => ({ ...f, level: e.target.value }))}
            className="input w-36 text-sm py-2"
          >
            <option value="">All Levels</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          {/* Language filter */}
          <select
            value={filter.language}
            onChange={e => setFilter(f => ({ ...f, language: e.target.value }))}
            className="input w-36 text-sm py-2"
          >
            <option value="">All Languages</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="sql">SQL</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-[#313244] rounded w-3/4 mb-3" />
              <div className="h-3 bg-[#313244] rounded w-full mb-2" />
              <div className="h-3 bg-[#313244] rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : filteredCourses.length === 0 ? (
        <div className="card text-center py-16">
          <AcademicCapIcon className="w-16 h-16 text-[#313244] mx-auto mb-4" />
          <h3 className="text-lg font-medium text-[#a6adc8]">No courses found</h3>
          <p className="text-[#585b70] mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map(course => {
            const enrollment = getEnrollment(course.id)
            return (
              <div key={course.id} className="card hover:border-primary-600/50 transition-all duration-200 flex flex-col">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`badge ${LEVEL_COLORS[course.level] || 'badge-info'}`}>
                      {course.level}
                    </span>
                    <span className={`badge ${LANG_COLORS[course.language] || 'badge-info'}`}>
                      {course.language}
                    </span>
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-white mb-2 line-clamp-2">{course.title}</h3>
                <p className="text-sm text-[#a6adc8] mb-4 line-clamp-3 flex-1">{course.description}</p>

                {/* Meta */}
                <div className="flex items-center gap-3 text-xs text-[#585b70] mb-4">
                  {course.total_duration > 0 && (
                    <span className="flex items-center gap-1">
                      <ClockIcon className="w-3 h-3" />
                      {course.total_duration} mins
                    </span>
                  )}
                </div>

                {/* Progress */}
                {enrollment && (
                  <div className="mb-4">
                    <div className="flex justify-between text-xs text-[#585b70] mb-1">
                      <span>Progress</span>
                      <span>{Math.round(enrollment.progress)}%</span>
                    </div>
                    <div className="w-full bg-[#313244] rounded-full h-1.5">
                      <div
                        className="bg-primary-500 h-1.5 rounded-full"
                        style={{ width: `${enrollment.progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Action */}
                {enrollment ? (
                  <Link
                    to={`/courses/${course.id}`}
                    className="btn-primary text-center text-sm flex items-center justify-center gap-2"
                  >
                    Continue Learning
                    <ChevronRightIcon className="w-4 h-4" />
                  </Link>
                ) : (
                  <button
                    onClick={() => handleEnroll(course.id)}
                    className="btn-secondary text-sm w-full"
                  >
                    Enroll Now
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
