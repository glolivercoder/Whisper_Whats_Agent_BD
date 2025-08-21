# utils/exceptions.py
"""Exceções customizadas para o sistema"""

class BaseAgentError(Exception):
    """Exceção base para o sistema"""
    pass

class DatabaseError(BaseAgentError):
    """Erro relacionado a banco de dados"""
    pass

class AgentError(BaseAgentError):
    """Erro no processamento do agente"""
    pass

class STTError(BaseAgentError):
    """Erro no serviço de Speech-to-Text"""
    pass

class TTSError(BaseAgentError):
    """Erro no serviço de Text-to-Speech"""
    pass

class EvolutionAPIError(BaseAgentError):
    """Erro na Evolution API"""
    pass

class AudioProcessingError(BaseAgentError):
    """Erro no processamento de áudio"""
    pass

# utils/logger.py
import logging
import logging.config
from typing import Dict, Any

def setup_logging(level: str = "INFO") -> None:
    """Configura sistema de logging"""
    
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/bd_specialist.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "root": {
            "level": level,
            "handlers": ["console", "file"]
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }
    
    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)
    
    logging.config.dictConfig(config)

# utils/helpers.py
import re
import os
from typing import Optional, Dict, Any
from pathlib import Path

def extract_phone_number(remote_jid: str) -> str:
    """Extrai número de telefone do remote_jid"""
    # Remove sufixos como @c.us, @s.whatsapp.net
    phone = remote_jid.split('@')[0]
    # Remove código do país se presente (assumindo Brasil +55)
    if phone.startswith('55') and len(phone) > 11:
        phone = phone[2:]
    return phone

def is_audio_message(webhook_data: Dict[str, Any]) -> bool:
    """Verifica se a mensagem é de áudio"""
    try:
        message = webhook_data.get("data", {}).get("message", {})
        message_type = message.get("messageType") or message.get("type")
        return message_type in ["audioMessage", "audio"]
    except:
        return False

def format_file_size(bytes_size: int) -> str:
    """