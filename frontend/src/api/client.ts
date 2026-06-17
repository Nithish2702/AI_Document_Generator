import axios, { InternalAxiosRequestConfig } from 'axios'
import { logger } from '../utils/logger'

// Extend Axios config to include metadata
declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    metadata?: {
      startTime: number
    }
  }
}

// API URL must be set in .env file
const API_URL = import.meta.env.VITE_API_URL

if (!API_URL) {
  throw new Error('VITE_API_URL must be set in .env file')
}

logger.info(`🔧 API Client initialized with base URL: ${API_URL}`)

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 180000, // 3 minutes for document generation
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const startTime = Date.now()
    config.metadata = { startTime }
    
    // Log request
    logger.apiRequest(
      config.method?.toUpperCase() || 'GET',
      config.url || '',
      config.data
    )
    
    // Add auth token if available
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    logger.error('❌ Request interceptor error', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    const duration = Date.now() - (response.config.metadata?.startTime || 0)
    
    // Log response
    logger.apiResponse(
      response.config.method?.toUpperCase() || 'GET',
      response.config.url || '',
      response.status,
      duration
    )
    
    return response
  },
  (error) => {
    const duration = Date.now() - (error.config?.metadata?.startTime || 0)
    
    // Log error
    logger.apiError(
      error.config?.method?.toUpperCase() || 'GET',
      error.config?.url || '',
      {
        status: error.response?.status,
        message: error.message,
        data: error.response?.data,
        duration
      }
    )
    
    if (error.response?.status === 401) {
      // Handle unauthorized
      logger.warn('🔒 Unauthorized - redirecting to login')
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
