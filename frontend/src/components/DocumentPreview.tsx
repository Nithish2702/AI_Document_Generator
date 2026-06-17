import { useEffect, useState } from 'react'

interface ContentBlock {
  type: 'heading1' | 'heading2' | 'heading3' | 'paragraph' | 'bullet' | 'table' | 'spacer'
  text?: string
  title?: string
  rows?: string[][]
}

interface PreviewData {
  id: string
  title: string
  document_type: string
  created_at: string
  content_blocks: ContentBlock[]
}

interface DocumentPreviewProps {
  documentId: string
  onTextSelected?: (text: string) => void
}

export default function DocumentPreview({ documentId, onTextSelected }: DocumentPreviewProps) {
  const [preview, setPreview] = useState<PreviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showContextButton, setShowContextButton] = useState(false)
  const [buttonPosition, setButtonPosition] = useState({ x: 0, y: 0 })
  const [selectedText, setSelectedText] = useState('')

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        setLoading(true)
        const response = await fetch(`http://localhost:8000/api/documents/generated/${documentId}/preview`)
        if (!response.ok) {
          throw new Error('Failed to load preview')
        }
        const data = await response.json()
        setPreview(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load preview')
      } finally {
        setLoading(false)
      }
    }

    fetchPreview()
  }, [documentId])

  // Handle text selection
  const handleMouseUp = (e: React.MouseEvent) => {
    const selection = window.getSelection()
    const text = selection?.toString().trim()
    
    console.log('Text selected:', text)
    
    if (text && text.length > 10) {
      setSelectedText(text)
      setShowContextButton(true)
      
      // Position button near the selection
      const range = selection?.getRangeAt(0)
      const rect = range?.getBoundingClientRect()
      if (rect) {
        setButtonPosition({
          x: rect.right + 10,
          y: rect.top + window.scrollY
        })
      }
      console.log('Button should show at:', buttonPosition)
    } else {
      setShowContextButton(false)
    }
  }

  const handleAddContext = () => {
    console.log('Add context clicked, text:', selectedText)
    console.log('onTextSelected callback exists:', !!onTextSelected)
    
    if (onTextSelected && selectedText) {
      onTextSelected(selectedText)
      setShowContextButton(false)
      setSelectedText('')
      window.getSelection()?.removeAllRanges()
      console.log('Context added successfully')
    } else {
      console.error('Cannot add context - missing callback or text')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !preview) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-700">{error || 'Failed to load preview'}</p>
      </div>
    )
  }

  const cleanText = (text: string) => {
    // Remove markdown artifacts
    return text.replace(/\*\*/g, '').replace(/\*/g, '').trim()
  }

  return (
    <div className="bg-gray-300 p-4 overflow-y-auto h-full relative" onMouseUp={handleMouseUp}>
      {/* Add Context Button - Fixed positioning */}
      {showContextButton && (
        <button
          className="fixed z-50 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-xl hover:bg-blue-700 transition-colors flex items-center gap-2 font-medium"
          style={{ 
            left: `${Math.min(buttonPosition.x, window.innerWidth - 200)}px`, 
            top: `${buttonPosition.y}px` 
          }}
          onClick={handleAddContext}
          onMouseDown={(e) => e.preventDefault()} // Prevent text deselection
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          Add to Context
        </button>
      )}
      
      {/* Single continuous document - no pagination */}
      <div className="mx-auto pb-4" style={{ transform: 'scale(0.85)', transformOrigin: 'top center' }}>
        <div 
          className="bg-white shadow-2xl mx-auto select-text" 
          style={{ 
            width: '8.5in', 
            paddingTop: '1in',
            paddingBottom: '1in',
            paddingLeft: '0.75in',
            paddingRight: '0.75in',
            fontFamily: 'Calibri, Arial, sans-serif'
          }}
        >
          {/* Document Title */}
          <h1 className="font-bold text-center text-black mb-1" style={{ fontFamily: 'Calibri, Arial, sans-serif', fontSize: '16pt' }}>
            {preview.title}
          </h1>
          
          <p className="text-center text-black mb-6" style={{ fontFamily: 'Calibri, Arial, sans-serif', fontSize: '10pt', fontStyle: 'italic' }}>
            Generated on: {new Date(preview.created_at).toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>

          {/* All Content Blocks */}
          {preview.content_blocks.map((block, index) => {
            switch (block.type) {
              case 'heading1':
                return (
                  <h2 
                    key={index} 
                    className="font-bold text-black"
                    style={{ 
                      fontFamily: 'Calibri, Arial, sans-serif',
                      fontSize: '14pt',
                      marginTop: '8pt',
                      marginBottom: '6pt'
                    }}
                  >
                    {cleanText(block.text || '')}
                  </h2>
                )
              
              case 'heading2':
                return (
                  <h3 
                    key={index} 
                    className="font-bold text-black"
                    style={{ 
                      fontFamily: 'Calibri, Arial, sans-serif',
                      fontSize: '12pt',
                      marginTop: '6pt',
                      marginBottom: '4pt'
                    }}
                  >
                    {cleanText(block.text || '')}
                  </h3>
                )
              
              case 'heading3':
                return (
                  <h4 
                    key={index} 
                    className="font-bold text-black"
                    style={{ 
                      fontFamily: 'Calibri, Arial, sans-serif',
                      fontSize: '11pt',
                      marginTop: '6pt',
                      marginBottom: '4pt'
                    }}
                  >
                    {cleanText(block.text || '')}
                  </h4>
                )
              
              case 'paragraph':
                return (
                  <p 
                    key={index} 
                    className="text-black"
                    style={{ 
                      fontFamily: 'Calibri, Arial, sans-serif',
                      fontSize: '11pt',
                      lineHeight: '1.15',
                      textAlign: 'justify',
                      marginBottom: '6pt'
                    }}
                  >
                    {cleanText(block.text || '')}
                  </p>
                )
              
              case 'bullet':
                return (
                  <div key={index} className="flex items-start" style={{ marginBottom: '3pt' }}>
                    <span className="text-black" style={{ fontFamily: 'Calibri, Arial, sans-serif', fontSize: '11pt', marginRight: '8pt' }}>•</span>
                    <p 
                      className="text-black flex-1"
                      style={{ 
                        fontFamily: 'Calibri, Arial, sans-serif',
                        fontSize: '11pt',
                        lineHeight: '1.15',
                        textAlign: 'justify'
                      }}
                    >
                      {cleanText(block.text || '')}
                    </p>
                  </div>
                )
              
              case 'table':
                const tableRows = block.rows || []
                const hasRows = tableRows.length > 0
                
                return (
                  <div key={index} style={{ marginTop: '6pt', marginBottom: '6pt' }}>
                    {block.title && (
                      <p className="font-bold text-black" style={{ fontFamily: 'Calibri, Arial, sans-serif', fontSize: '11pt', marginBottom: '4pt' }}>
                        {block.title}
                      </p>
                    )}
                    {hasRows ? (
                      <table className="w-full border-collapse" style={{ borderColor: '#000', borderWidth: '1px', borderStyle: 'solid' }}>
                        <thead>
                          <tr>
                            {tableRows[0].map((cell, cellIndex) => (
                              <th 
                                key={cellIndex}
                                className="border text-left bg-white text-black"
                                style={{ 
                                  fontFamily: 'Calibri, Arial, sans-serif',
                                  fontSize: '11pt',
                                  fontWeight: 'bold',
                                  borderWidth: '1px',
                                  borderColor: '#000',
                                  borderStyle: 'solid',
                                  padding: '6px'
                                }}
                              >
                                {String(cell)}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {tableRows.slice(1).map((row, rowIndex) => (
                            <tr key={rowIndex}>
                              {row.map((cell, cellIndex) => (
                                <td 
                                  key={cellIndex}
                                  className="border bg-white text-black"
                                  style={{ 
                                    fontFamily: 'Calibri, Arial, sans-serif',
                                    fontSize: '10pt',
                                    borderWidth: '1px',
                                    borderColor: '#000',
                                    borderStyle: 'solid',
                                    padding: '6px'
                                  }}
                                >
                                  {String(cell)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p className="text-gray-500 italic">No table data available</p>
                    )}
                  </div>
                )
              
              case 'spacer':
                return <div key={index} style={{ height: '3pt' }}></div>
              
              default:
                return null
            }
          })}
        </div>
      </div>
    </div>
  )
}
