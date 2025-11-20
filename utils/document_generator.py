"""Document generators with WORKING logo embedding"""

from io import BytesIO
from typing import List, Dict
import os
import re
import base64

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except:
    WEASYPRINT_AVAILABLE = False

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

from utils.company_template import PARTNER_LOGOS, ROYAL_BLUE
from utils.important_words_detector import ImportantWordsDetector

def get_cover_html_with_embedded_logo(title: str, topic: str, partner_institute: str) -> str:
    """Generate cover page with BASE64 embedded logo (fixes logo loading)"""
    logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
    
    # Embed logo as base64 to avoid path issues
    logo_data_uri = ""
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                logo_bytes = f.read()
                logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
                logo_data_uri = f"data:image/jpeg;base64,{logo_base64}"
        except Exception as e:
            print(f"Logo loading error: {e}")
            logo_data_uri = ""
    
    return f"""
    <div class="cover-page">
        <div class="cover-main">
            <h1 class="cover-title">{title}</h1>
            <h2 class="cover-topic">{topic}</h2>
        </div>
        <div class="cover-footer">
            {f'<img src="{logo_data_uri}" class="partner-banner" alt="{partner_institute}">' if logo_data_uri else f'<p style="text-align:center;color:#666;">[{partner_institute} Logo]</p>'}
        </div>
    </div>
    <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        .cover-page {{
            height: 297mm;
            width: 210mm;
            display: flex;
            flex-direction: column;
            page-break-after: always;
            margin: 0;
            padding: 0;
        }}
        .cover-main {{
            flex: 1;
            background-color: {ROYAL_BLUE} !important;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #FFFFFF !important;
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 80px 40px;
        }}
        .cover-title {{
            font-size: 18pt !important;
            margin: 0 0 40px 0 !important;
            font-weight: bold;
            color: #FFFFFF !important;
        }}
        .cover-topic {{
            font-size: 18pt !important;
            margin: 40px 0 0 0 !important;
            font-weight: bold;
            color: #FFFFFF !important;
        }}
        .cover-footer {{
            background-color: #FFFFFF !important;
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
            object-fit: contain;
        }}
    </style>
    """

def get_content_styles() -> str:
    """Content page styles"""
    return f"""
    <style>
        @page {{
            size: A4;
            margin: 25mm;
        }}
        body {{
            font-family: Calibri, sans-serif !important;
            font-size: 18pt !important;
            line-height: 1.5;
            color: #000000;
        }}
        .question-block {{
            margin: 35px 0;
            page-break-inside: avoid;
        }}
        .question-number {{
            font-size: 18pt !important;
            font-weight: bold;
            margin-bottom: 12px;
        }}
        .question-text {{
            font-weight: bold;
            text-align: justify;
            font-size: 18pt !important;
            line-height: 1.5;
            margin-bottom: 12px;
        }}
        .answer-text {{
            text-align: justify;
            font-size: 18pt !important;
            line-height: 1.5;
            margin-bottom: 20px;
        }}
        .important {{
            font-weight: bold !important;
            color: {ROYAL_BLUE} !important;
        }}
        .type-badge {{
            font-size: 14pt !important;
            font-style: italic;
            color: #666666;
            margin-bottom: 10px;
        }}
    </style>
    """

class PDFGenerator:
    def __init__(self, title: str, topic: str, partner_institute: str = "IIT Kanpur"):
        self.title = title
        self.topic = topic
        self.partner_institute = partner_institute
        self.detector = ImportantWordsDetector()
    
    def generate(self, qa_pairs: List[Dict]) -> bytes:
        if not WEASYPRINT_AVAILABLE:
            raise Exception("WeasyPrint not available")
        
        important_words_map = self.detector.detect_batch(qa_pairs)
        
        # Build HTML with embedded logo
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.title}</title>
    {get_content_styles()}
</head>
<body>
{get_cover_html_with_embedded_logo(self.title, self.topic, self.partner_institute)}

<div class="content-page">
"""
        
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            qa_id = qa.get('id')
            
            important_words = important_words_map.get(qa_id, [])
            
            # Format answer with important words
            formatted_answer = answer
            if important_words:
                for word in sorted(important_words, key=len, reverse=True):
                    if word:
                        pattern = re.compile(re.escape(word), re.IGNORECASE)
                        formatted_answer = pattern.sub(f'<span class="important">{word}</span>', formatted_answer)
            
            html_content += f"""
<div class="question-block">
    <div class="question-number">Question {i}</div>
    <div class="question-text">{question}</div>
    <div class="type-badge">[{qa_type}]</div>
    <div class="answer-text">{formatted_answer}</div>
</div>
"""
        
        html_content += """
</div>
</body>
</html>"""
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes


class WordDocumentGenerator:
    def __init__(self):
        self.detector = ImportantWordsDetector()
    
    def generate(self, qa_pairs: List[Dict], title: str, topic: str, partner_institute: str = "IIT Kanpur") -> bytes:
        doc = Document()
        
        # Set margins
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
        title_run.font.color.rgb = RGBColor(48, 48, 255)
        
        doc.add_paragraph()
        doc.add_paragraph()
        
        # Topic
        topic_para = doc.add_paragraph()
        topic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        topic_run = topic_para.add_run(topic)
        topic_run.font.name = 'Arial'
        topic_run.font.size = Pt(18)
        topic_run.font.bold = True
        topic_run.font.color.rgb = RGBColor(48, 48, 255)
        
        for _ in range(6):
            doc.add_paragraph()
        
        # Logo - WITH ABSOLUTE PATH
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        absolute_logo_path = os.path.abspath(logo_path)
        
        logo_para = doc.add_paragraph()
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        if os.path.exists(absolute_logo_path):
            try:
                logo_para.add_run().add_picture(absolute_logo_path, width=Inches(5.0))
            except Exception as e:
                error_run = logo_para.add_run(f"[Logo Error: {str(e)}]")
                error_run.font.size = Pt(10)
        else:
            error_run = logo_para.add_run(f"[Logo not found at: {absolute_logo_path}]")
            error_run.font.size = Pt(10)
        
        doc.add_page_break()
        
        # CONTENT
        important_words_map = self.detector.detect_batch(qa_pairs)
        
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            qa_id = qa.get('id')
            
            # Question number
            q_num_para = doc.add_paragraph()
            q_num_run = q_num_para.add_run(f"Question {i}")
            q_num_run.font.name = 'Calibri'
            q_num_run.font.size = Pt(18)
            q_num_run.font.bold = True
            
            # Question
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(question)
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(18)
            q_run.font.bold = True
            q_para.paragraph_format.line_spacing = 1.5
            
            # Type
            type_para = doc.add_paragraph()
            type_run = type_para.add_run(f"[{qa_type}]")
            type_run.font.name = 'Calibri'
            type_run.font.size = Pt(14)
            type_run.font.italic = True
            
            # Answer with important words
            a_para = doc.add_paragraph()
            a_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            a_para.paragraph_format.line_spacing = 1.5
            
            important_words = important_words_map.get(qa_id, [])
            remaining = answer
            
            if important_words:
                for word in sorted(important_words, key=len, reverse=True):
                    if word and word.lower() in remaining.lower():
                        pattern = re.compile(re.escape(word), re.IGNORECASE)
                        match = pattern.search(remaining)
                        
                        if match:
                            if match.start() > 0:
                                run = a_para.add_run(remaining[:match.start()])
                                run.font.name = 'Calibri'
                                run.font.size = Pt(18)
                            
                            imp_run = a_para.add_run(match.group())
                            imp_run.font.name = 'Calibri'
                            imp_run.font.size = Pt(18)
                            imp_run.font.bold = True
                            imp_run.font.color.rgb = RGBColor(48, 48, 255)
                            
                            remaining = remaining[match.end():]
            
            if remaining:
                run = a_para.add_run(remaining)
                run.font.name = 'Calibri'
                run.font.size = Pt(18)
            
            doc.add_paragraph()
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
