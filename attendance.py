import time
import threading
import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

_registry = {}
_lock = threading.Lock()


def add_person(name: str, confidence: float, uniforme: bool = True) -> bool:
    with _lock:
        if name in _registry:
            return False

        data = {
            "name": name,
            "confidence": round(confidence, 1),
            "time": time.strftime("%H:%M:%S"),
            "date": time.strftime("%Y-%m-%d"),
            "uniforme": uniforme,
        }

        try:
            # Evitar duplicados en base de datos
            existing = supabase.table("attendance")\
                .select("id")\
                .eq("name", name)\
                .eq("date", data["date"])\
                .execute()

            if existing.data:
                return False

            supabase.table("attendance").insert(data).execute()
            _registry[name] = data

            print(f"[ATTENDANCE] Registrado: {name}")
            return True

        except Exception as e:
            print(f"[ERROR] {e}")
            return False


def clear():
    with _lock:
        try:
            hoy = time.strftime("%Y-%m-%d")

            supabase.table("attendance")\
                .delete()\
                .eq("date", hoy)\
                .execute()

            _registry.clear()
            print("[ATTENDANCE] Limpieza por día realizada")

        except Exception as e:
            print(f"[ERROR] {e}")