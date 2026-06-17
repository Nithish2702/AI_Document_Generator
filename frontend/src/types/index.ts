export interface GenerateDocumentRequest {
  documentType: string
  title: string
  description: string
  context: string
  tone: 'formal' | 'casual' | 'technical'
  length: 'short' | 'medium' | 'long'
  format: 'pdf' | 'docx'
}

export interface GeneratedDocument {
  id: string
  user_id?: string
  request_text: string
  document_type: string
  title: string
  status: 'pending' | 'completed' | 'failed'
  file_path?: string
  output_format: string
  created_at: string
  generation_time_ms?: number
}

export interface GeneratedDocumentListResponse {
  documents: GeneratedDocument[]
  total: number
  page: number
  page_size: number
}

export interface Document {
  id: string
  title: string
  document_type: string
  category?: string
  content_text: string
  file_path?: string
  file_format?: string
  created_date?: string
  uploaded_date: string
  word_count?: number
  page_count?: number
  success_rating?: number
  usage_count: number
}
