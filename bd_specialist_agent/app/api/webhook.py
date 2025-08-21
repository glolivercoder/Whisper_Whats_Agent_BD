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
        #if not _is_valid_webhook(webhook_data):
        #    logger.warning("⚠️ Webhook inválido recebido")
        #    return JSONResponse({"status": "ignored", "reason": "invalid_webhook"})
        
        # Handle only audio messages
        if not is_audio_message(webhook_data):
            logger.info("ℹ️ Mensagem não é de áudio, ignorando")
            return JSONResponse({"status": "ignored", "reason": "not_audio_message"})
        
        # Extract message data
        message_data = webhook_data #_extract_message_data(webhook_data)
        phone_number = extract_phone_number(message_data["key"]["remoteJid"])
        
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
                    logger.debug(f"Arquivo temporário removido: {temp_file}")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao remover arquivo temporário {temp_file}: {e}")
