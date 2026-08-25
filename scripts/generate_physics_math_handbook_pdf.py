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
            self.drawString(54, 750, "ORVEXA // ASTRODYNAMICS & PHYSICS HANDBOOK")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(612 - 54, 750, "MATHEMATICAL FORMULATIONS & PHYSICAL MODELS")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, 744, 612 - 54, 744)
            
            # Running Footer
            self.line(54, 45, 612 - 54, 45)
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0D47A1"))
            self.drawString(54, 32, "ORVEXA — CORE ASTRODYNAMICS, SGP4, FOSTER-1992 & SOLAR PHYSICS")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(612 - 54, 32, page_text)
            self.restoreState()


def create_physics_pdf():
    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "ORVEXA_Mathematics_and_Physics_Handbook.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0F172A")    # Deep Navy
    SECONDARY = colors.HexColor("#0369A1")  # Cyan / Blue
    ACCENT = colors.HexColor("#0284C7")     # Sky Blue
    DARK_CODE_BG = colors.HexColor("#0F172A")
    LIGHT_BG = colors.HexColor("#F8FAFC")
    FORMULA_BG = colors.HexColor("#F1F5F9")
    BORDER_COLOR = colors.HexColor("#CBD5E1")

    # Typography
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Header1',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=SECONDARY,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=3
    )

    formula_style = ParagraphStyle(
        'FormulaText',
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#0C4A6E")
    )

    def formula_box(formula_str, explanation=""):
        rows = [[Paragraph(formula_str, formula_style)]]
        if explanation:
            rows.append([Paragraph(explanation, callout_style)])
        t = Table(rows, colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), FORMULA_BG),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94A3B8")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        return t

    story = []

    # ── TITLE & OVERVIEW ───────────────────────────────────────────────────
    story.append(Paragraph("ORVEXA: MATHEMATICS & PHYSICS SPECIFICATION", title_style))
    story.append(Paragraph("A Complete Guide to Astrodynamics, Perturbations, Collision Radar & Solar Flux Physics", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=10))

    intro_text = """
    <b>EXECUTIVE SUMMARY:</b> ORVEXA is engineered upon rigorous orbital mechanics, perturbation analysis, 
    stochastic conjunction assessment, and upper-atmospheric thermodynamic modeling. This handbook provides the 
    exact governing differential equations, analytical models, and matrix transformations implemented in the codebase.
    """
    story.append(formula_box(intro_text))
    story.append(Spacer(1, 10))

    # ── 1. TWO-BODY ORBITAL MECHANICS & KEPLER'S LAWS ───────────────────────
    story.append(Paragraph("1. Classical Two-Body Orbital Mechanics & Vis-Viva Equation", h1_style))
    story.append(Paragraph(
        "Under Newtonian gravity, the unperturbed motion of a satellite of mass <i>m</i> orbiting Earth (mass <i>M</i>, where <i>M >> m</i>) is governed by:",
        body_style
    ))
    story.append(formula_box(
        "r''(t) + (μ / ||r||³) · r = 0",
        "where μ = G·M_Earth = 3.986004418 × 10¹⁴ m³/s² (Earth's Standard Gravitational Parameter)."
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Key Orbital Conservation Laws & State Equations:", h2_style))
    story.append(Paragraph("• <b>Specific Mechanical Energy (ε):</b> ε = (v² / 2) - (μ / r) = - μ / (2a)", bullet_style))
    story.append(Paragraph("• <b>Vis-Viva Orbital Velocity:</b> v = √[ μ · (2/r - 1/a) ]", bullet_style))
    story.append(Paragraph("• <b>Orbital Period (T):</b> T = 2π · √(a³ / μ)", bullet_style))
    story.append(Paragraph("• <b>Kepler's Equation (Mean to Eccentric Anomaly):</b> M = E - e · sin(E)", bullet_style))
    story.append(Paragraph("Solved in ORVEXA via Newton-Raphson iteration: E_{k+1} = E_k - (E_k - e·sin(E_k) - M) / (1 - e·cos(E_k)).", body_style))
    story.append(Spacer(1, 8))

    # ── 2. SGP4 ORBITAL PROPAGATION & EARTH OBLATENESS ─────────────────────
    story.append(Paragraph("2. SGP4 Propagator & Geopotential Perturbations (J₂, J₃, J₄)", h1_style))
    story.append(Paragraph(
        "Earth is an oblate spheroid. ORVEXA utilizes the <b>SGP4 (Simplified General Perturbations-4)</b> analytical propagator to model gravitational zonal harmonics and secular orbital drifts:",
        body_style
    ))

    story.append(formula_box(
        "V(r, φ) = - (μ / r) · [ 1 - ∑_{n=2}^{4} J_n · (R_E / r)ⁿ · P_n(sin φ) ]",
        "where R_E = 6378.137 km (WGS84 Earth Radius), J₂ = 1.08263 × 10⁻³ (Oblateness), J₃ = -2.53266 × 10⁻⁶, J₄ = -1.61962 × 10⁻⁶."
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Key Secular Drift Rates Implemented in SGP4:", h2_style))
    story.append(Paragraph("• <b>Right Ascension of Ascending Node Precession (Ω'):</b><br/>"
                           "Ω' = - (3/2) · J₂ · (R_E / p)² · n · cos(i)", bullet_style))
    story.append(Paragraph("• <b>Argument of Perigee Drift (ω'):</b><br/>"
                           "ω' = (3/4) · J₂ · (R_E / p)² · n · (5·cos²(i) - 1)", bullet_style))
    story.append(Paragraph("• <b>Atmospheric Drag Ballistic Term (B*):</b><br/>"
                           "B* = (1/2) · (C_D · A / m) · ρ₀ (Incorporated into Mean Motion drift n' and n'').", bullet_style))
    story.append(Spacer(1, 8))

    # ── 3. FOSTER (1992) CONJUNCTION ASSESSMENT & B-PLANE RADAR ─────────────
    story.append(Paragraph("3. Conjunction Assessment & Foster (1992) Collision Probability (P_c)", h1_style))
    story.append(Paragraph(
        "When two orbital objects reach a close approach, ORVEXA computes the <b>Time of Closest Approach (TCA)</b> and integrates the 2D collision probability on the encounter B-Plane:",
        body_style
    ))

    story.append(formula_box(
        "t_{TCA} = t₀ - [ (r_rel · v_rel) / ||v_rel||² ]\n"
        "d_{min} = || r_rel(t_{TCA}) || = || (r₂ - r₁) - [ (r_rel · v_rel)/||v_rel||² ] · v_rel ||",
        "where r_rel = r₂ - r₁ is relative position and v_rel = v₂ - v₁ is relative velocity vector."
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Foster (1992) B-Plane Projection & 2D Covariance Integration:", h2_style))
    story.append(Paragraph(
        "1. Construct encounter frame with unit vector k along v_rel, ξ orthogonal in orbital plane, and ζ = k × ξ.<br/>"
        "2. Combine position error covariance matrices: <b>C = C₁ + C₂</b>.<br/>"
        "3. Project 3D covariance onto 2D B-plane: <b>C₂_D = P · C · Pᵀ</b>, yielding primary dispersion axes (σ_x, σ_y) and correlation ρ.<br/>"
        "4. Integrate 2D Gaussian probability density over the combined hard-body radius <b>R = R_primary + R_secondary</b>:",
        body_style
    ))

    story.append(formula_box(
        "P_c = (1 / [2π σ_x σ_y √(1-ρ²)]) ∬_{Circle(R)} exp{ - [1/(2(1-ρ²))] · [ (x - x_e)²/σ_x² - 2ρ(x-x_e)(y-y_e)/(σ_x σ_y) + (y-y_e)²/σ_y² ] } dx dy",
        "Foster-1992 2D Probability of Collision Integral (Implemented in backend/services/foster_algorithm.py)"
    ))
    story.append(Spacer(1, 8))

    # ── 4. ATMOSPHERIC DRAG & ADITYA-L1 SOLAR WEATHER COUPLING ──────────────
    story.append(Paragraph("4. Atmospheric Drag, Thermospheric Expansion & Solar Weather", h1_style))
    story.append(Paragraph(
        "In Low Earth Orbit (LEO, 160–2000 km), aerodynamic drag is the dominant orbital decay mechanism. The aerodynamic drag force vector is:",
        body_style
    ))

    story.append(formula_box(
        "F_drag = - (1/2) · ρ(h) · v_{rel}² · C_D · A · v_hat\n"
        "da/dt = - 2π · [ (ρ · a²) / B ] · √(μ · a)",
        "where B = m / (C_D · A) is the satellite Ballistic Coefficient (kg/m²)."
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Aditya-L1 & NOAA Dynamic Thermospheric Density Scaling:", h2_style))
    story.append(Paragraph(
        "Solar extreme ultraviolet (EUV) radiation and coronal mass ejections (CMEs) heat and expand the thermosphere. ORVEXA dynamically scales exponential scale-height density ρ₀(h) using live solar indices:",
        body_style
    ))
    story.append(formula_box(
        "ρ_eff(h, F_{10.7}, A_p) = ρ₀(h) · [ 1 + α · (F_{10.7} - 70.0)/80.0 + β · (A_p - 7.0)/15.0 ]",
        "where F_{10.7} is 10.7cm Solar Radio Flux (sfu), A_p is Planetary Geomagnetic Amplitude Index, α=1.0, β=0.6."
    ))
    story.append(Spacer(1, 8))

    # ── 5. IMPULSIVE COLLISION AVOIDANCE MANEUVER PHYSICS ───────────────────
    story.append(Paragraph("5. Collision Avoidance Maneuver (CAM) & Fuel Consumption", h1_style))
    story.append(Paragraph(
        "To mitigate an impending conjunction (P_c > 10⁻⁴), ORVEXA calculates the minimal impulsive along-track burn (ΔV) required to achieve a safe separation distance Δr at TCA (Δt seconds ahead):",
        body_style
    ))
    story.append(formula_box(
        "ΔV_{along-track} ≈ (n · Δr) / [ 4 · sin(n · Δt / 2) ]\n"
        "Δm_{propellant} = m₀ · [ 1 - exp( - ΔV / (I_{sp} · g₀) ) ]",
        "Tsiolkovsky Rocket Equation, where I_sp is specific impulse (e.g. 220s for monopropellant hydrazine) and g₀ = 9.80665 m/s²."
    ))
    story.append(Spacer(1, 8))

    # ── 6. UN COPUOS 5-YEAR LIFETIME COMPLIANCE MATH ────────────────────────
    story.append(Paragraph("6. UN COPUOS & IN-SPACe 5-Year Orbital Lifetime Model", h1_style))
    story.append(Paragraph(
        "ORVEXA evaluates post-mission disposal compliance using the King-Hele analytical orbital decay lifetime formulation:",
        body_style
    ))
    story.append(formula_box(
        "L ≈ (H · m) / [ ρ_{perigee} · C_D · A · √(2π · a · e · μ) ]\n"
        "Compliance Rule: If L ≤ 5.0 Years -> STATUS: COMPLIANT [PASS]",
        "where H is the local density scale height at perigee altitude."
    ))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {pdf_path}")
    return pdf_path

if __name__ == '__main__':
    create_physics_pdf()
