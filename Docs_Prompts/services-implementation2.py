# services/stt_service.py
import logging
import aiofiles
import aiohttp
from typing import Optional
from pathlib import Path

from app.config import settings
from utils.exceptions import STTError

logger = logging.getLogger(__name__)

class STTService:
    """Serviço de Speech-to-Text usando Whisper-Fast"""
    
    def __init__(self):
        self.base_url = settings.STT_SERVICE_URL
        self.timeout = aiohttp.ClientTimeout(total=60)  # 1 minuto para transcrição
        
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcreve áudio para texto usando Whisper-Fast API"""
        
        if not Path(audio_file_path).exists():
            raise STTError(f"Arquivo de áudio não encontrado: {audio_file_path}")
        
        try:
            logger.info(f"🎤 Iniciando transcrição: {audio_file_path}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data for upload
                data = aiohttp.FormData()
                
                async with aiofiles.open(audio_file_path, 'rb') as f:
                    audio_content = await f.read()
                    data.add_field('file', 
                                 audio_content,
                                 filename=Path(audio_file_path).name,
                                 content_type='audio/mpeg')
                
                data.add_field('model', 'whisper-1')  # Required by OpenAI-compatible API
                data.add_field('language', 'pt')  # Portuguese
                
                # Make request to Whisper-Fast API
                async with session.post(
                    f"{self.base_url}/audio/transcriptions",
                    data=data
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise STTError(f"STT API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    transcription = result.get('text', '').strip()
                    
                    if not transcription:
                        raise STTError("Transcrição retornou texto vazio")
                    
                    logger.info(f"✅ Transcrição concluída: {len(transcription)} caracteres")
                    return transcription
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão STT: {str(e)}")
            raise STTError(f"Erro de conexão com serviço STT: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado na transcrição: {str(e)}")
            raise STTError(f"Erro na transcrição: {str(e)}")
    
    async def health_check(self) -> bool:
        """Verifica se o serviço STT está funcionando"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False

# services/tts_service.py
import logging
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional

from app.config import settings
from utils.exceptions import TTSError

logger = logging.getLogger(__name__)

class TTSService:
    """Serviço de Text-to-Speech usando Piper TTS"""
    
    def __init__(self):
        self.base_url = settings.TTS_SERVICE_URL
        self.default_voice = settings.DEFAULT_VOICE
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def synthesize_speech(self, text: str, output_filename: Optional[str] = None) -> str:
        """Sintetiza texto em áudio usando Piper TTS"""
        
        if not text or len(text.strip()) == 0:
            raise TTSError("Texto vazio fornecido para síntese")
        
        if len(text) > 5000:  # Limite de caracteres
            text = text[:4997] + "..."
            logger.warning("⚠️ Texto truncado para síntese TTS")
        
        # Define output path
        if not output_filename:
            import time
            output_filename = f"tts_output_{int(time.time())}.wav"
        
        output_path = Path("temp") / output_filename
        output_path.parent.mkdir(exist_ok=True)
        
        try:
            logger.info(f"🔊 Iniciando síntese TTS: {len(text)} caracteres")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare request parameters
                params = {
                    'text': text,
                    'voice': self.default_voice,
                    'speed': settings.TTS_SPEED
                }
                
                async with session.get(self.base_url, params=params) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSError(f"TTS API error {response.status}: {error_text}")
                    
                    # Save audio content to file
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"✅ Síntese TTS concluída: {output_path}")
                    return str(output_path)
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão TTS: {str(e)}")
            raise TTSError(f"Erro de conexão com serviço TTS: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado na síntese: {str(e)}")
            raise TTSError(f"Erro na síntese de voz: {str(e)}")
    
    async def health_check(self) -> bool:
        """Verifica se o serviço TTS está funcionando"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                params = {'text': 'test', 'voice': self.default_voice}
                async with session.get(f"{self.base_url}/health", params=params) as response:
                    return response.status == 200
        except:
            return False

# services/evolution_service.py
import logging
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
import time

from app.config import settings
from utils.exceptions import EvolutionAPIError

logger = logging.getLogger(__name__)

class EvolutionService:
    """Serviço para interagir com a Evolution API (WhatsApp Gateway)"""
    
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def send_text_message(self, phone_number: str, text: str) -> Dict[str, Any]:
        """Envia mensagem de texto via WhatsApp"""
        
        try:
            logger.info(f"📤 Enviando mensagem de texto para: {phone_number}")
            
            url = f"{self.base_url}/message/sendText/{self.instance}"
            
            payload = {
                "number": phone_number,
                "text": text
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload, headers=self.headers) as response:
                    
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise EvolutionAPIError(f"Evolution API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    logger.info("✅ Mensagem de texto enviada com sucesso")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão Evolution API: {str(e)}")
            raise EvolutionAPIError(f"Erro de conexão: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar texto: {str(e)}")
            raise EvolutionAPIError(f"Erro ao enviar mensagem: {str(e)}")
    
    async def send_audio_message(self, phone_number: str, audio_path: str) -> Dict[str, Any]:
        """Envia mensagem de áudio via WhatsApp"""
        
        if not Path(audio_path).exists():
            raise EvolutionAPIError(f"Arquivo de áudio não encontrado: {audio_path}")
        
        try:
            logger.info(f"📤 Enviando áudio para: {phone_number}")
            
            url = f"{self.base_url}/message/sendMedia/{self.instance}"
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('number', phone_number)
            
            async with aiofiles.open(audio_path, 'rb') as f:
                audio_content = await f.read()
                data.add_field('file', 
                             audio_content,
                             filename=Path(audio_path).name,
                             content_type='audio/wav')
            
            # Headers without Content-Type for multipart
            headers = {"apikey": self.api_key}
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, data=data, headers=headers) as response:
                    
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise EvolutionAPIError(f"Evolution API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    logger.info("✅ Áudio enviado com sucesso")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão Evolution API: {str(e)}")
            raise EvolutionAPIError(f"Erro de conexão: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar áudio: {str(e)}")
            raise EvolutionAPIError(f"Erro ao enviar áudio: {str(e)}")
    
    async def download_audio(self, audio_url: str, phone_number: str) -> str:
        """Baixa arquivo de áudio do WhatsApp"""
        
        try:
            logger.info(f"⬇️ Baixando áudio de: {phone_number}")
            
            # Generate unique filename
            timestamp = int(time.time())
            filename = f"audio_{phone_number}_{timestamp}.ogg"
            output_path = Path("temp") / filename
            output_path.parent.mkdir(exist_ok=True)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(audio_url, headers={"apikey": self.api_key}) as response:
                    
                    if response.status != 200:
                        raise EvolutionAPIError(f"Erro ao baixar áudio: {response.status}")
                    
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"✅ Áudio baixado: {output_path}")
                    return str(output_path)
                    
        except Exception as e:
            logger.error(f"❌ Erro ao baixar áudio: {str(e)}")
            raise EvolutionAPIError(f"Erro no download: {str(e)}")
    
    async def get_instance_status(self) -> Dict[str, Any]:
        """Verifica status da instância do WhatsApp"""
        
        try:
            url = f"{self.base_url}/instance/fetchInstances"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    
                    if response.status != 200:
                        raise EvolutionAPIError(f"Erro ao verificar status: {response.status}")
                    
                    result = await response.json()
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {str(e)}")
            raise EvolutionAPIError(f"Erro de status: {str(e)}")

# services/audio_processor.py
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional

from utils.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Utilitários para processamento de áudio"""
    
    @staticmethod
    async def convert_audio_format(input_path: str, output_path: str, target_format: str = "wav") -> str:
        """Converte áudio para formato específico usando FFmpeg"""
        
        if not Path(input_path).exists():
            raise AudioProcessingError(f"Arquivo não encontrado: {input_path}")
        
        try:
            logger.info(f"🔄 Convertendo áudio: {input_path} -> {target_format}")
            
            # FFmpeg command
            cmd = [
                "ffmpeg", "-i", input_path,
                "-acodec", "pcm_s16le" if target_format == "wav" else "libmp3lame",
                "-ar", "16000",  # Sample rate 16kHz
                "-ac", "1",      # Mono channel
                "-y",            # Overwrite output
                output_path
            ]
            
            # Run FFmpeg asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                raise AudioProcessingError(f"FFmpeg error: {error_msg}")
            
            if not Path(output_path).exists():
                raise AudioProcessingError("Output file was not created")
            
            logger.info(f"✅ Conversão concluída: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Erro na conversão de áudio: {str(e)}")
            raise AudioProcessingError(f"Erro de conversão: {str(e)}")
    
    @staticmethod
    async def get_audio_duration(file_path: str) -> float:
        """Obtém duração do áudio em segundos"""
        
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise AudioProcessingError("Failed to get audio duration")
            
            duration = float(stdout.decode().strip())
            return duration
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter duração: {str(e)}")
            return 0.0
    
    @staticmethod
    def validate_audio_file(file_path: str, max_size_mb: int = 25) -> bool:
        """Valida arquivo de áudio"""
        
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            logger.warning(f"⚠️ Arquivo muito grande: {size_mb:.2f}MB")
            return False
        
        # Check file extension
        valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
        if path.suffix.lower() not in valid_extensions:
            logger.warning(f"⚠️ Formato não suportado: {path.suffix}")
            return False
        
        return True

# database/database_manager.py
import logging
from typing import Dict, Any, Optional, List
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from contextlib import asynccontextmanager

from app.config import settings
from utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador centralizado de conexões com múltiplos bancos de dados"""
    
    def __init__(self):
        self.engines: Dict[str, Engine] = {}
        self.async_engines: Dict[str, AsyncEngine] = {}
        self.connection_configs: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Inicializa todas as conexões de banco configuradas"""
        logger.info("🔌 Inicializando conexões com bancos de dados...")
        
        # Configurar conexões baseadas nas variáveis de ambiente
        await self._setup_mysql_connection()
        await self._setup_postgres_connection()
        await self._setup_supabase_connection()
        await self._setup_oracle_connection()
        await self._setup_sqlserver_connection()
        
        logger.info(f"✅ {len(self.engines)} bancos de dados conectados")
        
        # Test all connections
        await self._test_all_connections()
    
    async def _setup_mysql_connection(self):
        """Configura conexão MySQL/MariaDB"""
        if all([settings.MYSQL_HOST, settings.MYSQL_USER, settings.MYSQL_PASSWORD]):
            try:
                connection_string = (
                    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
                    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE or ''}"
                )
                
                engine = create_engine(
                    connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                db_name = f"mysql_{settings.MYSQL_HOST.replace('.', '_')}"
                self.engines[db_name] = engine
                self.connection_configs[db_name] = {
                    "type": "mysql",
                    "host": settings.MYSQL_HOST,
                    "port": settings.MYSQL_PORT,
                    "database": settings.MYSQL_DATABASE,
                    "description": f"MySQL Database at {settings.MYSQL_HOST}"
                }
                
                logger.info(f"✅ MySQL conectado: {db_name}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao conectar MySQL: {str(e)}")
    
    async def _setup_postgres_connection(self):
        """Configura conexão PostgreSQL"""
        if all([settings.POSTGRES_HOST, settings.POSTGRES_USER, settings.POSTGRES_PASSWORD]):
            try:
                connection_string = (
                    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
                    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE or 'postgres'}"
                )
                
                engine = create_engine(
                    connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                db_name = f"postgres_{settings.POSTGRES_HOST.replace('.', '_')}"
                self.engines[db_name] = engine
                self.connection_configs[db_name] = {
                    "type": "postgres",
                    "host": settings.POSTGRES_HOST,
                    "port": settings.POSTGRES_PORT,
                    "database": settings.POSTGRES_DATABASE,
                    "description": f"PostgreSQL Database at {settings.POSTGRES_HOST}"
                }
                
                logger.info(f"✅ PostgreSQL conectado: {db_name}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao conectar PostgreSQL: {str(e)}")
    
    async def _setup_supabase_connection(self):
        """Configura conexão Supabase (PostgreSQL)"""
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                # Extract connection details from Supabase URL
                import re
                match = re.match(r'https://([^.]+)\.supabase\.co', settings.SUPABASE_URL)
                if not match:
                    raise ValueError("Invalid Supabase URL format")
                
                project_id = match.group(1)
                
                # Use service role key for database access
                connection_string = (
                    f"postgresql+psycopg2://postgres:{settings.SUPABASE_SERVICE_ROLE_KEY}"
                    f"@db.{project_id}.supabase.co:5432/postgres"
                )
                
                engine = create_engine(
                    connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                db_name = f"supabase_{project_id}"
                self.engines[db_name] = engine
                self.connection_configs[db_name] = {
                    "type": "supabase",
                    "host": f"db.{project_id}.supabase.co",
                    "port": 5432,
                    "database": "postgres",
                    "description": f"Supabase Database ({project_id})"
                }
                
                logger.info(f"✅ Supabase conectado: {db_name}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao conectar Supabase: {str(e)}")
    
    async def _setup_oracle_connection(self):
        """Configura conexão Oracle Database"""
        if all([settings.ORACLE_HOST, settings.ORACLE_USER, settings.ORACLE_PASSWORD]):
            try:
                connection_string = (
                    f"oracle+cx_oracle://{settings.ORACLE_USER}:{settings.ORACLE_PASSWORD}"
                    f"@{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME or 'XE'}"
                )
                
                engine = create_engine(
                    connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1 FROM DUAL"))
                
                db_name = f"oracle_{settings.ORACLE_HOST.replace('.', '_')}"
                self.engines[db_name] = engine
                self.connection_configs[db_name] = {
                    "type": "oracle",
                    "host": settings.ORACLE_HOST,
                    "port": settings.ORACLE_PORT,
                    "service_name": settings.ORACLE_SERVICE_NAME,
                    "description": f"Oracle Database at {settings.ORACLE_HOST}"
                }
                
                logger.info(f"✅ Oracle conectado: {db_name}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao conectar Oracle: {str(e)}")
    
    async def _setup_sqlserver_connection(self):
        """Configura conexão SQL Server"""
        if all([settings.SQLSERVER_HOST, settings.SQLSERVER_USER, settings.SQLSERVER_PASSWORD]):
            try:
                connection_string = (
                    f"mssql+pyodbc://{settings.SQLSERVER_USER}:{settings.SQLSERVER_PASSWORD}"
                    f"@{settings.SQLSERVER_HOST}:{settings.SQLSERVER_PORT}/{settings.SQLSERVER_DATABASE or 'master'}"
                    f"?driver=ODBC+Driver+17+for+SQL+Server"
                )
                
                engine = create_engine(
                    connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                db_name = f"sqlserver_{settings.SQLSERVER_HOST.replace('.', '_')}"
                self.engines[db_name] = engine
                self.connection_configs[db_name] = {
                    "type": "sqlserver",
                    "host": settings.SQLSERVER_HOST,
                    "port": settings.SQLSERVER_PORT,
                    "database": settings.SQLSERVER_DATABASE,
                    "description": f"SQL Server Database at {settings.SQLSERVER_HOST}"
                }
                
                logger.info(f"✅ SQL Server conectado: {db_name}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao conectar SQL Server: {str(e)}")
    
    async def _test_all_connections(self):
        """Testa todas as conexões estabelecidas"""
        for db_name, engine in self.engines.items():
            try:
                with engine.connect() as conn:
                    if "oracle" in db_name:
                        conn.execute(text("SELECT 1 FROM DUAL"))
                    else:
                        conn.execute(text("SELECT 1"))
                logger.info(f"🔍 Teste de conexão OK: {db_name}")
            except Exception as e:
                logger.error(f"❌ Teste de conexão falhou: {db_name} - {str(e)}")
    
    async def get_engine(self, db_name: str) -> Optional[Engine]:
        """Retorna engine de um banco específico"""
        return self.engines.get(db_name)
    
    async def get_connected_databases(self) -> Dict[str, Dict[str, Any]]:
        """Retorna informações sobre bancos conectados"""
        return self.connection_configs.copy()
    
    async def execute_query(self, db_name: str, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Executa query em um banco específico"""
        
        if db_name not in self.engines:
            raise DatabaseError(f"Banco de dados não encontrado: {db_name}")
        
        engine = self.engines[db_name]
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                
                # Convert result to list of dictionaries
                columns = result.keys()
                rows = []
                for row in result.fetchall():
                    rows.append(dict(zip(columns, row)))
                
                return rows
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar query em {db_name}: {str(e)}")
            raise DatabaseError(f"Erro na execução da query: {str(e)}")
    
    async def get_table_schema(self, db_name: str, table_name: str) -> Dict[str, Any]:
        """Obtém schema de uma tabela específica"""
        
        if db_name not in self.engines:
            raise DatabaseError(f"Banco de dados não encontrado: {db_name}")
        
        engine = self.engines[db_name]
        db_type = self.connection_configs[db_name]["type"]
        
        try:
            # Query específica por tipo de banco
            if db_type == "mysql":
                query = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = :table_name AND TABLE_SCHEMA = DATABASE()
                ORDER BY ORDINAL_POSITION
                """
            elif db_type in ["postgres", "supabase"]:
                query = """
                SELECT column_name, data_type, is_nullable, column_default,
                       CASE WHEN column_name IN (
                           SELECT column_name FROM information_schema.key_column_usage 
                           WHERE table_name = :table_name
                       ) THEN 'PRI' ELSE '' END as column_key
                FROM information_schema.columns 
                WHERE table_name = :table_name AND table_schema = 'public'
                ORDER BY ordinal_position
                """
            elif db_type == "oracle":
                query = """
                SELECT COLUMN_NAME, DATA_TYPE, NULLABLE as IS_NULLABLE, DATA_DEFAULT as COLUMN_DEFAULT,
                       CASE WHEN COLUMN_NAME IN (
                           SELECT COLUMN_NAME FROM USER_CONS_COLUMNS WHERE TABLE_NAME = :table_name
                       ) THEN 'PRI' ELSE '' END as COLUMN_KEY
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = UPPER(:table_name)
                ORDER BY COLUMN_ID
                """
            elif db_type == "sqlserver":
                query = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
                       CASE WHEN COLUMN_NAME IN (
                           SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                           WHERE TABLE_NAME = :table_name
                       ) THEN 'PRI' ELSE '' END as COLUMN_KEY
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
                """
            else:
                raise DatabaseError(f"Tipo de banco não suportado para schema: {db_type}")
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {"table_name": table_name})
                
                columns = []
                for row in result.fetchall():
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2],
                        "default": row[3],
                        "is_primary_key": row[4] == 'PRI'
                    })
                
                return {
                    "table_name": table_name,
                    "database": db_name,
                    "columns": columns
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter schema da tabela {table_name}: {str(e)}")
            raise DatabaseError(f"Erro ao obter schema: {str(e)}")
    
    async def list_tables(self, db_name: str) -> List[str]:
        """Lista todas as tabelas de um banco"""
        
        if db_name not in self.engines:
            raise DatabaseError(f"Banco de dados não encontrado: {db_name}")
        
        engine = self.engines[db_name]
        db_type = self.connection_configs[db_name]["type"]
        
        try:
            if db_type == "mysql":
                query = "SHOW TABLES"
            elif db_type in ["postgres", "supabase"]:
                query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            elif db_type == "oracle":
                query = "SELECT TABLE_NAME FROM USER_TABLES"
            elif db_type == "sqlserver":
                query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
            else:
                raise DatabaseError(f"Tipo de banco não suportado: {db_type}")
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                tables = [row[0] for row in result.fetchall()]
                return tables
                
        except Exception as e:
            logger.error(f"❌ Erro ao listar tabelas de {db_name}: {str(e)}")
            raise DatabaseError(f"Erro ao listar tabelas: {str(e)}")
    
    async def close_all_connections(self):
        """Fecha todas as conexões"""
        logger.info("🔌 Fechando todas as conexões de banco de dados...")
        
        for db_name, engine in self.engines.items():
            try:
                engine.dispose()
                logger.info(f"✅ Conexão fechada: {db_name}")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar conexão {db_name}: {str(e)}")
        
        self.engines.clear()
        self.async_engines.clear()
        self.connection_configs.clear()