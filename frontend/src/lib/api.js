import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export const servers = {
  list: () => api.get('/servers/'),
  get: (id) => api.get(`/servers/${id}`),
  create: (data) => api.post('/servers/', data),
  update: (id, data) => api.put(`/servers/${id}`, data),
  remove: (id) => api.delete(`/servers/${id}`),
  status: (id) => api.get(`/servers/${id}/status`),
}

export const sessions = {
  list: (serverId) => api.get(`/servers/${serverId}/sessions`),
  create: (serverId, data) => api.post(`/servers/${serverId}/sessions`, data),
  get: (id) => api.get(`/sessions/${id}`),
  update: (id, data) => api.put(`/sessions/${id}`, data),
  remove: (id) => api.delete(`/sessions/${id}`),
  end: (id) => api.post(`/sessions/${id}/end`),
}

export const commands = {
  list: (sessionId) => api.get(`/sessions/${sessionId}/commands`),
  create: (data) => api.post('/commands', data),
  approve: (id) => api.post(`/commands/${id}/approve`),
  deny: (id) => api.post(`/commands/${id}/deny`),
  edit: (id, data) => api.post(`/commands/${id}/edit`, data),
  reexecute: (id) => api.post(`/commands/${id}/reexecute`),
  allowSession: (id) => api.post(`/commands/${id}/allow-session`),
}

export const chat = {
  getMessages: (sessionId) => api.get(`/sessions/${sessionId}/messages`),
  sendMessage: (sessionId, data) => api.post(`/sessions/${sessionId}/messages`, data),
}

export const memories = {
  list: (serverId) => api.get(`/servers/${serverId}/memories`),
  create: (serverId, data) => api.post(`/servers/${serverId}/memories`, data),
  update: (id, data) => api.put(`/memories/${id}`, data),
  remove: (id) => api.delete(`/memories/${id}`),
  approve: (id) => api.post(`/memories/${id}/approve`),
  reject: (id) => api.post(`/memories/${id}/reject`),
  batchApprove: (ids) => api.post('/memories/batch-approve', ids),
}

export const permissions = {
  list: () => api.get('/permissions/'),
  create: (data) => api.post('/permissions/', data),
  update: (id, data) => api.put(`/permissions/${id}`, data),
  remove: (id) => api.delete(`/permissions/${id}`),
  check: (command, serverId, sessionId) => api.get('/permissions/check', { params: { command, server_id: serverId, session_id: sessionId } }),
}

export const agents = {
  list: () => api.get('/agents/'),
  create: (data) => api.post('/agents/', data),
  update: (id, data) => api.put(`/agents/${id}`, data),
  remove: (id) => api.delete(`/agents/${id}`),
  models: (name) => api.get(`/agents/${name}/models`),
}

export const settings = {
  getDangerMode: (sessionId) => api.get('/settings/danger-mode', { params: { session_id: sessionId } }),
  setDangerMode: (enabled, sessionId) => api.put('/settings/danger-mode', { enabled }, { params: { session_id: sessionId } }),
}

export const acp = {
  status: () => api.get('/acp/status'),
  invokeTool: (toolName, payload) => api.post(`/acp/tools/${toolName}`, payload),
}

export default api
