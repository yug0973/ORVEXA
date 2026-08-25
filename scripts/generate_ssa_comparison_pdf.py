import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count 'Page X of Y'
    along with running header and footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber > 1:
            # Running Header
            self.saveState()
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0F172A"))
            self.drawString(54, 750, "ORVEXA // COMPETITIVE ADVANTAGE ANALYSIS")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(612 - 54, 750, "INDIAN SSA LANDSCAPE & COMPARATIVE BENCHMARK")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, 744, 612 - 54, 744)
            
            # Running Footer
            self.line(54, 45, 612 - 54, 45)
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0D47A1"))
            self.drawString(54, 32, "CONFIDENTIAL // SMART INDIA HACKATHON & SPACE TECH BENCHMARK")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(612 - 54, 32, page_text)
            self.restoreState()


def create_comparison_pdf():
    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "ORVEXA_vs_Indian_SSA_Landscape.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    PRIMARY = colors.HexColor("#0F172A")    # Deep Navy / Slate
    SECONDARY = colors.HexColor("#0369A1")  # Cyan / Blue
    ACCENT = colors.HexColor("#0284C7")     # Sky Blue
    DARK_BG = colors.HexColor("#1E293B")    # Slate Dark
    LIGHT_BG = colors.HexColor("#F8FAFC")   # Off-white
    BORDER_COLOR = colors.HexColor("#E2E8F0")
    SUCCESS_COLOR = colors.HexColor("#059669")
    WARNING_COLOR = colors.HexColor("#D97706")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Header1',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=PRIMARY
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#0C4A6E")
    )

    story = []

    # ── COVER HEADER ────────────────────────────────────────────────────────
    story.append(Paragraph("ORVEXA vs. INDIAN SSA LANDSCAPE", title_style))
    story.append(Paragraph("Strategic Advantages, Comparative Benchmarks & Commercial Viability", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceBefore=0, spaceAfter=12))

    # Executive Summary Banner
    summary_html = """
    <b>EXECUTIVE SUMMARY:</b> While India's space ecosystem has made significant strides with ISRO's classified 
    <b>Project NETRA</b> and emerging sensor hardware startups like <b>Digantara</b>, the Indian space ecosystem lacks an 
    accessible, cloud-native Space Situational Awareness (SSA), automated UN/IN-SPACe compliance, and AI-assisted collision 
    mitigation platform. <b>ORVEXA</b> bridges this critical gap by delivering a full-stack, browser-native mission control 
    platform powered by SGP4 propagation, Foster (1992) collision radar, real-time Aditya-L1 solar weather integration, 
    and automated regulatory audit generators.
    """
    
    callout_data = [[Paragraph(summary_html, callout_style)]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E0F2FE")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0284C7")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 12))

    # ── SECTION 1: THE INDIAN SSA ECOSYSTEM & GAPS ──────────────────────────
    story.append(Paragraph("1. Current State of SSA Platforms in India", h1_style))
    story.append(Paragraph(
        "India's space sector is undergoing rapid commercialization under IN-SPACe. However, existing SSA solutions face steep structural limitations:",
        body_style
    ))

    story.append(Paragraph("• <b>ISRO Project NETRA (Network for space object Tracking and Analysis):</b> Designed for sovereign defense and ISRO assets. It is highly classified, closed to commercial private operators, and lacks interactive web interfaces, open APIs, and automated compliance tools for new-space startups.", bullet_style))
    story.append(Paragraph("• <b>Digantara (ROBODET / Space-MAP):</b> Focused primarily on space-based hardware sensor constellations. It operates on a high-cost proprietary subscription model that is cost-prohibitive for universities, research labs, and early-stage satellite operators.", bullet_style))
    story.append(Paragraph("• <b>Foreign Software Dependencies (AGI STK / LeoLabs / Slingshot):</b> Indian space startups frequently rely on expensive Western desktop software licenses ($40,000 - $150,000/year/seat), introducing national data sovereignty risks and extreme financial overhead.", bullet_style))
    story.append(Spacer(1, 10))

    # ── SECTION 2: COMPREHENSIVE COMPARISON MATRIX ──────────────────────────
    story.append(Paragraph("2. Detailed Feature & Architectural Comparison Matrix", h1_style))

    headers = [
        Paragraph("<b>Evaluation Dimension</b>", table_header_style),
        Paragraph("<b>ISRO NETRA</b>", table_header_style),
        Paragraph("<b>Digantara</b>", table_header_style),
        Paragraph("<b>Western Tools (STK/LeoLabs)</b>", table_header_style),
        Paragraph("<b>ORVEXA (Our Platform)</b>", table_header_style)
    ]

    matrix_data = [headers]

    features = [
        ("Accessibility & Licensing", "Closed Gov/Defense Only", "Proprietary Paid B2B", "Costly ($50k-$150k/seat)", "Open Web Architecture & API"),
        ("3D Web Visualization", "Restricted Internal Ops", "Limited 2D/3D Web", "Heavy Desktop (C++/Win)", "Zero-Install 60FPS WebGL (Cesium)"),
        ("Collision Risk Algorithm", "Covariance Screening", "Observation Mapping", "Covariance / Foster 1992", "Foster (1992) B-Plane Probability"),
        ("Space Weather Coupling", "Classified/Custom", "Static Atmosphere", "Manual Atmospheric Inputs", "Live Aditya-L1 & NOAA Solar Ingest"),
        ("UN COPUOS 5-Yr Compliance", "Manual Defense Review", "Not Supported", "Manual Custom Scripting", "Automated Instant 1-Click PDF Audit"),
        ("AI Astrometry Copilot", "None", "None", "None", "Grounded Contextual AI Assistant"),
        ("Reentry Ground Corridor", "ISRO Internal Ballistics", "Not Core Focus", "Paid Addon Module", "Real-Time 2D Leaflet Ground-Track"),
        ("Data Sovereignty & Privacy", "100% Indian Sovereign", "Indian Private Cloud", "US / EU Cloud Servers", "100% Indian Sovereign & Self-Hostable"),
        ("Deployment Footprint", "Dedicated Data Centers", "Cloud SaaS", "Heavy Desktop Installation", "Lightweight Cloud / Docker Container")
    ]

    for f in features:
        matrix_data.append([
            Paragraph(f[0], table_cell_bold),
            Paragraph(f[1], table_cell_style),
            Paragraph(f[2], table_cell_style),
            Paragraph(f[3], table_cell_style),
            Paragraph(f"<b>{f[4]}</b>", table_cell_style)
        ])

    comp_table = Table(matrix_data, colWidths=[110, 95, 95, 100, 104])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (4, 1), (4, -1), colors.HexColor("#F0FDF4")), # Highlight ORVEXA column
    ]))
    
    story.append(comp_table)
    story.append(Spacer(1, 14))

    # ── SECTION 3: TOP 6 DISTINCT ADVANTAGES OF ORVEXA ──────────────────
    story.append(Paragraph("3. Top 6 Key Strategic Advantages of ORVEXA", h1_style))

    advantages = [
        ("1. Real-Time Aditya-L1 & NOAA Solar Weather Ingestion",
         "Standard orbital propagators assume static atmospheric density models. ORVEXA dynamically couples real-time Solar Radio Flux (F10.7) and Geomagnetic Ap indices from NOAA and India's Aditya-L1 satellite to compute dynamic thermospheric expansion and accelerated orbital decay rates during geomagnetic storms."),
        
        ("2. Mathematical Rigor via Foster-1992 B-Plane Collision Probability",
         "Instead of relying on simple Euclidean distance thresholds, ORVEXA integrates 2D probability density across combined 3D error covariance ellipsoids. This eliminates false-positive conjunction alarms and outputs minimal-fuel collision avoidance delta-V recommendations."),
        
        ("3. Automated UN COPUOS & IN-SPACe 5-Year Rule Audit Engine",
         "New international space debris regulations mandate de-orbiting within 5 years post-mission. ORVEXA automatically verifies satellite parameters against UN COPUOS and FCC standards, generating tamper-evident, official PDF audit certificates for launch clearance."),
        
        ("4. Zero-Installation 60 FPS 3D WebGL Mission Control",
         "Built on CesiumJS and modern WebGL hardware layers, ORVEXA runs directly in any modern web browser without requiring multi-gigabyte desktop software installations or expensive GPU workstations."),
        
        ("5. Grounded AI Astrometry Copilot",
         "Equipped with an intelligent LLM agent grounded in live telemetry, TLE data, and collision tables, enabling satellite operators to ask plain-language questions like 'Evaluate collision risk for Cartosat-2B' and receive instant mathematical insights."),
        
        ("6. Complete Data Sovereignty & Democratization for India's Spacetech Ecosystem",
         "By offering an open, cost-effective, self-hostable architecture, ORVEXA democratizes space situational awareness for Indian universities, research institutions, and emerging space startups without relying on foreign proprietary suites.")
    ]

    for title, desc in advantages:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(Spacer(1, 12))

    # ── SECTION 4: ALIGNMENT WITH NATIONAL MISSIONS (SIH FOCUS) ─────────────
    story.append(Paragraph("4. Alignment with National Initiatives (ISRO / IN-SPACe / SIH)", h1_style))
    story.append(Paragraph("ORVEXA directly supports India's vision of becoming a global space leader by addressing:", body_style))
    story.append(Paragraph("• <b>IN-SPACe Authorization Framework:</b> Provides new private space startups with the exact regulatory audit tools needed for satellite licensing and frequency allocations.", bullet_style))
    story.append(Paragraph("• <b>Project NETRA Augmentation:</b> Offers an open civilian/commercial layer that complements ISRO's sovereign military SSA infrastructure.", bullet_style))
    story.append(Paragraph("• <b>Sustainable Space Operations:</b> Proactively prevents Kessler syndrome cascades by tracking debris and enforcing international disposal timelines.", bullet_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {pdf_path}")
    return pdf_path

if __name__ == '__main__':
    create_comparison_pdf()
