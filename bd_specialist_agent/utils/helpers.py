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
    """Formata bytes em KB, MB, GB"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024**2:
        return f"{bytes_size/1024:.2f} KB"
    elif bytes_size < 1024**3:
        return f"{bytes_size/1024**2:.2f} MB"
    else:
        return f"{bytes_size/1024**3:.2f} GB"
