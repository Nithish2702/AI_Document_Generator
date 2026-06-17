"""
Main FastAPI Application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.database import init_db
from app.api import documents
from app.services.vector_store import vector_store
from app import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting AI Document Generator API")
    logger.info("=" * 60)
    
    logger.info("📊 Initializing database...")
    init_db()
    logger.info("✅ Database initialized")
    
    # Load vector store index if exists
    try:
        logger.info("🔍 Loading vector store...")
        vector_store.load()
        vector_count = vector_store.get_size()
        logger.info(f"✅ Vector store loaded with {vector_count} vectors")
    except Exception as e:
        logger.warning(f"⚠️  Could not load vector store: {e}")
        logger.info("📝 Vector store will be created when documents are uploaded")
    
    logger.info("=" * 60)
    logger.info(f"✅ API is ready at http://{settings.HOST}:{settings.PORT}")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 Shutting down API...")
    logger.info("=" * 60)
    
    # Save vector store
    try:
        logger.info("💾 Saving vector store...")
        vector_store.save()
        logger.info("✅ Vector store saved")
    except Exception as e:
        logger.error(f"❌ Could not save vector store: {e}")
    
    logger.info("👋 Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Document Generator API",
    description="RAG-based document generation system",
    version=__version__,
    lifespan=lifespan
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    logger.info(f"📥 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}ms")
    
    return response


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)


@app.get("/")
def read_root():
    """Root endpoint"""
    logger.info("🏠 Root endpoint accessed")
    return {
        "message": "AI Document Generator API",
        "version": __version__,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    logger.info("💚 Health check requested")
    return {
        "status": "healthy",
        "version": __version__,
        "database": "connected",
        "vector_store_size": vector_store.get_size()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
