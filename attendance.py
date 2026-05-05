"""
attendance.py — Registro offline-first con sincronización a Supabase
─────────────────────────────────────────────────────────────────────
Flujo:
  1. Cada registro se guarda SIEMPRE en cola local (JSON en disco)
  2. Un hilo de fondo intenta sincronizar la cola con Supabase
  3. Si no hay internet, los registros esperan en cola y se sincronizan
     automáticamente cuando vuelve la conexión
  4. El cooldown funciona aunque no haya internet (basado en memoria)
"""

import time
import threading
import os
import json

from supabase import create_client
from config import ATTENDANCE_FILE

# ── Conexión Supabase ────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None
    print(f"[ATTENDANCE] Supabase no disponible al arrancar: {e}")

# ── Archivos locales ─────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(BASE_DIR, "attendance_queue.json")   # pendientes

# ── Estado en memoria ────────────────────────────────────────────────────────
_registry: dict[str, float] = {}   # name → timestamp último registro
_lock      = threading.Lock()

COOLDOWN_SEG       = 10    # segundos mínimos entre registros por persona
SYNC_INTERVALO_SEG = 15    # cada cuántos segundos intenta sincronizar la cola


# ─────────────────────────────────────────────────────────────────────────────
# Cola local (disco)
# ─────────────────────────────────────────────────────────────────────────────

def _queue_load() -> list[dict]:
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _queue_save(queue: list[dict]):
    try:
        tmp = QUEUE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
        os.replace(tmp, QUEUE_FILE)
    except Exception as e:
        print(f"[ATTENDANCE] Error guardando cola local: {e}")


def _queue_push(registro: dict):
    queue = _queue_load()
    queue.append(registro)
    _queue_save(queue)


# ─────────────────────────────────────────────────────────────────────────────
# Sincronización con Supabase
# ─────────────────────────────────────────────────────────────────────────────

def _sync_queue():
    """
    Envía los registros pendientes a Supabase.
    Al primer fallo de red se detiene — los demás quedan en cola.
    """
    queue = _queue_load()
    if not queue or supabase is None:
        return

    enviados = []
    for registro in queue:
        try:
            supabase.table("attendance").insert(registro).execute()
            enviados.append(registro)
        except Exception:
            remaining = len(queue) - len(enviados)
            print(f"[ATTENDANCE] Sin conexión — {remaining} registros "
                  f"pendientes en cola local")
            break

    if enviados:
        pendientes = [r for r in queue if r not in enviados]
        _queue_save(pendientes)
        print(f"[ATTENDANCE] Sincronizados {len(enviados)} registros con Supabase")


def _hilo_sync():
    """Hilo daemon que intenta sincronizar la cola cada SYNC_INTERVALO_SEG."""
    while True:
        time.sleep(SYNC_INTERVALO_SEG)
        try:
            _sync_queue()
        except Exception as e:
            print(f"[ATTENDANCE] Error en hilo de sync: {e}")


# Arrancar hilo de sincronización al importar el módulo
threading.Thread(target=_hilo_sync, daemon=True, name="attendance-sync").start()


# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────

def add_person(name: str, confidence: float, uniforme: bool = True) -> bool:
    """
    Registra a una persona.
    Siempre escribe en cola local primero — nunca se pierde un registro.
    Retorna True si fue registrado, False si está en cooldown.
    """
    with _lock:
        ahora = time.time()

        if name in _registry and ahora - _registry[name] < COOLDOWN_SEG:
            return False

        tipo = _determinar_tipo(name)

        registro = {
            "name":       name,
            "confidence": round(confidence, 1),
            "time":       time.strftime("%H:%M:%S"),
            "date":       time.strftime("%Y-%m-%d"),
            "uniforme":   uniforme,
            "tipo":       tipo,
        }

        # 1. Guardar localmente siempre
        _queue_push(registro)
        _registry[name] = ahora

        estado_u = "con uniforme" if uniforme else "SIN uniforme"
        print(f"[ATTENDANCE] {tipo.upper()}: {name} ({confidence:.1f}%) "
              f"— {estado_u} [guardado localmente]")


        threading.Thread(target=_sync_queue, daemon=True).start()

        return True


def get_people() -> list[dict]:
    """
    Registros del día. Intenta Supabase primero; si falla usa cola local.
    """
    hoy = time.strftime("%Y-%m-%d")

    if supabase is not None:
        try:
            res = supabase.table("attendance")\
                .select("*")\
                .eq("date", hoy)\
                .execute()
            return res.data or []
        except Exception:
            pass

    return [r for r in _queue_load() if r.get("date") == hoy]


def clear():
    """Limpia registros del día en Supabase y cola local."""
    with _lock:
        hoy = time.strftime("%Y-%m-%d")

        queue = _queue_load()
        _queue_save([r for r in queue if r.get("date") != hoy])
        _registry.clear()

        if supabase is not None:
            try:
                supabase.table("attendance")\
                    .delete()\
                    .eq("date", hoy)\
                    .execute()
                print("[ATTENDANCE] Limpieza realizada en Supabase y local")
            except Exception as e:
                print(f"[ATTENDANCE] Limpieza local OK, Supabase falló: {e}")




def _determinar_tipo(name: str) -> str:
    """Alterna entrada/salida según el último registro de la persona."""
    if supabase is not None:
        try:
            ultimo = supabase.table("attendance")\
                .select("tipo")\
                .eq("name", name)\
                .order("id", desc=True)\
                .limit(1)\
                .execute()
            if ultimo.data:
                return "salida" if ultimo.data[0]["tipo"] == "entrada" else "entrada"
            return "entrada"
        except Exception:
            pass

    registros = [r for r in _queue_load() if r.get("name") == name]
    if registros:
        return "salida" if registros[-1].get("tipo") == "entrada" else "entrada"
    return "entrada"
