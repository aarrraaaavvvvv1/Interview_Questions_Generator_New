from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from typing import Dict
from datetime import datetime
import os
import re
from config import PDF_MARGIN_INCH

class PDFGenerator:
    """Generates formatted PDF documents for interview questions with safe wrapping."""

    def __init__(self):
        self.page_size = letter
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='TitleBig', fontSize=18, leading=22, spaceAfter=12))
        self.styles.add(ParagraphStyle(name='SectionHeader', fontSize=13, leading=16, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor('#222222')))
        self.styles.add(ParagraphStyle(name='Body', fontSize=10.5, leading=14, alignment=TA_LEFT))
        self.styles.add(ParagraphStyle(name='Mono', fontName='Courier', fontSize=9, leading=12))
        self.styles.add(ParagraphStyle(name='Meta', fontSize=8.5, leading=11, textColor=colors.grey))

    def _sanitize(self, text: str) -> str:
        if not text: 
            return ""
        text = re.sub(r'<[^>]+>', '', str(text))  # strip HTML tags
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return text

    def _para(self, text: str, style='Body'):
        return Paragraph(self._sanitize(text), self.styles[style])

    def _pref(self, code: str):
        safe = self._sanitize(code)
        # Preformatted ensures monospace and preserves newlines
        return Preformatted(safe, self.styles['Mono'], maxLineLength=110)

    def generate(self, data: Dict, filename: str = None) -> str:
        os.makedirs('generated_pdfs', exist_ok=True)
        topic = data.get('topic', 'Interview')
        filename = filename or f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join('generated_pdfs', filename)

        doc = SimpleDocTemplate(
            path, pagesize=self.page_size,
            leftMargin=PDF_MARGIN_INCH*inch, rightMargin=PDF_MARGIN_INCH*inch,
            topMargin=PDF_MARGIN_INCH*inch, bottomMargin=PDF_MARGIN_INCH*inch
        )

        elements = []
        # Title
        elements.append(self._para(f"Interview Questions: {topic}", 'TitleBig'))
        meta = f"Difficulty: {data.get('difficulty','-')} | Types: {', '.join(data.get('question_types', []))} | Total: {data.get('total_questions', 0)}"
        elements.append(self._para(meta, 'Meta'))
        elements.append(Spacer(1, 0.2*inch))

        # Context
        ctx = data.get('context') or []
        if ctx:
            elements.append(self._para("Context", 'SectionHeader'))
            for c in ctx:
                elements.append(self._para(f"• {c}"))
            elements.append(Spacer(1, 0.15*inch))

        # Questions
        qlist = data.get('questions') or []
        for i, q in enumerate(qlist, start=1):
            elements.append(self._para(f"Q{i}. {q.get('text','')}", 'SectionHeader'))
            qtype = q.get('type', '')
            elements.append(self._para(f"Type: {qtype} | Difficulty: {q.get('difficulty','-')} | {'Generic' if q.get('is_generic') else 'Practical'}", 'Meta'))

            if qtype == 'mcq' and isinstance(q.get('options'), list):
                for idx, opt in enumerate(q['options'], start=1):
                    mark = ' (✔)' if opt.get('is_correct') else ''
                    elements.append(self._para(f"{idx}. {opt.get('option','')}{mark}"))
                if q.get('explanation'):
                    elements.append(self._para(f"Explanation: {q.get('explanation','')}"))
            elif qtype == 'coding' and q.get('code'):
                elements.append(self._para("Solution:", 'Meta'))
                elements.append(self._pref(q.get('code','')))
            if q.get('answer') and qtype != 'mcq':
                elements.append(self._para(f"Answer: {q.get('answer','')}"))
            if q.get('explanation') and qtype != 'mcq':
                elements.append(self._para(f"Explanation: {q.get('explanation','')}"))

            elements.append(Spacer(1, 0.12*inch))

            # Page breaks occasionally for large sets
            if i % 10 == 0:
                elements.append(PageBreak())

        # Footer
        elements.append(Spacer(1, 0.2*inch))
        footer = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Questions: {len(qlist)}"
        elements.append(self._para(footer, 'Meta'))

        doc.build(elements)
        return path
