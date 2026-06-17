import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentService } from '../api/documentService'
import DocumentPreview from '../components/DocumentPreview'

export default function DocumentViewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', id],
    queryFn: () => documentService.getGeneratedDocument(id!),
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => documentService.deleteDocument(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['generated-documents'] })
      navigate('/documents')
    },
  })

  const handleDownload = async () => {
    try {
      const blob = await documentService.downloadDocument(id!)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${document?.title}.${document?.output_format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert('Error downloading document')
    }
  }

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate()
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-700">Document not found</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{document.title}</h2>
              <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                <span className="inline-block px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded">
                  {document.document_type}
                </span>
                <span>{new Date(document.created_at).toLocaleString()}</span>
                {document.generation_time_ms && (
                  <span>Generated in {(document.generation_time_ms / 1000).toFixed(1)}s</span>
                )}
              </div>
            </div>
            <span
              className={`inline-block px-3 py-1 text-sm font-semibold rounded ${
                document.status === 'completed'
                  ? 'text-green-700 bg-green-100'
                  : document.status === 'failed'
                  ? 'text-red-700 bg-red-100'
                  : 'text-yellow-700 bg-yellow-100'
              }`}
            >
              {document.status}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Request</h3>
            <p className="text-gray-700">{document.request_text}</p>
          </div>

          {document.status === 'completed' && (
            <>
              {/* Preview Section */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Preview</h3>
                <DocumentPreview documentId={id!} />
              </div>

              {/* Download Section */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Download Options</h3>
                <p className="text-gray-600 mb-4">
                  Your document has been generated and is ready to download.
                </p>
                <div className="flex space-x-3">
                  <button
                    onClick={handleDownload}
                    className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                  >
                    Download {document.output_format.toUpperCase()}
                  </button>
                  <button
                    onClick={() => navigate('/documents')}
                    className="px-6 py-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 font-medium"
                  >
                    Back to List
                  </button>
                </div>
              </div>
            </>
          )}

          {document.status === 'failed' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-red-900 mb-2">Generation Failed</h3>
              <p className="text-red-700 mb-4">
                There was an error generating your document. Please try again.
              </p>
              <button
                onClick={() => navigate('/')}
                className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
              >
                Generate New Document
              </button>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-end">
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 text-red-600 hover:text-red-700 font-medium"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete Document'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
