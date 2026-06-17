import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { documentService } from '../api/documentService'

export default function DocumentListPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['generated-documents'],
    queryFn: () => documentService.getGeneratedDocuments(0, 20),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-700">Error loading documents</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">My Documents</h2>
        <Link
          to="/"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Generate New
        </Link>
      </div>

      {data?.documents.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <p className="text-gray-500 mb-4">No documents generated yet</p>
          <Link
            to="/"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Generate Your First Document
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.documents.map((doc) => (
            <Link
              key={doc.id}
              to={`/documents/${doc.id}`}
              className="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="inline-block px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded">
                  {doc.document_type}
                </span>
                <span
                  className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
                    doc.status === 'completed'
                      ? 'text-green-700 bg-green-100'
                      : doc.status === 'failed'
                      ? 'text-red-700 bg-red-100'
                      : 'text-yellow-700 bg-yellow-100'
                  }`}
                >
                  {doc.status}
                </span>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                {doc.title}
              </h3>
              
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                {doc.request_text}
              </p>
              
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                <span className="uppercase">{doc.output_format}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
