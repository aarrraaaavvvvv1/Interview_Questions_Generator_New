"""Document generators with proper margins, logo loading, and formatting"""

from io import BytesIO
from typing import List, Dict
import os
import re

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except:
    WEASYPRINT_AVAILABLE = False

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

from utils.company_template import get_cover_page_html, get_content_page_styles, format_answer_with_important_words, PARTNER_LOGOS
from utils.important_words_detector import ImportantWordsDetector

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
        
        # Build HTML with proper structure
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.title}</title>
    {get_content_page_styles()}
</head>
<body>
{get_cover_page_html(self.title, self.topic, self.partner_institute)}

<div class="content-page">
"""
        
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            qa_id = qa.get('id')
            
            important_words = important_words_map.get(qa_id, [])
            formatted_answer = format_answer_with_important_words(answer, important_words)
            
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
        
        # Generate PDF - use string directly so base_url resolves relative paths
        pdf_bytes = HTML(string=html_content, base_url=os.getcwd()).write_pdf()
        return pdf_bytes


class WordDocumentGenerator:
    def __init__(self):
        self.detector = ImportantWordsDetector()
    
    def generate(self, qa_pairs: List[Dict], title: str, topic: str, partner_institute: str = "IIT Kanpur") -> bytes:
        doc = Document()
        
        # Set proper margins - 1 inch all sides
        section = doc.sections[0]
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # COVER PAGE
        # Spacing
        for _ in range(6):
            doc.add_paragraph()
        
        # Title - blue bold 18pt
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.name = 'Arial'
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(48, 48, 255)
        
        # Spacing
        doc.add_paragraph()
        doc.add_paragraph()
        
        # Topic - blue bold 18pt
        topic_para = doc.add_paragraph()
        topic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        topic_run = topic_para.add_run(topic)
        topic_run.font.name = 'Arial'
        topic_run.font.size = Pt(18)
        topic_run.font.bold = True
        topic_run.font.color.rgb = RGBColor(48, 48, 255)
        
        # Spacing before logo
        for _ in range(6):
            doc.add_paragraph()
        
        # Logo
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        logo_para = doc.add_paragraph()
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        if os.path.exists(logo_path):
            try:
                logo_para.add_run().add_picture(logo_path, width=Inches(5.0))
            except Exception as e:
                error_run = logo_para.add_run(f"[Logo Error: {str(e)}]")
                error_run.font.size = Pt(10)
                error_run.font.italic = True
        else:
            placeholder_run = logo_para.add_run(f"[Logo not found: {logo_path}]")
            placeholder_run.font.size = Pt(10)
            placeholder_run.font.italic = True
        
        # Page break
        doc.add_page_break()
        
        # CONTENT PAGES
        important_words_map = self.detector.detect_batch(qa_pairs)
        
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            qa_id = qa.get('id')
            
            # Question number - Calibri 18pt bold
            q_num_para = doc.add_paragraph()
            q_num_run = q_num_para.add_run(f"Question {i}")
            q_num_run.font.name = 'Calibri'
            q_num_run.font.size = Pt(18)
            q_num_run.font.bold = True
            
            # Question text - Calibri 18pt bold, justified, 1.5 spacing
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(question)
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(18)
            q_run.font.bold = True
            q_para.paragraph_format.line_spacing = 1.5
            
            # Type badge - Calibri 14pt italic gray
            type_para = doc.add_paragraph()
            type_run = type_para.add_run(f"[{qa_type}]")
            type_run.font.name = 'Calibri'
            type_run.font.size = Pt(14)
            type_run.font.italic = True
            type_run.font.color.rgb = RGBColor(102, 102, 102)
            
            # Answer - Calibri 18pt, justified, 1.5 spacing, important words blue+bold
            a_para = doc.add_paragraph()
            a_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            a_para.paragraph_format.line_spacing = 1.5
            
            important_words = important_words_map.get(qa_id, [])
            
            # Format answer with important words
            if important_words:
                remaining = answer
                for word in sorted(important_words, key=len, reverse=True):
                    if not word:
                        continue
                    if word.lower() in remaining.lower():
                        pattern = re.compile(re.escape(word), re.IGNORECASE)
                        match = pattern.search(remaining)
                        
                        if match:
                            # Text before
                            before = remaining[:match.start()]
                            if before:
                                run = a_para.add_run(before)
                                run.font.name = 'Calibri'
                                run.font.size = Pt(18)
                            
                            # Important word - BLUE + BOLD
                            imp_run = a_para.add_run(match.group())
                            imp_run.font.name = 'Calibri'
                            imp_run.font.size = Pt(18)
                            imp_run.font.bold = True
                            imp_run.font.color.rgb = RGBColor(48, 48, 255)
                            
                            remaining = remaining[match.end():]
                
                # Remaining text
                if remaining:
                    run = a_para.add_run(remaining)
                    run.font.name = 'Calibri'
                    run.font.size = Pt(18)
            else:
                # No important words
                run = a_para.add_run(answer)
                run.font.name = 'Calibri'
                run.font.size = Pt(18)
            
            # Spacing between questions
            doc.add_paragraph()
        
        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
