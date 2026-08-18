from __future__ import annotations

from supabase import Client, create_client

from ..config import settings


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_active_sources() -> list[dict]:
    response = (
        get_supabase()
        .table("sources")
        .select("id,name,url,source_type,country,language")
        .eq("active", True)
        .execute()
    )
    return response.data or []
