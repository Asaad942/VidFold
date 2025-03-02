"""
Supabase database operations for VidFold backend
"""
from typing import Dict, Any, List, Optional
from supabase import create_client
from ..core.config import get_settings

settings = get_settings()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def insert_one(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a single record into a table"""
    try:
        response = await supabase.table(table).insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Error inserting into {table}: {str(e)}")

async def select_by_id(table: str, id: str) -> Optional[Dict[str, Any]]:
    """Select a single record by id"""
    try:
        response = await supabase.table(table).select("*").eq("id", id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise Exception(f"Error selecting from {table}: {str(e)}")

async def select_all(table: str) -> List[Dict[str, Any]]:
    """Select all records from a table"""
    try:
        response = await supabase.table(table).select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        raise Exception(f"Error selecting from {table}: {str(e)}")

async def update_by_id(table: str, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a single record by id"""
    try:
        response = await supabase.table(table).update(data).eq("id", id).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Error updating {table}: {str(e)}")

async def delete_by_id(table: str, id: str) -> bool:
    """Delete a single record by id"""
    try:
        response = await supabase.table(table).delete().eq("id", id).execute()
        return bool(response.data)
    except Exception as e:
        raise Exception(f"Error deleting from {table}: {str(e)}")

__all__ = [
    'insert_one',
    'select_by_id',
    'select_all',
    'update_by_id',
    'delete_by_id',
    'supabase'
] 