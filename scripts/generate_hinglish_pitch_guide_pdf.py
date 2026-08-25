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
            self.saveState()
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0F172A"))
            self.drawString(54, 750, "ORVEXA // SIH JUDGE PITCH & EXPLANATION GUIDE")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(612 - 54, 750, "MATHEMATICS & PHYSICS IN HINGLISH")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, 744, 612 - 54, 744)
            
            self.line(54, 45, 612 - 54, 45)
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0D47A1"))
            self.drawString(54, 32, "ORVEXA — HOW TO EXPLAIN MATH & PHYSICS TO JUDGES")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(612 - 54, 32, page_text)
            self.restoreState()


def create_hinglish_pdf():
    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "ORVEXA_Judge_Pitch_Hinglish_Guide.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0F172A")
    SECONDARY = colors.HexColor("#0369A1")
    FORMULA_BG = colors.HexColor("#F8FAFC")
    BORDER_COLOR = colors.HexColor("#CBD5E1")
    DIALOGUE_BG = colors.HexColor("#EFF6FF")

    title_style = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=PRIMARY, spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubtitle', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=SECONDARY, spaceAfter=12)
    h1_style = ParagraphStyle('Header1', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=PRIMARY, spaceBefore=12, spaceAfter=6, keepWithNext=True)
    body_style = ParagraphStyle('BodyDark', fontName='Helvetica', fontSize=8.5, leading=12.5, textColor=colors.HexColor("#334155"), spaceAfter=5)
    bullet_style = ParagraphStyle('BulletText', fontName='Helvetica', fontSize=8, leading=12, textColor=colors.HexColor("#334155"), leftIndent=10, firstLineIndent=-6, spaceAfter=3)

    dialogue_style = ParagraphStyle('DialogueText', fontName='Helvetica-Oblique', fontSize=8.5, leading=12.5, textColor=colors.HexColor("#1E3A8A"))

    def dialogue_box(text):
        t = Table([[Paragraph(text, dialogue_style)]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DIALOGUE_BG),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        return t

    story = []

    story.append(Paragraph("ORVEXA: HOW TO EXPLAIN MATH & PHYSICS TO JUDGES", title_style))
    story.append(Paragraph("Complete Hinglish Dialogue Script & Technical Q&A for SIH / Hackathon / Viva", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=10))

    # Intro Pitch
    story.append(Paragraph("1. Opening Hook: Judges ka Dhyan Kaise Grab Karein", h1_style))
    story.append(dialogue_box(
        "<b>Aapko bolna hai:</b><br/>"
        "\"Good morning / afternoon Judges! Space me satellites <b>7.8 km/s (yaani 28,000 km/h)</b> ki hyper-velocity par travel karti hain. "
        "Is kinetic speed par ek 1 cm ka chhota sa space debris bullet se 10 guna zyada impact karta hai aur poori satellite ko destroy kar sakta hai.<br/>"
        "ORVEXA koi basic 3D simulation ya dummy animation nahi hai — iske peeche <b>Orbital Mechanics, SGP4 Perturbations, Foster (1992) B-Plane Probability, aur Aditya-L1 Solar Weather Physics</b> ka real-time engine chal raha hai.\""
    ))
    story.append(Spacer(1, 8))

    # Concept 1: SGP4 & J2
    story.append(Paragraph("2. Concept 1: SGP4 Propagator aur Earth Oblateness (J2 Perturbation)", h1_style))
    story.append(Paragraph("<b>Judges ka typical question:</b> <i>\"Aap satellite ki position kaise calculate kar rahe ho?\"</i>", body_style))
    story.append(dialogue_box(
        "<b>Aapko explain karna hai:</b><br/>"
        "\"Sir, standard Physics me hum Earth ko perfect sphere maante hain (Keplerian two-body problem). Lekin real life me Earth equator par thodi phooli hui hai (oblate spheroid). Is gravitational asymmetry ko hum <b>J2 Zonal Harmonic (J₂ = 1.08263 × 10⁻³)</b> bolte hain.<br/><br/>"
        "Is J2 bulge ki wajah se do major gravitational perturbations aate hain:<br/>"
        "1. <b>Nodal Precession (Ω'):</b> Satellite ka orbit plane space me dheere-dheere rotate hota hai.<br/>"
        "2. <b>Apsidal Precession (ω'):</b> Perigee (closest point) orbit me drift karta hai.<br/><br/>"
        "Hum <b>SGP4 (Simplified General Perturbations-4)</b> analytical propagator use karte hain jo TLE data se J2, J3, J4 aur atmospheric drag parameter (B*) ko integrate karke har second exact 3D Cartesian (TEME/ECEF) coordinates nikalta hai.\""
    ))
    story.append(Spacer(1, 8))

    # Concept 2: Foster 1992
    story.append(Paragraph("3. Concept 2: Conjunction Assessment aur Foster (1992) Collision Probability", h1_style))
    story.append(Paragraph("<b>Judges ka typical question:</b> <i>\"Do satellite pass aane par collision kaise detect hota hai?\"</i>", body_style))
    story.append(dialogue_box(
        "<b>Aapko explain karna hai:</b><br/>"
        "\"Sir, amateur systems sirf Euclidean distance (e.g. < 5km) dekh kar false alarm dete hain. Lekin radar tracking me <b>position uncertainty</b> hoti hai, jise hum 3D Covariance Ellipsoid kehte hain.<br/><br/>"
        "ORVEXA me hum <b>Foster (1992) Algorithm</b> implement karte hain:<br/>"
        "1. Pehle hum <b>Time of Closest Approach (TCA)</b> nikalte hain relative velocity vector (v_rel) use karke.<br/>"
        "2. Dono satellites ke 3D uncertainty covariance matrices (C₁ + C₂) ko combine karke 2D encounter plane (<b>B-Plane</b>) par project karte hain.<br/>"
        "3. Phir dono satellites ke combined hard-body radius (cross-section area) ke upar <b>2D Gaussian Probability Integral</b> solve karte hain.<br/>"
        "Agar Probability of Collision <b>P_c > 10⁻⁴ (0.01%)</b> hoti hai, tabhi system Critical Conjunction Alert trigger karta hai — zero false alarms ke saath!\""
    ))
    story.append(Spacer(1, 8))

    # Concept 3: Reentry & Solar Weather
    story.append(Paragraph("4. Concept 3: Atmospheric Drag aur Aditya-L1 Solar Weather Physics", h1_style))
    story.append(Paragraph("<b>Judges ka typical question:</b> <i>\"Aapka space weather solar storm simulation me kya physics hai?\"</i>", body_style))
    story.append(dialogue_box(
        "<b>Aapko explain karna hai:</b><br/>"
        "\"Sir, LEO satellites (200-1000 km) par main opposing force <b>Aerodynamic Drag Force: F_d = ½ · ρ · v² · C_D · A</b> hoti hai.<br/><br/>"
        "Sabse badi problem ye hai ki upper atmosphere (Thermosphere) ki density (ρ) constant nahi rehti! Jab Sun par solar flare ya Coronal Mass Ejection (CME) aati hai, to extreme UV radiation thermosphere ko heat karke <b>expand</b> kar deti hai.<br/><br/>"
        "ORVEXA India ke <b>Aditya-L1</b> aur NOAA se real-time <b>F10.7 Solar Radio Flux</b> aur <b>Ap Geomagnetic Index</b> ingest karta hai. Agar Solar storm aati hai, to density scaling factor ×3 ho jata hai, jisse satellite ka orbital decay rate instantly spike karta hai. Hum isse exact ground impact corridor predict karte hain.\""
    ))
    story.append(Spacer(1, 8))

    # Concept 4: CAM & Rocket Equation
    story.append(Paragraph("5. Concept 4: Collision Avoidance Maneuver (CAM) & Fuel Calculation", h1_style))
    story.append(Paragraph("<b>Judges ka typical question:</b> <i>\"Collision avoid karne ke liye system kya recommend karta hai?\"</i>", body_style))
    story.append(dialogue_box(
        "<b>Aapko explain karna hai:</b><br/>"
        "\"Sir, agar collision predict ho jaye, to satellite ko blind thrust nahi de sakte kyunki fuel bohot limited hota hai. ORVEXA <b>Vis-Viva equation</b> use karke minimal along-track velocity change (ΔV ≈ 0.5 to 2 m/s) calculate karta hai.<br/>"
        "Aur <b>Tsiolkovsky Rocket Equation: Δm = m₀ [ 1 - exp(-ΔV / (I_sp · g₀)) ]</b> se operator ko exact propellant mass (e.g. 48 grams of Hydrazine) batata hai taaki satellite safely dodge bhi ho jaye aur fuel bhi waste na ho.\""
    ))
    story.append(Spacer(1, 8))

    # Concept 5: UN COPUOS 5-Year Rule
    story.append(Paragraph("6. Concept 5: UN COPUOS 5-Year Post-Mission Disposal Rule", h1_style))
    story.append(Paragraph("<b>Judges ka typical question:</b> <i>\"Compliance panel kya verify karta hai?\"</i>", body_style))
    story.append(dialogue_box(
        "<b>Aapko explain karna hai:</b><br/>"
        "\"Sir, UN COPUOS aur FCC ka naya international guideline hai ki har satellite ko mission end hone ke <b>5 saal ke andar naturally de-orbit</b> hona hoga taaki Kessler Syndrome na bane.<br/>"
        "Hum <b>King-Hele analytical lifetime decay equation</b> se satellite ka remaining lifetime estimate karte hain. Agar Lifetime ≤ 5 Years hai to Pass, warna Fail — aur IN-SPACe licensing ke liye instant official PDF audit report generate ho jati hai!\""
    ))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {pdf_path}")
    return pdf_path

if __name__ == '__main__':
    create_hinglish_pdf()
