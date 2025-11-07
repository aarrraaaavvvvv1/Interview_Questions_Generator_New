# PDF generator with lazy reportlab import and clear error messages

from typing import Dict
from datetime import datetime
import os
import re

# Attempt to import reportlab lazily
_reportlab_ok = True
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors
except Exception:
    _reportlab_ok = False

from config import PDF_MARGIN_INCH

def _ensure_reportlab():
    if not _reportlab_ok:
        raise ImportError("reportlab is not installed. Install it with `pip install reportlab` to generate PDFs.")

class PDFGenerator:
    """Generates formatted PDF documents for interview questions with safe wrapping."""

    def __init__(self, output_dir: str = ".", margin_inch: float = PDF_MARGIN_INCH):
        self.output_dir = output_dir or "."
        self.margin_inch = margin_inch

    def _para(self, text: str, style_name: str = "Body"):
        _ensure_reportlab()
        styles = getSampleStyleSheet()
        if style_name == "Title":
            return Paragraph(text, styles["Title"])
        if style_name == "Heading":
            return Paragraph(text, styles["Heading2"])
        if style_name == "Meta":
            return Paragraph(text, ParagraphStyle("meta", parent=styles["Normal"], fontSize=8))
        return Paragraph(text, styles["BodyText"])

    def generate(self, generation_payload: Dict, filename: str = None) -> str:
        """
        generation_payload should be a dict with:
          - topic
          - questions: list of questions (each a dict with type, text, options, etc.)
        Returns path to generated PDF.
        """
        _ensure_reportlab()

        qlist = generation_payload.get("questions", [])
        topic = generation_payload.get("topic", "Interview Questions")
        safe_name = (filename or f"{topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        # sanitize simple
        safe_name = re.sub(r'[<>:"/\\|?*]', "", safe_name).replace(" ", "_")[:255]
        path = os.path.join(self.output_dir, safe_name + ".pdf")

        doc = SimpleDocTemplate(path, pagesize=letter,
                                leftMargin=self.margin_inch * inch,
                                rightMargin=self.margin_inch * inch,
                                topMargin=self.margin_inch * inch,
                                bottomMargin=self.margin_inch * inch)

        elements = []
        elements.append(self._para(f"{topic}", "Title"))
        elements.append(Spacer(1, 0.12 * inch))
        meta = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elements.append(self._para(meta, "Meta"))
        elements.append(Spacer(1, 0.2 * inch))

        for i, q in enumerate(qlist, start=1):
            qtext = f"{i}. ({q.get('type','')}) {q.get('text','')}"
            elements.append(self._para(qtext, "Heading"))
            elements.append(Spacer(1, 0.06 * inch))

            if q.get("type") == "mcq" and q.get("options"):
                # table of options
                rows = []
                for opt in q.get("options", []):
                    label = opt.get("option", "")
                    rows.append([label])
                t = Table(rows, hAlign="LEFT")
                t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 6),
                                       ("TOPPADDING", (0, 0), (-1, -1), 2)]))
                elements.append(t)
            else:
                # free text / code / answer
                if q.get("code"):
                    elements.append(Preformatted(q.get("code", ""), getSampleStyleSheet()["Code"]))
                if q.get("answer"):
                    elements.append(self._para("Answer: " + str(q.get("answer")), "Body"))
            elements.append(Spacer(1, 0.12 * inch))

            # Page breaks occasionally for large sets
            if i % 10 == 0:
                elements.append(PageBreak())

        elements.append(Spacer(1, 0.2 * inch))
        footer = f"Total Questions: {len(qlist)}"
        elements.append(self._para(footer, "Meta"))

        doc.build(elements)
        return path
