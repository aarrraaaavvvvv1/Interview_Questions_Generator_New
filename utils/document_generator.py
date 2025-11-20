"""Document generators with proper PDF margins matching sample"""

from io import BytesIO
from typing import List, Dict
import os

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except:
    WEASYPRINT_AVAILABLE = False

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from utils.company_template import PARTNER_LOGO_URLS, PARTNER_LOGOS

def get_cover_page_html(title: str, topic: str, partner_institute: str) -> str:
    logo_url = PARTNER_LOGO_URLS.get(partner_institute, PARTNER_LOGO_URLS["Default"])
    
    return f"""
    <div class="cover-page">
        <div class="cover-main">
            <h1 class="cover-title">{title}</h1>
            <h2 class="cover-topic">{topic}</h2>
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
        /* Cover page - no margins */
        @page cover {{
            size: A4;
            margin: 0;
        }}
        
        /* Content pages - with margins */
        @page content {{
            size: A4;
            margin: 25mm 25mm 25mm 25mm;
        }}
        
        body {{
            margin: 0;
            padding: 0;
            font-family: Calibri, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #000000;
        }}
        
        /* Cover page styling */
        .cover-page {{
            page: cover;
            height: 297mm;
            width: 210mm;
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }}
        
        .cover-main {{
            flex: 1;
            background-color: #3030ff;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #FFFFFF;
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 80px 40px;
        }}
        
        .cover-title {{
            font-size: 18pt;
            margin: 0 0 40px 0;
            font-weight: bold;
            color: #FFFFFF;
        }}
        
        .cover-topic {{
            font-size: 18pt;
            margin: 40px 0 0 0;
            font-weight: bold;
            color: #FFFFFF;
        }}
        
        .cover-footer {{
            background-color: #FFFFFF;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 160px;
        }}
        
        .partner-banner {{
            max-width: 80%;
            max-height: 100px;
            height: auto;
        }}
        
        /* Content pages styling */
        .content-page {{
            page: content;
        }}
        
        .question-block {{
            margin-bottom: 25px;
            page-break-inside: avoid;
        }}
        
        .question-header {{
            font-size: 11pt;
            font-weight: bold;
            margin-bottom: 10px;
            color: #000000;
            font-family: Calibri, sans-serif;
        }}
        
        .answer-header {{
            font-size: 11pt;
            font-weight: bold;
            margin-bottom: 10px;
            margin-top: 10px;
            color: #000000;
            font-family: Calibri, sans-serif;
        }}
        
        .answer-text {{
            font-size: 11pt;
            text-align: justify;
            line-height: 1.5;
            margin-bottom: 15px;
            color: #000000;
            font-family: Calibri, sans-serif;
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
    <div class="answer-header">Answer:</div>
    <div class="answer-text">{answer}</div>
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
    
    def generate(self, qa_pairs: List[Dict], title: str, topic: str, partner_institute: str = "IIT Kanpur") -> bytes:
        doc = Document()
        
        # Set margins - 1 inch all sides
        section = doc.sections[0]
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # COVER PAGE
        for _ in range(6):
            doc.add_paragraph()
        
        # Title
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.name = 'Arial'
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        
        doc.add_paragraph()
        doc.add_paragraph()
        
        # Topic
        topic_para = doc.add_paragraph()
        topic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        topic_run = topic_para.add_run(topic)
        topic_run.font.name = 'Arial'
        topic_run.font.size = Pt(18)
        topic_run.font.bold = True
        
        for _ in range(6):
            doc.add_paragraph()
        
        # Logo
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        logo_para = doc.add_paragraph()
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        if os.path.exists(logo_path):
            try:
                logo_para.add_run().add_picture(logo_path, width=Inches(5.0))
            except:
                pass
        
        doc.add_page_break()
        
        # CONTENT PAGES
        for i, qa in enumerate(qa_pairs, 1):
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            
            # Question header
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            q_run = q_para.add_run(f"Question {i}: {question}")
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(11)
            q_run.font.bold = True
            
            # Empty line
            doc.add_paragraph()
            
            # Answer header
            ans_header_para = doc.add_paragraph()
            ans_header_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            ans_header_run = ans_header_para.add_run("Answer:")
            ans_header_run.font.name = 'Calibri'
            ans_header_run.font.size = Pt(11)
            ans_header_run.font.bold = True
            
            # Empty line
            doc.add_paragraph()
            
            # Answer text
            ans_para = doc.add_paragraph()
            ans_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            ans_run = ans_para.add_run(answer)
            ans_run.font.name = 'Calibri'
            ans_run.font.size = Pt(11)
            ans_para.paragraph_format.line_spacing = 1.5
            
            # Empty line between questions
            doc.add_paragraph()
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
