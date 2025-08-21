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
