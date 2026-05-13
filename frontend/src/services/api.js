import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

export const osintProfile = (query, queryType) =>
  api.post('/osint/profile', { query, query_type: queryType }).then(r => r.data)

export const cryptoTrace = (address, chain) =>
  api.post('/crypto/trace', { address, chain }).then(r => r.data)

export const packageFraudCase = (caseData) =>
  api.post('/fraud/package', caseData).then(r => r.data)

export const addMonitorTarget = (keyword, keywordType, clientId) =>
  api.post('/darkweb/monitor', { keyword, keyword_type: keywordType, client_id: clientId }).then(r => r.data)

export const getAlerts = (clientId) =>
  api.get(`/darkweb/alerts/${clientId}`).then(r => r.data)

export const scanDeedFraud = (propertyAddress, ownerName, county, state) =>
  api.post('/deed/scan', { property_address: propertyAddress, owner_name: ownerName, county, state }).then(r => r.data)

export const scoreReputation = (value, valueType) =>
  api.post('/reputation/score', { value, value_type: valueType }).then(r => r.data)

export const healthCheck = () =>
  api.get('/health').then(r => r.data)
