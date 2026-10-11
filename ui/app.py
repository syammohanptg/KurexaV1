"""
ui/app.py – Streamlit frontend
Run with:  streamlit run ui/app.py --server.port 8501
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import requests
import json
from datetime import datetime

import config

API = config.API_BASE_URL

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="HealthAI Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 50%, #0f1117 100%);
    color: #e8eaf0;
}

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141824 0%, #1e2333 100%);
    border-right: 1px solid #2a3050;
}
section[data-testid="stSidebar"] * { color: #c8cfe0 !important; }

/* ── Cards ── */
.card {
    background: rgba(30, 35, 55, 0.85);
    border: 1px solid #2a3050;
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
}
.card-accent-green  { border-left: 4px solid #22c55e; }
.card-accent-yellow { border-left: 4px solid #eab308; }
.card-accent-red    { border-left: 4px solid #ef4444; }
.card-accent-blue   { border-left: 4px solid #3b82f6; }
.card-accent-purple { border-left: 4px solid #a855f7; }
.card-accent-teal   { border-left: 4px solid #14b8a6; }

/* ── Risk badges ── */
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 99px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.badge-low      { background: rgba(34,197,94,0.2);  color: #22c55e; border: 1px solid #22c55e; }
.badge-moderate { background: rgba(234,179,8,0.2);  color: #eab308; border: 1px solid #eab308; }
.badge-high     { background: rgba(239,68,68,0.2);  color: #ef4444; border: 1px solid #ef4444; }
.badge-mild     { background: rgba(34,197,94,0.15); color: #4ade80; }
.badge-moderate-sev { background: rgba(234,179,8,0.15); color: #fbbf24; }
.badge-severe   { background: rgba(239,68,68,0.15); color: #f87171; }

/* ── Progress bars ── */
.prob-bar {
    height: 8px;
    border-radius: 99px;
    background: #2a3050;
    margin: 6px 0 12px;
    overflow: hidden;
}
.prob-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

/* ── Section headers ── */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    color: #93c5fd;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Hero ── */
.hero {
    text-align: center;
    padding: 32px 0 16px;
}
.hero h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 42px;
    background: linear-gradient(135deg, #60a5fa, #c084fc, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.hero p {
    color: #94a3b8;
    font-size: 16px;
    margin-top: 8px;
}

/* ── Input area ── */
textarea {
    background: #1e2333 !important;
    border: 1px solid #3b4270 !important;
    color: #e8eaf0 !important;
    border-radius: 12px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-weight: 600;
    font-size: 15px;
    transition: all 0.2s;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(99,102,241,0.4);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #141824;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94a3b8;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #2a3050 !important;
    color: #93c5fd !important;
}

/* ── History item ── */
.history-item {
    background: #1e2333;
    border: 1px solid #2a3050;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    cursor: pointer;
    transition: border-color 0.2s;
}
.history-item:hover { border-color: #3b82f6; }

/* ── Admin toggle ── */
.toggle-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #2a3050;
}

/* ── Remedy category pill ── */
.cat-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: rgba(59,130,246,0.15);
    color: #60a5fa;
    margin-right: 6px;
}

.divider { height: 1px; background: #2a3050; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def init_session():
    for k, v in {
        "token": None, "is_admin": False, "full_name": "",
        "user_id": None, "page": "login", "result": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


def api(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = getattr(requests, method)(f"{API}{path}", headers=headers, timeout=90, **kwargs)
        return r
    except requests.exceptions.ConnectionError:
        st.error("⚠️  Cannot connect to the API. Make sure the FastAPI server is running.")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:16px 0 8px'>
        <span style='font-size:36px'>🩺</span>
        <div style='font-family:"DM Serif Display",serif; font-size:20px; color:#93c5fd; margin-top:4px'>
            HealthAI
        </div>
        <div style='font-size:12px; color:#64748b'>Intelligent symptom analysis</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if st.session_state.token:
        st.markdown(f"**👤 {st.session_state.full_name}**")
        if st.session_state.is_admin:
            st.markdown('<span style="color:#f59e0b;font-size:12px">⭐ Admin</span>',
                        unsafe_allow_html=True)

        st.divider()
        nav_options = ["🔍 Symptom Check", "📋 My History"]
        if st.session_state.is_admin:
            nav_options.append("⚙️ Admin Panel")

        for opt in nav_options:
            key = opt.split()[-1].lower().replace("panel", "admin").replace("check", "check").replace("history", "history")
            if st.button(opt, key=f"nav_{key}"):
                st.session_state.page = key
                st.session_state.result = None

        st.divider()
        if st.button("🚪 Logout"):
            for k in ["token", "is_admin", "full_name", "user_id", "result"]:
                st.session_state[k] = None if k != "result" else None
            st.session_state.page = "login"
            st.rerun()
    else:
        st.markdown("*Please log in to continue.*")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: LOGIN / REGISTER
# ══════════════════════════════════════════════════════════════════════════════
def render_login():
    st.markdown("""
    <div class='hero'>
        <h1>HealthAI Assistant</h1>
        <p>AI-powered symptom analysis & personalised health guidance</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        tab_login, tab_reg = st.tabs(["🔑 Sign In", "📝 Register"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email    = st.text_input("Email", key="l_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="l_pass")
            if st.button("Sign In", key="btn_login"):
                if email and password:
                    r = api("post", "/auth/login",
                            data={"username": email, "password": password})
                    if r and r.status_code == 200:
                        d = r.json()
                        st.session_state.token     = d["access_token"]
                        st.session_state.is_admin  = d["is_admin"]
                        st.session_state.full_name = d["full_name"]
                        st.session_state.user_id   = d["user_id"]
                        st.session_state.page      = "check"
                        st.rerun()
                    else:
                        msg = r.json().get("detail", "Login failed") if r else "Connection error"
                        st.error(f"❌ {msg}")

        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            r_name  = st.text_input("Full Name", key="r_name")
            r_email = st.text_input("Email", key="r_email")
            r_pass  = st.text_input("Password", type="password", key="r_pass")
            if st.button("Create Account", key="btn_reg"):
                if r_email and r_pass:
                    r = api("post", "/auth/register",
                            json={"email": r_email, "password": r_pass, "full_name": r_name})
                    if r and r.status_code == 201:
                        st.success("✅ Account created! Please sign in.")
                    else:
                        msg = r.json().get("detail", "Registration failed") if r else "Connection error"
                        st.error(f"❌ {msg}")

        st.markdown("""
        <div style='text-align:center; color:#475569; font-size:12px; margin-top:16px'>
            Default admin: admin@healthai.com / Admin@123
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  RESULT RENDERER
# ══════════════════════════════════════════════════════════════════════════════
def sev_badge(sev: str) -> str:
    s = (sev or "").lower()
    cls = {"mild": "badge-mild", "moderate": "badge-moderate-sev",
           "severe": "badge-severe"}.get(s, "badge-mild")
    return f'<span class="badge {cls}">{sev or "—"}</span>'


def risk_card(level: str, explanation: str):
    cfg = {
        "low":      ("🟢", "Low Risk", "card-accent-green",  "badge-low",      "#22c55e"),
        "moderate": ("🟡", "Moderate", "card-accent-yellow", "badge-moderate", "#eab308"),
        "high":     ("🔴", "High Risk","card-accent-red",    "badge-high",     "#ef4444"),
    }
    icon, label, card_cls, badge_cls, color = cfg.get(
        (level or "low").lower(), cfg["low"])
    st.markdown(f"""
    <div class='card {card_cls}'>
        <div class='section-header'>{icon} Risk & Urgency Indicator</div>
        <div style='margin-top:12px'>
            <span class='badge {badge_cls}'>{label}</span>
            <p style='color:#94a3b8; margin-top:12px; margin-bottom:0'>{explanation or ""}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_result(data: dict):
    result   = data.get("result", {})
    features = data.get("features", [])

    # ── Risk indicator (top, full width) ────────────────────────────────────
    if "risk_indicator" in features and result.get("risk_level"):
        risk_card(result["risk_level"], result.get("risk_explanation", ""))

    # ── Conditions + Remedies side by side ───────────────────────────────────
    show_cond = "possible_conditions" in features and result.get("possible_conditions")
    show_rem  = "home_remedies" in features and result.get("home_remedies")

    if show_cond or show_rem:
        col_l, col_r = st.columns(2) if (show_cond and show_rem) else (st.columns(1)[0], None), None
        if show_cond and show_rem:
            col_l, col_r = st.columns(2)
        elif show_cond:
            col_l = st.columns(1)[0]; col_r = None
        else:
            col_r = st.columns(1)[0]; col_l = None

    if show_cond:
        with col_l:
            st.markdown("<div class='card card-accent-blue'>", unsafe_allow_html=True)
            st.markdown("<div class='section-header'>🧬 Possible Conditions</div>", unsafe_allow_html=True)
            for cond in result["possible_conditions"]:
                prob = cond.get("probability", 0)
                st.markdown(f"""
                <div style='margin-top:14px'>
                    <div style='display:flex; justify-content:space-between; align-items:center'>
                        <b style='color:#e2e8f0'>{cond.get('name','')}</b>
                        {sev_badge(cond.get('severity'))}
                    </div>
                    <div style='color:#94a3b8; font-size:13px; margin:4px 0'>{cond.get('description','')}</div>
                    <div style='display:flex; align-items:center; gap:10px'>
                        <div class='prob-bar' style='flex:1'>
                            <div class='prob-fill' style='width:{prob}%'></div>
                        </div>
                        <span style='font-size:13px; color:#60a5fa; font-weight:600; min-width:36px'>{prob}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if show_rem:
        cat_colors = {
            "hydration": "#06b6d4", "diet": "#22c55e", "sleep": "#8b5cf6",
            "herbal": "#f59e0b", "exercise": "#ec4899",
        }
        with col_r:
            st.markdown("<div class='card card-accent-teal'>", unsafe_allow_html=True)
            st.markdown("<div class='section-header'>🌿 Home Remedies</div>", unsafe_allow_html=True)
            for rem in result["home_remedies"]:
                cat   = (rem.get("category") or "").lower()
                color = cat_colors.get(cat, "#60a5fa")
                st.markdown(f"""
                <div style='margin-top:12px; padding:12px; background:rgba(255,255,255,0.03);
                            border-radius:10px; border-left:3px solid {color}'>
                    <span class='cat-pill' style='background:rgba(99,102,241,0.15); color:{color}'>{cat}</span>
                    <span style='font-size:13px; color:#e2e8f0'>{rem.get('remedy','')}</span>
                    <div style='font-size:11px; color:#64748b; margin-top:4px'>
                        ⏱ Try for: {rem.get('duration','—')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Doctor Recommendations ───────────────────────────────────────────────
    if "doctor_recommendations" in features and result.get("doctor_recommendations"):
        st.markdown("<div class='card card-accent-purple'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>👨‍⚕️ Recommended Specialists</div>", unsafe_allow_html=True)
        for doc in result["doctor_recommendations"]:
            nearby = doc.get("nearby_doctors") or []
            st.markdown(f"""
            <div style='margin-top:14px'>
                <b style='color:#c4b5fd'>{doc.get('specialist_type','')}</b>
                <p style='color:#94a3b8; font-size:13px; margin:4px 0'>{doc.get('reason','')}</p>
            """, unsafe_allow_html=True)
            if nearby:
                st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
                for d in nearby:
                    st.markdown(f"""
                    <div style='font-size:12px; color:#94a3b8; padding:4px 0'>
                        📍 <b>{d.get('name','')}</b> — {d.get('address','')}
                        {"⭐ "+str(d.get('rating')) if d.get('rating') else ""}
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Disclaimer ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; color:#475569; font-size:12px; margin-top:20px;
                padding:12px; background:#141824; border-radius:10px'>
        ⚠️ This is AI-generated information for educational purposes only.
        Always consult a qualified healthcare professional for medical advice.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: SYMPTOM CHECK
# ══════════════════════════════════════════════════════════════════════════════
def render_check():
    st.markdown("""
    <div class='hero' style='padding:16px 0 8px'>
        <h1>Symptom Checker</h1>
        <p>Describe your symptoms and get AI-powered health insights</p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch enabled features for preview
    feat_r = api("get", "/features")
    enabled = [f["key"] for f in (feat_r.json() if feat_r else [])] if feat_r and feat_r.ok else []
    if not enabled:
        st.warning("⚠️ No features are currently enabled. Contact the administrator.")
        return

    feat_labels = {
        "possible_conditions": "🧬 Conditions",
        "home_remedies": "🌿 Remedies",
        "doctor_recommendations": "👨‍⚕️ Doctors",
        "risk_indicator": "🚦 Risk Level",
        "history_tracking": "📋 History",
    }
    pills = " ".join([f'<span class="badge badge-low" style="margin:2px">{feat_labels.get(f,f)}</span>'
                      for f in enabled if f != "history_tracking"])
    st.markdown(f"<div style='margin-bottom:12px'>Active features: {pills}</div>",
                unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        symptoms = st.text_area(
            "Describe your symptoms",
            height=140,
            placeholder="e.g. I have had a headache for 2 days, mild fever around 99°F, sore throat, and feeling tired...",
            key="symptoms_input",
        )
    with col2:
        st.markdown("**📍 Location** *(optional, for nearby doctors)*")
        location_name = st.text_input("City / Area", placeholder="e.g. Bengaluru, KA", key="loc_name")
        col_lat, col_lng = st.columns(2)
        with col_lat:
            lat = st.number_input("Latitude",  value=0.0, format="%.4f", key="lat")
        with col_lng:
            lng = st.number_input("Longitude", value=0.0, format="%.4f", key="lng")

    if st.button("🔍 Analyze Symptoms", key="btn_analyze"):
        if not symptoms.strip():
            st.warning("Please describe your symptoms first.")
        else:
            with st.spinner("🤖 Consulting AI health model..."):
                payload = {
                    "symptoms": symptoms,
                    "location_name": location_name,
                    "latitude":  lat if lat != 0.0 else None,
                    "longitude": lng if lng != 0.0 else None,
                }
                r = api("post", "/symptom-check", json=payload)
                if r and r.status_code == 200:
                    st.session_state.result = r.json()
                    st.success("✅ Analysis complete!")
                else:
                    msg = r.json().get("detail", "Analysis failed") if r else "Connection error"
                    st.error(f"❌ {msg}")

    if st.session_state.result:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("### 📊 Analysis Results")
        render_result(st.session_state.result)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: HISTORY
# ══════════════════════════════════════════════════════════════════════════════
def render_history():
    st.markdown("## 📋 My Health History")

    r = api("get", "/history")
    if not r or not r.ok:
        st.error("Failed to load history.")
        return

    checks = r.json()
    if not checks:
        st.info("No symptom checks yet. Head to the Symptom Check page to get started.")
        return

    # Summary metrics
    total   = len(checks)
    highs   = sum(1 for c in checks if (c.get("risk_level") or "").lower() == "high")
    mods    = sum(1 for c in checks if (c.get("risk_level") or "").lower() == "moderate")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Checks", total)
    col2.metric("🔴 High Risk",  highs)
    col3.metric("🟡 Moderate",   mods)

    st.divider()

    for check in checks:
        risk = (check.get("risk_level") or "low").lower()
        risk_badge = {
            "low": "🟢 Low", "moderate": "🟡 Moderate", "high": "🔴 High"
        }.get(risk, "—")

        top_cond = check["conditions"][0]["name"] if check.get("conditions") else "—"
        date_str = check["created_at"][:10]
        time_str = check["created_at"][11:16]

        with st.expander(
            f"**{date_str} {time_str}** — {top_cond}  |  Risk: {risk_badge}"
        ):
            st.markdown(f"**Symptoms:** {check['symptoms']}")
            st.markdown(f"**Location:** {check.get('location','—')}")

            if check.get("conditions"):
                st.markdown("**Conditions identified:**")
                for cond in check["conditions"]:
                    sev = cond.get("severity", "")
                    st.markdown(
                        f"- **{cond['name']}** — {cond['probability']}% match  "
                        f"| Severity: {sev}"
                    )

            if st.button("View Full Details", key=f"detail_{check['id']}"):
                detail_r = api("get", f"/history/{check['id']}")
                if detail_r and detail_r.ok:
                    full = detail_r.json()
                    st.session_state.result = {
                        "features": ["possible_conditions","home_remedies",
                                     "doctor_recommendations","risk_indicator"],
                        "result": full.get("result", {}),
                    }
                    st.session_state.page = "check"
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
def render_admin():
    st.markdown("## ⚙️ Admin Panel")

    tab_feat, tab_users = st.tabs(["🎛️ Feature Flags", "👥 User Management"])

    # ── Feature Flags ──────────────────────────────────────────────────────────
    with tab_feat:
        st.markdown("### Enable / Disable AI response features")
        st.caption("Only enabled features will be included in the GPT prompt and shown to users.")

        r = api("get", "/features")
        if not r or not r.ok:
            st.error("Failed to load features."); return

        features = r.json()
        for feat in features:
            col_label, col_toggle = st.columns([4, 1])
            with col_label:
                st.markdown(f"**{feat['label']}**  \n`{feat['key']}`")
            with col_toggle:
                new_val = st.toggle("", value=feat["enabled"], key=f"flag_{feat['key']}")
                if new_val != feat["enabled"]:
                    patch = api("patch", f"/admin/features/{feat['key']}",
                                json={"is_enabled": new_val})
                    if patch and patch.ok:
                        st.success(f"Updated {feat['key']}")
                        st.rerun()

    # ── User Management ────────────────────────────────────────────────────────
    with tab_users:
        st.markdown("### Manage Users")

        with st.expander("➕ Create New User"):
            nu_name  = st.text_input("Full Name", key="nu_name")
            nu_email = st.text_input("Email",     key="nu_email")
            nu_pass  = st.text_input("Password",  type="password", key="nu_pass")
            nu_admin = st.checkbox("Grant Admin Access", key="nu_admin")
            if st.button("Create User", key="btn_create_user"):
                if nu_email and nu_pass:
                    cr = api("post", "/admin/users", json={
                        "email": nu_email, "password": nu_pass,
                        "full_name": nu_name, "is_admin": nu_admin,
                    })
                    if cr and cr.status_code == 201:
                        st.success("User created!"); st.rerun()
                    else:
                        msg = cr.json().get("detail","Error") if cr else "Error"
                        st.error(msg)

        ur = api("get", "/admin/users")
        if ur and ur.ok:
            users = ur.json()
            for u in users:
                col_info, col_badge, col_act = st.columns([3, 1, 1])
                with col_info:
                    st.markdown(f"**{u['full_name'] or u['email']}**  \n{u['email']}")
                with col_badge:
                    if u["is_admin"]:
                        st.markdown('<span class="badge badge-moderate">⭐ Admin</span>',
                                    unsafe_allow_html=True)
                    status_color = "#22c55e" if u["is_active"] else "#ef4444"
                    status_text  = "Active" if u["is_active"] else "Disabled"
                    st.markdown(f'<span style="color:{status_color}; font-size:12px">● {status_text}</span>',
                                unsafe_allow_html=True)
                with col_act:
                    btn_label = "Disable" if u["is_active"] else "Enable"
                    if st.button(btn_label, key=f"toggle_user_{u['id']}"):
                        tr = api("patch", f"/admin/users/{u['id']}/toggle")
                        if tr and tr.ok:
                            st.rerun()
                st.divider()


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.token:
    render_login()
elif st.session_state.page == "check":
    render_check()
elif st.session_state.page == "history":
    render_history()
elif st.session_state.page == "admin" and st.session_state.is_admin:
    render_admin()
else:
    render_check()
