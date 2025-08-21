# app/main.py
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.webhook import router as webhook_router
from app.api.connections import router as connections_router
from app.api.status import router as status_router
#from app.api.health import router as health_router
#from agents.db_specialist_agent import DBSpecialistAgent
from database.connections import DatabaseManager
from utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global instances
db_manager = None
specialist_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    global db_manager, specialist_agent
    
    logger.info("🚀 Iniciando BD Specialist Agent...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Initialize specialist agent
    #specialist_agent = DBSpecialistAgent(db_manager)
    #await specialist_agent.initialize()
    
    # Store in app state
    app.state.db_manager = db_manager
    #app.state.specialist_agent = specialist_agent
    
    logger.info("✅ BD Specialist Agent iniciado com sucesso!")
    
    yield
    
    # Cleanup
    logger.info("🔄 Encerrando aplicação...")
    await db_manager.close_all_connections()

# Create FastAPI app
app = FastAPI(
    title="BD Specialist Agent",
    description="Agente especialista em banco de dados para atendimento via WhatsApp",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
app.include_router(connections_router, prefix="/connections", tags=["Database Connections"])
app.include_router(status_router, prefix="/status", tags=["Service Status"])
#app.include_router(health_router, prefix="/health", tags=["Health"])

@app.get("/")
async def root():
    return {
        "message": "BD Specialist Agent API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
