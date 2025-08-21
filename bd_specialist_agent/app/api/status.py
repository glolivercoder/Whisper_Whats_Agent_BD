# app/api/status.py
import logging
from fastapi import APIRouter
from typing import List, Dict, Any

from services.stt_service import STTService
from services.tts_service import TTSService
from services.evolution_service import EvolutionService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Dict[str, Any]])
async def get_services_status():
    """Verifica e retorna o status dos serviços externos."""
    services = [
        {"name": "STT Service (Whisper)", "service": STTService()},
        {"name": "TTS Service (Piper)", "service": TTSService()},
        {"name": "Evolution API", "service": EvolutionService()},
    ]
    
    status_list = []
    for service_info in services:
        is_healthy = await service_info["service"].health_check()
        status_list.append({
            "name": service_info["name"],
            "status": "Online" if is_healthy else "Offline"
        })
        
    return status_list
