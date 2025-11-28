"""Document generators - Fixed formatting and standardized font sizes"""

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
            <div class="footer-logo-wrapper">
                <img src="{logo_url}" class="partner-banner" alt="{partner_institute}">
            </div>
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
            margin: 25.4mm 25.4mm 25.4mm 25.4mm; /* Standard 1 inch margins */
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: Calibri, sans-serif;
            font-size: 11pt; /* Reduced from 14pt */
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
            justify-content: flex-end;
            page-break-after: always;
        }}
        
        .cover-main {{
            background-color: #3030ff;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 85%;
            padding: 0;
        }}
        .cover-content {{
            width: 80%;
            text-align: center;
        }}
        .cover-title {{
            font-size: 24pt; /* Reduced from 27pt */
            font-weight: bold;
            color: #FFFFFF;
            margin: 0 0 20px 0;
            line-height: 1.2;
        }}
        
        .cover-topic {{
            font-size: 18pt; /* Reduced from 27pt for hierarchy */
            font-weight: normal;
            color: #FFFFFF;
            margin: 0;
            line-height: 1.2;
        }}
        .cover-footer {{
            height: 15%;
            background: #FFF;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px 0;
        }}
        .partner-banner {{
            max-width: 80%;
            max-height: 80px;
            height: auto;
            width: auto;
        }}

        /* CONTENT PAGES */
        .content-page {{
            page: content;
        }}

        .question-block {{
            margin-bottom: 20px;
            page-break-inside: avoid; /* Prevents splitting Q and A across pages */
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
            font-size: 11pt; /* Reduced from 14pt */
            text-align: justify;
            line-height: 1.5;
            color: #000000;
            display: inline;
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
        section.top_margin = Inches(0)
        section.bottom_margin = Inches(0)
        section.left_margin = Inches(0)
        section.right_margin = Inches(0)
        
        # Spacing adjustment for cover page
        # Using fewer, specifically sized paragraphs to be more robust
        for _ in range(10):
            para = doc.add_paragraph()
            self._add_blue_background(para)
        
        # TITLE
        title_para = doc.add_paragraph()
        self._add_blue_background(title_para)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.name = 'Calibri'
        title_run.font.size = Pt(24) # Reduced
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(255, 255, 255)
        title_para.paragraph_format.space_after = Pt(12)
        
        # TOPIC
        topic_para = doc.add_paragraph()
        self._add_blue_background(topic_para)
        topic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        topic_run = topic_para.add_run(topic)
        topic_run.font.name = 'Calibri'
        topic_run.font.size = Pt(18) # Reduced for hierarchy
        topic_run.font.bold = False
        topic_run.font.color.rgb = RGBColor(255, 255, 255)
        topic_para.paragraph_format.space_after = Pt(0)
        
        # Fill rest with blue
        for _ in range(10):
            para = doc.add_paragraph()
            self._add_blue_background(para)
        
        # WHITE FOOTER - Logo
        logo_para = doc.add_paragraph()
        self._add_blue_background(logo_para) 
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        
        if os.path.exists(logo_path):
            try:
                run = logo_para.add_run()
                run.add_picture(logo_path, width=Inches(2.5))
            except:
                pass
        logo_para.paragraph_format.space_before = Pt(20)
        
        # === PAGE BREAK ===
        doc.add_page_break()
        
        # === CONTENT PAGES ===
        section = doc.sections[-1]
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
        for i, qa in enumerate(qa_pairs, 1):
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            
            # Question - 11pt bold, justified
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(f"Question {i}: {question}")
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(11) # Reduced from 14
            q_run.font.bold = True
            
            # Formatting
            q_para.paragraph_format.line_spacing = 1.15
            q_para.paragraph_format.space_after = Pt(3)
            q_para.paragraph_format.keep_with_next = True # Keep question with answer
            
            # Answer Paragraph
            ans_para = doc.add_paragraph()
            ans_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # "Answer:" Label
            ans_header_run = ans_para.add_run("Answer: ")
            ans_header_run.font.name = 'Calibri'
            ans_header_run.font.size = Pt(11) # Reduced from 14
            ans_header_run.font.bold = True
            
            # Answer Text
            ans_run = ans_para.add_run(answer)
            ans_run.font.name = 'Calibri'
            ans_run.font.size = Pt(11) # Reduced from 14
            ans_run.font.bold = False
            
            # Spacing
            ans_para.paragraph_format.line_spacing = 1.15
            ans_para.paragraph_format.space_after = Pt(18) # Space between Q&A pairs
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
