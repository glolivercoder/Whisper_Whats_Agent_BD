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
