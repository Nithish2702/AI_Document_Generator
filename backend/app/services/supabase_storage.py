"""
Supabase Storage Service
Handles file upload/download to Supabase Storage
"""
from supabase import create_client, Client
from pathlib import Path
from typing import Optional
import os
from app.config import settings


class SupabaseStorage:
    """Service for managing files in Supabase Storage"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.bucket_name = settings.SUPABASE_BUCKET
        
        # Validate required settings
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL must be set in .env file")
        if not self.supabase_key:
            raise ValueError("SUPABASE_KEY must be set in .env file")
        if not self.bucket_name:
            raise ValueError("SUPABASE_BUCKET must be set in .env file")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            # Try to get bucket
            self.client.storage.get_bucket(self.bucket_name)
        except Exception:
            # Bucket doesn't exist, create it
            try:
                self.client.storage.create_bucket(
                    self.bucket_name,
                    options={"public": False}  # Private bucket
                )
                print(f"Created Supabase bucket: {self.bucket_name}")
            except Exception as e:
                print(f"Note: Could not create bucket (may already exist): {e}")
    
    def upload_file(self, file_path: str, destination_path: str) -> str:
        """
        Upload a file to Supabase Storage
        
        Args:
            file_path: Local file path to upload
            destination_path: Path in Supabase bucket (e.g., 'uploads/doc.docx')
            
        Returns:
            Public URL or signed URL of the uploaded file
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase
            response = self.client.storage.from_(self.bucket_name).upload(
                path=destination_path,
                file=file_data,
                file_options={"content-type": self._get_content_type(file_path)}
            )
            
            # Get public URL
            url = self.client.storage.from_(self.bucket_name).get_public_url(destination_path)
            
            return url
            
        except Exception as e:
            raise Exception(f"Error uploading file to Supabase: {str(e)}")
    
    def download_file(self, source_path: str, destination_path: str) -> str:
        """
        Download a file from Supabase Storage
        
        Args:
            source_path: Path in Supabase bucket
            destination_path: Local path to save file
            
        Returns:
            Local file path
        """
        try:
            # Download from Supabase
            response = self.client.storage.from_(self.bucket_name).download(source_path)
            
            # Save to local file
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            with open(destination_path, 'wb') as f:
                f.write(response)
            
            return destination_path
            
        except Exception as e:
            raise Exception(f"Error downloading file from Supabase: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage
        
        Args:
            file_path: Path in Supabase bucket
            
        Returns:
            True if successful
        """
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            print(f"Error deleting file from Supabase: {str(e)}")
            return False
    
    def get_public_url(self, file_path: str) -> str:
        """
        Get public URL for a file
        
        Args:
            file_path: Path in Supabase bucket
            
        Returns:
            Public URL
        """
        return self.client.storage.from_(self.bucket_name).get_public_url(file_path)
    
    def create_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Create a signed URL for temporary access
        
        Args:
            file_path: Path in Supabase bucket
            expires_in: Expiration time in seconds (default 1 hour)
            
        Returns:
            Signed URL
        """
        try:
            response = self.client.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in
            )
            return response['signedURL']
        except Exception as e:
            raise Exception(f"Error creating signed URL: {str(e)}")
    
    def list_files(self, folder: str = "") -> list:
        """
        List files in a folder
        
        Args:
            folder: Folder path in bucket
            
        Returns:
            List of file objects
        """
        try:
            response = self.client.storage.from_(self.bucket_name).list(folder)
            return response
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def _get_content_type(self, file_path: str) -> str:
        """Get content type based on file extension"""
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
        }
        return content_types.get(ext, 'application/octet-stream')


# Global instance
supabase_storage = None

def get_supabase_storage() -> SupabaseStorage:
    """Get or create Supabase storage instance"""
    global supabase_storage
    if supabase_storage is None:
        supabase_storage = SupabaseStorage()
    return supabase_storage
