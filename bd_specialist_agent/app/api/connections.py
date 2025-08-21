# app/api/connections.py
import logging
from fastapi import APIRouter, Depends, Request
from typing import List, Dict, Any

from database.connections import DatabaseManager

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db_manager(request: Request) -> DatabaseManager:
    return request.app.state.db_manager

@router.get("/", response_model=List[Dict[str, Any]])
async def list_database_connections(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Lista todas as conexões de banco de dados ativas."""
    connections = await db_manager.get_connected_databases()
    return list(connections.values())
