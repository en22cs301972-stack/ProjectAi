import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.flowables import HRFlowable
import structlog

logger = structlog.get_logger()

CERTIFICATES_DIR = Path("certificates")
CERTIFICATES_DIR.mkdir(exist_ok=True)


def generate_certificate(
    user_name: str,
    course_title: str,
    completion_date: datetime,
    certificate_number: str,
) -> Optional[str]:
    """Generate a PDF certificate for course completion."""
    try:
        filename = f"certificate_{certificate_number}.pdf"
        filepath = CERTIFICATES_DIR / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=landscape(A4),
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CertTitle",
            parent=styles["Title"],
            fontSize=42,
            textColor=colors.HexColor("#1a1a2e"),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName="Helvetica-Bold",
        )

        subtitle_style = ParagraphStyle(
            "CertSubtitle",
            parent=styles["Normal"],
            fontSize=18,
            textColor=colors.HexColor("#16213e"),
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName="Helvetica",
        )

        name_style = ParagraphStyle(
            "RecipientName",
            parent=styles["Normal"],
            fontSize=32,
            textColor=colors.HexColor("#0f3460"),
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=10,
            fontName="Helvetica-BoldOblique",
        )

        course_style = ParagraphStyle(
            "CourseName",
            parent=styles["Normal"],
            fontSize=20,
            textColor=colors.HexColor("#e94560"),
            alignment=TA_CENTER,
            spaceBefore=5,
            spaceAfter=15,
            fontName="Helvetica-Bold",
        )

        detail_style = ParagraphStyle(
            "Detail",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
            spaceAfter=5,
        )

        cert_num_style = ParagraphStyle(
            "CertNumber",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#999999"),
            alignment=TA_CENTER,
        )

        story = []

        # Certificate Header
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("🎓 Certificate of Completion", title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#e94560")))
        story.append(Spacer(1, 0.3 * inch))

        # Body
        story.append(Paragraph("This is to certify that", subtitle_style))
        story.append(Paragraph(user_name, name_style))
        story.append(Paragraph("has successfully completed the course", subtitle_style))
        story.append(Paragraph(course_title, course_style))

        story.append(Spacer(1, 0.2 * inch))
        story.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.2 * inch))

        # Details
        story.append(Paragraph(
            f"Date of Completion: {completion_date.strftime('%B %d, %Y')}",
            detail_style
        ))
        story.append(Paragraph(
            f"Certificate ID: {certificate_number}",
            cert_num_style
        ))

        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("AI-Powered Learning Platform", subtitle_style))

        doc.build(story)
        logger.info("Certificate generated", path=str(filepath))
        return str(filepath)

    except Exception as e:
        logger.error("Certificate generation failed", error=str(e))
        return None
