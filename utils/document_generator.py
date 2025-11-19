"""Document generators"""

from io import BytesIO
from typing import List, Dict
import os
import base64

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except:
    WEASYPRINT_AVAILABLE = False

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
import re

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
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
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
        
        html_content += "</div></body></html>"
        return HTML(string=html_content).write_pdf()

class WordDocumentGenerator:
    def __init__(self):
        self.detector = ImportantWordsDetector()
    
    def _apply_answer_formatting(self, paragraph, answer: str, important_words: List[str]):
        if not important_words:
            run = paragraph.add_run(answer)
            run.font.name = 'Calibri'
            run.font.size = Pt(18)
            return
        
        remaining = answer
        for word in sorted(important_words, key=len, reverse=True):
            if not word or not isinstance(word, str):
                continue
            if word.lower() in remaining.lower():
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                match = pattern.search(remaining)
                
                if match:
                    before = remaining[:match.start()]
                    if before:
                        run = paragraph.add_run(before)
                        run.font.name = 'Calibri'
                        run.font.size = Pt(18)
                    
                    important_run = paragraph.add_run(match.group())
                    important_run.font.name = 'Calibri'
                    important_run.font.size = Pt(18)
                    important_run.font.bold = True
                    important_run.font.color.rgb = RGBColor(65, 105, 225)
                    
                    remaining = remaining[match.end():]
        
        if remaining:
            run = paragraph.add_run(remaining)
            run.font.name = 'Calibri'
            run.font.size = Pt(18)
    
    def generate(self, qa_pairs: List[Dict], title: str, topic: str, partner_institute: str = "IIT Kanpur") -> bytes:
        doc = Document()
        
        for _ in range(5):
            doc.add_paragraph()
        
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.name = 'Arial'
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        
        doc.add_paragraph()
        
        topic_para = doc.add_paragraph()
        topic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        topic_run = topic_para.add_run(topic)
        topic_run.font.name = 'Arial'
        topic_run.font.size = Pt(18)
        topic_run.font.bold = True
        
        for _ in range(8):
            doc.add_paragraph()
        
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        if os.path.exists(logo_path):
            logo_para = doc.add_paragraph()
            logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            logo_para.add_run().add_picture(logo_path, width=Inches(5))
        
        doc.add_page_break()
        
        important_words_map = self.detector.detect_batch(qa_pairs)
        
        for i, qa in enumerate(qa_pairs, 1):
            qa_type = qa.get('type', 'generic').upper()
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            qa_id = qa.get('id')
            
            q_num_para = doc.add_paragraph()
            q_run = q_num_para.add_run(f"Question {i}")
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(16)
            q_run.font.bold = True
            
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(question)
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(18)
            q_run.font.bold = True
            q_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            
            type_para = doc.add_paragraph()
            type_run = type_para.add_run(f"[{qa_type}]")
            type_run.font.name = 'Calibri'
            type_run.font.size = Pt(12)
            type_run.font.italic = True
            
            a_para = doc.add_paragraph()
            a_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            a_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            
            important_words = important_words_map.get(qa_id, [])
            self._apply_answer_formatting(a_para, answer, important_words)
            
            doc.add_paragraph()
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
