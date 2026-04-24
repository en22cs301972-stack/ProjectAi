import { useState, useEffect, useRef } from 'react'
import {
  PaperAirplaneIcon, PlusIcon, TrashIcon, ChatBubbleLeftRightIcon,
  SparklesIcon, ArrowPathIcon, CodeBracketIcon,
} from '@heroicons/react/24/outline'
import { tutorAPI } from '../services/api'
import useAuthStore from '../store/authStore'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'

export default function TutorPage() {
  const { user } = useAuthStore()
  const [sessions, setSessions] = useState([])
  const [currentSession, setCurrentSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [codeContext, setCodeContext] = useState('')
  const [showCodeContext, setShowCodeContext] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    fetchSessions()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const fetchSessions = async () => {
    try {
      const res = await tutorAPI.getSessions()
      setSessions(res.data)
    } catch (err) {
      console.error(err)
    }
  }

  const fetchMessages = async (sessionId) => {
    try {
      const res = await tutorAPI.getSessionMessages(sessionId)
      setMessages(res.data)
    } catch (err) {
      toast.error('Failed to load messages')
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input, id: Date.now() + '', created_at: new Date().toISOString() }
    setMessages(prev => [...prev, userMessage])
    const sentInput = input
    setInput('')
    setLoading(true)

    try {
      const res = await tutorAPI.chat({
        content: sentInput,
        session_id: currentSession,
        code_context: codeContext || null,
        response_language: user?.response_language || 'en',
      })

      if (!currentSession) {
        setCurrentSession(res.data.session_id)
        fetchSessions()
      }

      setMessages(prev => [...prev, res.data])
    } catch (err) {
      toast.error('Failed to get AI response')
      setMessages(prev => [...prev, {
        id: Date.now() + '',
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleNewChat = () => {
    setCurrentSession(null)
    setMessages([])
    setInput('')
  }

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation()
    try {
      await tutorAPI.deleteSession(sessionId)
      if (currentSession === sessionId) handleNewChat()
      setSessions(prev => prev.filter(s => s.id !== sessionId))
      toast.success('Chat deleted')
    } catch (err) {
      toast.error('Failed to delete chat')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const suggestedQuestions = [
    'Explain recursion with an example',
    'What is Big O notation?',
    'How does async/await work in Python?',
    'Explain SQL JOIN types',
  ]

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4 animate-fade-in">
      {/* Sessions sidebar */}
      <div className="w-64 flex-shrink-0 flex flex-col bg-[#11111b] rounded-xl border border-[#313244] overflow-hidden">
        <div className="p-4 border-b border-[#313244]">
          <button
            onClick={handleNewChat}
            className="btn-primary w-full flex items-center justify-center gap-2 text-sm"
          >
            <PlusIcon className="w-4 h-4" />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map(session => (
            <div
              key={session.id}
              onClick={() => { setCurrentSession(session.id); fetchMessages(session.id) }}
              className={`group flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-colors ${
                currentSession === session.id ? 'bg-primary-600/20 text-primary-400' : 'hover:bg-[#1e1e2e] text-[#a6adc8]'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <ChatBubbleLeftRightIcon className="w-4 h-4 flex-shrink-0" />
                <span className="text-xs truncate">{session.title}</span>
              </div>
              <button
                onClick={(e) => handleDeleteSession(session.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-all"
              >
                <TrashIcon className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-h-0 bg-[#11111b] rounded-xl border border-[#313244] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-[#313244] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SparklesIcon className="w-5 h-5 text-primary-400" />
            <h2 className="font-semibold text-white">AI Tutor</h2>
            {user?.response_language === 'hinglish' && (
              <span className="badge badge-purple text-xs">Hinglish Mode</span>
            )}
          </div>
          <button
            onClick={() => setShowCodeContext(!showCodeContext)}
            className={`btn-secondary flex items-center gap-2 text-xs py-1.5 ${showCodeContext ? 'text-primary-400' : ''}`}
          >
            <CodeBracketIcon className="w-4 h-4" />
            Code Context
          </button>
        </div>

        {/* Code context panel */}
        {showCodeContext && (
          <div className="p-3 border-b border-[#313244] bg-[#0d0d17]">
            <label className="label text-xs">Paste your code here for context-aware help</label>
            <textarea
              value={codeContext}
              onChange={e => setCodeContext(e.target.value)}
              className="input h-24 text-xs font-mono resize-none"
              placeholder="Paste your code here..."
            />
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <SparklesIcon className="w-16 h-16 text-primary-400/30 mb-4" />
              <h3 className="text-lg font-medium text-[#a6adc8] mb-2">Ask me anything!</h3>
              <p className="text-sm text-[#585b70] mb-6">
                I can explain concepts, debug code, and answer your programming questions.
              </p>
              <div className="grid grid-cols-2 gap-2 w-full max-w-md">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); }}
                    className="text-left p-3 bg-[#1e1e2e] rounded-lg text-sm text-[#a6adc8] hover:bg-[#313244] hover:text-white transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' ? 'bg-primary-600' : 'bg-[#1e1e2e] border border-[#313244]'
              }`}>
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className={`max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                <div className={`px-4 py-3 rounded-xl text-sm ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white rounded-tr-none'
                    : 'bg-[#1e1e2e] border border-[#313244] rounded-tl-none'
                }`}>
                  {msg.role === 'assistant' ? (
                    <div className="markdown-content text-sm">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  )}
                </div>
                <span className="text-xs text-[#585b70] mt-1 px-1">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-[#1e1e2e] border border-[#313244] flex items-center justify-center">🤖</div>
              <div className="bg-[#1e1e2e] border border-[#313244] rounded-xl rounded-tl-none px-4 py-3">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-[#313244]">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question... (Enter to send, Shift+Enter for new line)"
              className="input flex-1 resize-none text-sm h-12 py-3"
              rows={1}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="btn-primary px-4 flex items-center justify-center"
            >
              {loading ? (
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
              ) : (
                <PaperAirplaneIcon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
