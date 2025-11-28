"""Document generators - Fixed PDF spacing and Word cover page full-bleed layout"""

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
            align-items: flex-end; /* Align image to bottom */
            padding: 0;
            margin: 0;
        }}

        .partner-banner {{
            width: 100%;
            height: auto;
            display: block;
            margin: 0;
        }}

        /* CONTENT PAGES */
        .content-page {{
            page: content;
        }}

        .question-block {{
            margin-bottom: 40px; /* Increased empty space after answer */
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
        
        # === COVER PAGE ===
        section = doc.sections[0]
        # STRICT ZERO MARGINS to prevent "Box" effect
        section.top_margin = Inches(0)
        section.bottom_margin = Inches(0)
        section.left_margin = Inches(0)
        section.right_margin = Inches(0)
        section.header_distance = Inches(0)
        section.footer_distance = Inches(0)
        
        # Helper to create blue filler paragraphs without white gaps
        def add_blue_para(text="", font_size=11, bold=False, line_height_pt=None):
            p = doc.add_paragraph()
            self._add_blue_background(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Critical: remove spacing to ensure solid color block
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

        # 1. Spacer Top (Solid Blue)
        # Add ~15 empty blue lines to push content down
        for _ in range(12): 
            add_blue_para(line_height_pt=24) # Taller lines fill space faster
        
        # 2. TITLE (Solid Blue)
        add_blue_para(title, font_size=32, bold=True)
        # Small spacer between Title and Topic
        add_blue_para(line_height_pt=12) 
        
        # 3. TOPIC (Solid Blue)
        add_blue_para(topic, font_size=24, bold=False)
        
        # 4. Spacer Bottom (Solid Blue)
        # Push footer to bottom. Adjust range to fill page length.
        for _ in range(10): 
            add_blue_para(line_height_pt=24)
            
        # 5. WHITE FOOTER - Logo Only
        logo_para = doc.add_paragraph()
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Remove all spacing so it fits perfectly
        logo_para.paragraph_format.space_before = Pt(0)
        logo_para.paragraph_format.space_after = Pt(0)
        logo_para.paragraph_format.line_spacing = WD_LINE_SPACING.SINGLE
        
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        if os.path.exists(logo_path):
            try:
                run = logo_para.add_run()
                # Maximize width to fit page (A4 width is approx 8.27in)
                run.add_picture(logo_path, width=Inches(7.5)) 
            except:
                pass

        # === PAGE BREAK ===
        doc.add_page_break()
        
        # === CONTENT PAGES ===
        section = doc.sections[-1]
        # Restore standard margins for content
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.header_distance = Inches(0.5)
        section.footer_distance = Inches(0.5)
        
        for i, qa in enumerate(qa_pairs, 1):
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            
            # Question - 14pt (Requested)
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(f"Question {i}: {question}")
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(14) 
            q_run.font.bold = True
            
            q_para.paragraph_format.line_spacing = 1.15
            q_para.paragraph_format.space_after = Pt(6)
            q_para.paragraph_format.keep_with_next = True
            
            # Answer - 14pt (Requested)
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
            ans_para.paragraph_format.space_after = Pt(24) # Space between pairs
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
