from supabase import create_client
from flask import current_app
import os
from dotenv import load_dotenv

# تحميل متغيرات .env
load_dotenv()

_cached = None

def get_supabase():
    """إنشاء اتصال واحد فقط بـ Supabase"""
    global _cached
    if _cached:
        return _cached

    # قراءة القيم من config أو من .env
    url = current_app.config.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("❌ Supabase credentials are missing! Check your .env file")

    print(f"✅ Connected to Supabase: {url}")  # Debug في التيرمنال

    _cached = create_client(url, key)
    return _cached
