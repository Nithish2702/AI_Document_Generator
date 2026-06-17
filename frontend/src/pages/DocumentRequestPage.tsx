import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { documentService } from '../api/documentService'
import type { GenerateDocumentRequest } from '../types'

export default function DocumentRequestPage() {
  const navigate = useNavigate()
  const [isGenerating, setIsGenerating] = useState(false)
  
  const { register, handleSubmit, formState: { errors } } = useForm<GenerateDocumentRequest>({
    defaultValues: {
      tone: 'formal',
      length: 'long',  // Always long
      format: 'pdf',
    },
  })

  const generateMutation = useMutation({
    mutationFn: documentService.generateDocument,
    onSuccess: (data) => {
      setIsGenerating(false)
      navigate(`/documents/${data.id}`)
    },
    onError: (error) => {
      setIsGenerating(false)
      alert('Error generating document: ' + error)
    },
  })

  const onSubmit = (data: GenerateDocumentRequest) => {
    setIsGenerating(true)
    generateMutation.mutate(data)
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Generate New Document
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Document Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Document Type *
            </label>
            <select
              {...register('documentType', { required: 'Document type is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select type...</option>
              <option value="proposal">Marketing Proposal</option>
              <option value="report">Business Report</option>
              <option value="memo">Memo</option>
              <option value="summary">Executive Summary</option>
              <option value="deliverable">Client Deliverable</option>
            </select>
            {errors.documentType && (
              <p className="mt-1 text-sm text-red-600">{errors.documentType.message}</p>
            )}
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Document Title *
            </label>
            <input
              type="text"
              {...register('title', { required: 'Title is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Q1 2024 Marketing Campaign Proposal"
            />
            {errors.title && (
              <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              {...register('description', { required: 'Description is required' })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe what the document should contain..."
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            )}
          </div>

          {/* Context */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Context
            </label>
            <textarea
              {...register('context')}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Any additional context, requirements, or constraints..."
            />
          </div>

          {/* Tone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tone
            </label>
            <select
              {...register('tone')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="formal">Formal</option>
              <option value="casual">Casual</option>
              <option value="technical">Technical</option>
            </select>
          </div>

          {/* Hidden length field - always long */}
          <input type="hidden" {...register('length')} value="long" />

          {/* Format */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Output Format
            </label>
            <select
              {...register('format')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="pdf">PDF</option>
              <option value="docx">DOCX (Word)</option>
            </select>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isGenerating}
              className={`px-6 py-3 rounded-md text-white font-medium ${
                isGenerating
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isGenerating ? 'Generating...' : 'Generate Document'}
            </button>
          </div>
        </form>

        {isGenerating && (
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
              <p className="text-blue-700">
                Generating your document... This may take 30-60 seconds.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
