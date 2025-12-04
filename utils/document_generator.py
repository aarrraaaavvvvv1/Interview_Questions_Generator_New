"""Document generators - Fixed Word vertical filling and logo sizing"""

from io import BytesIO
from typing import List, Dict
import os

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from utils.company_template import PARTNER_LOGO_URLS, PARTNER_LOGOS

def get_cover_page_html(title: str, topic: str, partner_institute: str) -> str:
    logo_url = PARTNER_LOGO_URLS.get(partner_institute, PARTNER_LOGO_URLS["Default"])
    return f"""
    <div class="cover-page">
        <div class="cover-main">
            <div class="cover-content">
                <h1 class="cover-title">{title}</h1>
                <h2 class="cover-topic">{topic}</h2>
            </div>
        </div>
        <div class="cover-footer">
            <img src="{logo_url}" class="partner-banner" alt="{partner_institute}">
        </div>
    </div>
    """

class PDFGenerator:
    def __init__(self, title: str, topic: str, partner_institute: str = "IIT Kanpur"):
        self.title = title
        self.topic = topic
        self.partner_institute = partner_institute

    def generate(self, qa_pairs: List[Dict]) -> bytes:
        if not WEASYPRINT_AVAILABLE:
            raise Exception("WeasyPrint not available")

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page cover {{
            size: A4;
            margin: 0;
        }}
        
        @page content {{
            size: A4;
            margin: 25.4mm;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: Calibri, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #000000;
        }}
        
        /* COVER PAGE */
        .cover-page {{
            page: cover;
            height: 297mm;
            width: 210mm;
            display: flex;
            flex-direction: column;
            margin: 0;
            padding: 0;
        }}
        
        .cover-main {{
            background-color: #3030ff;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
        }}

        .cover-content {{
            width: 80%;
            text-align: center;
        }}

        .cover-title {{
            font-size: 32pt;
            font-weight: bold;
            color: #FFFFFF;
            margin: 0 0 30px 0;
            line-height: 1.2;
        }}
        
        .cover-topic {{
            font-size: 24pt;
            font-weight: normal;
            color: #FFFFFF;
            margin: 0;
            line-height: 1.2;
        }}

        .cover-footer {{
            height: auto;
            background-color: #FFFFFF;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: flex-end;
            padding: 0;
            margin: 0;
        }}

        /* 50% size banner for PDF */
        .partner-banner {{
            max-width: 50%;
            height: auto;
            display: block;
            margin: 0 auto;
        }}

        /* CONTENT PAGES */
        .content-page {{
            page: content;
        }}

        .question-block {{
            margin-bottom: 40px;
            page-break-inside: avoid;
        }}

        .question-header {{
            font-size: 11pt;
            font-weight: bold;
            margin-bottom: 5px;
            color: #000000;
            text-align: justify;
        }}

        .answer-header {{
            font-size: 11pt;
            font-weight: bold;
            color: #000000;
        }}

        .answer-text {{
            font-size: 11pt;
            text-align: justify;
            line-height: 1.5;
            color: #000000;
        }}
    </style>
</head>
<body>
{get_cover_page_html(self.title, self.topic, self.partner_institute)}
<div class="content-page">
"""
        for i, qa in enumerate(qa_pairs, 1):
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            html_content += f"""
<div class="question-block">
    <div class="question-header">Question {i}: {question}</div>
    <span class="answer-header">Answer: </span><span class="answer-text">{answer}</span>
</div>
"""
        html_content += """
</div>
</body>
</html>"""
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes

class WordDocumentGenerator:
    def __init__(self):
        pass

    def _add_blue_background(self, paragraph):
        """Add royal blue #3030ff background to paragraph"""
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), '3030FF')
        paragraph._element.get_or_add_pPr().append(shading_elm)

    def generate(self, qa_pairs: List[Dict], title: str, topic: str, partner_institute: str = "IIT Kanpur") -> bytes:
        doc = Document()

        # === SECTION 1: COVER PAGE ===
        section_cover = doc.sections[0]
        section_cover.top_margin = Inches(0)
        section_cover.bottom_margin = Inches(0)
        section_cover.left_margin = Inches(0)
        section_cover.right_margin = Inches(0)
        section_cover.header_distance = Inches(0)
        section_cover.footer_distance = Inches(0)

        # Helper to create blue filler paragraphs
        def add_blue_para(text="", font_size=11, bold=False, line_height_pt=None):
            p = doc.add_paragraph()
            self._add_blue_background(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            if line_height_pt:
                p.paragraph_format.line_spacing = Pt(line_height_pt)
            if text:
                run = p.add_run(text)
                run.font.name = 'Calibri'
                run.font.size = Pt(font_size)
                run.font.bold = bold
                run.font.color.rgb = RGBColor(255, 255, 255)
            return p

        # 1. Spacer Top (~4 inches)
        for _ in range(9): 
            add_blue_para(line_height_pt=36)

        # 2. TITLE
        add_blue_para(title, font_size=32, bold=True)
        add_blue_para(line_height_pt=12) 

        # 3. TOPIC
        add_blue_para(topic, font_size=24, bold=False)

        # 4. Spacer Bottom (~4.5 inches)
        for _ in range(9): 
            add_blue_para(line_height_pt=36)

        # 5. WHITE FOOTER - Logo Only
        logo_para = doc.add_paragraph()
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        logo_para.paragraph_format.space_before = Pt(0)
        logo_para.paragraph_format.space_after = Pt(0)
        logo_para.paragraph_format.line_spacing = WD_LINE_SPACING.SINGLE

        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        if os.path.exists(logo_path):
            try:
                run = logo_para.add_run()
                # A4 width is ~8.27in. Previously ~full width; now 50%.
                run.add_picture(logo_path, width=Inches(4.1))  # ~half page width
            except:
                pass

        # === SECTION 2: CONTENT ===
        section_content = doc.add_section(WD_SECTION.NEW_PAGE)

        section_content.top_margin = Inches(1)
        section_content.bottom_margin = Inches(1)
        section_content.left_margin = Inches(1)
        section_content.right_margin = Inches(1)
        section_content.header_distance = Inches(0.5)
        section_content.footer_distance = Inches(0.5)

        for i, qa in enumerate(qa_pairs, 1):
            question = qa.get('question', '')
            answer = qa.get('answer', '')

            # Question
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(f"Question {i}: {question}")
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(14) 
            q_run.font.bold = True

            q_para.paragraph_format.line_spacing = 1.15
            q_para.paragraph_format.space_after = Pt(6)
            q_para.paragraph_format.keep_with_next = True

            # Answer
            ans_para = doc.add_paragraph()
            ans_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            ans_header_run = ans_para.add_run("Answer: ")
            ans_header_run.font.name = 'Calibri'
            ans_header_run.font.size = Pt(14)
            ans_header_run.font.bold = True

            ans_run = ans_para.add_run(answer)
            ans_run.font.name = 'Calibri'
            ans_run.font.size = Pt(14)
            ans_run.font.bold = False

            ans_para.paragraph_format.line_spacing = 1.15
            ans_para.paragraph_format.space_after = Pt(24)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
