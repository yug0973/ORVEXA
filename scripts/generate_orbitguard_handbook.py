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
            self.setFillColor(colors.HexColor("#0D47A1"))
            self.drawString(54, 750, "ORVEXA: SPACE SITUATIONAL AWARENESS & TRAFFIC MANAGEMENT")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(612 - 54, 750, "ULTRA-DETAILED HINGLISH SYSTEM MANUAL")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, 744, 612 - 54, 744)
            
            # Running Footer
            self.line(54, 45, 612 - 54, 45)
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0D47A1"))
            self.drawString(54, 32, "ORVEXA — COMPLETE TECHNICAL & OPERATIONAL SPECIFICATION")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(612 - 54, 32, page_text)
            self.restoreState()


def create_handbook():
    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.abspath(os.path.join(output_dir, "ORVEXA_Complete_Project_Handbook_Hinglish.pdf"))
    
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
    
    # Custom Palette
    PRIMARY = colors.HexColor("#0A192F")    # Deep Navy
    ACCENT_BLUE = colors.HexColor("#0284C7")# Bright Sky Blue
    TEXT_DARK = colors.HexColor("#1E293B")  # Slate 800
    CARD_BG = colors.HexColor("#F8FAFC")    # Slate 50
    BORDER_COLOR = colors.HexColor("#CBD5E1")# Slate 300
    GOLD = colors.HexColor("#B45309")       # Amber 700
    CRITICAL_RED = colors.HexColor("#B91C1C")# Red 700

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        alignment=1,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=ACCENT_BLUE,
        alignment=1,
        spaceAfter=10
    )
    
    h1_style = ParagraphStyle(
        'H1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=ACCENT_BLUE,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=TEXT_DARK,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-7,
        spaceAfter=2.5
    )
    
    code_box_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A")
    )
    
    callout_style = ParagraphStyle(
        'Callout_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E3A8A")
    )

    # ── COVER / HEADER ───────────────────────────────────────────────────────
    story.append(Paragraph("🛰️ ORVEXA: ULTRA-DETAILED HINGLISH DEFENSE HANDBOOK", title_style))
    story.append(Paragraph("Step-by-Step Architecture, Physics Equations, Mathematics, Every Button &amp; UI Action, Swarm Pipeline &amp; Judges Defense", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE, spaceAfter=8))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>Target Event:</b> Smart Space Hackathon (22 Aug 2026)", body_style),
            Paragraph("<b>Standard:</b> IN-SPACe (India) &amp; IADC Space Debris Rules", body_style)
        ],
        [
            Paragraph("<b>Stack:</b> React 19 + CesiumJS 3D + FastAPI + Local Llama 3.2", body_style),
            Paragraph("<b>Coverage:</b> 100% Granular Button-by-Button &amp; Math Manual", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # ── SECTION 1: GLOBAL TOPBAR & ENTRY PORTAL ──────────────────────────────
    story.append(Paragraph("1. Entry Portal &amp; Global Navigation Topbar (Har Button Ka Kaam)", h1_style))
    story.append(Paragraph("<b>A. Entry Portal (Hero Canvas):</b>", h2_style))
    story.append(Paragraph("&bull; <b>'LAUNCH SSA MISSION DECK' Button:</b> WebGL particle canvas se transition karke main 3D Space Command Dashboard par enter karta hai aur audio synthesize karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Sound Toggle Button (Volume Icon):</b> HTML5 / Web Audio API sci-fi ambient telemetry sound effects ko mute/unmute karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Live HUD Counters:</b> Active cataloged satellites, spatial screening bubble radius (10 km), aur AI engine readiness verify karta hai.", bullet_style))

    story.append(Paragraph("<b>B. Topbar Elements &amp; Controls:</b>", h2_style))
    story.append(Paragraph("&bull; <b>System Status Badge ('LIVE LEO TELEMETRY'):</b> Backend SGP4 stream connection state aur real-time orbital time status display karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Tracked Satellite Count Badge ('104 SATELLITES TRACKED'):</b> Database mein currently monitored active payloads, rocket bodies, aur debris fragments ka exact count dikhata hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Aditya-L1 / NOAA Weather Pill ('F10.7 | Ap | Drag Scaler'):</b> Live solar radio flux (F10.7 sfu), geomagnetic storm planetary index (Ap), aur thermospheric drag multiplier live stream karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'TRIGGER X-CLASS SOLAR FLARE' / 'CLEAR SOLAR FLARE' Button:</b> Backend endpoint `POST /api/solar/trigger-flare/X` ko call karta hai. Yeh real-time mein X-class flare inject karta hai, WebSockets par alert broadcast karta hai, atmospheric drag 3.5x spike karta hai, aur sabhi decaying objects ki ETA dynamically recalculate karta hai. Dubara click karne par `/api/solar/clear-flare` se orbit baseline restore ho jaati hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'DATA SOURCES &amp; ACCURACY' Button:</b> Modal popup open karta hai jo CelesTrak, NOAA SWPC, ISRO Aditya-L1 coronagraph, aur numerical error budgets explain karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'ASTROMETRY COPILOT' Button:</b> Slide-out local AI assistant drawer ko screen ke right side se toggle karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Bottom Navigation Bar (Sidebar):</b> Exactly 4 core dashboards switch karta hai: [1] 3D Orbit Map, [2] Conjunction Hazards, [3] Decay &amp; Reentry, [4] Compliance &amp; Swarm.", bullet_style))

    # ── SECTION 2: PAGE 1 — 3D ORBIT GLOBE ───────────────────────────────────
    story.append(Paragraph("2. Page 1: 3D Orbit Globe &amp; Fleet Tracking (OrbitMapPage.tsx &amp; OrbitGlobe.tsx)", h1_style))
    story.append(Paragraph("<b>A. Physics, Astrodynamics &amp; Equations:</b>", h2_style))
    story.append(Paragraph("&bull; <b>SGP4 Analytical Propagator:</b> CelesTrak TLE lines se Keplerian elements (a, e, i, &Omega;, &omega;, M) parse karke Earth gravity harmonics (J2, J3, J4) aur drag ke sath ECI cartesian state vectors nikaalta hai: Position (X, Y, Z) [km] aur Velocity (Vx, Vy, Vz) [km/s].", bullet_style))
    story.append(Paragraph("&bull; <b>Orbital Vis-Viva Velocity Equation:</b> v = &radic;(&mu; (2/r - 1/a)), jahan &mu; = 398,600.4418 km&sup3;/s&sup2;. LEO speed ~7.8 km/s hoti hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Hohmann Transfer Delta-V Math:</b> Burn delta-V slider &Delta;v apply karta hai: &Delta;v1 = &radic;(&mu;/r1) &times; (&radic;(2r2 / (r1 + r2)) - 1), jisse post-maneuver new orbit instantly calculate hokar draw hoti hai.", bullet_style))

    story.append(Paragraph("<b>B. Every Single Button &amp; Control on Page 1:</b>", h2_style))
    story.append(Paragraph("&bull; <b>Camera Reset Button (Home/Compass):</b> Camera ko smooth fly-to animation (1.5s) se global altitude overview par reset karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Earth Style Selector ('Satellite' | 'Dark' | 'Natural'):</b> Esri World Imagery (day satellite), NASA VIIRS Black Marble (night lights), ya Street Map toggle karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Time Multiplier Speed Controls ('1x, 10x, 60x, 300x'):</b> Cesium clock multiplier ko speed-up karta hai taaki satellites ki orbital motion fast-forward mein dekh saken.", bullet_style))
    story.append(Paragraph("&bull; <b>'Show Ground Stations' Toggle:</b> 4 Deep Space Radars (Svalbard, ISRO Bengaluru ISTRAC, Goldstone NASA, Hartebeesthoek) ke 800 km sensor coverage cones render karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'Show Hazard Shells' Toggle:</b> 700&ndash;900 km LEO Polar Debris Shell aur 35,786 km GEO Belt hollow 3D spheres ko render karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'Self-Serve TLE Import' Drawer:</b> Custom satellite name + TLE Line 1 + Line 2 enter karke <b>'IMPORT &amp; SCREEN SATELLITE'</b> dabane par backend `/api/satellites/import` instant screening run karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'Pin Trajectory Line' Button:</b> Selected satellite ka continuous 3D orbital path Cesium PolylineGraphics se lock karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Maneuver Delta-V Slider (-10 to +10 m/s):</b> Thruster burn simulation slider jo live Hohmann burn path draw karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'Export CCSDS OPM' Button:</b> International standard CCSDS 502.0-B-2 Orbit Parameter Message text file download karta hai for mission operations.", bullet_style))
    story.append(Paragraph("&bull; <b>'START CINEMATIC SIMULATION' Button:</b> 3-phase automated collision simulation run karta hai (Wide convergence &rarr; Close approach &rarr; Kinetic breakup with GPU debris blast).", bullet_style))

    # ── SECTION 3: PAGE 2 — CONJUNCTIONS & B-PLANE ───────────────────────────
    story.append(Paragraph("3. Page 2: Conjunction Hazards &amp; B-Plane Astrodynamics (ConjunctionPage.tsx)", h1_style))
    story.append(Paragraph("<b>A. Mathematics &amp; Algorithms:</b>", h2_style))
    
    math_pc_content = [
        [
            Paragraph(
                "<b>1. Spatial KD-Tree 3D Screening:</b> O(N&sup2;) 50M distance checks ko O(N log N) tree search mein 10.0 km threshold filter karta hai.<br/>"
                "<b>2. Time of Closest Approach (TCA):</b> Condition d/dt ||r_rel||&sup2; = 0 &implies; r_rel &sdot; v_rel = 0 solve karta hai.<br/>"
                "<b>3. Foster-Elrod 2D Collision Probability Formula (Pc):</b><br/>"
                "&nbsp;&nbsp;&nbsp;&nbsp;<b>Pc = &iint;<sub>x&sup2;+y&sup2; &le; R<sub>HBR</sub>&sup2;</sub> &frac;1{2&pi; &sigma;<sub>&xi;</sub> &sigma;<sub>&zeta;</sub> &radic;(1-&rho;&sup2;)} exp( - &frac;1{2(1-&rho;&sup2;)} [ &frac;(x-x0)&sup2;{&sigma;<sub>&xi;</sub>&sup2;} - &frac;2&rho;(x-x0)(y-y0){&sigma;<sub>&xi;</sub>&sigma;<sub>&zeta;</sub>} + &frac;(y-y0)&sup2;{&sigma;<sub>&zeta;</sub>&sup2;} ] ) dx dy</b><br/>"
                "Jahan R<sub>HBR</sub> = R1 + R2 (Combined Hard Body Radius), (&sigma;<sub>&xi;</sub>, &sigma;<sub>&zeta;</sub>, &rho;) B-Plane encounter covariance parameters hain.",
                code_box_style
            )
        ]
    ]
    math_table = Table(math_pc_content, colWidths=[504])
    math_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(math_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>B. Every Single Button &amp; Action on Page 2:</b>", h2_style))
    story.append(Paragraph("&bull; <b>Conjunction Hazard Cards (Left List):</b> Har card par Primary Sat vs Debris, TCA timestamp, Miss Distance (km), aur Pc Probability display hoti hai. Click karne par us event ka full B-Plane analysis load hota hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Filter Pills ('ALL', 'CRITICAL (Pc &ge; 1e-4)', 'WARNING'):</b> List ko risk severity ke mutabiq filter karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>2D Interactive B-Plane Plotter (Canvas):</b> Encounter plane (&xi;, &zeta;) par 1&sigma;, 2&sigma;, 3&sigma; Mahalanobis covariance ellipses, HBR circle, aur miss distance vector render karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Maneuver Allocation Wheel (OptionWheel.tsx):</b> Game-theoretic de-confliction slider jo Primary vs Secondary operator ke beech fuel-optimal burn share (&Delta;V_R, &Delta;V_I, &Delta;V_C) allot karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'PROPOSE MANEUVER PLAN' Button:</b> Backend `/api/compliance/negotiate` par coordinated maneuver plan propose karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'APPROVE &amp; EXECUTE MANEUVER' Button:</b> Simulated clearance execute karke post-burn miss distance &gt;5.0 km verify karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'INITIATE REGULATORY FILING' Button:</b> Seedha Page 4 par le jaata hai pre-filled event parameters ke sath.", bullet_style))

    # ── SECTION 4: PAGE 3 — DECAY, REENTRY & ADITYA-L1 ───────────────────────
    story.append(Paragraph("4. Page 3: Atmospheric Decay, Reentry &amp; Aditya-L1 Solar Weather (ReentryPage.tsx)", h1_style))
    story.append(Paragraph("<b>A. Physics, Equations &amp; Space Weather Coupling:</b>", h2_style))
    story.append(Paragraph("&bull; <b>King-Hele Perigee Decay Rate:</b> da/dt = -2&pi; (C<sub>D</sub> A / m) &rho;<sub>0</sub> a&sup2; exp( - (a(1-e) - R<sub>E</sub>) / H ). C<sub>D</sub> &approx; 2.2, H &approx; 50&ndash;80 km scale height.", bullet_style))
    story.append(Paragraph("&bull; <b>Aditya-L1 Solar Coupling Drag Scaler:</b> Drag Scaler = 1.0 + 0.015 &times; (F10.7 - 70) + 0.035 &times; Ap. X-Class solar flare aane par drag 3.5x spike karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Ground Casualty Probability (Ec):</b> Ec = P<sub>impact</sub> &times; &rho;<sub>population</sub> &times; A<sub>casualty</sub> vs IADC/NASA limit 10<sup>-4</sup> (1 in 10,000).", bullet_style))

    story.append(Paragraph("<b>B. Every Single Button &amp; Control on Page 3:</b>", h2_style))
    story.append(Paragraph("&bull; <b>Tabs Switcher ('DECAY CANDIDATES' | 'ADITYA-L1 WEATHER'):</b> Orbital decay risk view aur solar physics dashboard ke beech switch karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Decay Candidate Cards:</b> Object name, NORAD ID, Altitude (km), Decay Rate (m/day), ETA, Survival %, Casualty risk dikhata hai. Click karne par 2D map par landing footprint load hota hai.", bullet_style))
    story.append(Paragraph("&bull; <b>2D Leaflet World Reentry Corridor Map:</b> 50 Monte Carlo stochastic runs se computed landing uncertainty corridor (GeoJSON MultiPolygon) render karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Aditya-L1 Live Coronagraph Feed:</b> CME speed (km/s), Flare Class (X/M/C), CME Travel Progress %, aur Impact Active status display karta hai.", bullet_style))

    # ── SECTION 5: PAGE 4 — COMPLIANCE & MULTI-AGENT SWARM ───────────────────
    story.append(Paragraph("5. Page 4: Regulatory Compliance &amp; Multi-Agent Swarm (CompliancePage.tsx)", h1_style))
    story.append(Paragraph("<b>A. 5-Agent Autonomous Swarm Architecture:</b>", h2_style))
    story.append(Paragraph("&bull; <b>Agent 1 (Data Ingestion):</b> CelesTrak / Space-Track live TLEs ingest aur validate karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Agent 2 (Spatial Screening):</b> 3D KD-Tree nearest neighbor indexing se 10 km bounding box ke close encounters filter karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Agent 3 (Astrodynamics &amp; Pc):</b> Encounter frame (R,T,N) mein Foster-Elrod 2D integration se Pc calculate karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Agent 4 (Autonomous Negotiation):</b> Primary aur secondary commercial operators ke beech fuel-optimal burn share negotiate karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>Agent 5 (Compliance Officer):</b> ReportLab engine trigger karke official INSPACE-CAM-2026 PDF generate karta hai.", bullet_style))

    story.append(Paragraph("<b>B. Every Single Button &amp; Control on Page 4:</b>", h2_style))
    story.append(Paragraph("&bull; <b>'TRIGGER AUTONOMOUS SWARM RUN' Button:</b> WebSocket `/api/ws/swarm/run` open karke sabhi 5 agents ko live sequence mein execute karta hai aur real-time terminal logs stream karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'GENERATE &amp; SUBMIT IN-SPACe FILING' Button:</b> Form data (Operator Name, Sat ID, Maneuver Strategy) lekar backend `POST /api/compliance/file` par formal regulatory filing submit karta hai aur Llama 3.2 briefing add karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'DOWNLOAD OFFICIAL PDF' Button:</b> Generated INSPACE-CAM-2026 legal document ko new browser tab mein download/open karta hai.", bullet_style))

    # ── SECTION 6: AIR-GAPPED AI COPILOT ─────────────────────────────────────
    story.append(Paragraph("6. AI Astrometry Copilot Drawer (Local Llama 3.2 Air-Gapped)", h1_style))
    story.append(Paragraph("&bull; <b>Why 100% Local Ollama (Port 11434)?</b> Defense aur ISRO satellite telemetry confidential hoti hai. Zero cloud leaks guarantee karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>RAG Context Injection:</b> Query se NORAD ID, satellite name, conjunction event, aur Aditya-L1 indices detect karke real-time database context aur UTC timestamp prompt mein inject karta hai.", bullet_style))
    story.append(Paragraph("&bull; <b>'Send Message' &amp; 'Clear Chat Logs' Buttons:</b> Real-time AI stream query execute karta hai aur conversation reset karta hai.", bullet_style))

    # ── SECTION 7: JUDGES Q&A DEFENSE ────────────────────────────────────────
    story.append(Paragraph("7. Judges Top 5 Q&amp;A Defense &amp; Elevator Pitch", h1_style))
    story.append(Paragraph("<b>Q1: 'SGP4 kyun chuna Cowell propagator ki jagah?'</b><br/>"
                           "<i>Ans: SGP4 10,000+ satellites ko real-time mein propagate karne ke liye mathematically fast closed-form solution hai (~1 ms). Critical burn execution ke waqt numerical integrators use hote hain.</i>", body_style))
    story.append(Paragraph("<b>Q2: 'Foster-Elrod 2D algorithm Monte Carlo se better kyun hai?'</b><br/>"
                           "<i>Ans: 3D Monte Carlo mein 1M runs lagte hain (15-30 seconds). Foster-Elrod 2D B-Plane projection aur modified Bessel function I_0 quadrature se exact Pc sirf 2 milliseconds mein nikaal deta hai.</i>", body_style))
    story.append(Paragraph("<b>Q3: 'Aditya-L1 data ka practical use case kya hai?'</b><br/>"
                           "<i>Ans: Solar storm aane par thermosphere 300% expand hoti hai (jaise 2022 mein Starlink ke 40 sats gir gaye the). ORVEXA live CME speed se drag multiplier calculate karke early warning deta hai.</i>", body_style))
    story.append(Paragraph("<b>Q4: 'AI Copilot cloud APIs par depend kyun nahi karta?'</b><br/>"
                           "<i>Ans: Defense data sovereignty compliance ke liye. ORVEXA local Llama 3.2 model par air-gapped run hota hai.</i>", body_style))
    story.append(Paragraph("<b>Q5: '2-Minute Elevator Pitch Summary:'</b><br/>"
                           "<i>'Respected Judges, ORVEXA India ka pehla autonomous Space Situational Awareness platform hai. Hum 3D KD-Tree se real-time close approaches dhoondte hain, Foster-Elrod math se Collision Probability nikaalte hain, Aditya-L1 solar data se atmospheric decay predict karte hain, aur autonomous multi-agent swarm se IN-SPACe regulatory filings automatically generate karte hain with zero cloud data leaks!'</i>", callout_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Ultra-Detailed ORVEXA Handbook at: {pdf_path}")
    
    import shutil
    root_pdf_path = os.path.abspath("ORVEXA_Complete_Project_Handbook_Hinglish.pdf")
    shutil.copyfile(pdf_path, root_pdf_path)
    print(f"Copied to project root at: {root_pdf_path}")
    return root_pdf_path

if __name__ == "__main__":
    create_handbook()
