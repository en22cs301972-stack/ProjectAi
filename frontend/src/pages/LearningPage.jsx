import { useState, useCallback } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { java } from '@codemirror/lang-java'
import { sql } from '@codemirror/lang-sql'
import { oneDark } from '@codemirror/theme-one-dark'
import {
  PlayIcon, BugAntIcon, LightBulbIcon, ArrowPathIcon,
  ChevronDownIcon, ClockIcon, CheckCircleIcon, XCircleIcon,
} from '@heroicons/react/24/outline'
import { learningAPI } from '../services/api'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'

const LANGUAGE_STARTERS = {
  python: `# Python Code Editor
# Write your code here

def solve():
    # Your solution here
    pass

# Test your solution
result = solve()
print(result)
`,
  java: `// Java Code Editor
public class Main {
    public static void main(String[] args) {
        // Your code here
        System.out.println("Hello, World!");
    }
}
`,
  sql: `-- SQL Code Editor
-- Write your SQL queries here

SELECT 'Hello, World!' AS greeting;
`,
}

const getLanguageExtension = (lang) => {
  switch (lang) {
    case 'python': return python()
    case 'java': return java()
    case 'sql': return sql()
    default: return python()
  }
}

export default function LearningPage() {
  const [language, setLanguage] = useState('python')
  const [code, setCode] = useState(LANGUAGE_STARTERS.python)
  const [output, setOutput] = useState(null)
  const [aiDebug, setAiDebug] = useState(null)
  const [loading, setLoading] = useState(false)
  const [debugLoading, setDebugLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('output')
  const [stdin, setStdin] = useState('')

  const handleLanguageChange = (lang) => {
    setLanguage(lang)
    setCode(LANGUAGE_STARTERS[lang])
    setOutput(null)
    setAiDebug(null)
  }

  const handleRunCode = async () => {
    setLoading(true)
    setOutput(null)
    setActiveTab('output')
    try {
      const res = await learningAPI.executeCode({
        code,
        language,
        stdin: stdin || null,
      })
      setOutput(res.data)
      if (res.data.status === 'success') {
        toast.success('Code executed successfully!')
      } else if (res.data.status === 'runtime_error') {
        toast.error('Runtime error detected')
        // Auto-debug if error
        if (res.data.error) {
          handleDebugCode(res.data.error)
        }
      }
    } catch (err) {
      toast.error('Failed to execute code')
      setOutput({ status: 'error', error: err.response?.data?.detail || 'Execution failed' })
    } finally {
      setLoading(false)
    }
  }

  const handleDebugCode = async (errorMsg = null) => {
    const error = errorMsg || output?.error
    if (!error) {
      toast.error('No error to debug. Run your code first.')
      return
    }
    setDebugLoading(true)
    setActiveTab('debug')
    try {
      const res = await learningAPI.debugCode({
        code,
        language,
        error_message: error,
      })
      setAiDebug(res.data)
    } catch (err) {
      toast.error('Failed to get debug info')
    } finally {
      setDebugLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      success: 'badge-success',
      accepted: 'badge-success',
      runtime_error: 'badge-error',
      compile_error: 'badge-error',
      timeout: 'badge-warning',
      wrong_answer: 'badge-warning',
      error: 'badge-error',
    }
    return badges[status] || 'badge-info'
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col gap-4 animate-fade-in">
      {/* Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-white">Code Editor</h1>
          {/* Language selector */}
          <div className="flex bg-[#1e1e2e] rounded-lg p-1 gap-1">
            {['python', 'java', 'sql'].map((lang) => (
              <button
                key={lang}
                onClick={() => handleLanguageChange(lang)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                  language === lang
                    ? 'bg-primary-600 text-white'
                    : 'text-[#a6adc8] hover:text-white'
                }`}
              >
                {lang.charAt(0).toUpperCase() + lang.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCode(LANGUAGE_STARTERS[language])}
            className="btn-secondary flex items-center gap-2 text-sm py-2"
          >
            <ArrowPathIcon className="w-4 h-4" />
            Reset
          </button>
          <button
            onClick={() => handleDebugCode()}
            disabled={debugLoading || !output?.error}
            className="btn-secondary flex items-center gap-2 text-sm py-2"
          >
            <BugAntIcon className="w-4 h-4" />
            AI Debug
          </button>
          <button
            onClick={handleRunCode}
            disabled={loading}
            className="btn-primary flex items-center gap-2 text-sm py-2"
          >
            {loading ? (
              <ArrowPathIcon className="w-4 h-4 animate-spin" />
            ) : (
              <PlayIcon className="w-4 h-4" />
            )}
            Run Code
          </button>
        </div>
      </div>

      {/* Editor + Output */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
        {/* Editor */}
        <div className="flex flex-col min-h-0">
          <div className="flex items-center justify-between px-3 py-2 bg-[#181825] border border-[#313244] rounded-t-lg">
            <span className="text-sm font-medium text-[#a6adc8]">solution.{language === 'java' ? 'java' : language === 'sql' ? 'sql' : 'py'}</span>
            <span className="text-xs text-[#585b70]">{code.split('\n').length} lines</span>
          </div>
          <div className="flex-1 overflow-hidden rounded-b-lg border border-t-0 border-[#313244]">
            <CodeMirror
              value={code}
              height="100%"
              theme={oneDark}
              extensions={[getLanguageExtension(language)]}
              onChange={setCode}
              className="h-full text-sm"
              basicSetup={{
                lineNumbers: true,
                highlightActiveLineGutter: true,
                highlightSpecialChars: true,
                history: true,
                foldGutter: true,
                drawSelection: true,
                dropCursor: true,
                allowMultipleSelections: true,
                indentOnInput: true,
                syntaxHighlighting: true,
                bracketMatching: true,
                closeBrackets: true,
                autocompletion: true,
              }}
            />
          </div>

          {/* Stdin */}
          <div className="mt-2">
            <label className="label text-xs">Standard Input (stdin)</label>
            <textarea
              value={stdin}
              onChange={(e) => setStdin(e.target.value)}
              className="input text-sm h-16 resize-none font-mono text-xs"
              placeholder="Enter input for your program..."
            />
          </div>
        </div>

        {/* Output Panel */}
        <div className="flex flex-col min-h-0">
          {/* Tabs */}
          <div className="flex bg-[#181825] border border-[#313244] rounded-t-lg">
            {[
              { id: 'output', label: 'Output', icon: PlayIcon },
              { id: 'debug', label: 'AI Debug', icon: BugAntIcon },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                  activeTab === id
                    ? 'text-white border-b-2 border-primary-500'
                    : 'text-[#585b70] hover:text-[#a6adc8]'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          <div className="flex-1 bg-[#11111b] border border-t-0 border-[#313244] rounded-b-lg p-4 overflow-auto font-mono text-sm">
            {activeTab === 'output' && (
              <div>
                {!output ? (
                  <div className="flex flex-col items-center justify-center h-32 text-[#585b70]">
                    <PlayIcon className="w-10 h-10 mb-2" />
                    <p>Run your code to see output</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className={`badge ${getStatusBadge(output.status)}`}>
                        {output.status?.replace('_', ' ').toUpperCase()}
                      </span>
                      {output.execution_time && (
                        <span className="text-xs text-[#585b70] flex items-center gap-1">
                          <ClockIcon className="w-3 h-3" />
                          {output.execution_time}s
                        </span>
                      )}
                    </div>

                    {output.output && (
                      <div>
                        <p className="text-xs text-[#585b70] mb-1">Output:</p>
                        <pre className="text-green-400 whitespace-pre-wrap">{output.output}</pre>
                      </div>
                    )}

                    {output.error && (
                      <div>
                        <p className="text-xs text-[#585b70] mb-1">Error:</p>
                        <pre className="text-red-400 whitespace-pre-wrap">{output.error}</pre>
                      </div>
                    )}

                    {output.test_results && (
                      <div>
                        <p className="text-xs text-[#585b70] mb-2">Test Results:</p>
                        <div className="space-y-1">
                          {output.test_results.map((test, i) => (
                            <div key={i} className={`flex items-center gap-2 text-xs p-2 rounded ${test.passed ? 'bg-green-900/20 text-green-400' : 'bg-red-900/20 text-red-400'}`}>
                              {test.passed ? <CheckCircleIcon className="w-4 h-4" /> : <XCircleIcon className="w-4 h-4" />}
                              Test {test.test_case}: {test.passed ? 'Passed' : `Failed (got: ${test.actual}, expected: ${test.expected})`}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {output.ai_feedback && (
                      <div className="mt-3 p-3 bg-[#1e1e2e] rounded-lg">
                        <p className="text-xs text-primary-400 mb-2 flex items-center gap-1">
                          <LightBulbIcon className="w-4 h-4" /> AI Feedback
                        </p>
                        <div className="markdown-content text-xs">
                          <ReactMarkdown>{output.ai_feedback}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'debug' && (
              <div>
                {debugLoading ? (
                  <div className="flex flex-col items-center justify-center h-32 text-[#585b70]">
                    <ArrowPathIcon className="w-8 h-8 animate-spin mb-2 text-primary-400" />
                    <p>AI is analyzing your code...</p>
                  </div>
                ) : !aiDebug ? (
                  <div className="flex flex-col items-center justify-center h-32 text-[#585b70]">
                    <BugAntIcon className="w-10 h-10 mb-2" />
                    <p>Run code with an error to get AI debug help</p>
                  </div>
                ) : (
                  <div className="space-y-4 text-xs">
                    {/* Explanation */}
                    <div>
                      <p className="text-primary-400 font-medium mb-1">🔍 Error Explanation</p>
                      <p className="text-[#cdd6f4]">{aiDebug.explanation}</p>
                    </div>

                    {/* Line fixes */}
                    {aiDebug.line_fixes?.length > 0 && (
                      <div>
                        <p className="text-yellow-400 font-medium mb-2">🛠 Line-by-Line Fixes</p>
                        <div className="space-y-2">
                          {aiDebug.line_fixes.map((fix, i) => (
                            <div key={i} className="bg-[#1e1e2e] p-2 rounded">
                              <p className="text-[#585b70]">Line {fix.line_number}: {fix.issue}</p>
                              <p className="text-green-400 mt-1">Fix: {fix.fix}</p>
                              {fix.fixed_code && (
                                <code className="block mt-1 text-blue-400">{fix.fixed_code}</code>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Suggestions */}
                    {aiDebug.suggestions?.length > 0 && (
                      <div>
                        <p className="text-green-400 font-medium mb-1">💡 Suggestions</p>
                        <ul className="space-y-1">
                          {aiDebug.suggestions.map((s, i) => (
                            <li key={i} className="text-[#a6adc8]">• {s}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Optimized code */}
                    {aiDebug.optimized_code && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-blue-400 font-medium">✨ Optimized Code</p>
                          <button
                            onClick={() => setCode(aiDebug.optimized_code)}
                            className="text-xs text-primary-400 hover:underline"
                          >
                            Apply Fix
                          </button>
                        </div>
                        <pre className="bg-[#1e1e2e] p-2 rounded overflow-x-auto text-green-300">
                          {aiDebug.optimized_code}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
