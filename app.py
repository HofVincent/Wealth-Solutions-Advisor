import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from openai import OpenAI
import base64
from email.utils import parsedate_to_datetime
import hmac
import re

# --- CREAR ARCHIVO JSON DESDE SECRETS ---
if not os.path.exists("client_secret.json"):
    try:
        google_creds = st.secrets["GOOGLE_CREDENTIALS"]
        with open("client_secret.json", "w") as f:
            f.write(google_creds)
    except Exception:
        st.error("No se encontró el secreto GOOGLE_CREDENTIALS en la configuración.")

# =============================================================================
# CONSTANTES
# CAMBIO: Centralizar. Antes había magic numbers dispersos por el código.
# =============================================================================
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = "https://wealth-solutions-advisor.streamlit.app/"
HISTORY_FILE = "client_history.json"
MAX_EMAILS_ALLOWED = 500
MAX_CHARS_TOTAL = 100000
MAX_CHARS_FOR_AI = 80000

# =============================================================================
# PAGE CONFIG - Debe ser el primer comando de Streamlit
# =============================================================================
st.set_page_config(page_title="Wealth Solutions Advisor", page_icon="🏦", layout="wide", initial_sidebar_state="expanded")

# --- CSS PREMIUM v2 ---
# CAMBIO: Jerarquía visual clara para botones (primario/secundario/terciario),
# fix colores de texto en sidebar, mejor contraste general, link_buttons legibles.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    /* === BASE === */
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    .stApp { background: #f8f9fb; }

    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: #1a1d29; font-weight: 600; letter-spacing: -0.02em;
    }
    h1 { font-size: 42px; } h2 { font-size: 32px; } h3 { font-size: 24px; }
    p, label, .stMarkdown { color: #4a5568; font-weight: 400; line-height: 1.7; }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1a1d29; font-weight: 600;
    }
    /* FIX: Texto sidebar legible (antes había color:white sobre fondo blanco) */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #4a5568 !important;
        font-size: 14px;
    }
    /* Radio buttons sidebar */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        background-color: transparent; display: flex; flex-direction: column; gap: 8px;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 12px 16px; transition: all 0.2s ease; cursor: pointer;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #edf2f7; border-color: #cbd5e0;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background: #1a1d29; border-color: #1a1d29; color: white !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] span,
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p {
        color: white !important;
    }

    /* === TABS HORIZONTALES (main area) === */
    section[data-testid="stMain"] div[role="radiogroup"] {
        background: white; border: 1px solid #e2e8f0; padding: 4px;
        border-radius: 10px; display: flex; gap: 4px;
    }
    section[data-testid="stMain"] div[role="radiogroup"] label {
        flex: 1; text-align: center; background: transparent; border: none;
        padding: 10px 16px; border-radius: 8px; color: #4a5568;
        font-weight: 500; font-size: 14px; transition: all 0.2s ease;
    }
    section[data-testid="stMain"] div[role="radiogroup"] label:hover {
        background: #f7fafc; color: #1a1d29;
    }
    section[data-testid="stMain"] div[role="radiogroup"] label[data-checked="true"] {
        background: #1a1d29; color: white !important; font-weight: 600;
        box-shadow: 0 2px 8px rgba(26,29,41,0.15);
    }

    /* === BOTONES: JERARQUÍA VISUAL CLARA === */

    /* PRIMARIO: Fondo oscuro, texto blanco — para acciones principales */
    .stButton>button[kind="primary"],
    .stButton>button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #004e98 0%, #003d7a 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600; font-size: 14px;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0,78,152,0.2);
    }
    .stButton>button[kind="primary"]:hover,
    .stButton>button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #003d7a 0%, #002d5e 100%) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0,78,152,0.3);
    }

    /* SECUNDARIO: Borde visible, fondo blanco — para acciones complementarias */
    .stButton>button[kind="secondary"],
    .stButton>button[data-testid="stBaseButton-secondary"],
    .stButton>button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {
        background: white !important;
        color: #1a1d29 !important;
        border: 2px solid #cbd5e0 !important;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600; font-size: 14px;
        transition: all 0.2s ease;
    }
    .stButton>button[kind="secondary"]:hover,
    .stButton>button[data-testid="stBaseButton-secondary"]:hover,
    .stButton>button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {
        background: #f7fafc !important;
        border-color: #004e98 !important;
        color: #004e98 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* DOWNLOAD BUTTONS: Estilo propio distinguible */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600; font-size: 14px;
        width: 100%;
        box-shadow: 0 2px 8px rgba(46,125,50,0.2);
        transition: all 0.2s ease;
    }
    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #1b5e20 0%, #0d3d13 100%) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(46,125,50,0.3);
    }

    /* LINK BUTTONS: Claramente clicables */
    .stLinkButton>a {
        background: white !important;
        color: #004e98 !important;
        border: 2px solid #004e98 !important;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600; font-size: 14px;
        text-decoration: none !important;
        transition: all 0.2s ease;
        display: inline-block;
        text-align: center;
    }
    .stLinkButton>a:hover {
        background: #004e98 !important;
        color: white !important;
    }

    /* === INPUTS === */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>div {
        border: 1.5px solid #e2e8f0; border-radius: 8px;
        padding: 10px 14px; font-size: 14px;
        background: white; transition: all 0.2s ease;
    }
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus {
        border-color: #004e98;
        box-shadow: 0 0 0 3px rgba(0,78,152,0.1);
    }

    /* === EXPANDERS (email cards) === */
    .streamlit-expanderHeader {
        background: white; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 14px 18px; font-size: 14px;
        transition: all 0.2s ease;
    }
    .streamlit-expanderHeader:hover {
        background: #f7fafc; border-color: #cbd5e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* === MÉTRICAS === */
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 600; color: #1a1d29; }
    [data-testid="stMetricLabel"] { font-size: 13px; color: #718096; text-transform: uppercase; letter-spacing: 0.5px; }

    /* === ANIMACIONES === */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stMarkdown > div { animation: fadeIn 0.3s ease-out; }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #f7fafc; }
    ::-webkit-scrollbar-thumb { background: #cbd5e0; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #a0aec0; }

    /* === SLIDER === */
    .stSlider [data-testid="stThumbValue"] { color: #1a1d29; font-weight: 600; }

    /* === TOAST / SUCCESS / WARNING — mejorar contraste === */
    .stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPER: Acceso seguro a API Key
# CAMBIO: Eliminar variable global OPENAI_API_KEY.
# RAZÓN: Si un traceback imprime la global, la key queda expuesta en logs.
# =============================================================================
def get_openai_key():
    """Acceso centralizado a la API key. Nunca en variable global."""
    try:
        return st.secrets["OPENAI_KEY"]
    except Exception:
        return None

# =============================================================================
# COMPONENTES REUTILIZABLES DE UI
# =============================================================================
def show_error_box(title, message, details=None, suggestions=None):
    suggestions_html = ""
    if suggestions:
        suggestions_html = "<div style='margin-top:16px;padding:16px;background:#fff5f5;border-radius:6px;'>"
        suggestions_html += "<p style='color:#742a2a;font-size:13px;font-weight:600;margin:0 0 8px 0;'>Sugerencias:</p>"
        suggestions_html += "<ul style='color:#742a2a;font-size:13px;margin:0;padding-left:20px;line-height:1.8;'>"
        for s in suggestions:
            suggestions_html += f"<li>{s}</li>"
        suggestions_html += "</ul></div>"
    details_html = ""
    if details:
        details_html = f"<details style='margin-top:16px;'><summary style='cursor:pointer;color:#742a2a;font-weight:600;font-size:13px;'>Ver detalles técnicos</summary><pre style='background:#fff5f5;padding:12px;border-radius:6px;margin-top:8px;font-size:11px;overflow-x:auto;color:#742a2a;border:1px solid #feb2b2;'>{details}</pre></details>"
    st.markdown(f"""
<div style='background:white;border:1px solid #feb2b2;border-left:4px solid #e53e3e;padding:24px;border-radius:8px;margin:24px 0;'>
<div style='display:flex;align-items:flex-start;gap:12px;'>
<div style='font-size:20px;line-height:1;'>⚠️</div>
<div style='flex:1;'>
<h4 style='color:#742a2a;margin:0 0 8px 0;font-size:16px;font-weight:600;'>{title}</h4>
<p style='color:#742a2a;margin:0;font-size:14px;line-height:1.6;'>{message}</p>
{suggestions_html}{details_html}
</div></div></div>
""", unsafe_allow_html=True)

def show_warning_box(title, message, tips=None):
    tips_html = ""
    if tips:
        tips_html = "<div style='margin-top:16px;padding:16px;background:#fffbeb;border-radius:6px;'>"
        tips_html += "<p style='color:#744210;font-size:13px;font-weight:600;margin:0 0 8px 0;'>Recomendaciones:</p>"
        tips_html += "<ul style='color:#744210;font-size:13px;margin:0;padding-left:20px;line-height:1.8;'>"
        for t in tips:
            tips_html += f"<li>{t}</li>"
        tips_html += "</ul></div>"
    st.markdown(f"""
<div style='background:white;border:1px solid #fbd38d;border-left:4px solid #ed8936;padding:24px;border-radius:8px;margin:24px 0;'>
<div style='display:flex;align-items:flex-start;gap:12px;'>
<div style='font-size:20px;line-height:1;'>⚡</div>
<div style='flex:1;'>
<h4 style='color:#744210;margin:0 0 8px 0;font-size:16px;font-weight:600;'>{title}</h4>
<p style='color:#744210;margin:0;font-size:14px;line-height:1.6;'>{message}</p>
{tips_html}
</div></div></div>
""", unsafe_allow_html=True)

def show_success_box(title, message):
    st.markdown(f"""
<div style='background:white;border:1px solid #9ae6b4;border-left:4px solid #38a169;padding:24px;border-radius:8px;margin:24px 0;'>
<div style='display:flex;align-items:flex-start;gap:12px;'>
<div style='font-size:20px;line-height:1;'>✓</div>
<div style='flex:1;'>
<h4 style='color:#22543d;margin:0 0 8px 0;font-size:16px;font-weight:600;'>{title}</h4>
<p style='color:#22543d;margin:0;font-size:14px;line-height:1.6;'>{message}</p>
</div></div></div>
""", unsafe_allow_html=True)

def show_info_box(title, message, icon="ℹ️"):
    st.markdown(f"""
<div style='background:white;border:1px solid #bee3f8;border-left:4px solid #3182ce;padding:24px;border-radius:8px;margin:24px 0;'>
<div style='display:flex;align-items:flex-start;gap:12px;'>
<div style='font-size:20px;line-height:1;'>{icon}</div>
<div style='flex:1;'>
<h4 style='color:#2c5282;margin:0 0 8px 0;font-size:16px;font-weight:600;'>{title}</h4>
<p style='color:#2c5282;margin:0;font-size:14px;line-height:1.6;'>{message}</p>
</div></div></div>
""", unsafe_allow_html=True)

def show_empty_state(icon, title, subtitle, suggestions=None):
    suggestions_html = ""
    if suggestions:
        suggestions_html = "<div style='background:#f7fafc;padding:20px;border-radius:6px;border:1px solid #e2e8f0;margin-top:24px;'>"
        suggestions_html += "<p style='color:#2d3748;font-size:13px;font-weight:600;margin:0 0 12px 0;'>Sugerencias:</p>"
        suggestions_html += "<ul style='color:#4a5568;font-size:13px;margin:0;padding-left:20px;line-height:1.8;'>"
        for s in suggestions:
            suggestions_html += f"<li>{s}</li>"
        suggestions_html += "</ul></div>"
    st.markdown(f"""
<div style='background:white;border:1px solid #e2e8f0;padding:48px 32px;border-radius:8px;margin:32px 0;text-align:center;'>
<div style='font-size:56px;margin-bottom:16px;opacity:0.5;'>{icon}</div>
<h3 style='color:#1a1d29;margin:0 0 8px 0;font-size:20px;font-weight:600;'>{title}</h3>
<p style='color:#718096;margin:0;font-size:15px;line-height:1.6;'>{subtitle}</p>
{suggestions_html}
</div>
""", unsafe_allow_html=True)

# =============================================================================
# EXPORTACIÓN
# =============================================================================
def generate_analysis_summary_text(analysis_data, evidence_data, target_email):
    """
    CAMBIO: Esta función ya existía pero NUNCA se llamaba en la UI.
    Ahora se conecta a un botón de descarga en la vista principal.
    """
    text = f"""
╔═══════════════════════════════════════════════════════════════╗
║          WEALTH SOLUTIONS ADVISOR - ANÁLISIS DE CLIENTE        ║
╚═══════════════════════════════════════════════════════════════╝

📧 CLIENTE: {target_email}
📅 FECHA ANÁLISIS: {datetime.now().strftime('%d/%m/%Y %H:%M')}
📊 EMAILS ANALIZADOS: {len(evidence_data)}

───────────────────────────────────────────────────────────────
📖 RESUMEN EJECUTIVO:
{analysis_data.get('resumen_exhaustivo', 'N/A')}

───────────────────────────────────────────────────────────────
🎯 PERFIL DEL CLIENTE:
{analysis_data.get('perfil_cliente', 'N/A')}

───────────────────────────────────────────────────────────────
⚡ URGENCIA: {analysis_data.get('urgencia', 'N/A')}

───────────────────────────────────────────────────────────────
💡 ACCIÓN RECOMENDADA:
{analysis_data.get('accion_recomendada', 'N/A')}

───────────────────────────────────────────────────────────────
💎 INSIGHTS CLAVE:
"""
    for idx, insight in enumerate(analysis_data.get('insights_clave', []), 1):
        text += f"{idx}. {insight}\n"
    text += "\n───────────────────────────────────────────────────────────────\n📊 EVOLUCIÓN DE SENTIMIENTO:\n\n"
    for sent in analysis_data.get('analisis_sentimiento', [])[:10]:
        score = sent.get('sentimiento_score', 0)
        bar = "█" * max(0, int((score + 10) / 2))
        text += f"Email #{sent.get('email_num', 'N/A')}: [{score:+3d}/10] {bar}\n"
        text += f"           {sent.get('explicacion', 'N/A')}\n\n"
    text += "───────────────────────────────────────────────────────────────\n✉️ BORRADOR DE RESPUESTA SUGERIDO:\n\n"
    text += analysis_data.get('borrador_respuesta', 'N/A')
    text += "\n\n═══════════════════════════════════════════════════════════════\n"
    text += "         Generado por Wealth Solutions Advisor v2.0\n"
    text += "═══════════════════════════════════════════════════════════════\n"
    return text

def generate_brief_pdf(brief_data, target_email, output_path="brief.pdf"):
    """Genera un PDF profesional del Pre-Meeting Brief."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=80, bottomMargin=50)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1a2b4b'), spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#004e98'), spaceAfter=12, spaceBefore=20, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#2c3e50'), spaceAfter=10, alignment=TA_JUSTIFY, leading=16)
    elements = []

    # Header
    ht = Table([[Paragraph("🏦 WEALTH SOLUTIONS ADVISOR", title_style)], [Paragraph("PRE-MEETING BRIEF", subtitle_style)]], colWidths=[6.5*inch])
    ht.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f5f7fa')), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('TOPPADDING', (0,0), (-1,-1), 15), ('BOTTOMPADDING', (0,0), (-1,-1), 15)]))
    elements.extend([ht, Spacer(1, 20)])

    # Metadata
    mt = Table([[Paragraph("<b>Cliente:</b>", normal_style), Paragraph(target_email, normal_style)], [Paragraph("<b>Fecha:</b>", normal_style), Paragraph(datetime.now().strftime('%d/%m/%Y %H:%M'), normal_style)], [Paragraph("<b>Tipo:</b>", normal_style), Paragraph("Pre-Meeting Brief Ejecutivo", normal_style)]], colWidths=[1.5*inch, 5*inch])
    mt.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e3f2fd')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#90caf9')), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('LEFTPADDING', (0,0), (-1,-1), 10)]))
    elements.extend([mt, Spacer(1, 25)])

    # Contexto
    elements.append(Paragraph("📋 CONTEXTO RÁPIDO", subtitle_style))
    ct = Table([[Paragraph(brief_data.get('contexto_rapido', 'N/A'), normal_style)]], colWidths=[6.5*inch])
    ct.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e8f5e9')), ('BOX', (0,0), (-1,-1), 2, colors.HexColor('#4caf50')), ('TOPPADDING', (0,0), (-1,-1), 15), ('BOTTOMPADDING', (0,0), (-1,-1), 15), ('LEFTPADDING', (0,0), (-1,-1), 15), ('RIGHTPADDING', (0,0), (-1,-1), 15)]))
    elements.extend([ct, Spacer(1, 20)])

    # Temas
    elements.append(Paragraph("📌 AGENDA DE REUNIÓN", subtitle_style))
    for idx, tema in enumerate(brief_data.get('temas_reunion', [])[:5], 1):
        p = tema.get('prioridad', 'INFORMATIVO')
        cb = colors.HexColor('#ffebee') if p == 'URGENTE' else (colors.HexColor('#fff3e0') if p == 'IMPORTANTE' else colors.HexColor('#e3f2fd'))
        cbr = colors.HexColor('#d32f2f') if p == 'URGENTE' else (colors.HexColor('#f57c00') if p == 'IMPORTANTE' else colors.HexColor('#1976d2'))
        tt = Table([[Paragraph(f"<b>{idx}. {tema.get('tema', 'N/A')}</b> [{p}]", normal_style)], [Paragraph(tema.get('detalle', 'N/A'), normal_style)], [Paragraph(f"<i>💡 {tema.get('contexto', 'N/A')}</i>", normal_style)]], colWidths=[6.5*inch])
        tt.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), cb), ('BOX', (0,0), (-1,-1), 2, cbr), ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 12), ('RIGHTPADDING', (0,0), (-1,-1), 12)]))
        elements.extend([tt, Spacer(1, 10)])
    elements.append(Spacer(1, 15))

    # Pendientes
    elements.append(Paragraph("⚠️ PENDIENTES", subtitle_style))
    pcl = brief_data.get('pendientes_cliente', [])
    pbl = brief_data.get('pendientes_banco', [])
    ct_txt = "<br/>".join([f"• {p}" for p in pcl[:5]]) if pcl else "✅ Ninguno"
    bt_txt = "<br/>".join([f"• {p}" for p in pbl[:5]]) if pbl else "✅ Ninguno"
    pt = Table([[Paragraph("<b>👤 Cliente</b>", normal_style), Paragraph("<b>🏦 Banco</b>", normal_style)], [Paragraph(ct_txt, normal_style), Paragraph(bt_txt, normal_style)]], colWidths=[3.25*inch, 3.25*inch])
    pt.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), colors.HexColor('#ffebee')), ('BACKGROUND', (1,0), (1,0), colors.HexColor('#e3f2fd')), ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cfd8dc')), ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 10)]))
    elements.extend([pt, Spacer(1, 20)])

    # Talking points
    elements.append(Paragraph("🎤 TALKING POINTS SUGERIDOS", subtitle_style))
    for idx, point in enumerate(brief_data.get('talking_points', [])[:3], 1):
        tpt = Table([[Paragraph(f'<b>{idx}.</b> "{point}"', normal_style)]], colWidths=[6.5*inch])
        tpt.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f3e5f5')), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#9c27b0')), ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 12)]))
        elements.extend([tpt, Spacer(1, 8)])
    elements.append(Spacer(1, 15))

    # Timeline
    elements.append(Paragraph("⏰ TIMELINE RECIENTE", subtitle_style))
    tl = [["Fecha", "Quién", "Qué Pasó"]]
    for item in brief_data.get('timeline_reciente', [])[:5]:
        qp = item.get('que_paso', 'N/A')
        tl.append([item.get('fecha', 'N/A'), item.get('quien', 'N/A'), qp[:80] + "..." if len(qp) > 80 else qp])
    tlt = Table(tl, colWidths=[0.8*inch, 0.8*inch, 4.9*inch])
    tlt.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#004e98')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('LEFTPADDING', (0,0), (-1,-1), 8)]))
    elements.append(tlt)

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<i>Generado por Wealth Solutions Advisor | Documento confidencial</i>", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)))
    doc.build(elements)
    return output_path

# =============================================================================
# HISTORIAL
# =============================================================================
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_to_history(email):
    history = load_history()
    if email not in history:
        history.insert(0, email)
        history = history[:50]  # CAMBIO: Limitar a 50 clientes
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)

# =============================================================================
# AUTH GOOGLE
# =============================================================================
def create_auth_flow():
    try:
        return Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    except Exception as e:
        st.error(f"Error client_secret.json: {e}")
        return None

def authorize_google():
    flow = create_auth_flow()
    if flow:
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        return flow, auth_url
    return None, None

def exchange_code(code):
    try:
        flow = create_auth_flow()
        if flow:
            flow.fetch_token(code=code)
            return flow.credentials
    except Exception as e:
        st.error(f"Error auth: {e}")
    return None

# =============================================================================
# MOTOR GMAIL
# =============================================================================
def parse_email_body(payload):
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break
            elif 'parts' in part:
                body = parse_email_body(part)
                if body:
                    break
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    return body

def get_emails(creds, target_email, num_emails=None, fecha_desde=None, fecha_hasta=None, progress_callback=None):
    """
    CAMBIO: Añadido progress_callback para feedback visual real.
    El RM veía un spinner estático 30-60s. Ahora ve "Email 23 de 50..."
    """
    if not creds:
        return None, None, "❌ Credenciales no válidas. Vuelve a iniciar sesión."
    if not target_email or '@' not in target_email:
        return None, None, "❌ El email del cliente no es válido."

    try:
        service = build('gmail', 'v1', credentials=creds)
        query = f"from:{target_email} OR to:{target_email}"

        if fecha_desde and fecha_hasta:
            try:
                query += f" after:{fecha_desde.strftime('%Y/%m/%d')} before:{fecha_hasta.strftime('%Y/%m/%d')}"
                max_results = MAX_EMAILS_ALLOWED
            except Exception as e:
                return None, None, f"❌ Error en formato de fechas: {str(e)}"
        else:
            if not num_emails:
                num_emails = 15
            if num_emails > MAX_EMAILS_ALLOWED:
                return None, None, f"❌ Límite máximo: {MAX_EMAILS_ALLOWED} emails."
            max_results = num_emails

        try:
            results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        except Exception as api_error:
            em = str(api_error).lower()
            if "invalid_grant" in em:
                return None, None, "🔐 Sesión expirada. Cierra sesión y vuelve a autenticarte."
            elif "insufficient permission" in em:
                return None, None, "🔒 Permisos insuficientes en Gmail."
            elif "quota" in em:
                return None, None, "⏳ Límite de consultas Gmail. Intenta en unos minutos."
            else:
                return None, None, f"❌ Error Gmail: {str(api_error)[:200]}"

        messages = results.get('messages', [])
        if not messages:
            if fecha_desde and fecha_hasta:
                return None, None, f"📭 No se encontraron emails entre {fecha_desde.strftime('%d/%m/%Y')} y {fecha_hasta.strftime('%d/%m/%Y')}."
            return None, None, f"📭 No se encontraron emails con {target_email}."

        full_text = ""
        evidence = []
        current_chars = 0
        emails_procesados = 0
        emails_con_error = 0
        total_messages = len(messages)

        for idx, msg in enumerate(messages):
            if current_chars >= MAX_CHARS_TOTAL:
                break
            # CAMBIO: Progreso real
            if progress_callback:
                progress_callback(idx + 1, total_messages, "Descargando...")
            try:
                msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                headers = msg_detail['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "Sin Asunto")
                date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), "")
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "")
                try:
                    date_obj = parsedate_to_datetime(date_str)
                    date_formatted = date_obj.strftime('%Y-%m-%d %H:%M')
                    date_short = date_obj.strftime('%d %b')
                except Exception:
                    date_formatted = date_str[:16] if date_str else "Fecha desconocida"
                    date_short = "N/A"
                origin = "CLIENTE" if target_email.lower() in sender.lower() else "BANCO"
                body = parse_email_body(msg_detail['payload'])
                if not body:
                    body = msg_detail.get('snippet', '[Sin contenido]')
                body_cut = body[:3000]
                email_text = f"\n--- EMAIL {idx+1} ---\nID: {msg['id']}\nFECHA: {date_formatted}\nORIGEN: {origin}\nASUNTO: {subject}\nCONTENIDO: {body_cut}\n"
                full_text += email_text
                current_chars += len(email_text)
                evidence.append({"Nº": idx+1, "Id_Completo": msg['id'], "Id": msg['id'][:8], "Fecha": date_formatted, "Fecha_Corta": date_short, "Origen": origin, "Asunto": subject[:60] + "..." if len(subject) > 60 else subject, "Asunto_Completo": subject, "Cuerpo": body})
                emails_procesados += 1
                if progress_callback:
                    progress_callback(idx + 1, total_messages, subject[:40])
            except Exception:
                emails_con_error += 1
                continue

        if not evidence:
            return None, None, "❌ No se pudieron procesar los emails."
        evidence.reverse()
        warning_msg = None
        if emails_con_error > 0:
            warning_msg = f"⚠️ {emails_procesados} emails OK, {emails_con_error} con errores omitidos."
        return full_text, evidence, warning_msg
    except Exception as e:
        return None, None, f"❌ Error técnico: {str(e)[:300]}"

# =============================================================================
# MOTOR IA
# =============================================================================
@st.cache_data(show_spinner=False, ttl=3600)
def analyze_with_ai(text_data, num_emails):
    if not text_data or not text_data.strip():
        return None, "❌ No hay contenido para analizar."
    if num_emails <= 0:
        return None, "❌ Número de emails debe ser > 0."
    api_key = get_openai_key()
    if not api_key:
        return None, "🔑 Falta OPENAI_KEY en secrets.toml"
    if len(text_data) > MAX_CHARS_FOR_AI:
        text_data = text_data[:MAX_CHARS_FOR_AI] + "\n\n[NOTA: Contenido truncado]"

    prompt = f"""
    Actúa como un Senior Private Banker. Analiza el historial de {num_emails} correos.
    OBJETIVO 1: NARRATIVA. 'resumen_exhaustivo' (6-8 líneas) contando la historia.
    OBJETIVO 2: SENTIMIENTO. Analiza CADA correo, score (-10 a +10).
    JSON Estricto:
    {{
        "resumen_exhaustivo": "...", "urgencia": "Alta|Media|Baja",
        "perfil_cliente": "...", "accion_recomendada": "...",
        "borrador_respuesta": "Email...",
        "analisis_sentimiento": [
            {{ "email_num": 1, "sentimiento_score": 5, "explicacion": "..." }}
        ],
        "insights_clave": ["Insight 1", "Insight 2"]
    }}"""

    try:
        client = OpenAI(api_key=api_key, timeout=60.0)
        response = client.chat.completions.create(
            model="gpt-4o", response_format={"type": "json_object"},
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": text_data}],
            temperature=0.2, max_tokens=4000)
        try:
            result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as je:
            return None, f"❌ IA devolvió formato inválido: {str(je)}"

        # Rellenar campos faltantes
        defaults = {'resumen_exhaustivo': "⚠️ Resumen no disponible.", 'urgencia': "Media", 'perfil_cliente': "Cliente con actividad reciente.", 'accion_recomendada': "Revisar conversación.", 'borrador_respuesta': "Estimado/a,\n\nGracias por tu mensaje.\n\nSaludos cordiales.", 'analisis_sentimiento': [], 'insights_clave': ["Revisar emails manualmente."]}
        for field, dv in defaults.items():
            if field not in result:
                result[field] = dv

        sents = result.get('analisis_sentimiento', [])
        if not sents:
            result['analisis_sentimiento'] = [{"email_num": i+1, "sentimiento_score": 0, "explicacion": "No disponible"} for i in range(num_emails)]
        elif len(sents) < num_emails:
            for i in range(len(sents), num_emails):
                result['analisis_sentimiento'].append({"email_num": i+1, "sentimiento_score": 0, "explicacion": "No disponible"})
        for s in result['analisis_sentimiento']:
            sc = s.get('sentimiento_score', 0)
            if not isinstance(sc, (int, float)) or sc < -10 or sc > 10:
                s['sentimiento_score'] = 0
        return result, None
    except Exception as e:
        em = str(e).lower()
        if "rate_limit" in em: return None, "⏳ Límite OpenAI. Intenta en unos minutos."
        elif "invalid_api_key" in em or "authentication" in em: return None, "🔑 API Key inválida."
        elif "timeout" in em: return None, "⏱️ Timeout. Reduce emails."
        elif "context_length" in em: return None, "📏 Contenido demasiado largo."
        elif "insufficient_quota" in em: return None, "💳 Sin créditos OpenAI."
        else: return None, f"❌ Error OpenAI: {str(e)[:300]}"

def generate_fallback_analysis(evidence, target_email):
    num = len(evidence)
    fc = sum(1 for e in evidence if e['Origen'] == 'CLIENTE')
    lo = evidence[-1]['Origen'] if evidence else 'DESCONOCIDO'
    return {
        'resumen_exhaustivo': f"Se analizaron {num} emails con {target_email}. Cliente envió {fc}, banco {num-fc}. Último del {lo}. ⚠️ Análisis IA no disponible.",
        'urgencia': 'Media', 'perfil_cliente': f"Cliente con {num} interacciones. {'Espera respuesta.' if lo == 'CLIENTE' else 'Último mensaje del banco.'}",
        'accion_recomendada': 'Revisar emails en Explorador Avanzado.',
        'borrador_respuesta': "Estimado/a,\n\nEstamos revisando tu solicitud.\n\nSaludos cordiales,\nEquipo Banca Privada",
        'analisis_sentimiento': [{'email_num': i+1, 'sentimiento_score': 0, 'explicacion': 'No disponible'} for i in range(num)],
        'insights_clave': ['⚠️ IA no disponible temporalmente', f'{num} emails en conversación', 'Revisar en "Explorador Avanzado"']
    }

# =============================================================================
# ANÁLISIS DE HILOS
# =============================================================================
def get_thread_content(creds, thread_id):
    try:
        service = build('gmail', 'v1', credentials=creds)
        thread = service.users().threads().get(userId='me', id=thread_id, format='full').execute()
        full = ""
        for msg in thread.get('messages', []):
            headers = msg['payload']['headers']
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), "N/A")
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Desconocido")
            body = parse_email_body(msg['payload'])
            if not body: body = msg.get('snippet', '')
            full += f"\n--- MENSAJE DEL {date} ---\nDE: {sender}\nCONTENIDO:\n{body[:2000]}\n"
        return full
    except Exception:
        return None

@st.cache_data(show_spinner=False, ttl=3600)
def analyze_thread_structure(thread_text):
    api_key = get_openai_key()
    if not api_key: return "Error: API Key no configurada."
    client = OpenAI(api_key=api_key)
    prompt = """Actúa como Analista Senior. Analiza este hilo de correos.
    OUTPUT en Markdown:
    ### 🧭 Timeline del Hilo
    * 🔵 **[DD/MM] – [Fase]** - Actor, Hecho clave, Impacto
    ---
    ### 📌 Estado Actual
    * **Estado:** [PENDIENTE|BLOQUEADO|CERRADO]
    * **Atasco:** [Cuello de botella]
    * **Responsable actual:** [Nombre]
    ### 🧠 Conclusión Ejecutiva
    [3-4 líneas]
    ### ▶️ Próximos Pasos
    * Acción | Responsable | Objetivo"""
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": prompt}, {"role": "user", "content": thread_text}], temperature=0.1)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

@st.cache_data(show_spinner=False, ttl=1800)
def generate_meeting_brief(text_data, num_emails, target_email):
    api_key = get_openai_key()
    if not api_key: return None, "Error: API Key no configurada."
    client = OpenAI(api_key=api_key)
    prompt = f"""Actúa como Asistente Ejecutivo Senior de Banca Privada.
    Reunión con {target_email}. {num_emails} emails analizados.
    PRE-MEETING BRIEF en 60 segundos.
    JSON exacto:
    {{ "contexto_rapido": "...", "temas_reunion": [{{"prioridad": "URGENTE|IMPORTANTE|INFORMATIVO", "tema": "...", "detalle": "...", "contexto": "..."}}],
    "pendientes_cliente": ["..."], "pendientes_banco": ["..."],
    "talking_points": ["..."], "timeline_reciente": [{{"fecha": "DD/MM", "quien": "CLIENTE|BANCO", "que_paso": "..."}}],
    "documentos_mencionar": ["..."] }}
    Max 5 temas, 5 timeline. Sé específico."""
    try:
        response = client.chat.completions.create(model="gpt-4o", response_format={"type": "json_object"}, messages=[{"role": "system", "content": prompt}, {"role": "user", "content": text_data}], temperature=0.3)
        return json.loads(response.choices[0].message.content), None
    except Exception as e:
        return None, f"Error brief: {str(e)}"

# =============================================================================
# AUTENTICACIÓN APP
# =============================================================================
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets.get("app_password", "WealthSolutions2026")):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False):
        return True
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
<div style='text-align:center;background:white;padding:60px 40px;border-radius:16px;border:1px solid #e2e8f0;box-shadow:0 4px 20px rgba(0,0,0,0.08);'>
<div style='width:64px;height:64px;background:#1a1d29;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:32px;margin:0 auto 24px;'>🏦</div>
<h1 style='color:#1a1d29;font-size:32px;margin-bottom:12px;'>Wealth Solutions Advisor</h1>
<p style='color:#718096;font-size:15px;margin-bottom:32px;'>Acceso restringido • Solo personal autorizado</p>
</div>
""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.text_input("🔐 Contraseña de acceso", type="password", on_change=password_entered, key="password", placeholder="Introduce la contraseña del equipo")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Contraseña incorrecta.")
        st.caption("🔒 Conexión segura • Datos encriptados")
    return False
# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if not check_password():
    st.stop()

if 'creds' not in st.session_state: st.session_state.creds = None
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'last_brief' not in st.session_state: st.session_state.last_brief = None

if 'code' in st.query_params and st.session_state.creds is None:
    st.session_state.creds = exchange_code(st.query_params['code'])
    st.query_params.clear()
    st.rerun()

if st.session_state.creds:
    try:
        build('gmail', 'v1', credentials=st.session_state.creds)
    except Exception as e:
        if "invalid_grant" in str(e).lower() or "invalid_client" in str(e).lower():
            st.session_state.creds = None
            st.warning("Tu sesion ha expirado. Vuelve a iniciar sesion.")
            st.rerun()

# =============================================================================
# PANTALLA LOGIN GMAIL
# =============================================================================
if not st.session_state.creds:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
<div style='text-align:center;background:white;padding:60px 40px;border-radius:20px;box-shadow:0 10px 40px rgba(0,0,0,0.12);'>
<div style='font-size:60px;margin-bottom:20px;'>🏦</div>
<h1 style='color:#004e98;font-size:48px;'>Wealth Solutions Advisor</h1>
<p style='color:#5a6c7d;font-size:18px;'>Sistema de inteligencia avanzada para seguimiento de clientes</p>
</div>
""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        _, auth_url = authorize_google()
        if auth_url:
            st.link_button("🔐 Iniciar Sesión Corporativa", auth_url, type="primary", use_container_width=True)
        else:
            st.error("Falta client_secret.json")

else:
    # =================================================================
    # SIDEBAR
    # =================================================================
    with st.sidebar:
        st.markdown("""
<div style='text-align:center;padding:30px 0;'>
<div style='font-size:48px;margin-bottom:10px;'>👤</div>
<h2 style='color:#1a1d29;margin:0;font-size:24px;'>RM Panel</h2>
</div>
""", unsafe_allow_html=True)

        st.markdown("### 📇 Cartera de Clientes")
        client_history = load_history()
        selected_client = st.selectbox("Seleccionar cliente reciente:", ["Nueva Busqueda"] + client_history, index=0)
        if selected_client != "Nueva Busqueda":
            st.session_state.default_email = selected_client
        else:
            st.session_state.default_email = ""
        st.markdown("---")

        st.markdown("### ⚙️ Configuración de Análisis")
        analysis_mode = st.radio("Modo de busqueda:", ["Por numero de emails", "Por rango de fechas"], index=0, key="analysis_mode")

        if analysis_mode == "Por numero de emails":
            email_count = st.slider("Numero de emails", min_value=5, max_value=100, value=15, step=5, help="Ultimos N emails")
            st.session_state.fecha_desde = None
            st.session_state.fecha_hasta = None
        else:
            def update_dates_from_selector():
                seleccion = st.session_state.quick_period
                hoy = datetime.now().date()
                if seleccion == "Personalizado": return
                nd, nh = hoy, hoy
                if seleccion == "Ultimos 7 dias": nd = hoy - timedelta(days=7)
                elif seleccion == "Ultimos 15 dias": nd = hoy - timedelta(days=15)
                elif seleccion == "Ultimos 30 dias": nd = hoy - timedelta(days=30)
                elif seleccion == "Ultimo mes completo":
                    nd = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
                    nh = hoy.replace(day=1) - timedelta(days=1)
                elif seleccion == "Ultimo trimestre": nd = hoy - timedelta(days=90)
                elif seleccion == "Ultimos 6 meses": nd = hoy - timedelta(days=180)
                elif seleccion == "Este anio": nd = hoy.replace(month=1, day=1)
                st.session_state.fecha_desde_sidebar = nd
                st.session_state.fecha_hasta_sidebar = nh

            def set_custom_mode():
                st.session_state.quick_period = "Personalizado"

            st.markdown("**Periodos rapidos:**")
            if "quick_period" not in st.session_state:
                st.session_state.quick_period = "Ultimos 7 dias"
            st.selectbox("Periodo:", ["Personalizado", "Ultimos 7 dias", "Ultimos 15 dias", "Ultimos 30 dias", "Ultimo mes completo", "Ultimo trimestre", "Ultimos 6 meses", "Este anio"], key="quick_period", on_change=update_dates_from_selector)

            st.markdown("**Ajusta las fechas:**")
            if "fecha_desde_sidebar" not in st.session_state:
                st.session_state.fecha_desde_sidebar = datetime.now().date() - timedelta(days=7)
            if "fecha_hasta_sidebar" not in st.session_state:
                st.session_state.fecha_hasta_sidebar = datetime.now().date()
            today = datetime.now().date()
            fecha_desde = st.date_input("Desde", max_value=today, key="fecha_desde_sidebar", format="DD/MM/YYYY", on_change=set_custom_mode)
            fecha_hasta = st.date_input("Hasta", min_value=fecha_desde, max_value=today, key="fecha_hasta_sidebar", format="DD/MM/YYYY", on_change=set_custom_mode)
            st.session_state.fecha_desde = fecha_desde
            st.session_state.fecha_hasta = fecha_hasta
            days_selected = (fecha_hasta - fecha_desde).days + 1
            st.markdown(f"""
<div style='background:#f7fafc;padding:15px;border-radius:8px;margin-top:10px;border-left:4px solid #38a169;'>
<p style='margin:0;font-size:13px;color:#2d3748;'>Periodo: Del <strong>{fecha_desde.strftime('%d/%m/%Y')}</strong> al <strong>{fecha_hasta.strftime('%d/%m/%Y')}</strong></p>
<p style='margin:5px 0 0 0;font-size:12px;color:#718096;'>{days_selected} {'dia' if days_selected == 1 else 'dias'}</p>
</div>
""", unsafe_allow_html=True)
            email_count = None

        st.markdown("---")
        st.success("Gmail Conectado")

        # CAMBIO NUEVO: Acceso rapido al ultimo brief
        if st.session_state.last_brief:
            bi = st.session_state.last_brief
            st.markdown(f"""
<div style='background:#f0fff4;padding:12px;border-radius:6px;border-left:3px solid #38a169;margin-bottom:12px;'>
<p style='margin:0;font-size:12px;color:#22543d;'>Brief: <strong>{bi['target_email'][:25]}</strong> - {bi['generated_at']}</p>
</div>
""", unsafe_allow_html=True)
            st.download_button("⬇️ Re-descargar Brief", data=bi['pdf_bytes'], file_name=bi['pdf_filename'], mime="application/pdf", use_container_width=True)
            st.markdown("---")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.creds = None
            st.session_state.analysis_results = None
            st.session_state.last_brief = None
            st.rerun()

    # =================================================================
    # HEADER PRINCIPAL
    # =================================================================
    st.markdown("""
<div style='background:white;border:1px solid #e2e8f0;padding:48px 40px;border-radius:8px;margin-bottom:32px;'>
<div style='display:flex;align-items:center;gap:16px;margin-bottom:12px;'>
<div style='width:48px;height:48px;background:#1a1d29;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:24px;'>🏦</div>
<h1 style='margin:0;color:#1a1d29;font-size:38px;font-weight:600;'>Wealth Solutions Advisor</h1>
</div>
<p style='color:#718096;margin:0;font-size:16px;padding-left:64px;'>Analisis inteligente de relaciones con clientes de banca privada</p>
</div>
""", unsafe_allow_html=True)

    c_s, c_b = st.columns([4, 1])
    default_val = st.session_state.get("default_email", "")
    with c_s:
        target_email = st.text_input("Email del Cliente", value=default_val, placeholder="cliente@empresa.com", label_visibility="collapsed")
    with c_b:
        col_btn_a, col_btn_b = st.columns(2)
        with col_btn_a:
            run_btn = st.button("🚀 Analizar", type="primary", use_container_width=True)
        with col_btn_b:
            brief_btn = st.button("📄 Brief", use_container_width=True, help="Pre-Meeting Brief")

    # =================================================================
    # BOTON ANALIZAR
    # =================================================================
    if run_btn and target_email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not target_email.strip():
            st.error("Introduce un email"); st.stop()
        if not re.match(email_pattern, target_email.strip()):
            show_warning_box("Formato invalido", "Formato: usuario@dominio.com"); st.stop()

        target_email = target_email.strip().lower()
        save_to_history(target_email)
        mode = st.session_state.get('analysis_mode', 'Por numero de emails')
        info_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current, total, subject):
            progress_bar.progress(current / total)
            status_text.markdown(f"<p style='color:#718096;font-size:13px;text-align:center;'>Email {current}/{total} - {subject}</p>", unsafe_allow_html=True)

        try:
            if mode == "Por numero de emails":
                with info_placeholder.container():
                    st.markdown(f"""
<div style='background:white;border:1px solid #bee3f8;border-left:4px solid #3182ce;padding:20px;border-radius:8px;text-align:center;'>
<h4 style='color:#2c5282;margin:0 0 8px 0;'>Obteniendo emails</h4>
<p style='color:#4a90d9;margin:0;font-size:14px;'>Ultimos <strong>{email_count}</strong> emails de <strong>{target_email}</strong></p>
</div>
""", unsafe_allow_html=True)
                raw, ev, err = get_emails(st.session_state.creds, target_email, num_emails=email_count, progress_callback=update_progress)
            else:
                fecha_desde = st.session_state.get('fecha_desde')
                fecha_hasta = st.session_state.get('fecha_hasta')
                if not fecha_desde or not fecha_hasta:
                    info_placeholder.empty(); progress_bar.empty(); status_text.empty()
                    st.error("Selecciona un rango de fechas valido"); st.stop()
                with info_placeholder.container():
                    st.markdown(f"""
<div style='background:white;border:1px solid #bee3f8;border-left:4px solid #3182ce;padding:20px;border-radius:8px;text-align:center;'>
<h4 style='color:#2c5282;margin:0 0 8px 0;'>Buscando en rango</h4>
<p style='color:#4a90d9;margin:0;font-size:14px;'>Del <strong>{fecha_desde.strftime('%d/%m/%Y')}</strong> al <strong>{fecha_hasta.strftime('%d/%m/%Y')}</strong></p>
</div>
""", unsafe_allow_html=True)
                raw, ev, err = get_emails(st.session_state.creds, target_email, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, progress_callback=update_progress)

            info_placeholder.empty(); progress_bar.empty(); status_text.empty()

            if err and (not raw or not ev):
                show_error_box("Error al obtener emails", err, suggestions=["Verifica el email", "Revisa permisos Gmail", "Cierra sesion y reautentica"]); st.stop()
            if not raw or not ev:
                show_empty_state("📭", "No se encontraron emails", f"No hay conversaciones con <strong>{target_email}</strong>", suggestions=["Verifica el email", "Amplia el rango"]); st.stop()
            if err:
                show_warning_box("Advertencia", err)

            ai_placeholder = st.empty()
            with ai_placeholder.container():
                st.markdown(f"""
<div style='background:white;border:1px solid #d6bcfa;border-left:4px solid #805ad5;padding:20px;border-radius:8px;text-align:center;'>
<h4 style='color:#553c9a;margin:0 0 8px 0;'>Analizando con IA</h4>
<p style='color:#6b46c1;margin:0;font-size:14px;'>Procesando <strong>{len(ev)} emails</strong>... (10-15s)</p>
</div>
""", unsafe_allow_html=True)
            an, ai_err = analyze_with_ai(raw, len(ev))
            ai_placeholder.empty()

            if ai_err:
                an = generate_fallback_analysis(ev, target_email)
                show_warning_box("Modo Basico", f"<strong>Motivo:</strong> {ai_err}", tips=[f"{len(ev)} emails cargados OK", 'Usa Explorador Avanzado'])

            st.session_state.analysis_results = {
                'analysis': an, 'evidence': ev, 'target_email': target_email,
                'analysis_mode': mode,
                'email_count': email_count if mode == "Por numero de emails" else None,
                'fecha_desde': fecha_desde if mode == "Por rango de fechas" else None,
                'fecha_hasta': fecha_hasta if mode == "Por rango de fechas" else None,
                'raw_text': raw
            }
            show_success_box("Analisis completado", "Resultados disponibles")
        except Exception as e:
            progress_bar.empty(); status_text.empty()
            show_error_box("Error inesperado", "Contacta a soporte.", details=str(e)); st.stop()

    # =================================================================
    # BOTON BRIEF
    # =================================================================
    if brief_btn and target_email:
        if '@' not in target_email:
            st.error("Email invalido")
        else:
            if (st.session_state.analysis_results and st.session_state.analysis_results.get('target_email') == target_email and st.session_state.analysis_results.get('raw_text')):
                raw_text = st.session_state.analysis_results['raw_text']
                evidence_brief = st.session_state.analysis_results['evidence']
            else:
                with st.spinner("Obteniendo emails..."):
                    raw_text, evidence_brief, err = get_emails(st.session_state.creds, target_email, num_emails=15)
                    if err and (not raw_text or not evidence_brief):
                        show_error_box("Error", err); st.stop()
                    if not raw_text or not evidence_brief:
                        show_empty_state("📭", "Sin emails", f"No hay datos de {target_email}"); st.stop()

            with st.spinner("Generando Brief..."):
                brief_data, brief_err = generate_meeting_brief(raw_text, len(evidence_brief), target_email)
                if brief_err:
                    show_error_box("Error brief", brief_err); st.stop()

            try:
                import tempfile
                with st.spinner("Generando PDF..."):
                    temp_dir = tempfile.gettempdir()
                    pdf_filename = f"brief_{target_email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    pdf_path = os.path.join(temp_dir, pdf_filename)
                    generate_brief_pdf(brief_data, target_email, pdf_path)
                    with open(pdf_path, "rb") as pf:
                        pdf_bytes = pf.read()
                    try: os.remove(pdf_path)
                    except Exception: pass

                st.session_state.last_brief = {'data': brief_data, 'pdf_bytes': pdf_bytes, 'pdf_filename': pdf_filename, 'target_email': target_email, 'generated_at': datetime.now().strftime('%H:%M')}

                col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
                with col_r2:
                    st.markdown("""
<div style='background:white;border:1px solid #9ae6b4;border-left:4px solid #38a169;padding:40px;border-radius:8px;text-align:center;'>
<div style='font-size:56px;margin-bottom:16px;'>✅</div>
<h2 style='color:#22543d;margin:0 0 12px 0;font-size:24px;'>Brief Generado</h2>
<p style='color:#38a169;margin:0;font-size:14px;'>Listo para descargar</p>
</div>
""", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.download_button("⬇️ Descargar Brief en PDF", data=pdf_bytes, file_name=pdf_filename, mime="application/pdf", use_container_width=True, type="primary")
            except Exception as e:
                import traceback
                show_error_box("Error PDF", str(e), details=traceback.format_exc())

    # =================================================================
    # RESULTADOS
    # =================================================================
    if st.session_state.analysis_results:
        data = st.session_state.analysis_results['analysis']
        evidence = st.session_state.analysis_results['evidence']
        mode_used = st.session_state.analysis_results.get('analysis_mode', 'N/A')
        urgencia = data.get('urgencia', 'Media')

        if mode_used == "Por numero de emails":
            periodo_text = f"Ultimos {st.session_state.analysis_results.get('email_count', len(evidence))} emails"
        else:
            fd = st.session_state.analysis_results.get('fecha_desde')
            fh = st.session_state.analysis_results.get('fecha_hasta')
            periodo_text = f"Del {fd.strftime('%d/%m')} al {fh.strftime('%d/%m')}" if fd and fh else "Periodo personalizado"

        if urgencia == 'Alta':     badge_color, badge_bg, badge_border = "#742a2a", "#fff5f5", "#feb2b2"
        elif urgencia == 'Baja':   badge_color, badge_bg, badge_border = "#22543d", "#f0fff4", "#9ae6b4"
        else:                      badge_color, badge_bg, badge_border = "#744210", "#fffbeb", "#fbd38d"

        badge_col, export_col = st.columns([3, 1])
        with badge_col:
            st.markdown(f"""
<div style='background:white;border:1px solid #e2e8f0;padding:20px 28px;border-radius:8px;'>
<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:20px;'>
<div style='display:flex;align-items:center;gap:20px;'>
<div style='background:{badge_bg};color:{badge_color};padding:6px 14px;border-radius:4px;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;border:1px solid {badge_border};'>{urgencia}</div>
<div style='color:#4a5568;font-size:14px;'><span style='color:#1a1d29;font-weight:600;'>{len(evidence)}</span> emails · {periodo_text}</div>
</div>
<div style='color:#718096;font-size:13px;'>📧 {st.session_state.analysis_results.get('target_email', '')}</div>
</div></div>
""", unsafe_allow_html=True)

        with export_col:
            summary_text = generate_analysis_summary_text(data, evidence, st.session_state.analysis_results.get('target_email', ''))
            st.download_button("⬇️ Exportar Análisis", data=summary_text, file_name=f"analisis_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain", use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📖 Historia de la Conversación")

        last_email = evidence[-1]
        if last_email['Origen'] == 'CLIENTE':
            e_icon, e_titulo, e_desc = "⏳", "Pendiente de respuesta", f"Ultimo mensaje del cliente: {last_email['Fecha']}"
            e_bg, e_border, e_color = "#fff5f5", "#feb2b2", "#742a2a"
        else:
            e_icon, e_titulo, e_desc = "✓", "Al dia", f"Tu ultima respuesta: {last_email['Fecha']}"
            e_bg, e_border, e_color = "#f0fff4", "#9ae6b4", "#22543d"

        st.markdown(f"""
<div style='background:{e_bg};border:1px solid {e_border};border-left:4px solid {e_border};padding:20px 24px;border-radius:8px;margin-bottom:24px;'>
<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px;'>
<span style='font-size:20px;'>{e_icon}</span>
<h4 style='color:{e_color};margin:0;font-size:15px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;'>{e_titulo}</h4>
</div>
<p style='color:{e_color};margin:0;font-size:14px;padding-left:32px;'>{e_desc}</p>
<p style='color:{e_color};margin:8px 0 0 32px;font-size:13px;font-style:italic;opacity:0.8;'>"{last_email['Asunto_Completo']}"</p>
</div>
""", unsafe_allow_html=True)

        st.markdown(f"""
<div style='background:white;border:1px solid #e2e8f0;padding:32px 36px;border-radius:8px;margin-bottom:32px;'>
<p style='color:#2d3748;font-size:17px;line-height:1.9;margin:0;'>{data.get('resumen_exhaustivo', 'Generando...')}</p>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:24px;'><h3 style='color:#1a1d29;font-size:18px;margin:0;font-weight:600;'>Metricas Clave</h3></div>", unsafe_allow_html=True)

        k1, k2, k3 = st.columns(3, gap="medium")
        with k1:
            urg = data.get('urgencia', 'N/A')
            if urg == "Alta":    urg_color, urg_icon = "#742a2a", "⚠️"
            elif urg == "Baja":  urg_color, urg_icon = "#22543d", "✓"
            else:                urg_color, urg_icon = "#744210", "○"
            st.markdown(f"""
<div style='background:white;border:1px solid #e2e8f0;padding:24px;border-radius:8px;text-align:center;'>
<div style='font-size:32px;margin-bottom:12px;'>{urg_icon}</div>
<p style='color:#718096;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px 0;font-weight:600;'>Urgencia</p>
<p style='color:{urg_color};font-size:24px;font-weight:700;margin:0;'>{urg}</p>
</div>
""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
<div style='background:white;border:1px solid #e2e8f0;padding:24px;border-radius:8px;text-align:center;'>
<div style='font-size:32px;margin-bottom:12px;'>📧</div>
<p style='color:#718096;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px 0;font-weight:600;'>Total Emails</p>
<p style='color:#1a1d29;font-size:24px;font-weight:700;margin:0;'>{len(evidence)}</p>
</div>
""", unsafe_allow_html=True)
        with k3:
            scores = [x['sentimiento_score'] for x in data.get('analisis_sentimiento', [])]
            avg = round(sum(scores) / len(scores), 1) if scores else 0
            if avg >= 5:    salud_color, salud_icon = "#22543d", "😊"
            elif avg >= 0:  salud_color, salud_icon = "#744210", "😐"
            else:           salud_color, salud_icon = "#742a2a", "😟"
            st.markdown(f"""
<div style='background:white;border:1px solid #e2e8f0;padding:24px;border-radius:8px;text-align:center;'>
<div style='font-size:32px;margin-bottom:12px;'>{salud_icon}</div>
<p style='color:#718096;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px 0;font-weight:600;'>Salud Relacion</p>
<p style='color:{salud_color};font-size:24px;font-weight:700;margin:0;'>{avg}<span style='font-size:16px;color:#718096;'>/10</span></p>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='border-top:2px solid #e0e6ed;margin:30px 0;'></div>", unsafe_allow_html=True)

        # GRAFICO SENTIMIENTO
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:24px;'><h3 style='color:#1a1d29;font-size:18px;margin:0;font-weight:600;'>Evolucion del Sentimiento</h3><p style='color:#718096;font-size:14px;margin:8px 0 0 0;'>Analisis cronologico de la relacion</p></div>", unsafe_allow_html=True)

        sent_data = data.get('analisis_sentimiento', [])
        limit = min(len(sent_data), len(evidence))

        if limit > 0:
            df_chart = pd.DataFrame({
                'Fecha': [e['Fecha'] for e in evidence[:limit]],
                'Score': [s['sentimiento_score'] for s in sent_data[:limit]],
                'Asunto': [e['Asunto'] for e in evidence[:limit]],
                'Explicacion': [s.get('explicacion', '') for s in sent_data[:limit]],
                'Origen': [e['Origen'] for e in evidence[:limit]],
                'ID': [e['Id'] for e in evidence[:limit]]
            })
            fig = go.Figure()
            fig.add_hrect(y0=5, y1=11, line_width=0, fillcolor="rgba(46,204,113,0.1)", layer="below")
            fig.add_hrect(y0=-11, y1=-5, line_width=0, fillcolor="rgba(231,76,60,0.1)", layer="below")
            fig.add_trace(go.Scatter(
                x=df_chart['Fecha'], y=df_chart['Score'], mode='lines+markers', name='Sentimiento',
                line=dict(color='#1a2b4b', width=3, shape='spline', smoothing=1.3),
                marker=dict(size=[max(8, abs(s)*1.5) for s in df_chart['Score']], color=df_chart['Score'], colorscale='RdYlGn', line=dict(width=2, color='white'), showscale=False, cmin=-10, cmax=10),
                customdata=df_chart[['Asunto', 'Explicacion', 'Origen', 'ID']],
                hovertemplate="<b>%{customdata[2]}</b> (ID: %{customdata[3]})<br>%{x}<br>---<br><b>%{customdata[0]}</b><br><i>%{customdata[1]}</i><br>---<br>Score: <b>%{y}</b><extra></extra>"
            ))
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="Neutral (0)", annotation_position="bottom right")
            fig.update_layout(height=500, plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='white', yaxis=dict(range=[-11, 11], title="Negativo - Positivo", showgrid=True, gridcolor='rgba(0,0,0,0.05)'), xaxis=dict(showgrid=False), hovermode='closest', margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Puntos grandes = emociones intensas. Verde = confort, Rojo = riesgo.")

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='border-top:2px solid #e0e6ed;margin:20px 0 30px 0;'></div>", unsafe_allow_html=True)

        # NAVEGACION
        NAV_ESTRATEGIA = "💡 Estrategia & Insights"
        NAV_GENERADOR = "✉️ Generador de Respuesta"
        NAV_EXPLORADOR = "📬 Explorador Avanzado"

        selected_view = st.radio("Navegacion", [NAV_ESTRATEGIA, NAV_GENERADOR, NAV_EXPLORADOR], horizontal=True, label_visibility="collapsed", key="navigation_view")
        st.markdown("<br>", unsafe_allow_html=True)

        # VISTA 1: ESTRATEGIA
        if selected_view == NAV_ESTRATEGIA:
            col_left, col_right = st.columns([1, 1], gap="medium")
            with col_left:
                st.markdown("<div style='margin-bottom:24px;'><h4 style='color:#1a1d29;font-size:16px;margin:0;font-weight:600;'>Tu Proxima Accion</h4></div>", unsafe_allow_html=True)
                te = st.session_state.analysis_results.get('target_email', '')
                st.markdown(f"""
<div style="background:white;border:1px solid #e2e8f0;padding:28px;border-radius:8px;">
<p style="color:#2d3748;margin:0 0 24px 0;font-size:15px;line-height:1.7;">{data.get('accion_recomendada', 'Sin accion definida')}</p>
<a href="https://mail.google.com/mail/?view=cm&fs=1&to={te}&su=Seguimiento" target="_blank" style="display:inline-block;background:linear-gradient(135deg,#004e98,#003d7a);color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;box-shadow:0 2px 8px rgba(0,78,152,0.2);transition:all 0.2s;">📧 Escribir Email</a>
</div>
""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:24px;'><h4 style='color:#1a1d29;font-size:16px;margin:0;font-weight:600;'>Perfil del Cliente</h4></div>", unsafe_allow_html=True)
                uv = data.get('urgencia', 'Media')
                if uv == 'Alta':    pf_ic, pf_cb, pf_cf = "🔴", "#d32f2f", "#ffebee"
                elif uv == 'Baja':  pf_ic, pf_cb, pf_cf = "🟢", "#388e3c", "#e8f5e9"
                else:               pf_ic, pf_cb, pf_cf = "🟡", "#f57c00", "#fff3e0"
                st.markdown(f"""
<div style="background:{pf_cf};padding:20px;border-radius:8px;border-left:5px solid {pf_cb};">
<div style="display:flex;align-items:flex-start;">
<span style="font-size:32px;margin-right:15px;">{pf_ic}</span>
<p style="color:#37474f;margin:0;font-size:15px;line-height:1.6;">{data.get('perfil_cliente', 'Perfil no identificado')}</p>
</div></div>
""", unsafe_allow_html=True)

            with col_right:
                st.markdown("<div style='margin-bottom:24px;'><h4 style='color:#1a1d29;font-size:16px;margin:0;font-weight:600;'>Insights Estrategicos</h4></div>", unsafe_allow_html=True)
                insights = data.get('insights_clave', [])
                if not insights:
                    st.markdown("<div style='background:white;border:1px solid #e2e8f0;padding:28px;border-radius:8px;text-align:center;'><p style='color:#718096;margin:0;'>No se detectaron insights</p></div>", unsafe_allow_html=True)
                else:
                    for idx, insight in enumerate(insights, 1):
                        bc = "#1a1d29" if idx == 1 else "#e2e8f0"
                        ibg = "#1a1d29" if idx == 1 else "#f7fafc"
                        ic_v = "white" if idx == 1 else "#4a5568"
                        st.markdown(f"""
<div style='background:white;border:1px solid {bc};padding:20px 24px;border-radius:8px;margin-bottom:12px;'>
<div style='display:flex;align-items:flex-start;gap:14px;'>
<div style='background:{ibg};color:{ic_v};min-width:32px;height:32px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;'>{idx}</div>
<p style='color:#2d3748;font-size:14px;line-height:1.7;margin:4px 0 0 0;'>{insight}</p>
</div></div>
""", unsafe_allow_html=True)

        # VISTA 2: GENERADOR
        elif selected_view == NAV_GENERADOR:
            st.markdown("<div style='text-align:center;padding:20px 0 10px 0;'><div style='font-size:48px;margin-bottom:10px;'>✉️</div><h3 style='color:#1a2b4b;margin:0;'>Email Generado</h3><p style='color:#7f8c8d;font-size:14px;margin-top:8px;'>Personaliza antes de enviar.</p></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.text_area("Contenido:", value=data.get('borrador_respuesta', 'No disponible'), height=400, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            cb1, cb2, cb3 = st.columns([2, 2, 1])
            with cb1:
                gu = f"https://mail.google.com/mail/?view=cm&fs=1&to={st.session_state.analysis_results.get('target_email', '')}&su=Seguimiento"
                st.link_button("🔗 Abrir en Gmail", gu, use_container_width=True, type="primary")
            with cb2:
                st.button("📋 Copiar texto", use_container_width=True, key="copy_draft")
            with cb3:
                st.button("🔄 Regenerar", use_container_width=True, help="Regenerar borrador", key="regenerate_draft")

        # VISTA 3: EXPLORADOR
        elif selected_view == NAV_EXPLORADOR:
            st.markdown("<div style='background:white;padding:20px 25px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:25px;border-left:5px solid #004e98;'><h4 style='margin:0;color:#1a2b4b;font-size:18px;'>Filtros de Busqueda</h4></div>", unsafe_allow_html=True)

            if 'f_origen_key' not in st.session_state: st.session_state.f_origen_key = "Todos"
            if 'f_texto_key' not in st.session_state: st.session_state.f_texto_key = ""
            if 'f_fecha_key' not in st.session_state: st.session_state.f_fecha_key = "Todas"

            fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 1])
            with fc1:
                f_origen = st.selectbox("Origen", ["Todos", "CLIENTE", "BANCO"], index=["Todos", "CLIENTE", "BANCO"].index(st.session_state.f_origen_key), key="f_origen_key")
            with fc2:
                f_texto = st.text_input("Buscar", value=st.session_state.f_texto_key, placeholder="Ej: inversion...", key="f_texto_key")
            with fc3:
                f_fecha = st.selectbox("Fecha", ["Todas", "7 dias", "30 dias"], index=["Todas", "7 dias", "30 dias"].index(st.session_state.f_fecha_key), key="f_fecha_key")
            with fc4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Limpiar", key="clear_filters", use_container_width=True):
                    st.session_state.f_origen_key = "Todos"
                    st.session_state.f_texto_key = ""
                    st.session_state.f_fecha_key = "Todas"
                    st.rerun()

            st.markdown("---")

            filtered_ev = evidence.copy()
            if f_origen != "Todos":
                filtered_ev = [e for e in filtered_ev if e['Origen'] == f_origen]
            if f_texto:
                term = f_texto.lower()
                filtered_ev = [e for e in filtered_ev if term in e['Asunto_Completo'].lower() or term in e['Cuerpo'].lower()]
            if f_fecha != "Todas":
                days = 7 if "7" in f_fecha else 30
                limit_date = datetime.now() - timedelta(days=days)
                filtered_ev = [e for e in filtered_ev if datetime.strptime(e['Fecha'], '%Y-%m-%d %H:%M') >= limit_date]

            if len(filtered_ev) < len(evidence):
                st.info(f"**{len(filtered_ev)}** de **{len(evidence)}** emails coinciden")
            else:
                st.success(f"Mostrando **{len(evidence)}** emails")

            st.markdown("<br>", unsafe_allow_html=True)

            if not filtered_ev:
                show_empty_state("📭", "Sin coincidencias", "Ajusta los filtros")
            else:
                for email in filtered_ev:
                    icon = "👤" if email['Origen'] == "CLIENTE" else "🏦"
                    color = "green" if email['Origen'] == "CLIENTE" else "blue"
                    with st.expander(f"{icon} {email['Fecha_Corta']} | {email['Asunto']}"):
                        st.markdown(f"""
<div style='background:#f7fafc;padding:12px 16px;border-radius:6px;margin-bottom:12px;'>
<b>De:</b> :{color}[{email['Origen']}] · <b>Fecha:</b> {email['Fecha']} · <b>Asunto:</b> {email['Asunto_Completo']}
</div>
""", unsafe_allow_html=True)
                        body_show = email['Cuerpo']
                        if f_texto:
                            body_show = re.sub(f"({re.escape(f_texto)})", r"<mark style='background:#fff9c4'>\1</mark>", body_show, flags=re.IGNORECASE)
                        st.markdown(f"<div style='font-size:14px;line-height:1.7;color:#2d3748;'>{body_show}</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                        cb1, cb2 = st.columns([1, 2])
                        analysis_key = f"thread_analysis_{email['Id']}"
                        with cb1:
                            gu = f"https://mail.google.com/mail/u/0/#inbox/{email['Id_Completo']}"
                            st.link_button("🔗 Abrir en Gmail", gu, use_container_width=True)
                        with cb2:
                            bl = "Analisis cargado" if analysis_key in st.session_state else "Analizar Hilo"
                            bt = "secondary" if analysis_key in st.session_state else "primary"
                            if st.button(bl, key=f"btn_{email['Id']}", use_container_width=True, type=bt):
                                ph = st.empty()
                                with ph.container():
                                    st.markdown("<div style='background:white;border:1px solid #d6bcfa;border-left:4px solid #805ad5;padding:20px;border-radius:8px;text-align:center;'><h4 style='color:#553c9a;margin:0;'>Analizando hilo...</h4></div>", unsafe_allow_html=True)
                                try:
                                    service = build('gmail', 'v1', credentials=st.session_state.creds)
                                    meta = service.users().messages().get(userId='me', id=email['Id_Completo'], format='minimal').execute()
                                    thread_id = meta.get('threadId')
                                    thread_content = get_thread_content(st.session_state.creds, thread_id)
                                    if thread_content:
                                        analysis_result = analyze_thread_structure(thread_content)
                                        st.session_state[analysis_key] = analysis_result
                                        ph.empty()
                                        st.rerun()
                                    else:
                                        ph.empty()
                                        st.error("No se pudo leer el hilo.")
                                except Exception as e:
                                    ph.empty()
                                    st.error(f"Error: {e}")

                        if analysis_key in st.session_state:
                            st.markdown("<br>", unsafe_allow_html=True)
                            ch1, ch2 = st.columns([4, 1])
                            with ch1:
                                st.markdown("<div style='background:#fff3e0;padding:15px 20px;border-radius:8px 8px 0 0;border-left:5px solid #ef6c00;'><h4 style='color:#ef6c00;margin:0;'>Inteligencia de Hilo</h4></div>", unsafe_allow_html=True)
                            with ch2:
                                if st.button("X", key=f"close_{email['Id']}", help="Cerrar"):
                                    del st.session_state[analysis_key]
                                    st.rerun()
                            st.markdown("<div style='background:white;border:2px solid #ffe0b2;border-top:none;padding:25px;border-radius:0 0 8px 8px;'>", unsafe_allow_html=True)
                            st.markdown(st.session_state[analysis_key])
                            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
<div style='text-align:center;padding:60px 40px;background:white;border-radius:16px;border:1px solid #e2e8f0;'>
<div style='font-size:80px;margin-bottom:20px;opacity:0.5;'>🔍</div>
<h2 style='color:#1a2b4b;margin-bottom:15px;'>Bienvenido a WS Advisor</h2>
<p style='color:#7f8c8d;font-size:16px;margin-bottom:40px;'>Analiza conversaciones con IA para obtener insights accionables</p>
<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:900px;margin:0 auto;text-align:left;'>
<div style='background:#f8f9fa;padding:22px;border-radius:14px;border-left:4px solid #004e98;'><strong style='color:#1a2b4b;'>1. Introduce el email</strong><p style='color:#7f8c8d;margin:8px 0 0 0;font-size:14px;'>En el campo de busqueda</p></div>
<div style='background:#f8f9fa;padding:22px;border-radius:14px;border-left:4px solid #004e98;'><strong style='color:#1a2b4b;'>2. Configura el periodo</strong><p style='color:#7f8c8d;margin:8px 0 0 0;font-size:14px;'>Emails o fechas en el panel lateral</p></div>
<div style='background:#f8f9fa;padding:22px;border-radius:14px;border-left:4px solid #004e98;'><strong style='color:#1a2b4b;'>3. Haz clic en Analizar</strong><p style='color:#7f8c8d;margin:8px 0 0 0;font-size:14px;'>Sentimiento, estrategia y borradores</p></div>
</div></div>
""", unsafe_allow_html=True)