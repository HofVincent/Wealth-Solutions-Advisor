import streamlit as st
import pandas as pd
import json
import os # <--- NUEVO: Para gestionar el archivo de historial
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from openai import OpenAI
import base64
from email.utils import parsedate_to_datetime
import hmac

# =============================================================================
# COMPONENTES REUTILIZABLES DE UI
# =============================================================================

# =============================================================================
# COMPONENTES REUTILIZABLES DE UI - ESTILO PREMIUM
# =============================================================================

def show_error_box(title, message, details=None, suggestions=None):
    """Muestra un cuadro de error con estilo premium minimalista."""
    suggestions_html = ""
    if suggestions:
        suggestions_html = "<div style='margin-top: 16px; padding: 16px; background: #fff5f5; border-radius: 6px;'>"
        suggestions_html += "<p style='color: #742a2a; font-size: 13px; font-weight: 600; margin: 0 0 8px 0;'>Sugerencias:</p>"
        suggestions_html += "<ul style='color: #742a2a; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8;'>"
        for suggestion in suggestions:
            suggestions_html += f"<li>{suggestion}</li>"
        suggestions_html += "</ul></div>"
    
    details_html = ""
    if details:
        details_html = f"""
        <details style='margin-top: 16px;'>
            <summary style='cursor: pointer; color: #742a2a; font-weight: 600; font-size: 13px;'>Ver detalles técnicos</summary>
            <pre style='background: #fff5f5; padding: 12px; border-radius: 6px; margin-top: 8px; font-size: 11px; overflow-x: auto; color: #742a2a; border: 1px solid #feb2b2;'>{details}</pre>
        </details>
        """
    
    st.markdown(f"""
<div style='background: white; border: 1px solid #feb2b2; border-left: 4px solid #e53e3e; padding: 24px; border-radius: 8px; margin: 24px 0;'>
    <div style='display: flex; align-items: flex-start; gap: 12px;'>
        <div style='font-size: 20px; line-height: 1;'>⚠️</div>
        <div style='flex: 1;'>
            <h4 style='color: #742a2a; margin: 0 0 8px 0; font-size: 16px; font-weight: 600; font-family: Inter, sans-serif;'>{title}</h4>
            <p style='color: #742a2a; margin: 0; font-size: 14px; line-height: 1.6;'>{message}</p>
            {suggestions_html}
            {details_html}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


def show_warning_box(title, message, tips=None):
    """Muestra un cuadro de advertencia con estilo premium minimalista."""
    tips_html = ""
    if tips:
        tips_html = "<div style='margin-top: 16px; padding: 16px; background: #fffbeb; border-radius: 6px;'>"
        tips_html += "<p style='color: #744210; font-size: 13px; font-weight: 600; margin: 0 0 8px 0;'>Recomendaciones:</p>"
        tips_html += "<ul style='color: #744210; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8;'>"
        for tip in tips:
            tips_html += f"<li>{tip}</li>"
        tips_html += "</ul></div>"
    
    st.markdown(f"""
<div style='background: white; border: 1px solid #fbd38d; border-left: 4px solid #ed8936; padding: 24px; border-radius: 8px; margin: 24px 0;'>
    <div style='display: flex; align-items: flex-start; gap: 12px;'>
        <div style='font-size: 20px; line-height: 1;'>⚡</div>
        <div style='flex: 1;'>
            <h4 style='color: #744210; margin: 0 0 8px 0; font-size: 16px; font-weight: 600; font-family: Inter, sans-serif;'>{title}</h4>
            <p style='color: #744210; margin: 0; font-size: 14px; line-height: 1.6;'>{message}</p>
            {tips_html}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


def show_success_box(title, message):
    """Muestra un cuadro de éxito con estilo premium minimalista."""
    st.markdown(f"""
<div style='background: white; border: 1px solid #9ae6b4; border-left: 4px solid #38a169; padding: 24px; border-radius: 8px; margin: 24px 0;'>
    <div style='display: flex; align-items: flex-start; gap: 12px;'>
        <div style='font-size: 20px; line-height: 1;'>✓</div>
        <div style='flex: 1;'>
            <h4 style='color: #22543d; margin: 0 0 8px 0; font-size: 16px; font-weight: 600; font-family: Inter, sans-serif;'>{title}</h4>
            <p style='color: #22543d; margin: 0; font-size: 14px; line-height: 1.6;'>{message}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


def show_info_box(title, message, icon="ℹ️"):
    """Muestra un cuadro informativo con estilo premium minimalista."""
    st.markdown(f"""
<div style='background: white; border: 1px solid #bee3f8; border-left: 4px solid #3182ce; padding: 24px; border-radius: 8px; margin: 24px 0;'>
    <div style='display: flex; align-items: flex-start; gap: 12px;'>
        <div style='font-size: 20px; line-height: 1;'>{icon}</div>
        <div style='flex: 1;'>
            <h4 style='color: #2c5282; margin: 0 0 8px 0; font-size: 16px; font-weight: 600; font-family: Inter, sans-serif;'>{title}</h4>
            <p style='color: #2c5282; margin: 0; font-size: 14px; line-height: 1.6;'>{message}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


def show_empty_state(icon, title, subtitle, suggestions=None):
    """Muestra un estado vacío con estilo premium minimalista."""
    suggestions_html = ""
    if suggestions:
        suggestions_html = "<div style='background: #f7fafc; padding: 20px; border-radius: 6px; border: 1px solid #e2e8f0; margin-top: 24px;'>"
        suggestions_html += "<p style='color: #2d3748; font-size: 13px; font-weight: 600; margin: 0 0 12px 0;'>Sugerencias:</p>"
        suggestions_html += "<ul style='color: #4a5568; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8;'>"
        for suggestion in suggestions:
            suggestions_html += f"<li>{suggestion}</li>"
        suggestions_html += "</ul></div>"
    
    st.markdown(f"""
<div style='background: white; border: 1px solid #e2e8f0; padding: 48px 32px; border-radius: 8px; margin: 32px 0; text-align: center;'>
    <div style='font-size: 56px; margin-bottom: 16px; opacity: 0.5;'>{icon}</div>
    <h3 style='color: #1a1d29; margin: 0 0 8px 0; font-size: 20px; font-weight: 600;'>{title}</h3>
    <p style='color: #718096; margin: 0; font-size: 15px; line-height: 1.6;'>{subtitle}</p>
    {suggestions_html}
</div>
""", unsafe_allow_html=True)

def generate_analysis_summary_text(analysis_data, evidence_data, target_email):
    """
    Genera un resumen de texto plano del análisis para exportar.
    
    Args:
        analysis_data: Resultado del análisis de IA
        evidence_data: Lista de emails procesados
        target_email: Email del cliente
    
    Returns:
        str: Texto formateado listo para copiar/exportar
    """
    from datetime import datetime
    
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
    
    insights = analysis_data.get('insights_clave', [])
    for idx, insight in enumerate(insights, 1):
        text += f"{idx}. {insight}\n"
    
    text += "\n───────────────────────────────────────────────────────────────\n\n"
    text += "📊 EVOLUCIÓN DE SENTIMIENTO:\n\n"
    
    sentimientos = analysis_data.get('analisis_sentimiento', [])
    for sent in sentimientos[:10]:  # Primeros 10 emails
        email_num = sent.get('email_num', 'N/A')
        score = sent.get('sentimiento_score', 0)
        explicacion = sent.get('explicacion', 'N/A')
        
        # Barra visual simple
        bar = "█" * max(0, int((score + 10) / 2))
        text += f"Email #{email_num}: [{score:+3d}/10] {bar}\n"
        text += f"           {explicacion}\n\n"
    
    text += "───────────────────────────────────────────────────────────────\n\n"
    text += "✉️ BORRADOR DE RESPUESTA SUGERIDO:\n\n"
    text += analysis_data.get('borrador_respuesta', 'N/A')
    text += "\n\n═══════════════════════════════════════════════════════════════\n"
    text += "         Generado por Wealth Solutions Advisor v1.0\n"
    text += "═══════════════════════════════════════════════════════════════\n"
    
    return text
def generate_brief_pdf(brief_data, target_email, output_path="brief.pdf"):
    """
    Genera un PDF profesional del Pre-Meeting Brief.
    
    Args:
        brief_data: Datos del brief generado por la IA
        target_email: Email del cliente
        output_path: Ruta donde guardar el PDF
    
    Returns:
        str: Ruta del archivo generado
    """
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        PageBreak, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from datetime import datetime
    
    # Crear el documento
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=80,
        bottomMargin=50
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para títulos
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a2b4b'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#004e98'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        leading=16
    )
    
    # Estilo para badges
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Container para elementos del PDF
    elements = []
    
    # === HEADER ===
    header_data = [
        [Paragraph("🏦 WEALTH SOLUTIONS ADVISOR", title_style)],
        [Paragraph("PRE-MEETING BRIEF", subtitle_style)],
    ]
    header_table = Table(header_data, colWidths=[6.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f7fa')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # === METADATA ===
    metadata_data = [
        [Paragraph("<b>Cliente:</b>", normal_style), Paragraph(target_email, normal_style)],
        [Paragraph("<b>Fecha:</b>", normal_style), Paragraph(datetime.now().strftime('%d/%m/%Y %H:%M'), normal_style)],
        [Paragraph("<b>Tipo:</b>", normal_style), Paragraph("Pre-Meeting Brief Ejecutivo", normal_style)],
    ]
    metadata_table = Table(metadata_data, colWidths=[1.5*inch, 5*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90caf9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 25))
    
    # === CONTEXTO RÁPIDO ===
    elements.append(Paragraph("📋 CONTEXTO RÁPIDO", subtitle_style))
    contexto_box = Table(
        [[Paragraph(brief_data.get('contexto_rapido', 'N/A'), normal_style)]],
        colWidths=[6.5*inch]
    )
    contexto_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#4caf50')),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(contexto_box)
    elements.append(Spacer(1, 20))
    
    # === TEMAS DE REUNIÓN ===
    elements.append(Paragraph("📌 AGENDA DE REUNIÓN", subtitle_style))
    
    temas = brief_data.get('temas_reunion', [])
    for idx, tema in enumerate(temas[:5], 1):
        prioridad = tema.get('prioridad', 'INFORMATIVO')
        
        # Color según prioridad
        if prioridad == 'URGENTE':
            color_bg = colors.HexColor('#ffebee')
            color_border = colors.HexColor('#d32f2f')
        elif prioridad == 'IMPORTANTE':
            color_bg = colors.HexColor('#fff3e0')
            color_border = colors.HexColor('#f57c00')
        else:
            color_bg = colors.HexColor('#e3f2fd')
            color_border = colors.HexColor('#1976d2')
        
        tema_content = [
            [Paragraph(f"<b>{idx}. {tema.get('tema', 'N/A')}</b> [{prioridad}]", normal_style)],
            [Paragraph(tema.get('detalle', 'N/A'), normal_style)],
            [Paragraph(f"<i>💡 {tema.get('contexto', 'N/A')}</i>", normal_style)],
        ]
        tema_table = Table(tema_content, colWidths=[6.5*inch])
        tema_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_bg),
            ('BOX', (0, 0), (-1, -1), 2, color_border),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(tema_table)
        elements.append(Spacer(1, 10))
    
    elements.append(Spacer(1, 15))
    
    # === PENDIENTES (2 columnas) ===
    elements.append(Paragraph("⚠️ PENDIENTES", subtitle_style))
    
    # Preparar pendientes del cliente
    pendientes_cliente_list = brief_data.get('pendientes_cliente', [])
    cliente_text = "<br/>".join([f"• {p}" for p in pendientes_cliente_list[:5]]) if pendientes_cliente_list else "✅ Ninguno"
    
    # Preparar pendientes del banco
    pendientes_banco_list = brief_data.get('pendientes_banco', [])
    banco_text = "<br/>".join([f"• {p}" for p in pendientes_banco_list[:5]]) if pendientes_banco_list else "✅ Ninguno"
    
    pendientes_data = [
        [Paragraph("<b>👤 Cliente</b>", normal_style), Paragraph("<b>🏦 Banco</b>", normal_style)],
        [Paragraph(cliente_text, normal_style), Paragraph(banco_text, normal_style)],
    ]
    pendientes_table = Table(pendientes_data, colWidths=[3.25*inch, 3.25*inch])
    pendientes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#ffebee')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#e3f2fd')),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#fff5f5')),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#f5f9ff')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cfd8dc')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(pendientes_table)
    elements.append(Spacer(1, 20))
    
    # === TALKING POINTS ===
    elements.append(Paragraph("🎤 TALKING POINTS SUGERIDOS", subtitle_style))
    
    talking_points = brief_data.get('talking_points', [])
    for idx, point in enumerate(talking_points[:3], 1):
        point_table = Table(
            [[Paragraph(f'<b>{idx}.</b> "{point}"', normal_style)]],
            colWidths=[6.5*inch]
        )
        point_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3e5f5')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#9c27b0')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(point_table)
        elements.append(Spacer(1, 8))
    
    elements.append(Spacer(1, 15))
    
    # === TIMELINE ===
    elements.append(Paragraph("⏰ TIMELINE RECIENTE", subtitle_style))
    
    timeline_data = [["Fecha", "Quién", "Qué Pasó"]]
    for item in brief_data.get('timeline_reciente', [])[:5]:
        timeline_data.append([
            item.get('fecha', 'N/A'),
            item.get('quien', 'N/A'),
            item.get('que_paso', 'N/A')[:80] + "..." if len(item.get('que_paso', '')) > 80 else item.get('que_paso', 'N/A')
        ])
    
    timeline_table = Table(timeline_data, colWidths=[0.8*inch, 0.8*inch, 4.9*inch])
    timeline_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004e98')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(timeline_table)
    
    # === FOOTER ===
    elements.append(Spacer(1, 30))
    footer_text = Paragraph(
        "<i>Generado por Wealth Solutions Advisor | Documento confidencial</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    )
    elements.append(footer_text)
    
    # Construir el PDF
    doc.build(elements)
    
    return output_path

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Wealth Solutions Advisor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PREMIUM WEALTH MANAGEMENT ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
    
    /* === 1. RESET Y BASE === */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #fafbfc;
    }
    
    /* Títulos con fuente serif elegante */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: #1a1d29;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    h1 { font-size: 42px; line-height: 1.2; }
    h2 { font-size: 32px; line-height: 1.3; }
    h3 { font-size: 24px; line-height: 1.4; }
    
    p, label, .stMarkdown {
        color: #4a5568;
        font-weight: 400;
        line-height: 1.7;
    }
    
    /* === 2. SIDEBAR ELEGANTE Y MINIMALISTA === */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1a1d29;
        font-weight: 600;
    }
    
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p {
        color: #4a5568;
        font-size: 14px;
    }
    
    /* Radio buttons del sidebar - vertical y elegante */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        background-color: transparent;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px 16px;
        color: #4a5568;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #edf2f7;
        border-color: #cbd5e0;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background: #1a1d29;
        border-color: #1a1d29;
        color: white;
    }
    
    /* === 3. NAVEGACIÓN PRINCIPAL (TABS HORIZONTALES) === */
    section[data-testid="stMain"] div[role="radiogroup"] {
        background: white;
        border: 1px solid #e2e8f0;
        padding: 4px;
        border-radius: 8px;
        display: flex;
        gap: 4px;
    }
    
    section[data-testid="stMain"] div[role="radiogroup"] label {
        flex: 1;
        text-align: center;
        background: transparent;
        border: none;
        padding: 10px 16px;
        border-radius: 6px;
        color: #4a5568;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    
    section[data-testid="stMain"] div[role="radiogroup"] label:hover {
        background: #f7fafc;
        color: #1a1d29;
    }
    
    section[data-testid="stMain"] div[role="radiogroup"] label[data-checked="true"] {
        background: #1a1d29;
        color: white;
        font-weight: 600;
    }
    
    /* === 4. BOTONES PREMIUM === */
    .stButton>button {
        background: #1a1d29;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        box-shadow: none;
    }
    
    .stButton>button:hover {
        background: #2d3748;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26, 29, 41, 0.15);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Botón primario */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #1a1d29 0%, #2d3748 100%);
    }
    
    /* Botón secundario */
    .stButton>button[kind="secondary"] {
        background: white;
        color: #1a1d29;
        border: 1px solid #e2e8f0;
    }
    
    .stButton>button[kind="secondary"]:hover {
        background: #f7fafc;
        border-color: #cbd5e0;
    }
    
    /* === 5. INPUTS Y SELECTBOXES === */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>div {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 14px;
        background: white;
        transition: all 0.2s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus {
        border-color: #1a1d29;
        box-shadow: 0 0 0 3px rgba(26, 29, 41, 0.1);
    }
    
    /* === 6. CARDS Y CONTENEDORES === */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: #cbd5e0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    }
    
    /* === 7. EXPANDERS (EMAILS) === */
    .streamlit-expanderHeader {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 14px 18px;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: #f7fafc;
        border-color: #cbd5e0;
    }
    
    /* === 8. MÉTRICAS DE STREAMLIT === */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
        color: #1a1d29;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 13px;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    
    /* === 9. TOOLTIPS === */
    [data-tooltip] {
        position: relative;
        cursor: help;
    }
    
    [data-tooltip]:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #1a1d29;
        color: white;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 12px;
        white-space: nowrap;
        z-index: 1000;
        margin-bottom: 8px;
    }
    
    /* === 10. ANIMACIONES SUTILES === */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stMarkdown > div {
        animation: fadeIn 0.4s ease-out;
    }
    
    /* === 11. SCROLLBAR PERSONALIZADA === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f7fafc;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e0;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a0aec0;
    }
    
    /* === 12. DOWNLOAD BUTTON === */
    .stDownloadButton>button {
        background: #1a1d29;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        width: 100%;
    }
    
    .stDownloadButton>button:hover {
        background: #2d3748;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# --- CREDENCIALES ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_KEY"]
except Exception:
    st.error("⚠️ Error: No se encontró OPENAI_KEY en secrets.toml")
    st.stop()

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = "http://localhost:8501"
HISTORY_FILE = "client_history.json" # Archivo donde guardaremos los emails

# --- GESTIÓN DE HISTORIAL (NUEVO) ---
def load_history():
    """Carga la lista de clientes previos"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_to_history(email):
    """Guarda un nuevo email en el historial sin duplicados"""
    history = load_history()
    if email not in history:
        history.insert(0, email) # Añadir al principio
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)

# --- FUNCIONES AUTH ---
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

# --- MOTOR GMAIL ---
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
                if body: break
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    return body

def get_emails(creds, target_email, num_emails=None, fecha_desde=None, fecha_hasta=None):
    """
    Obtiene y procesa emails de Gmail con manejo robusto de errores.
    
    Args:
        creds: Credenciales de Google OAuth
        target_email: Email del cliente a buscar
        num_emails: Número de emails a obtener (modo cantidad)
        fecha_desde: Fecha inicio (modo rango)
        fecha_hasta: Fecha fin (modo rango)
    
    Returns:
        tuple: (texto_completo, lista_evidencia, mensaje_error)
    """
    
    # === VALIDACIONES PREVIAS ===
    if not creds:
        return None, None, "❌ Credenciales no válidas. Por favor, vuelve a iniciar sesión."
    
    if not target_email or '@' not in target_email:
        return None, None, "❌ El email del cliente no es válido."
    
    # === LÍMITES DE SEGURIDAD ===
    MAX_EMAILS_ALLOWED = 500  # Límite absoluto
    MAX_CHARS_TOTAL = 100000  # Límite de caracteres para IA
    
    try:
        # Construcción del servicio con timeout
        service = build('gmail', 'v1', credentials=creds)
        
        # === CONSTRUIR QUERY ===
        query = f"from:{target_email} OR to:{target_email}"
        
        # Determinar modo y ajustar query
        if fecha_desde and fecha_hasta:
            # MODO FECHA
            try:
                fecha_desde_str = fecha_desde.strftime('%Y/%m/%d')
                fecha_hasta_str = fecha_hasta.strftime('%Y/%m/%d')
                query += f" after:{fecha_desde_str} before:{fecha_hasta_str}"
                max_results = MAX_EMAILS_ALLOWED
            except Exception as e:
                return None, None, f"❌ Error en el formato de fechas: {str(e)}"
        else:
            # MODO CANTIDAD
            if not num_emails:
                num_emails = 15  # Default seguro
            
            # Validar límite
            if num_emails > MAX_EMAILS_ALLOWED:
                return None, None, f"❌ El límite máximo es {MAX_EMAILS_ALLOWED} emails. Solicitaste {num_emails}."
            
            max_results = num_emails
        
        # === LLAMADA A GMAIL API ===
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
        except Exception as api_error:
            error_msg = str(api_error)
            
            # Errores comunes con mensajes amigables
            if "invalid_grant" in error_msg.lower():
                return None, None, "🔐 Tu sesión ha expirado. Por favor, cierra sesión y vuelve a autenticarte."
            elif "insufficient permission" in error_msg.lower():
                return None, None, "🔒 No tienes permisos suficientes en Gmail. Verifica tu configuración de OAuth."
            elif "quota" in error_msg.lower():
                return None, None, "⏳ Has alcanzado el límite de consultas de Gmail. Intenta de nuevo en unos minutos."
            else:
                return None, None, f"❌ Error al conectar con Gmail: {error_msg[:200]}"
        
        # === VERIFICAR RESULTADOS ===
        messages = results.get('messages', [])
        
        if not messages:
            if fecha_desde and fecha_hasta:
                return None, None, f"📭 No se encontraron emails entre el {fecha_desde.strftime('%d/%m/%Y')} y el {fecha_hasta.strftime('%d/%m/%Y')}."
            else:
                return None, None, f"📭 No se encontraron emails con {target_email}."
        
        # === PROCESAR EMAILS ===
        full_text = ""
        evidence = []
        current_chars = 0
        emails_procesados = 0
        emails_con_error = 0
        
        for idx, msg in enumerate(messages):
            # Límite de caracteres alcanzado
            if current_chars >= MAX_CHARS_TOTAL:
                break
            
            try:
                # Obtener detalles del email
                msg_detail = service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='full'
                ).execute()
                
                headers = msg_detail['payload']['headers']
                
                # Extraer metadata
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "Sin Asunto")
                date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), "")
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "")
                
                # Parsear fecha
                try:
                    date_obj = parsedate_to_datetime(date_str)
                    date_formatted = date_obj.strftime('%Y-%m-%d %H:%M')
                    date_short = date_obj.strftime('%d %b')
                except:
                    date_formatted = date_str[:16] if date_str else "Fecha desconocida"
                    date_short = "N/A"
                
                # Determinar origen
                origin = "CLIENTE" if target_email.lower() in sender.lower() else "BANCO"
                
                # Extraer cuerpo
                body = parse_email_body(msg_detail['payload'])
                if not body:
                    body = msg_detail.get('snippet', '[Sin contenido]')
                
                # Limitar longitud del cuerpo
                body_cut = body[:3000]
                
                # Construir texto para IA
                email_text = f"\n--- EMAIL {idx+1} ---\nID: {msg['id']}\nFECHA: {date_formatted}\nORIGEN: {origin}\nASUNTO: {subject}\nCONTENIDO: {body_cut}\n"
                full_text += email_text
                current_chars += len(email_text)
                
                # Guardar evidencia
                evidence.append({
                    "Nº": idx + 1,
                    "Id_Completo": msg['id'],
                    "Id": msg['id'][:8],
                    "Fecha": date_formatted,
                    "Fecha_Corta": date_short,
                    "Origen": origin,
                    "Asunto": subject[:60] + "..." if len(subject) > 60 else subject,
                    "Asunto_Completo": subject,
                    "Cuerpo": body
                })
                
                emails_procesados += 1
                
            except Exception as email_error:
                emails_con_error += 1
                # Continuar con el siguiente email en lugar de fallar
                continue
        
        # === VALIDAR RESULTADOS ===
        if not evidence:
            return None, None, "❌ No se pudieron procesar los emails. Puede que estén vacíos o corruptos."
        
        # Invertir para tener orden cronológico
        evidence.reverse()
        
        # Mensaje de advertencia si hubo errores parciales
        warning_msg = None
        if emails_con_error > 0:
            warning_msg = f"⚠️ Se procesaron {emails_procesados} emails correctamente. {emails_con_error} tuvieron errores y se omitieron."
        
        return full_text, evidence, warning_msg
    
    except Exception as e:
        # CAPTURA DE ERRORES INESPERADOS
        import traceback
        error_detail = traceback.format_exc()
        
        return None, None, f"❌ Error técnico inesperado al obtener emails. Detalles: {str(e)[:300]}"

# --- IA ---
@st.cache_data(show_spinner=False, ttl=3600)
def analyze_with_ai(text_data, num_emails):
    """
    Analiza emails con OpenAI GPT-4 con manejo robusto de errores.
    
    Args:
        text_data: Texto concatenado de todos los emails
        num_emails: Cantidad de emails analizados
    
    Returns:
        tuple: (resultado_json, mensaje_error)
    """
    
    # === VALIDACIONES PREVIAS ===
    if not text_data or not text_data.strip():
        return None, "❌ No hay contenido de emails para analizar."
    
    if num_emails <= 0:
        return None, "❌ El número de emails debe ser mayor a 0."
    
    # Validar que la API key existe
    if not OPENAI_API_KEY or OPENAI_API_KEY == "":
        return None, "🔑 Falta configurar OPENAI_KEY en secrets.toml"
    
    # === LÍMITE DE TOKENS ===
    # GPT-4o tiene límite de contexto. Vamos a truncar si es necesario
    MAX_CHARS_FOR_AI = 80000  # Margen de seguridad
    
    if len(text_data) > MAX_CHARS_FOR_AI:
        text_data = text_data[:MAX_CHARS_FOR_AI]
        text_data += "\n\n[NOTA: Contenido truncado por límite de tokens]"
    
    # === CONSTRUCCIÓN DEL PROMPT ===
    prompt = f"""
    Actúa como un Senior Private Banker. Analiza el historial de {num_emails} correos.
    
    OBJETIVO 1: NARRATIVA. Genera un campo 'resumen_exhaustivo' (6-8 líneas) contando la historia de la conversación.
    OBJETIVO 2: SENTIMIENTO. Analiza CADA UNO de los {num_emails} correos y asigna un score (-10 a +10).
    
    JSON Estricto:
    {{
        "resumen_exhaustivo": "Texto narrativo...",
        "urgencia": "Alta|Media|Baja",
        "perfil_cliente": "Estado actual...",
        "accion_recomendada": "Acción comercial...",
        "borrador_respuesta": "Email...",
        "analisis_sentimiento": [
            {{ "email_num": 1, "sentimiento_score": 5, "explicacion": "..." }},
            ... (UN OBJETO POR CADA EMAIL) ...
            {{ "email_num": {num_emails}, "sentimiento_score": -2, "explicacion": "..." }}
        ],
        "insights_clave": ["Insight 1", "Insight 2"]
    }}
    """
    
    try:
        # === LLAMADA A OPENAI CON TIMEOUT ===
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=60.0  # Timeout de 60 segundos
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text_data}
            ],
            temperature=0.2,
            max_tokens=4000  # Límite explícito
        )
        
        # === PARSEAR RESPUESTA ===
        try:
            result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as json_err:
            return None, f"❌ La IA devolvió un formato inválido. Error: {str(json_err)}"
        
        # === VALIDAR ESTRUCTURA DEL JSON ===
        required_fields = [
            'resumen_exhaustivo',
            'urgencia',
            'perfil_cliente',
            'accion_recomendada',
            'borrador_respuesta',
            'analisis_sentimiento',
            'insights_clave'
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            # Si faltan campos críticos, crear valores por defecto
            if 'resumen_exhaustivo' not in result:
                result['resumen_exhaustivo'] = "⚠️ No se pudo generar el resumen completo."
            if 'urgencia' not in result:
                result['urgencia'] = "Media"
            if 'perfil_cliente' not in result:
                result['perfil_cliente'] = "Cliente con actividad reciente."
            if 'accion_recomendada' not in result:
                result['accion_recomendada'] = "Revisar la conversación y responder según contexto."
            if 'borrador_respuesta' not in result:
                result['borrador_respuesta'] = "Estimado/a cliente,\n\nGracias por tu mensaje. Estamos revisando tu solicitud.\n\nSaludos cordiales."
            if 'analisis_sentimiento' not in result:
                result['analisis_sentimiento'] = []
            if 'insights_clave' not in result:
                result['insights_clave'] = ["Revisar el historial de emails manualmente para más detalles."]
        
        # === VALIDAR ANÁLISIS DE SENTIMIENTO ===
        sentimientos = result.get('analisis_sentimiento', [])
        
        # Si la IA no generó sentimientos, crear estructura básica
        if not sentimientos or len(sentimientos) == 0:
            result['analisis_sentimiento'] = [
                {
                    "email_num": i + 1,
                    "sentimiento_score": 0,
                    "explicacion": "Análisis no disponible"
                }
                for i in range(num_emails)
            ]
        
        # Si hay menos sentimientos que emails, rellenar
        elif len(sentimientos) < num_emails:
            for i in range(len(sentimientos), num_emails):
                result['analisis_sentimiento'].append({
                    "email_num": i + 1,
                    "sentimiento_score": 0,
                    "explicacion": "Análisis no disponible"
                })
        
        # Validar que los scores estén en rango válido
        for sent in result['analisis_sentimiento']:
            score = sent.get('sentimiento_score', 0)
            if not isinstance(score, (int, float)) or score < -10 or score > 10:
                sent['sentimiento_score'] = 0
        
        return result, None
    
    except Exception as e:
        error_msg = str(e)
        
        # === MANEJO DE ERRORES ESPECÍFICOS ===
        if "rate_limit" in error_msg.lower():
            return None, "⏳ Has alcanzado el límite de consultas de OpenAI. Intenta de nuevo en unos minutos."
        
        elif "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return None, "🔑 La API Key de OpenAI no es válida. Verifica tu configuración en secrets.toml"
        
        elif "timeout" in error_msg.lower():
            return None, "⏱️ La consulta tardó demasiado. Intenta con menos emails o un período más corto."
        
        elif "context_length_exceeded" in error_msg.lower():
            return None, f"📏 El contenido es demasiado largo para procesar ({len(text_data)} caracteres). Reduce el número de emails."
        
        elif "insufficient_quota" in error_msg.lower():
            return None, "💳 Tu cuenta de OpenAI no tiene créditos suficientes. Recarga tu saldo."
        
        else:
            # Error genérico con detalles
            return None, f"❌ Error al comunicarse con OpenAI: {error_msg[:300]}"


def generate_fallback_analysis(evidence, target_email):
    """
    Genera un análisis básico local cuando OpenAI falla.
    Permite al usuario seguir trabajando con los emails.
    """
    num_emails = len(evidence)
    
    # Contar origen de emails
    from_client = sum(1 for e in evidence if e['Origen'] == 'CLIENTE')
    from_bank = num_emails - from_client
    
    # Detectar último origen
    last_origin = evidence[-1]['Origen'] if evidence else 'DESCONOCIDO'
    
    # Análisis básico sin IA
    return {
        'resumen_exhaustivo': f"Se analizaron {num_emails} emails con {target_email}. El cliente envió {from_client} mensajes y el banco {from_bank}. El último mensaje fue del {last_origin}. ⚠️ Análisis automático no disponible - revisa los emails manualmente.",
        'urgencia': 'Media',
        'perfil_cliente': f"Cliente con {num_emails} interacciones recientes. {'Espera respuesta del banco.' if last_origin == 'CLIENTE' else 'Última respuesta enviada por el banco.'}",
        'accion_recomendada': 'Revisar el historial de emails manualmente en el Explorador Avanzado.',
        'borrador_respuesta': f"Estimado/a cliente,\n\nHemos recibido tu mensaje y estamos revisando tu solicitud.\n\nTe responderemos a la brevedad.\n\nSaludos cordiales,\nEquipo de Banca Privada",
        'analisis_sentimiento': [
            {
                'email_num': i + 1,
                'sentimiento_score': 0,
                'explicacion': 'Análisis automático no disponible'
            }
            for i in range(num_emails)
        ],
        'insights_clave': [
            '⚠️ El análisis de IA no está disponible temporalmente',
            f'Total de {num_emails} emails en la conversación',
            'Revisa los emails manualmente en la pestaña "Explorador Avanzado"'
        ]
    }

# --- NUEVAS FUNCIONES PARA ANÁLISIS DE HILOS (THREAD INTELLIGENCE) ---

def get_thread_content(creds, thread_id):
    """Obtiene el contenido completo de un hilo específico de Gmail"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        # Traemos el hilo completo
        thread = service.users().threads().get(userId='me', id=thread_id, format='full').execute()
        messages = thread.get('messages', [])
        
        full_thread_text = ""
        
        for msg in messages:
            # Extraer fecha
            headers = msg['payload']['headers']
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), "N/A")
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Desconocido")
            
            # Extraer cuerpo (reutilizando tu parser existente)
            body = parse_email_body(msg['payload'])
            if not body: body = msg.get('snippet', '')
            
            full_thread_text += f"\n--- MENSAJE DEL {date} ---\nDE: {sender}\nCONTENIDO:\n{body[:2000]}\n"
            
        return full_thread_text
    except Exception as e:
        return None

@st.cache_data(show_spinner=False, ttl=3600)
def analyze_thread_structure(thread_text):
    """Genera el Timeline Visual y el Análisis Ejecutivo Profundo"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # PROMPT DE ALTO NIVEL (SENIOR ANALYST ROLE)
    prompt = """
    Actúa como un Analista Senior de Información y UX Writer especializado en gestión ejecutiva.
    Analiza el siguiente hilo de correos completo como una conversación única y orgánica.
    
    OBJETIVO:
    Transformar el hilo en un informe de inteligencia visual. No quiero un resumen lineal.
    Debes identificar intenciones ocultas, fricciones, quién impulsa y quién bloquea.
    
    INPUT: Texto completo del hilo de correos.
    
    OUTPUT: Genera una respuesta EXCLUSIVAMENTE en formato Markdown siguiendo esta estructura estricta:
    
    ### 🧭 Timeline del Hilo
    (Genera una lista de hitos. Usa fechas aproximadas si no son exactas. NO resumas cada mail, solo hitos clave).
    
    * 🔵 **[DD/MM] – [Fase: Inicio / Seguimiento / Bloqueo / Escalado / Resolución]**
        * **Actor:** [Nombre de la persona principal]
        * **Hecho clave:** [Acción concisa. Ej: Solicita confirmación jurídica]
        * **Impacto:** [Consecuencia real. Ej: El proceso depende ahora de un tercero]
    
    (Repite el bloque anterior para cada hito relevante del hilo)
    
    ---
    
    ### 📌 Estado Actual
    * **Estado:** [PENDIENTE | BLOQUEADO | CERRADO] (Elige uno con criterio estricto)
    * **Atasco:** [Explica brevemente dónde está el cuello de botella real o la pelota]
    * **Responsable actual:** [Nombre de la persona que debe mover ficha ahora]
    
    ### 🧠 Conclusión Ejecutiva
    [Párrafo de 3-4 líneas. Demuestra comprensión profunda. ¿Es un problema operativo, de decisión o de falta de información? ¿Qué riesgo hay si no se avanza? Ve más allá de lo evidente.]
    
    ### ▶️ Próximos Pasos
    * 1. **Acción:** [Acción concreta] | **Responsable:** [Nombre] | **Objetivo:** [Para qué]
    (Añade más si son necesarios)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": prompt}, 
                {"role": "user", "content": thread_text}
            ],
            temperature=0.1 # Temperatura baja para máxima precisión y respeto al formato
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar inteligencia: {str(e)}"
@st.cache_data(show_spinner=False, ttl=1800)
def generate_meeting_brief(text_data, num_emails, target_email):
    """Genera un Pre-Meeting Brief ejecutivo"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    Actúa como un Asistente Ejecutivo Senior de Banca Privada.
    
    El RM tiene una reunión próximamente con el cliente {target_email}.
    Has analizado los últimos {num_emails} emails.
    
    Genera un PRE-MEETING BRIEF que se pueda leer en 60 segundos.
    
    Devuelve un JSON con esta estructura EXACTA:
    
    {{
        "contexto_rapido": "2-3 líneas explicando el estado actual de la relación y el mood del cliente",
        "temas_reunion": [
            {{
                "prioridad": "URGENTE|IMPORTANTE|INFORMATIVO",
                "tema": "Título del tema",
                "detalle": "Qué discutir o confirmar",
                "contexto": "Por qué es relevante ahora"
            }}
        ],
        "pendientes_cliente": [
            "Acción 1 que el cliente debe hacer/enviar",
            "Acción 2 pendiente del cliente"
        ],
        "pendientes_banco": [
            "Acción 1 que tú/el banco debe hacer",
            "Acción 2 pendiente de tu lado"
        ],
        "talking_points": [
            "Frase exacta para abrir tema 1",
            "Frase exacta para abrir tema 2"
        ],
        "timeline_reciente": [
            {{
                "fecha": "DD/MM",
                "quien": "CLIENTE|BANCO",
                "que_paso": "Descripción breve de la acción"
            }}
        ],
        "documentos_mencionar": [
            "Nombre de documento o email que debes referenciar en la reunión"
        ]
    }}
    
    IMPORTANTE:
    - temas_reunion: Máximo 5, ordenados por prioridad
    - timeline_reciente: Solo los últimos 5 hitos relevantes
    - talking_points: Frases naturales y profesionales
    - Sé específico, no genérico
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text_data}
            ],
            temperature=0.3
        )
        result = json.loads(response.choices[0].message.content)
        return result, None
    except Exception as e:
        return None, f"Error al generar brief: {str(e)}"
# =============================================================================
# SISTEMA DE AUTENTICACIÓN
# =============================================================================

def check_password():
    """Verifica que el usuario tenga la contraseña correcta."""
    
    def password_entered():
        """Comprueba si la contraseña es correcta."""
        if hmac.compare_digest(st.session_state["password"], st.secrets.get("app_password", "WealthSolutions2026")):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Si ya está autenticado, permitir acceso
    if st.session_state.get("password_correct", False):
        return True

    # Pantalla de login
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
<div style='text-align: center; background: white; padding: 60px 40px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 20px rgba(0,0,0,0.08);'>
    <div style='width: 64px; height: 64px; background: #1a1d29; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 24px;'>🏦</div>
    <h1 style='color: #1a1d29; font-size: 32px; margin-bottom: 12px;'>Wealth Solutions Advisor</h1>
    <p style='color: #718096; font-size: 15px; margin-bottom: 32px;'>Acceso restringido • Solo personal autorizado</p>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.text_input(
            "🔐 Contraseña de acceso",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Introduce la contraseña del equipo"
        )
        
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Contraseña incorrecta. Contacta al administrador si olvidaste la contraseña.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔒 Conexión segura • Datos encriptados")
    
    return False

# Verificar autenticación ANTES de mostrar la app
if not check_password():
    st.stop()

# --- UI PRINCIPAL ---
if 'creds' not in st.session_state: st.session_state.creds = None
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None

if 'code' in st.query_params and st.session_state.creds is None:
    st.session_state.creds = exchange_code(st.query_params['code'])
    st.query_params.clear()
    st.rerun()

# Validar que las credenciales sigan siendo válidas
if st.session_state.creds:
    try:
        # Intentar construir el servicio para verificar credenciales
        from googleapiclient.discovery import build
        test_service = build('gmail', 'v1', credentials=st.session_state.creds)
        # Si llegamos aquí, las credenciales son válidas
    except Exception as e:
        # Credenciales inválidas o expiradas
        if "invalid_grant" in str(e).lower() or "invalid_client" in str(e).lower():
            st.session_state.creds = None
            st.warning("🔐 Tu sesión ha expirado. Por favor, vuelve a iniciar sesión.")
            st.rerun()

# 1. PANTALLA LOGIN
if not st.session_state.creds:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div style='text-align: center; background: white; padding: 60px 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.12);'>
            <div style='font-size: 60px; margin-bottom: 20px;'>🏦</div>
            <h1 style='color: #004e98; font-size: 48px;'>Wealth Solutions Advisor</h1>
            <p style='color: #5a6c7d; font-size: 18px;'>Sistema de inteligencia avanzada para llevar el mejor seguimiento posible</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        _, auth_url = authorize_google()
        if auth_url: st.link_button("🔐 Iniciar Sesión Corporativa", auth_url, type="primary", use_container_width=True)
        else: st.error("Falta client_secret.json")

else:
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 30px 0;'>
            <div style='font-size: 48px; margin-bottom: 10px;'>👤</div>
            <h2 style='color: white; margin: 0; font-size: 24px;'>RM Panel</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # --- CARTERA DE CLIENTES (NUEVO) ---
        st.markdown("### 📇 Cartera de Clientes")
        client_history = load_history()
        
        selected_client = st.selectbox(
            "Seleccionar cliente reciente:",
            ["Nuevo Búsqueda"] + client_history,
            index=0
        )
        
        # Si selecciona un cliente del historial, lo ponemos en el estado para que rellene el input
        if selected_client != "Nuevo Búsqueda":
            st.session_state.default_email = selected_client
        else:
            st.session_state.default_email = ""
            
        st.markdown("---")
        
        # --- MODO DE ANÁLISIS (NUEVO) ---
        st.markdown("### ⚙️ Configuración de Análisis")
        
        analysis_mode = st.radio(
            "Modo de búsqueda:",
            ["📊 Por número de emails", "📅 Por rango de fechas"],
            index=0,
            key="analysis_mode"
        )
        
        if analysis_mode == "📊 Por número de emails":
            email_count = st.slider(
                "Número de emails",
                min_value=5,
                max_value=100,
                value=15,
                step=5,
                help="Últimos N emails del cliente"
            )
            # Resetear fechas
            st.session_state.fecha_desde = None
            st.session_state.fecha_hasta = None
        else:
            # --- LÓGICA INTELIGENTE DE FECHAS (CALLBACKS) ---
            
            # 1. Función que se ejecuta al cambiar el DESPLEGABLE
            def update_dates_from_selector():
                seleccion = st.session_state.quick_period
                hoy = datetime.now().date()
                
                if seleccion == "Personalizado":
                    return 
                
                nuevo_desde = hoy
                nuevo_hasta = hoy
                
                if seleccion == "Últimos 7 días":
                    nuevo_desde = hoy - timedelta(days=7)
                elif seleccion == "Últimos 15 días":
                    nuevo_desde = hoy - timedelta(days=15)
                elif seleccion == "Últimos 30 días":
                    nuevo_desde = hoy - timedelta(days=30)
                elif seleccion == "Último mes completo":
                    first_last_month = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
                    last_last_month = hoy.replace(day=1) - timedelta(days=1)
                    nuevo_desde = first_last_month
                    nuevo_hasta = last_last_month
                elif seleccion == "Último trimestre":
                    nuevo_desde = hoy - timedelta(days=90)
                elif seleccion == "Últimos 6 meses":
                    nuevo_desde = hoy - timedelta(days=180)
                elif seleccion == "Este año":
                    nuevo_desde = hoy.replace(month=1, day=1)
                
                # Actualizamos las fechas en el estado
                st.session_state.fecha_desde_sidebar = nuevo_desde
                st.session_state.fecha_hasta_sidebar = nuevo_hasta

            # 2. Función que se ejecuta al tocar las FECHAS manualmente
            def set_custom_mode():
                st.session_state.quick_period = "Personalizado"

            # --- INTERFAZ ---
            st.markdown("**⚡ Períodos rápidos:**")
            
            # Definimos las opciones en una lista
            opciones_periodo = [
                "Personalizado",
                "Últimos 7 días",
                "Últimos 15 días", 
                "Últimos 30 días",
                "Último mes completo",
                "Último trimestre",
                "Últimos 6 meses",
                "Este año"
            ]
            
            # Inicializamos el valor en memoria si no existe
            if "quick_period" not in st.session_state:
                st.session_state.quick_period = "Últimos 7 días"

            # Creamos el widget SIN el parámetro 'index'
            quick_options = st.selectbox(
                "Selecciona un período predefinido:",
                opciones_periodo,
                key="quick_period",
                on_change=update_dates_from_selector
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**📅 Ajusta las fechas:**")
            
            # Inicializar fechas por defecto si no existen en el estado
            if "fecha_desde_sidebar" not in st.session_state:
                st.session_state.fecha_desde_sidebar = datetime.now().date() - timedelta(days=7)
            if "fecha_hasta_sidebar" not in st.session_state:
                st.session_state.fecha_hasta_sidebar = datetime.now().date()

            today = datetime.now().date()

            fecha_desde = st.date_input(
                "Desde",
                max_value=today,
                key="fecha_desde_sidebar",
                format="DD/MM/YYYY",
                on_change=set_custom_mode
            )
            
            fecha_hasta = st.date_input(
                "Hasta", 
                min_value=fecha_desde,
                max_value=today,
                key="fecha_hasta_sidebar",
                format="DD/MM/YYYY",
                on_change=set_custom_mode
            )
            
            # Guardar en variables generales para el resto del código
            st.session_state.fecha_desde = fecha_desde
            st.session_state.fecha_hasta = fecha_hasta
            
            # Mostrar resumen visual
            days_selected = (fecha_hasta - fecha_desde).days + 1
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 4px solid #4CAF50;'>
                <p style='margin: 0; font-size: 13px; color: white;'>
                    📊 <strong>Período seleccionado:</strong><br>
                    Del <strong>{fecha_desde.strftime('%d/%m/%Y')}</strong><br>
                    al <strong>{fecha_hasta.strftime('%d/%m/%Y')}</strong>
                </p>
                <p style='margin: 5px 0 0 0; font-size: 12px; color: #b0bec5;'>
                    ⏱️ {days_selected} {'día' if days_selected == 1 else 'días'} de análisis
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            email_count = None
        
        st.markdown("---")
        st.success("✓ Gmail Conectado")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.creds = None
            st.session_state.analysis_results = None
            st.rerun()
    
    st.markdown("""
<div style='background: white; border: 1px solid #e2e8f0; padding: 48px 40px; border-radius: 8px; margin-bottom: 32px;'>
    <div style='display: flex; align-items: center; gap: 16px; margin-bottom: 12px;'>
        <div style='width: 48px; height: 48px; background: #1a1d29; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px;'>🏦</div>
        <h1 style='margin: 0; color: #1a1d29; font-size: 38px; font-weight: 600;'>Wealth Solutions Advisor</h1>
    </div>
    <p style='color: #718096; margin: 0; font-size: 16px; font-weight: 400; padding-left: 64px;'>Análisis inteligente de relaciones con clientes de banca privada</p>
</div>
""", unsafe_allow_html=True)
    
    c_s, c_b = st.columns([4, 1])
    
    # Usamos el valor del historial si existe
    default_val = st.session_state.get("default_email", "")
    
    with c_s: 
        target_email = st.text_input(
            "Email del Cliente", 
            value=default_val, 
            placeholder="cliente@empresa.com", 
            label_visibility="collapsed"
        )
        
    with c_b: 
        col_btn_a, col_btn_b = st.columns(2)
        with col_btn_a:
            run_btn = st.button("🚀 Analizar", type="primary", use_container_width=True)
        with col_btn_b:
            brief_btn = st.button("📄 Brief", use_container_width=True, help="Generar Pre-Meeting Brief")
    
    if run_btn and target_email:
        # === VALIDACIÓN MEJORADA ===
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not target_email.strip():
            st.error("⚠️ Por favor introduce un email")
            st.stop()
        
        if not re.match(email_pattern, target_email.strip()):
            show_warning_box(
                "Formato de email inválido",
                "El email debe tener el formato: <code>usuario@dominio.com</code><br>📝 Ejemplo válido: <strong>cliente@empresa.com</strong>"
            )
            st.stop()
        
        # Limpiar y normalizar
        target_email = target_email.strip().lower()
        
        # GUARDAR EN HISTORIAL
        save_to_history(target_email)
        
        # === INICIO DEL ANÁLISIS CON FEEDBACK MEJORADO ===
        with st.spinner("🔄 Conectando con Gmail..."):
            # Determinar parámetros según modo de análisis
            mode = st.session_state.get('analysis_mode', '📊 Por número de emails')
            
            # Mostrar un placeholder con info contextual
            info_placeholder = st.empty()
            
            try:
                if mode == "📊 Por número de emails":
                    with info_placeholder.container():
                        st.markdown(f"""
<div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #2196f3; text-align: center;'>
    <div style='font-size: 32px; margin-bottom: 10px;'>📥</div>
    <h4 style='color: #0d47a1; margin: 0 0 8px 0;'>Obteniendo emails de Gmail</h4>
    <p style='color: #1565c0; margin: 0; font-size: 14px;'>
        Buscando los últimos <strong>{email_count}</strong> emails de <strong>{target_email}</strong>
    </p>
</div>
""", unsafe_allow_html=True)
                    
                    raw, ev, err = get_emails(
                        st.session_state.creds, 
                        target_email, 
                        num_emails=email_count
                    )
                else:
                    fecha_desde = st.session_state.get('fecha_desde')
                    fecha_hasta = st.session_state.get('fecha_hasta')
                    
                    if not fecha_desde or not fecha_hasta:
                        info_placeholder.empty()
                        st.error("⚠️ Debes seleccionar un rango de fechas válido")
                        st.stop()
                    
                    with info_placeholder.container():
                        st.markdown(f"""
<div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #2196f3; text-align: center;'>
    <div style='font-size: 32px; margin-bottom: 10px;'>📅</div>
    <h4 style='color: #0d47a1; margin: 0 0 8px 0;'>Buscando en rango de fechas</h4>
    <p style='color: #1565c0; margin: 0; font-size: 14px;'>
        Del <strong>{fecha_desde.strftime('%d/%m/%Y')}</strong> al <strong>{fecha_hasta.strftime('%d/%m/%Y')}</strong>
    </p>
</div>
""", unsafe_allow_html=True)
                    
                    raw, ev, err = get_emails(
                        st.session_state.creds, 
                        target_email, 
                        fecha_desde=fecha_desde,
                        fecha_hasta=fecha_hasta
                    )
                
                info_placeholder.empty()
                
                # === MANEJO DE ERRORES GMAIL ===
                if err:
                    show_error_box(
                        "Error al obtener emails",
                        err,
                        suggestions=[
                            "Verifica que el email esté bien escrito",
                            "Asegúrate de tener permisos en Gmail",
                            "Si el problema persiste, cierra sesión y vuelve a autenticarte"
                        ]
                    )
                    st.stop()
                
                # === SI NO HAY EMAILS ===
                if not raw or not ev:
                    show_empty_state(
                        "📭",
                        "No se encontraron emails",
                        f"No hay conversaciones con <strong>{target_email}</strong> en el período seleccionado",
                        suggestions=[
                            "Verifica que el email sea correcto",
                            "Amplía el rango de fechas",
                            'Prueba con "Por número de emails" en el sidebar'
                        ]
                    )
                    st.stop()
                
                # === ANÁLISIS CON IA ===
                with info_placeholder.container():
                    st.markdown(f"""
<div style='background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #7b1fa2; text-align: center;'>
    <div style='font-size: 32px; margin-bottom: 10px;'>🤖</div>
    <h4 style='color: #4a148c; margin: 0 0 8px 0;'>Analizando con Inteligencia Artificial</h4>
    <p style='color: #6a1b9a; margin: 0; font-size: 14px;'>
        Procesando <strong>{len(ev)} emails</strong> con GPT-4o...<br>
        <em style='font-size: 12px; opacity: 0.8;'>Esto puede tardar 10-15 segundos</em>
    </p>
</div>
""", unsafe_allow_html=True)
                
                an, ai_err = analyze_with_ai(raw, len(ev))
                
                info_placeholder.empty()
                
                if ai_err:
                    # === ACTIVAR MODO FALLBACK ===
                    st.warning("⚠️ El análisis de IA no está disponible. Generando vista básica...")
                    an = generate_fallback_analysis(ev, target_email)
                    
                    show_warning_box(
                        "Modo Básico Activado",
                        f"<strong>Motivo:</strong> {ai_err}",
                        tips=[
                            f"Los {len(ev)} emails se cargaron correctamente",
                            'Usa el "Explorador Avanzado" para revisarlos manualmente',
                            "El análisis de sentimiento se generará cuando OpenAI esté disponible"
                        ]
                    )
                
                # === ÉXITO ===
                st.session_state.analysis_results = {
                    'analysis': an, 
                    'evidence': ev, 
                    'target_email': target_email,
                    'analysis_mode': mode,
                    'email_count': email_count if mode == "📊 Por número de emails" else None,
                    'fecha_desde': fecha_desde if mode == "📅 Por rango de fechas" else None,
                    'fecha_hasta': fecha_hasta if mode == "📅 Por rango de fechas" else None
                }
                
                show_success_box(
                    "Análisis completado correctamente",
                    "Los resultados ya están disponibles más abajo"
                )
                
            except Exception as e:
                # CAPTURA DE ERRORES INESPERADOS
                show_error_box(
                    "Error técnico inesperado",
                    "Ha ocurrido un error que no pudimos anticipar. Por favor, contacta a soporte.",
                    details=str(e)
                )
                st.stop()
                st.stop()
    # Manejar click en botón Brief
    if brief_btn and target_email:
        if '@' not in target_email:
            st.error("⚠️ Email inválido")
        else:
            # Si ya hay un análisis previo, usarlo; si no, hacer análisis rápido
            if st.session_state.analysis_results and st.session_state.analysis_results.get('target_email') == target_email:
                # Usar análisis existente
                evidence = st.session_state.analysis_results['evidence']
                raw_text = "\n".join([
                    f"EMAIL {e['Nº']}: {e['Fecha']} | {e['Origen']} | {e['Asunto_Completo']} | {e['Cuerpo'][:500]}"
                    for e in evidence
                ])
            else:
                # Hacer análisis rápido (últimos 15 emails)
                with st.spinner("📥 Obteniendo emails..."):
                    raw_text, evidence, err = get_emails(st.session_state.creds, target_email, num_emails=15)
                    
                    if err:
                        show_error_box(
                            "Error al obtener emails",
                            err,
                            suggestions=[
                                "Verifica que el email esté bien escrito",
                                "Asegúrate de tener permisos en Gmail"
                            ]
                        )
                        st.stop()
                    
                    if not raw_text or not evidence:
                        show_empty_state(
                            "📭",
                            "No se encontraron emails",
                            f"No hay conversaciones con <strong>{target_email}</strong>",
                            suggestions=["Verifica que el email sea correcto"]
                        )
                        st.stop()
            
            # Generar el brief
            with st.spinner("📄 Generando Pre-Meeting Brief con IA..."):
                brief_data, brief_err = generate_meeting_brief(raw_text, len(evidence), target_email)
                
                if brief_err:
                    show_error_box(
                        "Error al generar el brief",
                        brief_err,
                        suggestions=[
                            "Verifica tu conexión con OpenAI",
                            "Intenta con menos emails"
                        ]
                    )
                    st.stop()
            
            # === GENERAR PDF DIRECTAMENTE ===
            try:
                import tempfile
                import os
                
                with st.spinner("🖨️ Generando PDF del Brief..."):
                    # Usar directorio temporal del sistema
                    temp_dir = tempfile.gettempdir()
                    pdf_filename = f"brief_{target_email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    pdf_path = os.path.join(temp_dir, pdf_filename)
                    
                    generate_brief_pdf(brief_data, target_email, pdf_path)
                    
                    # Leer el archivo para descarga
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                    
                    # Limpiar archivo temporal
                    try:
                        os.remove(pdf_path)
                    except:
                        pass
                
                # === MOSTRAR RESULTADO COMPACTO ===
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_result1, col_result2, col_result3 = st.columns([1, 2, 1])
                
                with col_result2:
                    st.markdown("""
<div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 40px; border-radius: 15px; text-align: center; box-shadow: 0 8px 24px rgba(46,125,50,0.15);'>
    <div style='font-size: 72px; margin-bottom: 20px;'>✅</div>
    <h2 style='color: #1b5e20; margin: 0 0 12px 0;'>Brief Generado</h2>
    <p style='color: #2e7d32; margin: 0; font-size: 16px;'>
        Tu Pre-Meeting Brief está listo
    </p>
</div>
""", unsafe_allow_html=True)
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    st.download_button(
                        label="⬇️ Descargar Brief en PDF",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
            
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                
                show_error_box(
                    "Error al generar el PDF",
                    f"No se pudo crear el documento: {str(e)}",
                    details=error_details,
                    suggestions=[
                        "Verifica que reportlab esté instalado",
                        "Reinicia Streamlit",
                        "Intenta de nuevo"
                    ]
                )
    if st.session_state.analysis_results:
        data = st.session_state.analysis_results['analysis']
        evidence = st.session_state.analysis_results['evidence']
        
        # === BADGE DE RESUMEN EJECUTIVO ===
        mode_used = st.session_state.analysis_results.get('analysis_mode', 'N/A')
        urgencia = data.get('urgencia', 'Media')
        
        # Determinar texto del periodo
        if mode_used == "📊 Por número de emails":
            count_used = st.session_state.analysis_results.get('email_count', len(evidence))
            periodo_text = f"Últimos {count_used} emails"
        else:
            fecha_desde = st.session_state.analysis_results.get('fecha_desde')
            fecha_hasta = st.session_state.analysis_results.get('fecha_hasta')
            if fecha_desde and fecha_hasta:
                periodo_text = f"Del {fecha_desde.strftime('%d/%m')} al {fecha_hasta.strftime('%d/%m')}"
            else:
                periodo_text = "Período personalizado"
        
        # Determinar color según urgencia (colores sutiles)
        if urgencia == 'Alta':
            badge_color = "#742a2a"
            badge_bg = "#fff5f5"
            badge_border = "#feb2b2"
        elif urgencia == 'Baja':
            badge_color = "#22543d"
            badge_bg = "#f0fff4"
            badge_border = "#9ae6b4"
        else:
            badge_color = "#744210"
            badge_bg = "#fffbeb"
            badge_border = "#fbd38d"
        
        st.markdown(f"""
<div style='background: white; border: 1px solid #e2e8f0; padding: 20px 28px; border-radius: 8px; margin-bottom: 24px;'>
    <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;'>
        <div style='display: flex; align-items: center; gap: 20px;'>
            <div style='background: {badge_bg}; color: {badge_color}; padding: 6px 14px; border-radius: 4px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid {badge_border};'>
                {urgencia}
            </div>
            <div style='color: #4a5568; font-size: 14px; font-weight: 500;'>
                <span style='color: #1a1d29; font-weight: 600;'>{len(evidence)}</span> emails
                <span style='margin: 0 8px; color: #cbd5e0;'>·</span>
                {periodo_text}
            </div>
        </div>
        <div style='color: #718096; font-size: 13px; font-weight: 500;'>
            📧 {st.session_state.analysis_results.get('target_email', '')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
        
        # HISTORIA
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📖 Historia de la Conversación")
        # --- NUEVO: INDICADOR DE ESTADO (CORREGIDO) ---
        # Cogemos el último elemento de la lista [-1] porque es el más reciente
        last_email = evidence[-1] 
        
        # Lógica de estado
        if last_email['Origen'] == 'CLIENTE':
            estado_texto = "⚠️ EL CLIENTE ESPERA RESPUESTA"
            estado_sub = "Último mensaje recibido del cliente:"
            estado_color = "#ffebee" # Rojo muy suave
            borde_color = "#ef5350"  # Rojo alerta
            icono = "⏳"
        else:
            estado_texto = "✅ AL DÍA: TÚ ENVIASTE EL ÚLTIMO MENSAJE"
            estado_sub = "Tu última respuesta enviada:"
            estado_color = "#e8f5e9" # Verde muy suave
            borde_color = "#66bb6a"  # Verde éxito
            icono = "👍"

        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, {estado_color} 0%, white 100%);
            padding: 25px 30px; 
            border-radius: 15px; 
            border: 3px solid {borde_color};
            margin-bottom: 30px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            position: relative;
        '>
            <div style='display: flex; align-items: center; margin-bottom: 10px;'>
                <span style='font-size: 24px; margin-right: 15px;'>{icono}</span>
                <h3 style='margin: 0; color: {borde_color}; font-size: 18px; font-weight: 700;'>{estado_texto}</h3>
            </div>
            <div style='margin-left: 40px; color: #546e7a;'>
                <p style='margin: 0 0 5px 0; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>{estado_sub}</p>
                <p style='margin: 0; font-size: 16px; font-style: italic; color: #37474f;'>"{last_email['Asunto_Completo']}"</p>
                <div style='display: flex; align-items: center; margin-top: 8px;'>
                    <span style='font-size: 14px; margin-right: 5px;'>📅</span>
                    <span style='font-size: 14px; color: #78909c;'>{last_email['Fecha']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
<div style='background: white; border: 1px solid #e2e8f0; padding: 32px 36px; border-radius: 8px; margin-bottom: 32px;'>
    <p style='color: #2d3748; font-size: 17px; line-height: 1.9; margin: 0; font-weight: 400;'>
        {data.get('resumen_exhaustivo', 'Generando...')}
    </p>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)# === INDICADOR DE ESTADO ===
        last_email = evidence[-1]
        
        if last_email['Origen'] == 'CLIENTE':
            estado_icon = "⏳"
            estado_titulo = "Pendiente de respuesta"
            estado_desc = f"Último mensaje del cliente: {last_email['Fecha']}"
            estado_bg = "#fff5f5"
            estado_border = "#feb2b2"
            estado_color = "#742a2a"
        else:
            estado_icon = "✓"
            estado_titulo = "Al día"
            estado_desc = f"Tu última respuesta: {last_email['Fecha']}"
            estado_bg = "#f0fff4"
            estado_border = "#9ae6b4"
            estado_color = "#22543d"
        
        st.markdown(f"""
<div style='background: {estado_bg}; border: 1px solid {estado_border}; border-left: 4px solid {estado_border}; padding: 20px 24px; border-radius: 8px; margin-bottom: 32px;'>
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 8px;'>
        <span style='font-size: 20px;'>{estado_icon}</span>
        <h4 style='color: {estado_color}; margin: 0; font-size: 15px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>{estado_titulo}</h4>
    </div>
    <p style='color: {estado_color}; margin: 0; font-size: 14px; padding-left: 32px;'>{estado_desc}</p>
    <p style='color: {estado_color}; margin: 8px 0 0 32px; font-size: 13px; font-style: italic; opacity: 0.8;'>"{last_email['Asunto_Completo']}"</p>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # === KPIs EN CARDS PREMIUM ===
        st.markdown("""
<div style='margin-bottom: 32px;'>
    <h3 style='color: #1a1d29; font-size: 18px; margin-bottom: 20px; font-weight: 600;'>Métricas Clave</h3>
</div>
""", unsafe_allow_html=True)
        
        k1, k2, k3 = st.columns(3, gap="medium")
        
        with k1:
            urg = data.get('urgencia', 'N/A')
            if urg == "Alta":
                urg_color = "#742a2a"
                urg_bg = "#fff5f5"
                urg_icon = "⚠️"
            elif urg == "Baja":
                urg_color = "#22543d"
                urg_bg = "#f0fff4"
                urg_icon = "✓"
            else:
                urg_color = "#744210"
                urg_bg = "#fffbeb"
                urg_icon = "○"
            
            st.markdown(f"""
<div style='background: white; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; text-align: center;'>
    <div style='font-size: 32px; margin-bottom: 12px;'>{urg_icon}</div>
    <p style='color: #718096; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 8px 0; font-weight: 600;'>Urgencia</p>
    <p style='color: {urg_color}; font-size: 24px; font-weight: 700; margin: 0;'>{urg}</p>
</div>
""", unsafe_allow_html=True)
        
        with k2:
            st.markdown(f"""
<div style='background: white; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; text-align: center;'>
    <div style='font-size: 32px; margin-bottom: 12px;'>📧</div>
    <p style='color: #718096; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 8px 0; font-weight: 600;'>Total Emails</p>
    <p style='color: #1a1d29; font-size: 24px; font-weight: 700; margin: 0;'>{len(evidence)}</p>
</div>
""", unsafe_allow_html=True)
        
        with k3:
            scores = [x['sentimiento_score'] for x in data.get('analisis_sentimiento', [])]
            avg = round(sum(scores)/len(scores), 1) if scores else 0
            
            if avg >= 5:
                salud_color = "#22543d"
                salud_icon = "😊"
            elif avg >= 0:
                salud_color = "#744210"
                salud_icon = "😐"
            else:
                salud_color = "#742a2a"
                salud_icon = "😟"
            
            st.markdown(f"""
<div style='background: white; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; text-align: center;'>
    <div style='font-size: 32px; margin-bottom: 12px;'>{salud_icon}</div>
    <p style='color: #718096; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 8px 0; font-weight: 600;'>Salud Relación</p>
    <p style='color: {salud_color}; font-size: 24px; font-weight: 700; margin: 0;'>{avg}<span style='font-size: 16px; color: #718096;'>/10</span></p>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='border-top: 2px solid #e0e6ed; margin: 30px 0;'></div>
        """, unsafe_allow_html=True)
        
        # === GRÁFICO DE SENTIMIENTO ===
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
<div style='margin-bottom: 24px;'>
    <h3 style='color: #1a1d29; font-size: 18px; margin: 0; font-weight: 600;'>📈 Evolución del Sentimiento</h3>
    <p style='color: #718096; font-size: 14px; margin: 8px 0 0 0;'>Análisis cronológico de la relación</p>
</div>
""", unsafe_allow_html=True)
        sent_data = data.get('analisis_sentimiento', [])
        limit = min(len(sent_data), len(evidence))
        
        if limit > 0:
            df_chart = pd.DataFrame({
                'Fecha': [e['Fecha'] for e in evidence[:limit]],
                'Score': [s['sentimiento_score'] for s in sent_data[:limit]],
                'Asunto': [e['Asunto'] for e in evidence[:limit]],
                'Explicacion': [s.get('explicacion', '') for s in sent_data[:limit]],
                'Origen': [e['Origen'] for e in evidence[:limit]],
                'ID': [e['Id'] for e in evidence[:limit]] # Para referencia visual
            })
            
            # Crear figura
            fig = go.Figure()

            # 1. Zonas de fondo (Semáforo Visual)
            # Zona Éxito (Verde)
            fig.add_hrect(y0=5, y1=11, line_width=0, fillcolor="rgba(46, 204, 113, 0.1)", layer="below")
            # Zona Peligro (Rojo)
            fig.add_hrect(y0=-11, y1=-5, line_width=0, fillcolor="rgba(231, 76, 60, 0.1)", layer="below")

            # 2. Línea y Puntos
            fig.add_trace(go.Scatter(
                x=df_chart['Fecha'], 
                y=df_chart['Score'], 
                mode='lines+markers', 
                name='Sentimiento',
                # Línea curva suave y elegante
                line=dict(color='#1a2b4b', width=3, shape='spline', smoothing=1.3),
                # Marcadores dinámicos: Color según score, Tamaño según intensidad
                marker=dict(
                    size=[max(8, abs(s)*1.5) for s in df_chart['Score']], # Más grande si es más intenso
                    color=df_chart['Score'], 
                    colorscale='RdYlGn', # Rojo -> Amarillo -> Verde
                    line=dict(width=2, color='white'), 
                    showscale=False,
                    cmin=-10, cmax=10
                ),
                # Tooltip Informativo HTML
                customdata=df_chart[['Asunto', 'Explicacion', 'Origen', 'ID']],
                hovertemplate="""
                <b>%{customdata[2]}</b> (ID: %{customdata[3]})<br>
                📅 %{x}<br>
                ----------------<br>
                <b>%{customdata[0]}</b><br>
                <i>%{customdata[1]}</i><br>
                ----------------<br>
                🎯 Score: <b>%{y}</b>
                <extra></extra>
                """
            ))

            # 3. Línea Neutral
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="Neutral (0)", annotation_position="bottom right")
            
            # 4. Diseño Limpio
            fig.update_layout(
                height=500, 
                plot_bgcolor='rgba(255,255,255,0)', 
                paper_bgcolor='white', 
                yaxis=dict(
                    range=[-11, 11], 
                    title="Negativo ↔ Positivo", 
                    showgrid=True, 
                    gridcolor='rgba(0,0,0,0.05)'
                ),
                xaxis=dict(
                    showgrid=False
                ),
                hovermode='closest', # Importante para ver el punto exacto
                margin=dict(t=20, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Nota para el usuario sobre la interactividad
            st.caption("💡 *Nota: Los puntos más grandes indican emociones más intensas. El fondo verde indica zona de confort, el rojo zona de riesgo.*")
        
        # Separador antes de navegación
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='border-top: 2px solid #e0e6ed; margin: 20px 0 30px 0;'></div>
        """, unsafe_allow_html=True)
        
        # --- NAVEGACIÓN ROBUSTA (CONTROLADA POR ESTADO) ---
        # Usamos radio buttons horizontales que actúan como menú persistente
        
        # Opciones del menú
        NAV_ESTRATEGIA = "💡 Estrategia & Insights"
        NAV_GENERADOR = "✉️ Generador de Respuesta"
        NAV_EXPLORADOR = "📬 Explorador Avanzado"
        
        # Selector de vista
        selected_view = st.radio(
            "Navegación Principal",
            [NAV_ESTRATEGIA, NAV_GENERADOR, NAV_EXPLORADOR],
            horizontal=True,
            label_visibility="collapsed",
            key="navigation_view" # La clave hace que Streamlit recuerde la selección automáticamente
        )
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- VISTA 1: ESTRATEGIA ---
        if selected_view == NAV_ESTRATEGIA:
            col_left, col_right = st.columns([1, 1], gap="medium")
            
            # --- COLUMNA IZQUIERDA: ACCIÓN Y PERFIL ---
            with col_left:
                st.markdown("""
<div style='margin-bottom: 24px;'>
    <h4 style='color: #1a1d29; font-size: 16px; margin: 0; font-weight: 600;'>🎯 Tu Próxima Acción</h4>
</div>
""", unsafe_allow_html=True)
                
                st.markdown(f"""
<div style="background: white; border: 1px solid #e2e8f0; padding: 28px; border-radius: 8px;">
    <p style="color: #2d3748; margin: 0 0 24px 0; font-size: 15px; line-height: 1.7;">
        {data.get('accion_recomendada', 'Sin acción definida')}
    </p>
    <a href="https://mail.google.com/mail/?view=cm&fs=1&to={st.session_state.analysis_results.get('target_email', '')}&su=Seguimiento" 
       target="_blank"
       style="display: inline-block; background: #1a1d29; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px; transition: all 0.2s;">
        📧 Escribir Email
    </a>
</div>
""", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='margin-bottom: 24px;'>
    <h4 style='color: #1a1d29; font-size: 16px; margin: 0; font-weight: 600;'>👤 Perfil del Cliente</h4>
</div>
""", unsafe_allow_html=True)
                
                st.markdown(f"""
<div style="background: white; border: 1px solid #e2e8f0; padding: 28px; border-radius: 8px;">
    <p style="color: #2d3748; margin: 0; font-size: 15px; line-height: 1.7;">
        {data.get('perfil_cliente', 'Perfil no identificado')}
    </p>
</div>
""", unsafe_allow_html=True)
                
                # Determinar icono según urgencia
                urgencia = data.get('urgencia', 'Media')
                if urgencia == 'Alta':
                    icono_perfil = "🔴"
                    color_borde = "#d32f2f"
                    color_fondo = "#ffebee"
                elif urgencia == 'Baja':
                    icono_perfil = "🟢"
                    color_borde = "#388e3c"
                    color_fondo = "#e8f5e9"
                else:
                    icono_perfil = "🟡"
                    color_borde = "#f57c00"
                    color_fondo = "#fff3e0"
                
                st.markdown(f"""
                <div style="background-color: {color_fondo}; padding: 20px; border-radius: 10px; border-left: 5px solid {color_borde}; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                    <div style="display: flex; align-items: flex-start;">
                        <span style="font-size: 32px; margin-right: 15px; line-height: 1;">{icono_perfil}</span>
                        <p style="color: #37474f; margin: 0; font-size: 15px; line-height: 1.6;">
                            {data.get('perfil_cliente', 'Perfil no identificado')}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- COLUMNA DERECHA: INSIGHTS ---
            with col_right:
                st.markdown("""
<div style='margin-bottom: 24px;'>
    <h4 style='color: #1a1d29; font-size: 16px; margin: 0; font-weight: 600;'>💎 Insights Estratégicos</h4>
</div>
""", unsafe_allow_html=True)
                
                insights = data.get('insights_clave', [])
                
                if not insights:
                    st.markdown("""
<div style='background: white; border: 1px solid #e2e8f0; padding: 28px; border-radius: 8px; text-align: center;'>
    <p style='color: #718096; margin: 0; font-size: 14px;'>No se detectaron insights adicionales</p>
</div>
""", unsafe_allow_html=True)
                else:
                    # TODOS LOS INSIGHTS EN CARDS UNIFORMES
                    for idx, insight in enumerate(insights, 1):
                        # Determinar si es prioritario (el primero)
                        if idx == 1:
                            border_color = "#1a1d29"
                            icon_bg = "#1a1d29"
                            icon_color = "white"
                            card_bg = "white"
                        else:
                            border_color = "#e2e8f0"
                            icon_bg = "#f7fafc"
                            icon_color = "#4a5568"
                            card_bg = "white"
                        
                        st.markdown(f"""
<div style='background: {card_bg}; border: 1px solid {border_color}; padding: 20px 24px; border-radius: 8px; margin-bottom: 12px;'>
    <div style='display: flex; align-items: flex-start; gap: 14px;'>
        <div style='background: {icon_bg}; color: {icon_color}; min-width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0;'>
            {idx}
        </div>
        <p style='color: #2d3748; font-size: 14px; line-height: 1.7; margin: 4px 0 0 0;'>
            {insight}
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
                    
                    # 2. INSIGHTS SECUNDARIOS (agrupados en expander)
                    if len(insights) > 1:
                        with st.expander(f"📋 Ver {len(insights)-1} insights adicionales", expanded=False):
                            st.markdown("""
                            <div style='background-color: #fafbfc; padding: 15px; border-radius: 10px;'>
                            """, unsafe_allow_html=True)
                            
                            for i, insight in enumerate(insights[1:], start=1):
                                st.markdown(f"""
                                <div style="background-color: white; padding: 14px 18px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #90caf9; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                                    <div style="display: flex; align-items: flex-start;">
                                        <span style="background-color: #e3f2fd; color: #1976d2; font-weight: bold; font-size: 14px; min-width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                                            {i}
                                        </span>
                                        <p style="color: #546e7a; font-size: 14px; line-height: 1.5; margin: 2px 0 0 0;">
                                            {insight}
                                        </p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
        # --- VISTA 2: GENERADOR ---
        elif selected_view == NAV_GENERADOR:
            # Header con icono grande
            st.markdown("""
            <div style='text-align: center; padding: 20px 0 10px 0;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>✉️</div>
                <h3 style='color: #1a2b4b; margin: 0;'>Email Generado Automáticamente</h3>
                <p style='color: #7f8c8d; font-size: 14px; margin-top: 8px;'>
                    💡 Este borrador está optimizado según el contexto. Personalízalo antes de enviar.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.text_area(
                "Contenido del mensaje:",
                value=data.get('borrador_respuesta', 'No disponible'),
                height=400,
                label_visibility="collapsed"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
            with col_btn1:
                draft = data.get('borrador_respuesta', '')
                gmail_compose_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={st.session_state.analysis_results.get('target_email', '')}&su=Seguimiento"
                st.link_button("📧 Abrir en Gmail", gmail_compose_url, use_container_width=True, type="primary")
            with col_btn2:
                st.button("📋 Copiar texto", use_container_width=True, key="copy_draft")
            with col_btn3:
                st.button("🔄", use_container_width=True, help="Regenerar borrador", key="regenerate_draft")
        # --- VISTA 3: EXPLORADOR AVANZADO ---
        elif selected_view == NAV_EXPLORADOR:
            # === PANEL DE FILTROS (MEJORADO) ===
            st.markdown("""
            <div style='background: white; padding: 20px 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 25px; border-left: 5px solid #004e98;'>
                <h4 style='margin: 0 0 15px 0; color: #1a2b4b; font-size: 18px; display: flex; align-items: center;'>
                    🔍 <span style='margin-left: 10px;'>Filtros de Búsqueda</span>
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Inicializar valores por defecto si no existen
            if 'f_origen_key' not in st.session_state:
                st.session_state.f_origen_key = "Todos"
            if 'f_texto_key' not in st.session_state:
                st.session_state.f_texto_key = ""
            if 'f_fecha_key' not in st.session_state:
                st.session_state.f_fecha_key = "Todas"
            
            # Filtros en una sola línea compacta
            f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 1])
            with f_col1:
                f_origen = st.selectbox(
                    "Origen", 
                    ["Todos", "CLIENTE", "BANCO"], 
                    index=["Todos", "CLIENTE", "BANCO"].index(st.session_state.f_origen_key),
                    key="f_origen_key"
                )
            with f_col2:
                f_texto = st.text_input(
                    "Buscar palabra clave", 
                    value=st.session_state.f_texto_key,
                    placeholder="Ej: inversión...", 
                    key="f_texto_key"
                )
            with f_col3:
                f_fecha = st.selectbox(
                    "Fecha", 
                    ["Todas", "7 días", "30 días"],
                    index=["Todas", "7 días", "30 días"].index(st.session_state.f_fecha_key),
                    key="f_fecha_key"
                )
            with f_col4:
                st.markdown("<br>", unsafe_allow_html=True)  # Alinear verticalmente
                if st.button("🔄 Limpiar", key="clear_filters", use_container_width=True):
                    # Forzar reset borrando las keys del estado
                    for key in ['f_origen_key', 'f_texto_key', 'f_fecha_key']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            st.markdown("---")

            # === LÓGICA DE FILTRADO ===
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

            # Contador de resultados más visible
            if len(filtered_ev) < len(evidence):
                st.info(f"📊 **{len(filtered_ev)}** de **{len(evidence)}** emails coinciden con los filtros")
            else:
                st.success(f"📊 Mostrando los **{len(evidence)}** emails completos")
            
            st.markdown("<br>", unsafe_allow_html=True)

            # === VISUALIZACIÓN DE CARDS (PERSISTENTE) ===
            if not filtered_ev:
                st.markdown("""
                <div style='text-align: center; padding: 60px 40px; background: white; border-radius: 15px; border: 2px dashed #e0e6ed; margin: 30px 0;'>
                    <div style='font-size: 64px; margin-bottom: 20px; opacity: 0.3;'>📭</div>
                    <h3 style='color: #5a6c7d; margin-bottom: 10px;'>No hay emails que coincidan</h3>
                    <p style='color: #95a5a6; font-size: 15px;'>
                        Intenta ajustar los filtros o buscar otro término
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for email in filtered_ev:
                    icon = "👤" if email['Origen'] == "CLIENTE" else "🏦"
                    color = "green" if email['Origen'] == "CLIENTE" else "blue"
                    
                    with st.expander(f"{icon} {email['Fecha_Corta']} | {email['Asunto']}"):
                        # Cabecera
                        st.markdown(f"""
                        <div class='email-header-box'>
                            <b>De:</b> :{color}[{email['Origen']}] <br>
                            <b>Fecha:</b> {email['Fecha']} <br>
                            <b>Asunto:</b> {email['Asunto_Completo']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Cuerpo con resaltado
                        body_show = email['Cuerpo']
                        if f_texto:
                            import re
                            body_show = re.sub(f"({re.escape(f_texto)})", r"<mark style='background:#fff9c4'>\1</mark>", body_show, flags=re.IGNORECASE)
                        
                        st.markdown(f"<div class='email-content'>{body_show}</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # --- ZONA DE ACCIONES (ESTADO PERSISTENTE) ---
                        c_btn1, c_btn2 = st.columns([1, 2])
                        analysis_key = f"thread_analysis_{email['Id']}"
                        
                        with c_btn1:
                            gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{email['Id_Completo']}"
                            st.link_button("🔗 Abrir en Gmail", gmail_url, use_container_width=True)
                        
                        with c_btn2:
                            # 1. BOTÓN DE ANÁLISIS (MEJORADO)
                            button_label = "✅ Análisis cargado" if f"thread_analysis_{email['Id']}" in st.session_state else "🧶 Analizar Hilo Completo"
                            button_type = "secondary" if f"thread_analysis_{email['Id']}" in st.session_state else "primary"
                            
                            if st.button(button_label, key=f"btn_{email['Id']}", use_container_width=True, type=button_type):
                                # Mostrar placeholder mientras carga
                                placeholder = st.empty()
                                with placeholder.container():
                                    st.markdown("""
<div style='background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); padding: 30px; border-radius: 12px; text-align: center; border-left: 4px solid #7b1fa2; box-shadow: 0 4px 12px rgba(123,31,162,0.1);'>
    <div style='font-size: 48px; margin-bottom: 15px; animation: pulse 1.5s ease-in-out infinite;'>🧶</div>
    <h4 style='color: #4a148c; margin: 0 0 10px 0;'>Analizando hilo completo...</h4>
    <p style='color: #6a1b9a; font-size: 14px; margin: 0;'>Procesando conversación completa con IA</p>
    <div style='width: 50%; height: 4px; background: rgba(123,31,162,0.2); border-radius: 2px; margin: 15px auto 0; overflow: hidden;'>
        <div style='width: 100%; height: 100%; background: #7b1fa2; animation: loading 1.5s ease-in-out infinite;'></div>
    </div>
</div>

<style>
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
}
@keyframes loading {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}
</style>
""", unsafe_allow_html=True)
                                
                                try:
                                    # API Call
                                    service = build('gmail', 'v1', credentials=st.session_state.creds)
                                    meta = service.users().messages().get(userId='me', id=email['Id_Completo'], format='minimal').execute()
                                    thread_id = meta.get('threadId')
                                    
                                    # Backend Logic
                                    thread_content = get_thread_content(st.session_state.creds, thread_id)
                                    
                                    if thread_content:
                                        analysis = analyze_thread_structure(thread_content)
                                        # 💾 GUARDADO EN ESTADO
                                        st.session_state[analysis_key] = analysis
                                        placeholder.empty()  # Limpiar el loading
                                        st.rerun()  # Refrescar para mostrar resultado
                                    else:
                                        placeholder.empty()
                                        st.error("No se pudo leer el hilo.")
                                except Exception as e:
                                    placeholder.empty()
                                    st.error(f"Error técnico: {e}")

                        # 2. VISUALIZADOR (Lee del estado)
                        if analysis_key in st.session_state:
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Header con botón de cerrar
                            col_header1, col_header2 = st.columns([4, 1])
                            with col_header1:
                                st.markdown("""
                                <div style='background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 15px 20px; border-radius: 10px 10px 0 0; border-left: 5px solid #ef6c00;'>
                                    <h4 style='color: #ef6c00; margin: 0; display: flex; align-items: center;'>
                                        <span style='font-size: 24px; margin-right: 10px;'>🧶</span>
                                        Inteligencia de Hilo
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                            with col_header2:
                                if st.button("✕", key=f"close_{email['Id']}", help="Cerrar análisis"):
                                    del st.session_state[analysis_key]
                                    st.rerun()
                            
                            # Contenido del análisis en markdown nativo (mejor renderizado)
                            st.markdown(f"""
                            <div style='background-color: white; border: 2px solid #ffe0b2; border-top: none; padding: 25px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>
                            """, unsafe_allow_html=True)
                            
                            # Renderizar el markdown de la IA directamente
                            st.markdown(st.session_state[analysis_key])
                            
                            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Fíjate que esta línea tiene sangría (espacios al principio) respecto al 'else'
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Esta línea también tiene sangría
        st.markdown("""
<div style='text-align: center; padding: 60px 40px; background: white; border-radius: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);'>
    <div style='font-size: 80px; margin-bottom: 20px; opacity: 0.5;'>🔍</div>
    <h2 style='color: #1a2b4b; margin-bottom: 15px;'>Bienvenido a WS Advisor</h2>
    <p style='color: #7f8c8d; font-size: 16px; margin-bottom: 40px;'>
        Analiza conversaciones completas con IA para obtener insights accionables
    </p>
    <div style='
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        max-width: 900px;
        margin: 0 auto;
        text-align: left;
    '>
        <div style='background: #f8f9fa; padding: 22px; border-radius: 14px; border-left: 4px solid #004e98;'>
            <strong style='color: #1a2b4b;'>1️⃣ Introduce el email del cliente</strong>
            <p style='color: #7f8c8d; margin: 8px 0 0 0; font-size: 14px;'>
                En el campo de búsqueda superior
            </p>
        </div>
        <div style='background: #f8f9fa; padding: 22px; border-radius: 14px; border-left: 4px solid #004e98;'>
            <strong style='color: #1a2b4b;'>2️⃣ Configura el período</strong>
            <p style='color: #7f8c8d; margin: 8px 0 0 0; font-size: 14px;'>
                Elige número de emails o rango de fechas en el panel lateral
            </p>
        </div>
        <div style='background: #f8f9fa; padding: 22px; border-radius: 14px; border-left: 4px solid #004e98;'>
            <strong style='color: #1a2b4b;'>3️⃣ Haz clic en "Analizar"</strong>
            <p style='color: #7f8c8d; margin: 8px 0 0 0; font-size: 14px;'>
                Obtendrás análisis de sentimiento, estrategia y borradores automáticos
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)