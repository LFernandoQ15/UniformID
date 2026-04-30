import json, os, time
from supabase import create_client
import streamlit as st

# ── CONFIG ─────────────────────────────────────────────────────────────
LOGO_FULL_B64 = "TU_BASE64_AQUI"

st.set_page_config(
    page_title="UniformID – Asistencia",
    page_icon="👥",
    layout="wide",
)

# ── SUPABASE ───────────────────────────────────────────────────────────
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ── CACHE (🔥 mejora rendimiento) ──────────────────────────────────────
@st.cache_data(ttl=2)
def load_attendance():
    try:
        response = supabase.table("attendance")\
            .select("*")\
            .order("created_at", desc=False)\
            .execute()

        people = response.data

    except Exception:
        # 🔥 fallback offline
        if os.path.exists("attendance.json"):
            with open("attendance.json") as f:
                data = json.load(f)
                people = list(data.values())
        else:
            people = []

    # 🔥 limpieza de datos
    clean = []
    for p in people:
        if "name" in p and "confidence" in p:
            if p.get("confidence", 0) <= 1:
                p["confidence"] = round(p["confidence"] * 100, 1)
            clean.append(p)

    # 🔥 orden seguro
    clean = sorted(clean, key=lambda x: x.get("created_at", ""))

    return clean


people = load_attendance()

# ── DETECCIÓN DE EVENTOS ───────────────────────────────────────────────
if "last_count" not in st.session_state:
    st.session_state.last_count = 0

if "toast" not in st.session_state:
    st.session_state.toast = None

if len(people) > st.session_state.last_count:
    nuevo = people[-1]

    if "desconocido" in nuevo["name"].lower():
        st.session_state.toast = "⚠️ Desconocido detectado"
    else:
        st.session_state.toast = f"✔ {nuevo['name']} registrado"

st.session_state.last_count = len(people)

# ── TOAST NOTIFICATION ─────────────────────────────────────────────────
if st.session_state.toast:
    st.toast(st.session_state.toast)
    st.session_state.toast = None

# ── HEADER ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:20px;background:#1B2A4A;border-radius:5px;margin-bottom:20px;">
    <img src="data:image/jpeg;base64,{LOGO_FULL_B64}" style="max-height:90px;">
    <div style="color:#a8bedd;font-size:12px;">Sistema activo</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
total = len(people)
avg_conf = round(sum(p["confidence"] for p in people) / total, 1) if total else 0
last = people[-1]["name"] if people else "—"

st.markdown(f"""
<div style="display:flex;gap:10px;margin-bottom:20px;">
    <div style="flex:1;background:white;padding:10px;border-radius:5px;text-align:center;">
        <h2>{total}</h2><small>Personas</small>
    </div>
    <div style="flex:1;background:white;padding:10px;border-radius:5px;text-align:center;">
        <h2>{avg_conf}%</h2><small>Confianza</small>
    </div>
    <div style="flex:1;background:white;padding:10px;border-radius:5px;text-align:center;">
        <h4>{last}</h4><small>Último</small>
    </div>
</div>
""", unsafe_allow_html=True)

# ── LISTA ──────────────────────────────────────────────────────────────
st.markdown("### Registro")

if not people:
    st.info("Esperando detecciones...")
else:
    for p in reversed(people):
        conf = p["confidence"]
        color = "#5CB85C" if conf >= 80 else "#f3ba73" if conf >= 60 else "#f97d7d"

        st.markdown(f"""
        <div style="background:white;padding:10px;margin-bottom:5px;border-left:5px solid {color}">
            <b>{p['name']}</b> — {p['time']} — {conf:.0f}%
            {"⚠️ SIN UNIFORME" if not p.get("uniforme", True) else ""}
        </div>
        """, unsafe_allow_html=True)

# ── DEBUG / STATUS (invisible pero útil) ────────────────────────────────
st.caption(f"Última actualización: {time.strftime('%H:%M:%S')}")

# ── AUTO REFRESH ───────────────────────────────────────────────────────
time.sleep(2)
st.rerun()
