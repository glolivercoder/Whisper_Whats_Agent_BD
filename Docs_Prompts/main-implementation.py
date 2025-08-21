# app/main.py
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.webhook import router as webhook_router
from app.api.health import router as health_router
from agents.db_specialist_agent import DBSpecialistAgent
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
    specialist_agent = DBSpecialistAgent(db_manager)
    await specialist_agent.initialize()
    
    # Store in app state
    app.state.db_manager = db_manager
    app.state.specialist_agent = specialist_agent
    
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
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
app.include_router(health_router, prefix="/health", tags=["health"])

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

# app/config.py
import os
from typing import List, Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Evolution API
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    EVOLUTION_INSTANCE: str = os.getenv("EVOLUTION_INSTANCE", "bd-specialist")
    
    # External Services
    STT_SERVICE_URL: str = os.getenv("STT_SERVICE_URL", "http://localhost:8001/v1")
    TTS_SERVICE_URL: str = os.getenv("TTS_SERVICE_URL", "http://localhost:8002/api/tts")
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")  # openrouter, openai, gemini
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Default LLM Models
    DEFAULT_LLM_MODEL: str = "google/gemini-pro"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Database Configurations
    # MySQL
    MYSQL_HOST: Optional[str] = os.getenv("MYSQL_HOST")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER: Optional[str] = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: Optional[str] = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE: Optional[str] = os.getenv("MYSQL_DATABASE")
    
    # PostgreSQL
    POSTGRES_HOST: Optional[str] = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DATABASE: Optional[str] = os.getenv("POSTGRES_DATABASE")
    
    # Supabase
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Oracle
    ORACLE_HOST: Optional[str] = os.getenv("ORACLE_HOST")
    ORACLE_PORT: int = int(os.getenv("ORACLE_PORT", 1521))
    ORACLE_USER: Optional[str] = os.getenv("ORACLE_USER")
    ORACLE_PASSWORD: Optional[str] = os.getenv("ORACLE_PASSWORD")
    ORACLE_SERVICE_NAME: Optional[str] = os.getenv("ORACLE_SERVICE_NAME")
    
    # SQL Server
    SQLSERVER_HOST: Optional[str] = os.getenv("SQLSERVER_HOST")
    SQLSERVER_PORT: int = int(os.getenv("SQLSERVER_PORT", 1433))
    SQLSERVER_USER: Optional[str] = os.getenv("SQLSERVER_USER")
    SQLSERVER_PASSWORD: Optional[str] = os.getenv("SQLSERVER_PASSWORD")
    SQLSERVER_DATABASE: Optional[str] = os.getenv("SQLSERVER_DATABASE")
    
    # Security Settings
    MAX_QUERY_EXECUTION_TIME: int = 30  # seconds
    ALLOWED_OPERATIONS: List[str] = ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]
    RESTRICTED_OPERATIONS: List[str] = ["INSERT", "UPDATE", "CREATE", "ALTER"]
    FORBIDDEN_OPERATIONS: List[str] = ["DELETE", "DROP", "TRUNCATE"]
    
    # Audio Settings
    MAX_AUDIO_SIZE_MB: int = 25
    SUPPORTED_AUDIO_FORMATS: List[str] = [".mp3", ".wav", ".ogg", ".m4a"]
    
    # TTS Settings
    DEFAULT_VOICE: str = "pt_BR-faber-medium"
    TTS_SPEED: float = 1.0
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# app/api/webhook.py
import os
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from models.webhook_models import WebhookData, MessageData
from services.evolution_service import EvolutionService
from services.audio_processor import AudioProcessor
from services.stt_service import STTService
from services.tts_service import TTSService
from utils.helpers import extract_phone_number, is_audio_message

router = APIRouter()
logger = logging.getLogger(__name__)

evolution_service = EvolutionService()
audio_processor = AudioProcessor()
stt_service = STTService()
tts_service = TTSService()

@router.post("/evolution")
async def handle_evolution_webhook(request: Request):
    """Handler principal para webhooks da Evolution API"""
    try:
        # Parse webhook data
        webhook_data = await request.json()
        logger.info(f"📨 Webhook recebido: {webhook_data.get('event', 'unknown')}")
        
        # Validate webhook structure
        if not _is_valid_webhook(webhook_data):
            logger.warning("⚠️ Webhook inválido recebido")
            return JSONResponse({"status": "ignored", "reason": "invalid_webhook"})
        
        # Handle only audio messages
        if not _is_audio_message(webhook_data):
            logger.info("ℹ️ Mensagem não é de áudio, ignorando")
            return JSONResponse({"status": "ignored", "reason": "not_audio_message"})
        
        # Extract message data
        message_data = _extract_message_data(webhook_data)
        phone_number = extract_phone_number(message_data["remoteJid"])
        
        logger.info(f"🎵 Processando áudio do cliente: {phone_number}")
        
        # Process the audio message
        await _process_audio_message(message_data, phone_number, request.app.state)
        
        return JSONResponse({"status": "processed", "timestamp": datetime.utcnow().isoformat()})
        
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")

async def _process_audio_message(message_data: Dict[str, Any], phone_number: str, app_state):
    """Processa uma mensagem de áudio completa"""
    temp_files = []
    
    try:
        # 1. Download do áudio
        logger.info("⬇️ Baixando áudio...")
        audio_url = message_data.get("mediaUrl") or message_data.get("url")
        if not audio_url:
            raise ValueError("URL do áudio não encontrada na mensagem")
            
        audio_input_path = await evolution_service.download_audio(audio_url, phone_number)
        temp_files.append(audio_input_path)
        
        # 2. Transcrição (STT)
        logger.info("🎤 Transcrevendo áudio...")
        transcribed_text = await stt_service.transcribe_audio(audio_input_path)
        logger.info(f"📝 Texto transcrito: {transcribed_text[:100]}...")
        
        if not transcribed_text or transcribed_text.strip() == "":
            await evolution_service.send_text_message(
                phone_number, 
                "Desculpe, não consegui entender o áudio. Poderia repetir ou enviar uma mensagem de texto?"
            )
            return
        
        # 3. Processamento pelo Agente Especialista
        logger.info("🤖 Consultando agente especialista...")
        specialist_agent = app_state.specialist_agent
        
        # Adiciona contexto da conversa
        conversation_context = {
            "customer_phone": phone_number,
            "current_timestamp": datetime.utcnow().isoformat(),
            "message_type": "audio",
            "transcribed_text": transcribed_text
        }
        
        agent_response = await specialist_agent.process_query(
            query=transcribed_text,
            context=conversation_context
        )
        
        logger.info(f"🧠 Resposta do agente: {agent_response[:100]}...")
        
        # 4. Síntese de voz (TTS)
        logger.info("🔊 Gerando resposta em áudio...")
        audio_output_path = await tts_service.synthesize_speech(
            text=agent_response,
            output_filename=f"response_{phone_number}_{int(datetime.utcnow().timestamp())}.wav"
        )
        temp_files.append(audio_output_path)
        
        # 5. Envio da resposta
        logger.info("📤 Enviando resposta em áudio...")
        await evolution_service.send_audio_message(phone_number, audio_output_path)
        
        logger.info("✅ Processamento completo do áudio finalizado")
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento do áudio: {str(e)}")
        
        # Enviar mensagem de erro para o cliente
        error_message = (
            "Desculpe, ocorreu um erro ao processar sua consulta. "
            "Tente novamente em alguns instantes ou entre em contato com o suporte."
        )
        
        try:
            await evolution_service.send_text_message(phone_number, error_message)
        except:
            logger.error("❌ Falha ao enviar mensagem de erro para o cliente")
            
    finally:
        # Cleanup de arquivos temporários
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"