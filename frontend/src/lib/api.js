const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), options.timeout || 30000)
  try {
    const response = await fetch(`${API_URL}${path}`, { ...options, signal: controller.signal })
    const text = await response.text()
    let data
    try { data = text ? JSON.parse(text) : {} } catch { data = { detail: text } }
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`)
    return data
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The local service took too long to respond.')
    if (error instanceof TypeError) throw new Error('Backend is offline. Start the local FastAPI service and try again.')
    throw error
  } finally { clearTimeout(timer) }
}

const json = (path, body, options = {}) => request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), ...options })
const form = (path, data, options = {}) => { const body = new FormData(); Object.entries(data).forEach(([key, value]) => { if (value !== undefined && value !== null) body.append(key, value) }); return request(path, { method: 'POST', body, ...options }) }

export const api = {
  url: API_URL,
  health: () => request('/health', { timeout: 5000 }),
  status: () => request('/system/status', { timeout: 5000 }),
  documents: () => request('/documents'),
  document: (id) => request(`/documents/${id}`),
  uploadDocument: (file) => form('/documents/upload', { file }, { timeout: 180000 }),
  deleteDocument: (id) => request(`/documents/${id}`, { method: 'DELETE' }),
  reindexDocument: (id) => json(`/documents/${id}/index`, {}),
  chat: (message, conversation = []) => json('/chat', { message, conversation }, { timeout: 180000 }),
  vision: (file, machineId) => form('/vision/analyze', { file, machine_id: machineId }, { timeout: 180000 }),
  maintenance: (body) => json('/maintenance/analyze', body, { timeout: 180000 }),
  failure: (body) => json('/failure/analyze', body, { timeout: 180000 }),
  safety: (body) => json('/safety/analyze', body, { timeout: 180000 }),
  analytics: (file, machineId) => form('/analytics/analyze', { file, machine_id: machineId }, { timeout: 60000 }),
  reports: () => request('/reports'),
  generateReport: (body) => json('/reports/generate', body, { timeout: 180000 }),
  agents: () => request('/agents'),
  audit: () => request('/audit-logs'),
  knowledge: () => request('/knowledge'),
  createTask: (data) => form('/api/tasks', data, { timeout: 180000 }),
  taskStatus: (id) => request(`/api/tasks/${id}`),
  taskEvents: (id) => request(`/api/tasks/${id}/events`),
  taskResult: (id) => request(`/api/tasks/${id}/result`),
  securityStatus: () => request('/api/security/status'),
  sampleReportUrl: `${API_URL}/api/demo/sample-report`,
}

