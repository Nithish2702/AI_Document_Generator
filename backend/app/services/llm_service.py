"""
LLM Service for Document Generation
Uses Google Gemini
"""
import google.generativeai as genai
from app.config import settings
from typing import Optional
import os


class LLMService:
    """Service for LLM-based document generation using Google Gemini"""
    
    def __init__(self):
        """Initialize Gemini client"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    def generate_document(
        self,
        request_text: str,
        document_type: str,
        title: str,
        context: str,
        tone: str = "formal",
        length: str = "medium"
    ) -> str:
        """
        Generate document content using Gemini
        
        Args:
            request_text: User's request description
            document_type: Type of document
            title: Document title
            context: Retrieved context from similar documents
            tone: Writing tone
            length: Document length
            
        Returns:
            Generated document content
        """
        # Build prompt
        prompt = self._build_prompt(
            request_text=request_text,
            document_type=document_type,
            title=title,
            context=context,
            tone=tone,
            length=length
        )
        
        # Generate with Gemini
        try:
            return self._generate_with_gemini(prompt)
        except Exception as e:
            raise Exception(f"Error generating document with Gemini: {str(e)}")
    
    def _generate_with_gemini(self, prompt: str) -> str:
        """
        Generate using Google Gemini - single professional attempt
        
        Args:
            prompt: The generation prompt
            
        Returns:
            Complete generated document
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🤖 Generating document with professional prompt...")
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                    top_p=0.95,
                    top_k=40,
                ),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    },
                ]
            )
            
            # Get the text directly - let exceptions bubble up if blocked
            content = response.text
            
            logger.info(f"✅ Document generated successfully ({len(content)} characters)")
            
            return content
                    
        except Exception as e:
            logger.error(f"❌ Generation error: {str(e)}")
            # Provide more helpful error message
            if "block" in str(e).lower() or "safety" in str(e).lower():
                raise Exception("The content was flagged by safety filters. Please try rephrasing your request using more neutral, business-focused language.")
            raise Exception(f"Generation failed: {str(e)}")
    
    def _build_prompt(
        self,
        request_text: str,
        document_type: str,
        title: str,
        context: str,
        tone: str,
        length: str
    ) -> str:
        """Build a professional prompt optimized for long, comprehensive documents"""
        
        # Professional tone descriptions
        tone_guidance = {
            "formal": "Use formal professional business language.",
            "casual": "Use approachable professional language.",
            "technical": "Use technical terminology and industry language."
        }
        
        # Document type specific guidance - simplified and neutral
        doc_guidance = {
            "business_plan": "Create a detailed business plan with executive summary, market analysis, business model, financial projections, and implementation timeline.",
            "marketing_proposal": "Create a marketing proposal with situation analysis, target audience, marketing strategy, budget, and implementation plan.",
            "project_proposal": "Create a project proposal with overview, objectives, scope, methodology, timeline, resources, budget, and outcomes.",
            "executive_summary": "Create an executive summary with key points, findings, recommendations, and action items.",
            "business_proposal": "Create a business proposal with problem statement, solution, approach, pricing, timeline, and value proposition.",
            "default": "Create a well-structured professional business document with detailed sections and analysis."
        }
        
        doc_description = doc_guidance.get(document_type, doc_guidance["default"])
        tone_instruction = tone_guidance.get(tone, tone_guidance["formal"])
        
        # Simplified, neutral prompt
        prompt = f"""Create a comprehensive professional business document.

Title: {title}

Requirements:
{request_text}

Reference Context:
{context[:2000]}

Instructions:
- {tone_instruction}
- {doc_description}
- Use clear headings with # for main sections and ## for subsections
- Include relevant data in markdown tables
- Use bullet points for clarity
- Provide specific examples and recommendations
- Ensure logical flow between sections
- Make each section detailed with multiple paragraphs

Structure:
1. Executive summary or introduction
2. Multiple detailed content sections
3. Supporting data and analysis
4. Actionable recommendations
5. Conclusion with next steps

Generate a complete, detailed professional document."""
        
        return prompt
    
    def chat(self, message: str, conversation_history: list = None) -> str:
        """
        General chat function for interactive conversations
        
        Args:
            message: User's message
            conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            AI response
        """
        try:
            return self._chat_with_gemini(message, conversation_history)
        except Exception as e:
            raise Exception(f"Error in chat with Gemini: {str(e)}")
    
    def analyze_document_request(self, message: str, conversation_history: list = None) -> dict:
        """
        Analyze if user wants to create a document and what information is missing
        
        Args:
            message: User's message
            conversation_history: Previous conversation
            
        Returns:
            {
                "wants_document": bool,
                "has_sufficient_info": bool,
                "missing_info": str (question to ask user),
                "extracted_info": {
                    "title": str or None,
                    "description": str or None,
                    "document_type": str or None,
                    "context": str or None
                }
            }
        """
        try:
            return self._analyze_with_gemini(message, conversation_history)
        except Exception as e:
            raise Exception(f"Error analyzing request with Gemini: {str(e)}")
    
    
    def _analyze_with_gemini(self, message: str, conversation_history: list = None) -> dict:
        """Analyze document request using Gemini"""
        system_instruction = """Analyze if the user wants to create a document.

Extract information and respond with JSON only:
{
    "wants_document": true/false,
    "has_sufficient_info": true/false,
    "missing_info": "question to ask" or null,
    "extracted_info": {
        "title": "document title",
        "description": "what to include",
        "document_type": "business_plan/marketing_proposal/project_proposal/business_proposal/executive_summary",
        "context": "additional details"
    }
}

If user provides detailed request with document type and description, set has_sufficient_info to true."""
        
        # Build prompt
        if conversation_history:
            conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history[-3:]])
            prompt = f"{system_instruction}\n\nConversation:\n{conv_text}\n\nMessage: {message}\n\nJSON:"
        else:
            prompt = f"{system_instruction}\n\nMessage: {message}\n\nJSON:"
        
        import json
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500,
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            # Get text directly
            text = response.text.strip()
            
            # Remove markdown code blocks
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()
            
            # Try to find JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            
            # Parse JSON
            result = json.loads(text)
            
            # Validate and normalize
            return self._normalize_analysis_result(result, message)
                
        except Exception as e:
            logger.warning(f"⚠️ Analysis failed: {str(e)}. Using fallback.")
            return self._get_safe_default_response(message)
    
    def _normalize_analysis_result(self, result: dict, message: str) -> dict:
        """Normalize and validate analysis result with safe null handling"""
        # Ensure all required fields exist with proper defaults
        if not isinstance(result, dict):
            result = {}
        
        if 'wants_document' not in result:
            result['wants_document'] = False
        
        if 'has_sufficient_info' not in result:
            result['has_sufficient_info'] = False
        
        # Handle missing_info - convert list to string or set to None
        if 'missing_info' not in result or result['missing_info'] is None:
            result['missing_info'] = None
        elif isinstance(result['missing_info'], list):
            # Convert list to a question string - safely handle non-string items
            if len(result['missing_info']) > 0:
                # Convert all items to strings safely
                items = [str(item) for item in result['missing_info'] if item]
                if items:
                    result['missing_info'] = f"Could you please provide more details about: {', '.join(items)}?"
                else:
                    result['missing_info'] = None
            else:
                result['missing_info'] = None
        elif not isinstance(result['missing_info'], str):
            # Convert any other type to string or None
            result['missing_info'] = str(result['missing_info']) if result['missing_info'] else None
        
        if 'extracted_info' not in result or result['extracted_info'] is None:
            result['extracted_info'] = {}
        
        # Ensure extracted_info has all fields with safe null handling
        extracted = result['extracted_info']
        
        # Safe title extraction
        if 'title' not in extracted or not extracted.get('title'):
            desc = extracted.get('description')
            if desc and isinstance(desc, str):
                extracted['title'] = desc[:100]
            elif message and isinstance(message, str):
                extracted['title'] = message[:100]
            else:
                extracted['title'] = None
        
        # Safe description extraction
        if 'description' not in extracted or not extracted.get('description'):
            if message and isinstance(message, str):
                extracted['description'] = message
            else:
                extracted['description'] = None
        
        # Safe document_type extraction
        if 'document_type' not in extracted or not extracted.get('document_type'):
            extracted['document_type'] = None
        
        # Safe context extraction
        if 'context' not in extracted:
            extracted['context'] = None
        
        return result
    
    def _get_safe_default_response(self, message: str) -> dict:
        """Get a safe default response for non-document requests or errors"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Try to detect if this is a document request using simple keyword matching
        message_lower = message.lower() if message else ""
        
        document_keywords = [
            'create', 'generate', 'write', 'make', 'build', 'draft', 'prepare',
            'proposal', 'plan', 'report', 'document', 'business', 'marketing',
            'executive summary', 'project', 'strategy', 'analysis', 'presentation'
        ]
        
        # Check if message contains document-related keywords
        is_likely_document_request = any(keyword in message_lower for keyword in document_keywords)
        
        if is_likely_document_request and len(message) > 50:
            # This looks like a document request with substantial detail
            logger.info(f"🔍 Detected likely document request in fallback (length: {len(message)})")
            
            # Try to extract basic info from the message
            title = message[:100] if message else "Untitled Document"
            
            # Infer document type from keywords
            document_type = "business_document"
            if any(word in message_lower for word in ['proposal', 'bid']):
                document_type = "business_proposal"
            elif any(word in message_lower for word in ['plan', 'strategy']):
                document_type = "business_plan"
            elif any(word in message_lower for word in ['marketing', 'campaign']):
                document_type = "marketing_proposal"
            elif any(word in message_lower for word in ['project', 'implementation']):
                document_type = "project_proposal"
            elif any(word in message_lower for word in ['executive', 'summary']):
                document_type = "executive_summary"
            
            return {
                "wants_document": True,
                "has_sufficient_info": True,  # Assume detailed request has enough info
                "missing_info": None,
                "extracted_info": {
                    "title": title,
                    "description": message,
                    "document_type": document_type,
                    "context": "Generated from detailed user request"
                }
            }
        
        # Default: not a document request
        return {
            "wants_document": False,
            "has_sufficient_info": False,
            "missing_info": None,
            "extracted_info": {
                "title": None,
                "description": message if message else None,
                "document_type": None,
                "context": None
            }
        }
    
    
    def _chat_with_gemini(self, message: str, conversation_history: list = None) -> str:
        """Chat using Google Gemini"""
        import logging
        logger = logging.getLogger(__name__)
        
        system_instruction = """You are a professional business document writing assistant. 

CRITICAL RULES:
1. When asked to "add more", "expand", or "elaborate" - ALWAYS make content LONGER and MORE DETAILED
2. When asked to make content "formal" - KEEP all information and make it MORE FORMAL
3. NEVER summarize or shorten content unless explicitly asked to "shorten" or "summarize"
4. When modifying sections, PRESERVE all original information and ADD to it
5. Default to being MORE comprehensive rather than less

Be helpful and professional."""
        
        # Build conversation context - keep it minimal to save tokens
        conversation_text = ""
        if conversation_history:
            for msg in conversation_history[-2:]:  # Only last 2 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_text += f"{role}: {msg['content'][:200]}\n\n"  # Truncate long messages
        
        full_prompt = f"{system_instruction}\n\n{conversation_text}User: {message}\n\nAssistant:"
        
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=4096,  # Increased for longer responses
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            result = response.text
            
            # Log the response length for debugging
            logger.info(f"✅ Chat response generated: {len(result)} characters")
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Chat error: {str(e)}")
            return "I can help you create and modify professional business documents. What would you like me to do?"


# Global instance
llm_service = LLMService()
