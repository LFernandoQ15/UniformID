import os, time
import streamlit as st
from supabase import create_client

# ── CONFIG ─────────────────────────────────────────────
st.set_page_config(
    page_title="UniformID – Control de Acceso",
    page_icon="👁️",
    layout="wide",
)

# ── SUPABASE ───────────────────────────────────────────
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ── UI HEADER ──────────────────────────────────────────
st.markdown("""
<style>
:root {
    --navy:#1B2A4A;
    --blue:#2E6FC4;
    --green:#5CB85C;
    --light:#EEF2F8;
    --white:#FFFFFF;
    --border:#CDD6E8;
    --muted:#6B7A99;
}
html,body,[class*="css"]{
    background:var(--light);
    font-family:sans-serif;
}
.kpi{
    background:white;
    padding:1rem;
    border-radius:6px;
    text-align:center;
    border-top:4px solid var(--blue);
}
.kpi.green{border-top:4px solid var(--green);}
.row{
    background:white;
    padding:.6rem;
    border-left:4px solid var(--green);
    margin-bottom:.4rem;
    border-radius:4px;
}
.alert{
    background:#ffecec;
    color:#d32f2f;
    padding:.6rem;
    border-radius:4px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

st.title("👁️ UniformID – Sistema de Control de Acceso")

st.markdown("""
Sistema en tiempo real basado en reconocimiento facial.

✔ Registro automático de asistencia  
✔ Verificación de uniforme  
✔ Sincronización en la nube  
""")

st.success("🟢 Sistema en línea – Actualización automática")

# ── CARGA DATOS ────────────────────────────────────────
def load_data():
    try:
        res = supabase.table("attendance")\
            .select("*")\
            .order("created_at", desc=False)\
            .execute()

        data = res.data or []

        for p in data:
            if p.get("confidence", 0) <= 1:
                p["confidence"] *= 100

        return data

    except Exception as e:
        st.error(f"Error conexión: {e}")
        return []

people = load_data()

# ── KPI ────────────────────────────────────────────────
total = len(people)
avg = round(sum(p["confidence"] for p in people)/total,1) if total else 0
last = people[-1]["name"] if people else "—"

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"<div class='kpi'><h2>{total}</h2><p>Asistencia registrada</p></div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='kpi green'><h2>{avg:.0f}%</h2><p>Confianza promedio</p></div>", unsafe_allow_html=True)

with c3:
    st.markdown(f"<div class='kpi'><h2>{last}</h2><p>Último acceso</p></div>", unsafe_allow_html=True)

# ── ALERTA DESCONOCIDO ─────────────────────────────────
unknowns = [p for p in people if p.get("name") == "Desconocido"]

if unknowns:
    st.markdown(f"""
    <div class="alert">
    ⚠ {len(unknowns)} persona(s) desconocida(s) detectada(s)
    </div>
    """, unsafe_allow_html=True)

# ── LISTA ──────────────────────────────────────────────
st.markdown("### 📋 Registro en tiempo real")

if not people:
    st.info("📡 Esperando detecciones desde el sistema de cámara...")
else:
    for i, p in enumerate(reversed(people), 1):

        conf = p["confidence"]

        if conf >= 80:
            color = "#5CB85C"
        elif conf >= 60:
            color = "#f3ba73"
        else:
            color = "#f97d7d"

        uniforme = "✔ Uniforme" if p.get("uniforme", True) else "⚠ Sin uniforme"

        st.markdown(f"""
        <div class="row">
            <b>{i}. {p['name']}</b> — {p['time']} <br>
            Confianza: <span style="color:{color}">{conf:.0f}%</span> <br>
            {uniforme}
        </div>
        """, unsafe_allow_html=True)

# ── FOOTER ─────────────────────────────────────────────
st.markdown("---")
st.caption("UniformID · Sistema de control de acceso · v1.0")

# ── REFRESH ────────────────────────────────────────────
time.sleep(2)
st.rerun()
