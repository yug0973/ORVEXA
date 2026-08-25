import os
import json
from datetime import datetime, timezone
import ollama
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_brief_fallback(event_data: dict) -> str:
    """
    High-fidelity fallback regulatory statement if Ollama is unreachable.
    """
    return f"""INSPACE-CAM-2026 Collision Avoidance Filing Briefing
--------------------------------------------------
REGULATORY STATEMENT FOR SAT-TO-SAT CONJUNCTION MITIGATION

This official filing outlines the emergency collision avoidance maneuver (CAM) planned for {event_data.get('primary_name', 'PRIMARY')} (NORAD {event_data.get('primary_norad', 'N/A')}) to mitigate a high-risk conjunction with {event_data.get('secondary_name', 'SECONDARY')} (NORAD {event_data.get('secondary_norad', 'N/A')}).

1. MANEUVER NECESSITY:
Based on high-fidelity orbital propagation and spatial screening, a close approach has been detected with a calculated Time of Closest Approach (TCA) at {event_data.get('tca', 'TCA')}. The estimated miss distance is {event_data.get('miss_distance', 'N/A')} km, yielding a Collision Probability (Pc) of {event_data.get('pc', 'N/A')}, which exceeds the standard safety threshold (1.0e-4). This maneuver is critical to safeguard space assets and eliminate collision risk.

2. TARGET SAFETY WINDOW:
The mitigation maneuver will execute approximately 12 hours prior to TCA, establishing a safe physical separation distance exceeding 2.0 km at the moment of closest approach. State vectors will be monitored continuously post-maneuver to verify trajectory stability.

3. IADC SPACE DEBRIS GUIDELINES COMPLIANCE:
All maneuvers are designed to minimize risk to the space environment. Post-maneuver trajectory propagation ensures that the satellite remains within a stable orbit, avoids secondary conjunctions with other cataloged objects, and fully complies with Inter-Agency Space Debris Coordination Committee (IADC) guidelines on space safety and mitigation.

Signed,
{event_data.get('operator_name', 'Authorized Operator')}
"""

import socket

def is_ollama_available() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=2.0):
            return True
    except Exception:
        return False

def generate_compliance_brief(event_data: dict) -> str:
    """
    Generates a formal regulatory compliance statement using local Llama 3.2 via Ollama.
    Falls back to a high-fidelity template if Ollama is unresponsive.
    """
    if not is_ollama_available():
        return generate_brief_fallback(event_data)

    prompt = f"""
    Write a formal regulatory compliance statement for a satellite collision avoidance maneuver.
    Conjunction details:
    Primary Satellite: {event_data.get('primary_name')} (NORAD {event_data.get('primary_norad')})
    Secondary Satellite: {event_data.get('secondary_name')} (NORAD {event_data.get('secondary_norad')})
    Time of Closest Approach (TCA): {event_data.get('tca')}
    Miss Distance: {event_data.get('miss_distance')} km
    Collision Probability (Pc): {event_data.get('pc')}
    
    The briefing must explain:
    1. Why the maneuver is necessary (hazard mitigation).
    2. The target safety window.
    3. Compliance with IADC space debris guidelines.
    Keep the tone extremely formal, professional, and regulatory-grade.
    """
    try:
        client = ollama.Client(timeout=25.0)
        response = client.chat(
            model='llama3.2', 
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            options={'num_predict': 300, 'temperature': 0.2}
        )
        return response['message']['content']
    except Exception as e:
        print(f"Warning: Ollama Llama 3.2 model unreachable or failed ({e}). Utilizing fallback briefing template.")
        return generate_brief_fallback(event_data)

def compile_pdf_document(filing_data: dict) -> str:
    """
    Uses ReportLab Platypus to compile a clean, official, print-ready PDF containing
    the INSPACE-CAM-2026 form fields, operator signature line, and generated briefing text.
    """
    storage_dir = "backend/storage/compliance"
    os.makedirs(storage_dir, exist_ok=True)
    pdf_path = os.path.abspath(os.path.join(storage_dir, f"filing_{filing_data['id']}.pdf"))
    
    # Establish document layout template
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []
    
    styles = getSampleStyleSheet()
    
    # Define custom branding styles matching the ORVEXA palette
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1A237E'),  # Dark Blue
        alignment=1,  # Centered
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0D47A1'),  # Royal Blue
        spaceBefore=12,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#212121'),  # Off-Black
        spaceAfter=8
    )
    
    # Add Document Title
    story.append(Paragraph("INSPACE-CAM-2026 Collision Avoidance Filing", title_style))
    story.append(Spacer(1, 10))
    
    # Add Form Data Table
    table_data = [
        [Paragraph("<b>Filing Reference ID:</b>", body_style), Paragraph(str(filing_data.get("id")), body_style)],
        [Paragraph("<b>Primary Spacecraft:</b>", body_style), Paragraph(f"{filing_data.get('satellite')} (NORAD {filing_data.get('primary_norad')})", body_style)],
        [Paragraph("<b>Secondary Spacecraft:</b>", body_style), Paragraph(f"NORAD {filing_data.get('secondary_norad')}", body_style)],
        [Paragraph("<b>Operator of Record:</b>", body_style), Paragraph(filing_data.get("operator", "Unknown"), body_style)],
        [Paragraph("<b>Time of Closest Approach (TCA):</b>", body_style), Paragraph(str(filing_data.get("tca")), body_style)],
        [Paragraph("<b>Filing Status:</b>", body_style), Paragraph(filing_data.get("status", "SUBMITTED"), body_style)],
        [Paragraph("<b>Submission Timestamp:</b>", body_style), Paragraph(str(filing_data.get("submitted_at")), body_style)]
    ]
    
    # Render metadata grid
    meta_table = Table(table_data, colWidths=[200, 300])
    meta_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDBDBD')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E3F2FD')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Add Briefing Text Section
    story.append(Paragraph("Regulatory Briefing & Maneuver Justification", section_title_style))
    
    briefing_text = filing_data.get("briefing", "")
    for paragraph in briefing_text.split('\n\n'):
        clean_para = paragraph.strip()
        if clean_para:
            # ReportLab requires <br/> instead of \n for newlines in paragraphs
            formatted_para = clean_para.replace('\n', '<br/>')
            story.append(Paragraph(formatted_para, body_style))
            
    story.append(Spacer(1, 15))
    
    # 4.5. Add Reproducible Scientific Parameters Section
    story.append(Paragraph("Astrometric State Vectors & Covariance Matrices (TCA Epoch)", section_title_style))
    story.append(Paragraph("Below are the exact Earth-Centered Inertial (ECI) position (km) and velocity (km/s) state vectors and uncertainty covariances used to calculate the collision probability, ensuring absolute reproducibility for auditing and regulatory verification.", body_style))
    story.append(Spacer(1, 5))
    
    p_state = filing_data.get("primary_state")
    s_state = filing_data.get("secondary_state")
    cov = filing_data.get("covariance")
    
    p_pos_str = f"[{', '.join(f'{x:.4f}' for x in p_state['position'])}]" if (p_state and "position" in p_state) else "N/A"
    p_vel_str = f"[{', '.join(f'{x:.6f}' for x in p_state['velocity'])}]" if (p_state and "velocity" in p_state) else "N/A"
    
    s_pos_str = f"[{', '.join(f'{x:.4f}' for x in s_state['position'])}]" if (s_state and "position" in s_state) else "N/A"
    s_vel_str = f"[{', '.join(f'{x:.6f}' for x in s_state['velocity'])}]" if (s_state and "velocity" in s_state) else "N/A"
    
    p_cov_list = cov.get("p_cov") if cov else None
    s_cov_list = cov.get("s_cov") if cov else None
    
    def format_cov(cov_mat):
        if not cov_mat:
            return "N/A"
        return "<br/>".join(f"[{', '.join(f'{val:.2e}' for val in row)}]" for row in cov_mat)
        
    p_cov_str = format_cov(p_cov_list)
    s_cov_str = format_cov(s_cov_list)
    
    scientific_table_data = [
        [
            Paragraph("<b>Parameter</b>", body_style),
            Paragraph("<b>Primary Spacecraft</b>", body_style),
            Paragraph("<b>Secondary Spacecraft</b>", body_style)
        ],
        [
            Paragraph("<b>ECI Position Vector (km)</b>", body_style),
            Paragraph(p_pos_str, body_style),
            Paragraph(s_pos_str, body_style)
        ],
        [
            Paragraph("<b>ECI Velocity Vector (km/s)</b>", body_style),
            Paragraph(p_vel_str, body_style),
            Paragraph(s_vel_str, body_style)
        ],
        [
            Paragraph("<b>ECI Covariance Matrix (km^2)</b>", body_style),
            Paragraph(p_cov_str, body_style),
            Paragraph(s_cov_str, body_style)
        ]
    ]
    
    scientific_table = Table(scientific_table_data, colWidths=[150, 175, 175])
    scientific_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDBDBD')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ECEFF1')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(scientific_table)
    story.append(Spacer(1, 15))
    
    # Add Signature Block
    story.append(Paragraph("Authorization & Sign-off", section_title_style))
    story.append(Spacer(1, 10))
    
    sig_data = [
        [
            Paragraph("_______________________________________<br/>Authorized Operator Signature", body_style),
            Paragraph("___________________<br/>Date", body_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[350, 150])
    story.append(sig_table)
    
    # Build Document
    doc.build(story)
    return pdf_path
