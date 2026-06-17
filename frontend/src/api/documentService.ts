import apiClient from './client'
import { logger } from '../utils/logger'
import type { GenerateDocumentRequest, GeneratedDocument, GeneratedDocumentListResponse } from '../types'

export const documentService = {
  // Chat with AI
  chat: async (message: string, conversationHistory?: any[]): Promise<any> => {
    logger.info('💬 Sending chat message...', { message: message.substring(0, 50) })
    const response = await apiClient.post('/api/documents/chat', {
      message,
      conversation_history: conversationHistory
    })
    logger.success('✅ Chat response received')
    return response.data
  },

  // Analyze user request for document generation
  analyzeRequest: async (message: string, conversationHistory?: any[]): Promise<any> => {
    logger.info('🔍 Analyzing request...', { message: message.substring(0, 50) })
    const response = await apiClient.post('/api/documents/analyze', {
      message,
      conversation_history: conversationHistory
    })
    logger.success('✅ Analysis complete')
    return response.data
  },

  // Generate new document
  generateDocument: async (request: GenerateDocumentRequest): Promise<GeneratedDocument> => {
    logger.info('🤖 Generating document...', { title: request.title, type: request.document_type })
    const response = await apiClient.post('/api/documents/generate', request, {
      timeout: 300000, // 5 minutes for document generation
    })
    logger.success('✅ Document generated successfully', { id: response.data.id })
    return response.data
  },

  // Get all generated documents
  getGeneratedDocuments: async (skip = 0, limit = 20): Promise<GeneratedDocumentListResponse> => {
    logger.info(`📋 Fetching generated documents (skip: ${skip}, limit: ${limit})`)
    const response = await apiClient.get('/api/documents/generated/list', {
      params: { skip, limit },
    })
    logger.success(`✅ Fetched ${response.data.documents.length} documents`)
    return response.data
  },

  // Get single generated document
  getGeneratedDocument: async (id: string): Promise<GeneratedDocument> => {
    logger.info(`📄 Fetching document: ${id}`)
    const response = await apiClient.get(`/api/documents/generated/${id}`)
    logger.success(`✅ Document fetched: ${response.data.title}`)
    return response.data
  },

  // Download document
  downloadDocument: async (id: string, format?: 'docx' | 'pdf'): Promise<Blob> => {
    logger.info(`⬇️  Downloading document: ${id} (format: ${format || 'original'})`)
    const params = format ? { format } : {}
    const response = await apiClient.get(`/api/documents/generated/${id}/download`, {
      responseType: 'blob',
      params,
    })
    logger.success(`✅ Document downloaded (${response.data.size} bytes)`)
    return response.data
  },

  // Delete generated document
  deleteDocument: async (id: string): Promise<void> => {
    logger.info(`🗑️  Deleting document: ${id}`)
    await apiClient.delete(`/api/documents/generated/${id}`)
    logger.success(`✅ Document deleted`)
  },

  // Upload source document
  uploadDocument: async (file: File, documentType: string, category?: string): Promise<any> => {
    logger.info(`📤 Uploading document: ${file.name} (${file.size} bytes)`)
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: {
        document_type: documentType,
        category,
      },
    })
    logger.success(`✅ Document uploaded: ${response.data.title}`)
    return response.data
  },

  // Update document content
  updateDocumentContent: async (id: string, content: string): Promise<any> => {
    logger.info(`📝 Updating document content: ${id}`)
    const response = await apiClient.put(`/api/documents/generated/${id}`, {
      generated_content: content
    })
    logger.success(`✅ Document content updated`)
    return response.data
  },
}
