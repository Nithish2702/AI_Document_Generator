"""
Bulk Document Upload Script
Upload all documents from a folder to the RAG system
"""
import requests
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment
HOST = os.getenv('HOST', 'localhost')
# Convert 0.0.0.0 to localhost for client connections
if HOST == '0.0.0.0':
    HOST = 'localhost'
PORT = os.getenv('PORT', '8000')
API_URL = f"http://{HOST}:{PORT}"
DOCUMENTS_FOLDER = "../Documents"  # Default: ai-document-generator-rag/Documents

# Document type mapping based on filename or folder
DOCUMENT_TYPE_MAP = {
    'proposal': 'proposal',
    'report': 'report',
    'memo': 'memo',
    'summary': 'summary',
    'executive': 'summary',
    'deliverable': 'deliverable',
    'marketing': 'proposal',
    'business': 'report',
}

def get_document_type(filename):
    """Determine document type from filename"""
    filename_lower = filename.lower()
    
    for keyword, doc_type in DOCUMENT_TYPE_MAP.items():
        if keyword in filename_lower:
            return doc_type
    
    # Default to 'report' if can't determine
    return 'report'

def get_category(filename):
    """Determine category from filename"""
    filename_lower = filename.lower()
    
    if any(word in filename_lower for word in ['marketing', 'campaign', 'promotion']):
        return 'marketing'
    elif any(word in filename_lower for word in ['business', 'quarterly', 'annual']):
        return 'business'
    elif any(word in filename_lower for word in ['project', 'plan']):
        return 'project'
    elif any(word in filename_lower for word in ['executive', 'summary']):
        return 'executive'
    elif any(word in filename_lower for word in ['policy', 'memo']):
        return 'policy'
    
    return None

def upload_document(file_path, doc_type, category=None):
    """Upload a single document to the API"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            params = {
                'document_type': doc_type,
            }
            if category:
                params['category'] = category
            
            response = requests.post(
                f"{API_URL}/api/documents/upload",
                files=files,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.text
                
    except Exception as e:
        return False, str(e)

def main():
    """Main function to upload all documents"""
    
    # Get documents folder path
    if len(sys.argv) > 1:
        docs_folder = Path(sys.argv[1])
    else:
        docs_folder = Path(DOCUMENTS_FOLDER)
    
    if not docs_folder.exists():
        print(f"❌ Error: Folder '{docs_folder}' not found!")
        print(f"\nUsage: python upload_documents.py [path_to_documents_folder]")
        print(f"Example: python upload_documents.py C:/Users/YourName/Documents")
        return
    
    print(f"📁 Scanning folder: {docs_folder.absolute()}")
    print(f"🔗 API URL: {API_URL}")
    print("-" * 60)
    
    # Find all supported document files
    supported_extensions = ['.docx', '.doc', '.pdf', '.txt', '.md']
    documents = []
    
    for ext in supported_extensions:
        documents.extend(docs_folder.glob(f'*{ext}'))
        documents.extend(docs_folder.glob(f'**/*{ext}'))  # Include subfolders
    
    if not documents:
        print(f"❌ No documents found in {docs_folder}")
        print(f"   Looking for: {', '.join(supported_extensions)}")
        return
    
    print(f"📄 Found {len(documents)} documents\n")
    
    # Upload each document
    success_count = 0
    failed_count = 0
    
    for doc_path in documents:
        doc_type = get_document_type(doc_path.name)
        category = get_category(doc_path.name)
        
        print(f"⬆️  Uploading: {doc_path.name}")
        print(f"   Type: {doc_type}, Category: {category or 'None'}")
        
        success, result = upload_document(doc_path, doc_type, category)
        
        if success:
            print(f"   ✅ Success! Document ID: {result.get('id', 'N/A')}")
            success_count += 1
        else:
            print(f"   ❌ Failed: {result}")
            failed_count += 1
        
        print()
    
    # Summary
    print("-" * 60)
    print(f"📊 Upload Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📄 Total: {len(documents)}")
    
    if success_count > 0:
        print(f"\n🎉 Successfully uploaded {success_count} documents!")
        print(f"   The RAG system is now ready to generate documents.")
    
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} documents failed to upload.")
        print(f"   Check if the backend server is running at {API_URL}")

if __name__ == "__main__":
    print("=" * 60)
    print("  AI Document Generator - Bulk Upload Script")
    print("=" * 60)
    print()
    
    main()
