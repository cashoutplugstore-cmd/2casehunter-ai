from supabase import Client, create_client

from .config import settings


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase service credentials are not configured")

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
