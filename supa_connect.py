import os
from supabase import create_client, Client
from dotenv import load_dotenv

class SupabaseConfigError(RuntimeError):
    """Supabase 环境变量配置错误"""
    pass

class SupabaseInitError(RuntimeError):
    """Supabase 客户端初始化失败"""
    pass

def get_supabase_client() -> Client:
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url:
        raise SupabaseConfigError("缺少环境变量 SUPABASE_URL")

    if not key:
        raise SupabaseConfigError("缺少环境变量 SUPABASE_KEY")

    try:
        client: Client = create_client(url, key)
    except Exception as e:
        raise SupabaseInitError(f"Supabase 客户端初始化失败: {e}") from e

    return client
