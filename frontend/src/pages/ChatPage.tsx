import { useState, useRef, useEffect } from 'react'
import { documentService } from '../api/documentService'
import { logger } from '../utils/logger'
import DocumentPreview from '../components/DocumentPreview'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  documentId?: string
  documentContent?: string
  isGenerating?: boolean
  modifiedText?: string
  originalContext?: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your AI assistant. I can help you with:\n\n• Creating professional business documents (proposals, plans, reports, etc.)\n• Answering questions about business documents\n• General conversations and assistance\n\nWhat can I help you with today?",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [previewDocument, setPreviewDocument] = useState<{id: string, title: string, content: string} | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [selectedContext, setSelectedContext] = useState<string | null>(null)
  const [previewRefreshKey, setPreviewRefreshKey] = useState(0)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const addMessage = (role: 'user' | 'assistant' | 'system', content: string, documentId?: string, documentContent?: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role,
      content,
      timestamp: new Date(),
      documentId,
      documentContent
    }
    setMessages(prev => [...prev, newMessage])
    return newMessage
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    const contextToSend = selectedContext
    setInput('')
    setSelectedContext(null) // Clear context after sending
    
    // Add user message with context indicator
    const displayMessage = contextToSend 
      ? `📎 Context: "${contextToSend.substring(0, 50)}..."\n\n${userMessage}`
      : userMessage
    addMessage('user', displayMessage)
    setIsLoading(true)

    try {
      // Build conversation history
      const history = messages
        .filter(m => m.role !== 'system')
        .map(m => ({
          role: m.role,
          content: m.content
        }))
      
      // If there's selected context, use it for modification
      if (contextToSend && previewDocument) {
        logger.info('🔄 Modifying selected context...')
        
        // Build a better prompt that preserves or expands content
        let modificationPrompt = ''
        
        // Detect the type of request
        const requestLower = userMessage.toLowerCase()
        
        if (requestLower.includes('add more') || requestLower.includes('expand') || requestLower.includes('elaborate') || requestLower.includes('more data') || requestLower.includes('more detail')) {
          modificationPrompt = `You are a professional business document writer. The user wants you to SIGNIFICANTLY EXPAND this section with MORE CONTENT.

===== ORIGINAL SECTION (${contextToSend.split(' ').length} words) =====
${contextToSend}
==========

User's request: "${userMessage}"

CRITICAL INSTRUCTIONS:
1. KEEP 100% of the original content - do not remove or shorten anything
2. ADD substantial new information, details, examples, data, and analysis
3. The expanded version should be AT LEAST 2-3 times longer than the original
4. Add specific examples, case studies, statistics, or detailed explanations
5. Maintain the same professional tone and structure
6. If it's a bulleted list, add more bullet points
7. If it's paragraphs, add more paragraphs with deeper analysis
8. Do NOT summarize or condense - EXPAND and ELABORATE

OUTPUT FORMAT:
- Provide ONLY the complete expanded text for THIS SECTION
- Do NOT include other sections from the document
- Do NOT regenerate the entire document
- No explanations, no meta-commentary
- Start directly with the content

EXPANDED VERSION (target: ${contextToSend.split(' ').length * 3}+ words):`
        } else if (requestLower.includes('formal') || requestLower.includes('professional') || requestLower.includes('more formal')) {
          modificationPrompt = `You are a professional business document writer. The user wants you to make this section MORE FORMAL and PROFESSIONAL while EXPANDING it.

===== ORIGINAL SECTION =====
${contextToSend}
==========

User's request: "${userMessage}"

CRITICAL INSTRUCTIONS:
1. KEEP 100% of the original information - do not remove any content
2. Rewrite in highly formal, professional business language
3. EXPAND the content with additional formal details and analysis
4. The formal version should be LONGER than the original (at least 1.5-2x)
5. Use sophisticated vocabulary and professional terminology
6. Add formal transitions and connecting phrases
7. Include more detailed explanations in formal language
8. Do NOT shorten or summarize

OUTPUT FORMAT:
- Provide ONLY the complete formal text for THIS SECTION
- Do NOT include other sections from the document
- Do NOT regenerate the entire document
- No explanations, no meta-commentary
- Start directly with the content

FORMAL VERSION:`
        } else if (requestLower.includes('convert') && requestLower.includes('para')) {
          modificationPrompt = `You are a professional business document writer. The user wants you to convert bullet points into flowing paragraphs.

===== ORIGINAL SECTION =====
${contextToSend}
==========

User's request: "${userMessage}"

CRITICAL INSTRUCTIONS:
1. Convert all bullet points into well-structured paragraphs
2. KEEP 100% of the original information - do not remove any content
3. EXPAND each point into detailed sentences with explanations
4. Add transitions between ideas for smooth flow
5. The paragraph version should be LONGER than the bullet points
6. Maintain professional business tone
7. Do NOT summarize or condense

OUTPUT FORMAT:
- Provide ONLY the complete paragraph text for THIS SECTION
- Do NOT include other sections from the document
- Do NOT regenerate the entire document
- No explanations, no meta-commentary
- Start directly with the content

PARAGRAPH VERSION:`
        } else {
          modificationPrompt = `You are a professional business document writer. The user wants you to modify this section.

===== ORIGINAL SECTION =====
${contextToSend}
==========

User's request: "${userMessage}"

CRITICAL INSTRUCTIONS:
1. KEEP the same level of detail or ADD MORE
2. Do NOT shorten, summarize, or remove content unless explicitly asked
3. If in doubt, make it MORE detailed and comprehensive
4. Maintain professional business tone

OUTPUT FORMAT:
- Provide ONLY the complete modified text for THIS SECTION
- Do NOT include other sections from the document
- Do NOT regenerate the entire document
- No explanations, no meta-commentary
- Start directly with the content

MODIFIED VERSION:`
        }
        
        const chatResponse = await documentService.chat(modificationPrompt, history)
        
        // Extract the modified text (remove any markdown or extra formatting)
        let modifiedText = chatResponse.response.trim()
        
        // Safety check: If AI returned way more content than expected, it might be regenerating the whole document
        const originalWordCount = contextToSend.split(' ').length
        const modifiedWordCount = modifiedText.split(' ').length
        
        logger.info(`📊 Word count: Original=${originalWordCount}, Modified=${modifiedWordCount}`)
        
        // If modified text is suspiciously long (more than 10x original), warn the user
        if (modifiedWordCount > originalWordCount * 10) {
          logger.warn(`⚠️ Modified text is ${Math.round(modifiedWordCount / originalWordCount)}x longer than original. AI might have regenerated too much.`)
          addMessage('system', `⚠️ Warning: The AI generated ${modifiedWordCount} words from your ${originalWordCount}-word selection. This seems excessive. Please review carefully before applying changes.`)
        }
        
        // Add message with the modified text and metadata
        const contextPreview = contextToSend.substring(0, 150) + (contextToSend.length > 150 ? '...' : '')
        const assistantMessage = addMessage(
          'assistant', 
          `✏️ Here's the modified version:\n\n${modifiedText}\n\n---\n\n💡 **What will change when you click "Apply Changes":**\n\n📍 **This text will be REPLACED:**\n"${contextPreview}"\n\n✅ **With the modified version shown above**\n\n🔒 **Everything else stays unchanged** - Only your selected text (${originalWordCount} words) will be updated.\n\n**Modified version:** ${modifiedWordCount} words`
        )
        
        // Store the modified text and original context in the message
        assistantMessage.modifiedText = modifiedText
        assistantMessage.originalContext = contextToSend
        
        setIsLoading(false)
        return
      }
      
      // Analyze the request to see if user wants to create a document
      logger.info('🔍 Analyzing user request...')
      const analysis = await documentService.analyzeRequest(userMessage, history)
      
      logger.info('Analysis result:', analysis)
      
      if (analysis.wants_document) {
        // User wants to create a document
        
        if (analysis.has_sufficient_info) {
          // We have all the info needed, generate the document
          addMessage('assistant', "Perfect! I have all the information I need. Let me generate your document now... ⏳")
          
          const extractedInfo = analysis.extracted_info
          
          logger.info('🤖 Generating document', extractedInfo)

          const response = await documentService.generateDocument({
            document_type: extractedInfo.document_type || 'business_document',
            title: extractedInfo.title || 'Untitled Document',
            description: extractedInfo.description || userMessage,
            context: extractedInfo.context || 'Generated from conversational request',
            tone: 'professional',
            length: 'long',  // Always long, comprehensive documents
            format: 'docx'
          })

          logger.success('✅ Document generated', response)

          // Set preview
          setPreviewDocument({
            id: response.id,
            title: response.title,
            content: response.generated_content || 'Document content not available'
          })

          // Add success message
          addMessage(
            'assistant',
            `✅ Great! I've created your document: "${response.title}"\n\nIt took ${(response.generation_time_ms / 1000).toFixed(1)} seconds to generate.\n\nYou can view the preview on the left and download it in your preferred format.`,
            response.id,
            response.generated_content
          )

          setIsLoading(false)
        } else {
          // Missing information, ask the AI-generated question
          setTimeout(() => {
            addMessage('assistant', analysis.missing_info || "Could you provide more details about what you'd like in this document?")
            setIsLoading(false)
          }, 500)
        }
      } else {
        // General conversation - use chat endpoint
        logger.info('💬 General chat message')
        
        const chatResponse = await documentService.chat(userMessage, history)
        
        logger.success('✅ Chat response received')
        
        addMessage('assistant', chatResponse.response)
        setIsLoading(false)
      }
    } catch (error: any) {
      logger.error('❌ Error in chat', error)
      addMessage('assistant', `I encountered an error: ${error.response?.data?.detail || error.message}. Could you try rephrasing your request?`)
      setIsLoading(false)
    }
  }

  const handleDownload = async (documentId: string, format: 'docx' | 'pdf' = 'docx') => {
    try {
      logger.info(`⬇️ Downloading document as ${format.toUpperCase()}`, documentId)
      const blob = await documentService.downloadDocument(documentId, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `document-${documentId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      logger.success('✅ Download complete')
    } catch (error) {
      logger.error('❌ Download failed', error)
      alert('Failed to download document')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleContextFromPreview = (text: string) => {
    setSelectedContext(text)
    logger.info('📎 Context added from preview:', text.substring(0, 50))
  }

  const handleApplyChanges = async (messageId: string) => {
    const message = messages.find(m => m.id === messageId)
    if (!message || !message.modifiedText || !message.originalContext || !previewDocument) {
      logger.error('Cannot apply changes - missing data')
      return
    }

    try {
      logger.info('🔄 Applying changes to document...')
      setIsLoading(true)
      
      // Fetch the actual document from backend
      const document = await documentService.getGeneratedDocument(previewDocument.id)
      const currentContent = document.generated_content || ''
      
      // Enhanced text cleaning that preserves structure
      const cleanText = (text: string) => {
        return text
          .replace(/[•\-\*]/g, '') // Remove bullet points
          .replace(/#{1,6}\s*/g, '') // Remove markdown headings
          .replace(/\*\*/g, '') // Remove bold
          .replace(/\*/g, '') // Remove italic
          .replace(/__/g, '') // Remove underline
          .replace(/\s+/g, ' ') // Normalize whitespace
          .trim()
          .toLowerCase()
      }
      
      const originalContext = message.originalContext
      const cleanContext = cleanText(originalContext)
      
      logger.info('Original context:', originalContext.substring(0, 100))
      logger.info('Cleaned context:', cleanContext.substring(0, 100))
      
      const lines = currentContent.split('\n')
      
      // Strategy 1: Try to find heading match (for short selections like section titles)
      const contextWords = cleanContext.split(' ').filter(w => w.length > 2) // Ignore short words
      const contextLines = originalContext.trim().split('\n').filter(l => l.trim().length > 0)
      
      // Only use heading strategy if:
      // 1. Selection is short (≤8 words) OR
      // 2. Selection is only 1-2 lines (likely just a heading)
      if (contextWords.length <= 8 || contextLines.length <= 2) {
        // This might be a heading - search for heading lines
        logger.info('🔍 Trying heading match strategy...')
        logger.info(`   Context has ${contextWords.length} words and ${contextLines.length} lines`)
        
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim()
          
          // Check if this is a heading line
          if (line.startsWith('#') || (line.length < 100 && line.length > 5)) {
            const cleanLine = cleanText(line)
            
            // Check if all context words appear in this line
            const allWordsMatch = contextWords.every(word => cleanLine.includes(word))
            
            if (allWordsMatch) {
              logger.info(`✅ Found heading match at line ${i}: "${line}"`)
              
              // Determine if this is a markdown heading or plain text heading
              const isMarkdownHeading = line.startsWith('#')
              let sectionEnd = i
              
              if (isMarkdownHeading) {
                // For markdown headings, find next heading of same or higher level
                const currentLevel = (line.match(/^#+/) || [''])[0].length
                
                for (let j = i + 1; j < lines.length; j++) {
                  const nextLine = lines[j].trim()
                  if (nextLine.startsWith('#')) {
                    const nextLevel = (nextLine.match(/^#+/) || [''])[0].length
                    if (nextLevel <= currentLevel) {
                      sectionEnd = j - 1
                      break
                    }
                  }
                  sectionEnd = j
                }
              } else {
                // For plain text headings, find next heading (markdown or similar short line)
                for (let j = i + 1; j < lines.length; j++) {
                  const nextLine = lines[j].trim()
                  // Stop at next markdown heading OR another short line that looks like a heading
                  if (nextLine.startsWith('#') || 
                      (nextLine.length < 100 && nextLine.length > 5 && 
                       !nextLine.startsWith('•') && !nextLine.startsWith('-') && 
                       !nextLine.startsWith('*') && !nextLine.includes('|'))) {
                    sectionEnd = j - 1
                    break
                  }
                  sectionEnd = j
                }
              }
              
              logger.info(`📍 Section spans lines ${i} to ${sectionEnd}`)
              logger.info(`📍 Section type: ${isMarkdownHeading ? 'Markdown heading' : 'Plain text heading'}`)
              
              // Replace the entire section
              const before = lines.slice(0, i).join('\n')
              const after = lines.slice(sectionEnd + 1).join('\n')
              
              // Log what we're preserving
              logger.info(`🔒 Preserving ${i} lines BEFORE the section`)
              logger.info(`🔒 Preserving ${lines.length - sectionEnd - 1} lines AFTER the section`)
              logger.info(`✏️ Replacing ${sectionEnd - i + 1} lines in the matched section`)
              
              // SAFETY CHECK: Make sure we're not losing too much content
              const originalLength = currentContent.length
              const beforeLength = before.length
              const afterLength = after.length
              const modifiedLength = message.modifiedText.length
              const newTotalLength = beforeLength + modifiedLength + afterLength + 2 // +2 for newlines
              
              const contentLossPercentage = ((originalLength - newTotalLength) / originalLength) * 100
              
              logger.info(`📊 Content size check:`)
              logger.info(`   Original: ${originalLength} chars`)
              logger.info(`   New total: ${newTotalLength} chars`)
              logger.info(`   Change: ${contentLossPercentage > 0 ? '-' : '+'}${Math.abs(contentLossPercentage).toFixed(1)}%`)
              
              // If we're losing more than 30% of content, something is wrong - use fuzzy match instead
              if (contentLossPercentage > 30) {
                logger.warn(`⚠️ Heading match would lose ${contentLossPercentage.toFixed(1)}% of content. Falling back to fuzzy match.`)
                break // Exit heading match, try fuzzy match
              }
              
              // Keep the heading, replace the content
              const heading = lines[i]
              const updatedContent = before + 
                (before ? '\n' : '') + 
                heading + '\n' +
                message.modifiedText + 
                (after ? '\n' : '') + 
                after
              
              logger.info('📝 Content length change:', currentContent.length, '→', updatedContent.length)
              logger.info('✅ Other sections remain untouched')
              
              // Save to backend
              const response = await documentService.updateDocumentContent(previewDocument.id, updatedContent)
              logger.info('Backend response:', response)
              
              // Update preview
              setPreviewDocument({
                ...previewDocument,
                content: updatedContent
              })
              
              setPreviewRefreshKey(prev => prev + 1)
              addMessage('system', `✅ Changes applied successfully!\n\n📝 **What was changed:**\n- Replaced ${sectionEnd - i + 1} lines (lines ${i + 1} to ${sectionEnd + 1})\n- Section: "${heading.replace(/^#+\s*/, '')}"\n\n🔒 **What stayed the same:**\n- ${i} lines before this section\n- ${lines.length - sectionEnd - 1} lines after this section\n\nThe document preview and downloadable files have been updated.`)
              logger.info('✅ Changes applied successfully')
              setIsLoading(false)
              return
            }
          }
        }
        
        logger.info('⚠️ Heading match failed, trying fuzzy match...')
      }
      
      // Strategy 2: Fuzzy matching with sliding window
      logger.info('🔍 Trying fuzzy match strategy...')
      
      const allContextWords = cleanContext.split(' ').filter(w => w.length > 0)
      
      // Adjust matching threshold based on context length
      let minScore
      if (allContextWords.length <= 5) {
        minScore = 0.8 // 80% for very short
      } else if (allContextWords.length <= 15) {
        minScore = 0.6 // 60% for medium
      } else {
        minScore = 0.5 // 50% for long
      }
      
      let bestMatch = { start: -1, end: -1, score: 0 }
      
      // Search through the document with sliding window
      for (let i = 0; i < lines.length; i++) {
        for (let j = i; j < Math.min(i + 50, lines.length); j++) {
          const section = lines.slice(i, j + 1).join('\n')
          const cleanSection = cleanText(section)
          
          // Count matching words
          let matchCount = 0
          for (const word of allContextWords) {
            if (cleanSection.includes(word)) {
              matchCount++
            }
          }
          
          const score = matchCount / allContextWords.length
          
          if (score > bestMatch.score) {
            bestMatch = { start: i, end: j, score }
          }
        }
      }
      
      logger.info('Best fuzzy match:', bestMatch)
      
      if (bestMatch.score >= minScore) {
        // Replace the matched section
        const before = lines.slice(0, bestMatch.start).join('\n')
        const after = lines.slice(bestMatch.end + 1).join('\n')
        
        // Log what we're preserving
        logger.info(`🔒 Preserving ${bestMatch.start} lines BEFORE the matched section`)
        logger.info(`🔒 Preserving ${lines.length - bestMatch.end - 1} lines AFTER the matched section`)
        logger.info(`✏️ Replacing ${bestMatch.end - bestMatch.start + 1} lines in the matched section`)
        
        const updatedContent = before + 
          (before ? '\n' : '') + 
          message.modifiedText + 
          (after ? '\n' : '') + 
          after
        
        logger.info('📝 Content length change:', currentContent.length, '→', updatedContent.length)
        logger.info('✅ Other sections remain untouched')
        
        // Save to backend
        const response = await documentService.updateDocumentContent(previewDocument.id, updatedContent)
        logger.info('Backend response:', response)
        
        // Update preview
        setPreviewDocument({
          ...previewDocument,
          content: updatedContent
        })
        
        setPreviewRefreshKey(prev => prev + 1)
        addMessage('system', `✅ Changes applied successfully!\n\n📝 **What was changed:**\n- Replaced ${bestMatch.end - bestMatch.start + 1} lines (lines ${bestMatch.start + 1} to ${bestMatch.end + 1})\n- Match confidence: ${(bestMatch.score * 100).toFixed(0)}%\n\n🔒 **What stayed the same:**\n- ${bestMatch.start} lines before the matched section\n- ${lines.length - bestMatch.end - 1} lines after the matched section\n\nThe document preview and downloadable files have been updated.`)
        logger.info('✅ Changes applied successfully')
        setIsLoading(false)
        return
      }
      
      // Strategy 3: If all else fails, append to the end
      logger.warn('⚠️ Could not find exact match. Appending content to document.')
      
      const updatedContent = currentContent + '\n\n' + message.modifiedText
      
      // Save to backend
      const response = await documentService.updateDocumentContent(previewDocument.id, updatedContent)
      logger.info('Backend response:', response)
      
      // Update preview
      setPreviewDocument({
        ...previewDocument,
        content: updatedContent
      })
      
      setPreviewRefreshKey(prev => prev + 1)
      addMessage('system', '⚠️ Could not find exact location. Content has been appended to the end of the document. You may need to manually reorganize it.')
      logger.info('✅ Content appended to document')
      
    } catch (error: any) {
      logger.error('❌ Failed to apply changes', error)
      addMessage('system', `❌ Failed to apply changes: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-[#212121]">
      {/* Preview Panel - LEFT SIDE */}
      {previewDocument && (
        <div className="w-1/2 bg-[#2f2f2f] border-r border-gray-700 flex flex-col">
          {/* Preview Header */}
          <div className="bg-[#212121] border-b border-gray-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-100">Document Preview</h2>
                <p className="text-sm text-gray-400">{previewDocument.title}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleDownload(previewDocument.id, 'docx')}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  DOCX
                </button>
                <button
                  onClick={() => handleDownload(previewDocument.id, 'pdf')}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  PDF
                </button>
              </div>
            </div>
          </div>

          {/* Preview Content */}
          <div className="flex-1 overflow-y-auto bg-[#1a1a1a]">
            <DocumentPreview 
              key={`${previewDocument.id}-${previewRefreshKey}`}
              documentId={previewDocument.id} 
              onTextSelected={handleContextFromPreview}
            />
          </div>
        </div>
      )}

      {/* Chat Section - RIGHT SIDE */}
      <div className={`flex flex-col ${previewDocument ? 'w-1/2' : 'w-full'} transition-all duration-300`}>
      {/* Header */}
      <div className="bg-[#212121] border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">AI Document Generator</h1>
            <p className="text-sm text-gray-400">Chat with AI to create professional documents</p>
          </div>
          <div className="flex gap-3">
            {previewDocument && (
              <button
                onClick={() => setPreviewDocument(null)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Close Preview
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 bg-[#212121]">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-[#2f2f2f] text-white'
                    : 'bg-[#444654] text-gray-100 border border-gray-700'
                }`}
              >
                {/* Avatar */}
                <div className="flex items-start gap-3">
                  <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                      message.role === 'user'
                        ? 'bg-[#1a1a1a] text-white'
                        : 'bg-[#19c37d] text-white'
                    }`}
                  >
                    {message.role === 'user' ? '👤' : '🤖'}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    {/* Message content */}
                    <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    
                    {/* Download button if document is ready */}
                    {message.documentId && (
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => handleDownload(message.documentId!, 'docx')}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          Download DOCX
                        </button>
                        <button
                          onClick={() => handleDownload(message.documentId!, 'pdf')}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                          Download PDF
                        </button>
                        {message.documentContent && (
                          <button
                            onClick={() => setPreviewDocument({
                              id: message.documentId!,
                              title: 'Generated Document',
                              content: message.documentContent!
                            })}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            View Preview
                          </button>
                        )}
                      </div>
                    )}
                    
                    {/* Apply Changes button if this is a modification message */}
                    {message.modifiedText && message.originalContext && (
                      <div className="mt-3">
                        <button
                          onClick={() => handleApplyChanges(message.id)}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Apply Changes to Preview
                        </button>
                      </div>
                    )}
                    
                    {/* Timestamp */}
                    <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-gray-400' : 'text-gray-500'}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-[#444654] text-gray-100 border border-gray-700 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#19c37d] flex items-center justify-center text-white">
                    🤖
                  </div>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-[#212121] border-t border-gray-700 px-4 py-4">
        <div className="max-w-2xl mx-auto">
          {/* Selected Context Display */}
          {selectedContext && (
            <div className="mb-3 flex items-start gap-2 bg-[#2f2f2f] border border-gray-600 rounded-lg p-3">
              <svg className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-400 mb-1">Selected Context:</p>
                <p className="text-sm text-gray-200 line-clamp-2">{selectedContext}</p>
              </div>
              <button
                onClick={() => setSelectedContext(null)}
                className="text-gray-400 hover:text-gray-200 transition-colors"
                title="Clear context"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={selectedContext ? "Ask me to modify the selected text..." : "Type your message... (e.g., 'Create a marketing proposal for a SaaS product')"}
              className="w-full resize-none rounded-xl border border-gray-600 bg-[#40414f] text-white pl-4 pr-14 py-3 focus:outline-none focus:ring-1 focus:ring-white focus:border-white placeholder-gray-400 overflow-y-auto max-h-[200px]"
              rows={1}
              disabled={isLoading}
              style={{ minHeight: '48px' }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="absolute right-2 bottom-2 p-2 bg-white text-gray-900 rounded-lg hover:bg-gray-200 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
              title="Send message"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
    </div>
  )
}
