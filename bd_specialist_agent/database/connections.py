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