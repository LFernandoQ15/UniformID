
import time
import threading
import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

_registry = {}
_lock = threading.Lock()

COOLDOWN_SEG = 10  # tiempo mínimo entre registros por persona


def add_person(name: str, confidence: float, uniforme: bool = True) -> bool:
    with _lock:
        ahora = time.time()

        # ── Evitar rebotes (detecciones consecutivas) ───────────────────────
        if name in _registry and ahora - _registry[name] < COOLDOWN_SEG:
            return False

        fecha = time.strftime("%Y-%m-%d")
        hora  = time.strftime("%H:%M:%S")

        try:
            # ── Obtener último registro ────────────────────────────────────
            ultimo = supabase.table("attendance")\
                .select("tipo, time")\
                .eq("name", name)\
                .order("id", desc=True)\
                .limit(1)\
                .execute()

            # ── Determinar tipo (entrada/salida) ───────────────────────────
            if not ultimo.data:
                tipo = "entrada"
            else:
                tipo = "salida" if ultimo.data[0]["tipo"] == "entrada" else "entrada"

            # ── Construir registro ─────────────────────────────────────────
            data = {
                "name": name,
                "confidence": round(confidence, 1),
                "time": hora,
                "date": fecha,
                "uniforme": uniforme,
                "tipo": tipo,
            }

            # ── Insertar en Supabase ───────────────────────────────────────
            supabase.table("attendance").insert(data).execute()

            # ── Actualizar registro local ──────────────────────────────────
            _registry[name] = ahora

            print(f"[ATTENDANCE] {tipo.upper()}: {name}")
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
