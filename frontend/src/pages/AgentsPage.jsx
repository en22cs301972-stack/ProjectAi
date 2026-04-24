import { useState, useEffect } from 'react'
import {
  PlusIcon, PlayIcon, StopIcon, TrashIcon, DocumentTextIcon,
  CpuChipIcon, ArrowPathIcon, WrenchScrewdriverIcon, KeyIcon,
  CheckCircleIcon, ExclamationCircleIcon, ClockIcon,
} from '@heroicons/react/24/outline'
import { agentsAPI } from '../services/api'
import toast from 'react-hot-toast'

const STATUS_CONFIG = {
  idle: { color: 'text-[#585b70]', bg: 'bg-[#585b70]/20', label: 'Idle' },
  running: { color: 'text-green-400', bg: 'bg-green-900/20', label: 'Running' },
  stopped: { color: 'text-yellow-400', bg: 'bg-yellow-900/20', label: 'Stopped' },
  error: { color: 'text-red-400', bg: 'bg-red-900/20', label: 'Error' },
}

const AGENT_TYPES = ['custom', 'gmail', 'market', 'crypto']

export default function AgentsPage() {
  const [agents, setAgents] = useState([])
  const [availableTools, setAvailableTools] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [agentLogs, setAgentLogs] = useState([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [newAgent, setNewAgent] = useState({
    name: '', description: '', agent_type: 'custom',
    tools_enabled: [], config: {},
    api_keys: { openai_api_key: '' },
  })
  const [runTask, setRunTask] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [agentsRes, toolsRes] = await Promise.all([
        agentsAPI.list(),
        agentsAPI.getAvailableTools(),
      ])
      setAgents(agentsRes.data)
      setAvailableTools(toolsRes.data.tools || [])
    } catch (err) {
      toast.error('Failed to load agents')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAgent = async () => {
    if (!newAgent.name.trim()) {
      toast.error('Agent name is required')
      return
    }
    try {
      await agentsAPI.create(newAgent)
      toast.success('Agent created!')
      setShowCreate(false)
      setNewAgent({ name: '', description: '', agent_type: 'custom', tools_enabled: [], config: {}, api_keys: {} })
      fetchData()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create agent')
    }
  }

  const handleStartAgent = async (agentId) => {
    try {
      await agentsAPI.start(agentId, { task: runTask || 'Run default task' })
      toast.success('Agent started!')
      fetchData()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start agent')
    }
  }

  const handleStopAgent = async (agentId) => {
    try {
      await agentsAPI.stop(agentId)
      toast.success('Agent stopped')
      fetchData()
    } catch (err) {
      toast.error('Failed to stop agent')
    }
  }

  const handleDeleteAgent = async (agentId) => {
    if (!confirm('Delete this agent?')) return
    try {
      await agentsAPI.delete(agentId)
      toast.success('Agent deleted')
      if (selectedAgent?.id === agentId) setSelectedAgent(null)
      fetchData()
    } catch (err) {
      toast.error('Failed to delete agent')
    }
  }

  const handleViewLogs = async (agent) => {
    setSelectedAgent(agent)
    setLogsLoading(true)
    try {
      const res = await agentsAPI.getLogs(agent.id)
      setAgentLogs(res.data)
    } catch (err) {
      toast.error('Failed to load logs')
    } finally {
      setLogsLoading(false)
    }
  }

  const toggleTool = (toolName) => {
    setNewAgent(prev => ({
      ...prev,
      tools_enabled: prev.tools_enabled.includes(toolName)
        ? prev.tools_enabled.filter(t => t !== toolName)
        : [...prev.tools_enabled, toolName],
    }))
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Agents</h1>
          <p className="text-sm text-[#585b70] mt-1">Create and manage autonomous AI agents</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="w-5 h-5" />
          New Agent
        </button>
      </div>

      {/* Available Tools */}
      <div className="card">
        <h2 className="text-sm font-semibold text-[#a6adc8] mb-3 flex items-center gap-2">
          <WrenchScrewdriverIcon className="w-4 h-4" />
          Available MCP Tools
        </h2>
        <div className="flex flex-wrap gap-2">
          {availableTools.map(tool => (
            <div key={tool.name} className="badge badge-info">
              {tool.name}
            </div>
          ))}
          {availableTools.length === 0 && (
            <p className="text-sm text-[#585b70]">Configure API keys in agent settings to enable tools</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agents List */}
        <div className="space-y-4">
          {loading ? (
            [1, 2].map(i => <div key={i} className="card animate-pulse h-40" />)
          ) : agents.length === 0 ? (
            <div className="card text-center py-12">
              <CpuChipIcon className="w-12 h-12 text-[#313244] mx-auto mb-3" />
              <p className="text-[#a6adc8] font-medium">No agents yet</p>
              <p className="text-sm text-[#585b70] mt-1">Create your first AI agent</p>
            </div>
          ) : (
            agents.map(agent => {
              const statusConf = STATUS_CONFIG[agent.status] || STATUS_CONFIG.idle
              return (
                <div
                  key={agent.id}
                  className={`card border-2 transition-all ${selectedAgent?.id === agent.id ? 'border-primary-600/50' : 'border-transparent'}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-white">{agent.name}</h3>
                        <span className={`badge text-xs ${statusConf.bg} ${statusConf.color}`}>
                          {agent.status === 'running' && <span className="w-1.5 h-1.5 bg-green-400 rounded-full mr-1 animate-pulse inline-block" />}
                          {statusConf.label}
                        </span>
                      </div>
                      <p className="text-sm text-[#585b70] mt-1">{agent.description || 'No description'}</p>
                    </div>
                    <span className="badge badge-purple text-xs">{agent.agent_type}</span>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-[#585b70] mb-3">
                    <ClockIcon className="w-3.5 h-3.5" />
                    {agent.total_runs} runs
                    {agent.last_run_at && (
                      <span>· Last: {new Date(agent.last_run_at).toLocaleDateString()}</span>
                    )}
                  </div>

                  {agent.tools_enabled?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {agent.tools_enabled.map(t => (
                        <span key={t} className="badge badge-info text-xs">{t}</span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-2 mt-2">
                    {agent.status !== 'running' ? (
                      <button
                        onClick={() => handleStartAgent(agent.id)}
                        className="btn-success flex items-center gap-1 text-xs py-1.5 px-3"
                      >
                        <PlayIcon className="w-3.5 h-3.5" />
                        Start
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStopAgent(agent.id)}
                        className="btn-danger flex items-center gap-1 text-xs py-1.5 px-3"
                      >
                        <StopIcon className="w-3.5 h-3.5" />
                        Stop
                      </button>
                    )}
                    <button
                      onClick={() => handleViewLogs(agent)}
                      className="btn-secondary flex items-center gap-1 text-xs py-1.5 px-3"
                    >
                      <DocumentTextIcon className="w-3.5 h-3.5" />
                      Logs
                    </button>
                    <button
                      onClick={() => handleDeleteAgent(agent.id)}
                      className="ml-auto text-[#585b70] hover:text-red-400 transition-colors p-1.5"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Logs / Create Panel */}
        <div>
          {showCreate ? (
            <div className="card">
              <h2 className="text-lg font-semibold text-white mb-4">Create Agent</h2>
              <div className="space-y-4">
                <div>
                  <label className="label">Agent Name *</label>
                  <input
                    type="text"
                    value={newAgent.name}
                    onChange={e => setNewAgent(p => ({ ...p, name: e.target.value }))}
                    className="input"
                    placeholder="My Gmail Agent"
                  />
                </div>
                <div>
                  <label className="label">Description</label>
                  <input
                    type="text"
                    value={newAgent.description}
                    onChange={e => setNewAgent(p => ({ ...p, description: e.target.value }))}
                    className="input"
                    placeholder="What does this agent do?"
                  />
                </div>
                <div>
                  <label className="label">Agent Type</label>
                  <select
                    value={newAgent.agent_type}
                    onChange={e => setNewAgent(p => ({ ...p, agent_type: e.target.value }))}
                    className="input"
                  >
                    {AGENT_TYPES.map(t => (
                      <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label flex items-center gap-1">
                    <KeyIcon className="w-4 h-4" />
                    API Keys (encrypted)
                  </label>
                  <input
                    type="password"
                    placeholder="OpenAI API Key"
                    onChange={e => setNewAgent(p => ({ ...p, api_keys: { ...p.api_keys, openai_api_key: e.target.value } }))}
                    className="input mb-2 text-sm"
                  />
                  <input
                    type="password"
                    placeholder="Gmail Credentials JSON (optional)"
                    onChange={e => setNewAgent(p => ({ ...p, api_keys: { ...p.api_keys, gmail_credentials: e.target.value } }))}
                    className="input text-sm"
                  />
                </div>

                <div>
                  <label className="label">Enable Tools</label>
                  <div className="flex flex-wrap gap-2">
                    {availableTools.map(tool => (
                      <button
                        key={tool.name}
                        onClick={() => toggleTool(tool.name)}
                        className={`badge cursor-pointer transition-colors ${
                          newAgent.tools_enabled.includes(tool.name)
                            ? 'badge-success'
                            : 'badge-info'
                        }`}
                      >
                        {tool.name}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 mt-4">
                  <button onClick={handleCreateAgent} className="btn-primary flex-1">
                    Create Agent
                  </button>
                  <button onClick={() => setShowCreate(false)} className="btn-secondary">
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          ) : selectedAgent ? (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <DocumentTextIcon className="w-5 h-5 text-primary-400" />
                  {selectedAgent.name} Logs
                </h2>
                <button
                  onClick={() => handleViewLogs(selectedAgent)}
                  className="p-1.5 hover:bg-[#1e1e2e] rounded-lg"
                >
                  <ArrowPathIcon className="w-4 h-4 text-[#585b70]" />
                </button>
              </div>

              {/* Run task input */}
              <div className="mb-4">
                <label className="label text-xs">Task (optional)</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={runTask}
                    onChange={e => setRunTask(e.target.value)}
                    placeholder="Describe what the agent should do..."
                    className="input text-sm flex-1"
                  />
                  <button
                    onClick={() => handleStartAgent(selectedAgent.id)}
                    className="btn-primary text-sm px-3"
                  >
                    <PlayIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-2 max-h-80 overflow-y-auto">
                {logsLoading ? (
                  <div className="flex justify-center py-8">
                    <ArrowPathIcon className="w-6 h-6 animate-spin text-primary-400" />
                  </div>
                ) : agentLogs.length === 0 ? (
                  <div className="text-center py-8 text-[#585b70]">
                    <DocumentTextIcon className="w-10 h-10 mx-auto mb-2" />
                    <p className="text-sm">No logs yet. Start the agent to see activity.</p>
                  </div>
                ) : (
                  agentLogs.map(log => (
                    <div
                      key={log.id}
                      className={`flex gap-2 p-2 rounded-lg text-xs ${
                        log.level === 'error' ? 'bg-red-900/20 text-red-400' :
                        log.level === 'warning' ? 'bg-yellow-900/20 text-yellow-400' :
                        'bg-[#1e1e2e] text-[#a6adc8]'
                      }`}
                    >
                      {log.level === 'error' ? <ExclamationCircleIcon className="w-3.5 h-3.5 flex-shrink-0" /> :
                       <CheckCircleIcon className="w-3.5 h-3.5 flex-shrink-0" />}
                      <div>
                        <span className="text-[#585b70] mr-2">{new Date(log.created_at).toLocaleTimeString()}</span>
                        {log.message}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="card text-center py-16">
              <CpuChipIcon className="w-12 h-12 text-[#313244] mx-auto mb-3" />
              <p className="text-[#a6adc8]">Select an agent to view logs</p>
              <p className="text-sm text-[#585b70] mt-1">or create a new agent</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
