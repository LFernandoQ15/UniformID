"""
app.py  — Streamlit dashboard de asistencia · UniformID
Diseño del sistema original + lógica Supabase.
Ejecutar:  streamlit run app.py
"""
import os, time
import streamlit as st
from supabase import create_client

# ── Logos incrustados como base64 ──────────────────────────────────────────
LOGO_FULL_B64 = "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"

# ── CONFIG ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UniformID – Control de Acceso",
    page_icon="👁️",
    layout="wide",
)

# ── SUPABASE ───────────────────────────────────────────────────────────────
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ── ESTILOS (diseño original) ──────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700;900&family=Barlow+Condensed:wght@600;800&display=swap');
:root {{
    --navy:  #1B2A4A;
    --blue:  #2E6FC4;
    --green: #5CB85C;
    --light: #EEF2F8;
    --white: #FFFFFF;
    --border:#CDD6E8;
    --muted: #6B7A99;
}}
html,body,[class*="css"]{{font-family:'Barlow',sans-serif;background:var(--light);color:var(--navy);}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{{background:var(--light);}}

/* ── Hero ── */
.uid-hero{{
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    background:var(--navy);border-radius:4px;padding:2.2rem 1.8rem 1.6rem;
    margin-bottom:1.6rem;text-align:center;}}
.uid-hero img{{max-height:90px;object-fit:contain;margin-bottom:.9rem;}}
.uid-live{{display:flex;align-items:center;gap:8px;font-size:.78rem;font-weight:600;
    letter-spacing:1.5px;text-transform:uppercase;color:#a8bedd;}}
.uid-dot{{width:8px;height:8px;background:#5CB85C;border-radius:50%;
    animation:blink 1.2s ease-in-out infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.15;}}}}

/* ── KPIs ── */
.kpi-grid{{display:flex;gap:1rem;margin-bottom:1.4rem;}}
.kpi{{flex:1;background:var(--white);border:1px solid var(--border);
    border-top:3px solid var(--blue);border-radius:3px;padding:1.1rem 1.4rem;text-align:center;}}
.kpi.green{{border-top-color:var(--green);}}
.kpi .val{{font-family:'Barlow Condensed',sans-serif;font-size:2.8rem;font-weight:800;
    color:var(--navy);line-height:1.05;}}
.kpi .val.small{{font-size:1.35rem;}}
.kpi .lbl{{font-size:.68rem;color:var(--muted);text-transform:uppercase;
    letter-spacing:1.8px;margin-top:5px;}}

/* ── Section title ── */
.section-title{{font-size:.68rem;text-transform:uppercase;letter-spacing:2.5px;
    color:var(--muted);margin:1rem 0 .7rem;display:flex;align-items:center;gap:8px;}}
.section-title::after{{content:'';flex:1;height:1px;background:var(--border);}}

/* ── Rows ── */
.row{{display:flex;align-items:center;gap:1rem;background:var(--white);
    border:1px solid var(--border);border-left:4px solid var(--green);
    border-radius:3px;padding:.72rem 1.2rem;margin-bottom:.45rem;
    animation:slideIn .25s ease;}}
@keyframes slideIn{{from{{opacity:0;transform:translateY(-5px);}}to{{opacity:1;transform:translateY(0);}}}}
.row-num{{font-size:1rem;color:var(--muted);min-width:26px;text-align:right;font-weight:700;}}
.row-name{{font-weight:700;font-size:.97rem;color:var(--navy);flex:1;}}
.row-time{{font-size:.78rem;color:var(--muted);min-width:70px;}}
.conf-bar-wrap{{width:88px;}}
.conf-bar{{height:5px;border-radius:2px;background:#dde4f0;overflow:hidden;}}
.conf-bar-fill{{height:100%;border-radius:2px;}}
.conf-pct{{font-size:.73rem;font-weight:700;margin-top:3px;}}
.badge{{font-size:.65rem;font-weight:700;padding:3px 10px;border-radius:2px;
    background:#e8f5e9;color:var(--green);border:1px solid #c8e6c9;
    letter-spacing:.8px;text-transform:uppercase;}}
.alert-box{{background:#ffecec;color:#d32f2f;padding:.75rem 1.2rem;
    border-radius:3px;border-left:4px solid #d32f2f;font-weight:700;
    margin-bottom:.8rem;font-size:.88rem;}}

/* ── Empty state ── */
.empty-state{{text-align:center;padding:3rem;color:var(--muted);
    border:1px dashed var(--border);border-radius:4px;background:var(--white);font-size:.9rem;}}
.empty-state span{{font-size:2rem;display:block;margin-bottom:.6rem;}}
</style>
""", unsafe_allow_html=True)

# ── CARGA DATOS ────────────────────────────────────────────────────────────
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

# ── HEADER CON LOGO ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="uid-hero">
    <img src="data:image/jpeg;base64,{LOGO_FULL_B64}" alt="UniformID">
    <div class="uid-live">
        <div class="uid-dot"></div>
        Sistema activo · Actualización automática
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────────
total    = len(people)
avg_conf = round(sum(p["confidence"] for p in people) / total, 1) if total else 0
last     = people[-1]["name"] if people else "—"

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi">
        <div class="val">{total}</div>
        <div class="lbl">Asistencia registrada</div>
    </div>
    <div class="kpi green">
        <div class="val">{avg_conf:.0f}%</div>
        <div class="lbl">Confianza promedio</div>
    </div>
    <div class="kpi">
        <div class="val small">{last}</div>
        <div class="lbl">Último acceso</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── ALERTA DESCONOCIDO ─────────────────────────────────────────────────────
unknowns = [p for p in people if p.get("name") == "Desconocido"]
if unknowns:
    st.markdown(f"""
    <div class="alert-box">
        ⚠ {len(unknowns)} persona(s) desconocida(s) detectada(s)
    </div>
    """, unsafe_allow_html=True)

# ── LISTA EN TIEMPO REAL ───────────────────────────────────────────────────
st.markdown('<p class="section-title">Registro en tiempo real</p>', unsafe_allow_html=True)

if not people:
    st.markdown("""
    <div class="empty-state">
        <span>📡</span>
        Esperando detecciones desde el sistema de cámara…
    </div>""", unsafe_allow_html=True)
else:
    for i, p in enumerate(reversed(people), 1):
        conf = p["confidence"]
        bar_color = "#5CB85C" if conf >= 80 else "#f3ba73" if conf >= 60 else "#f97d7d"
        uniforme  = "✔ Uniforme" if p.get("uniforme", True) else "⚠ Sin uniforme"

        st.markdown(f"""
        <div class="row">
            <span class="row-num">{i}</span>
            <span class="row-name">{p['name']}</span>
            <span class="row-time">{p['time']}</span>
            <div class="conf-bar-wrap">
                <div class="conf-bar">
                    <div class="conf-bar-fill" style="width:{conf:.0f}%;background:{bar_color};"></div>
                </div>
                <div class="conf-pct" style="color:{bar_color};">{conf:.0f}%</div>
            </div>
            <span class="badge">{uniforme}</span>
        </div>""", unsafe_allow_html=True)

# ── FOOTER ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("UniformID · Sistema de control de acceso · v2.0")

# ── REFRESH ────────────────────────────────────────────────────────────────
time.sleep(2)
st.rerun()
