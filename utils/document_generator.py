"""Document generators"""

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
        
        # Build complete HTML with proper structure
        html_content = f"""
        <!DOCTYPE html>
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
        </html>
        """
        
        # Generate PDF with base_url for logo loading
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name
        
        try:
            pdf_bytes = HTML(filename=temp_path).write_pdf()
        finally:
            os.unlink(temp_path)
        
        return pdf_bytes


class WordDocumentGenerator:
    def __init__(self):
        self.detector = ImportantWordsDetector()
    
    def _add_cover_page(self, doc: Document, title: str, topic: str, partner_institute: str):
        """Add cover page with blue background simulation and logo"""
        # Add spacing
        for _ in range(8):
            doc.add_paragraph()
        
        # Title in blue (simulating blue background)
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.name = 'Arial'
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(48, 48, 255)  # #3030ff
        
        # Spacing
        for _ in range(2):
            doc.add_paragraph()
        
        # Topic in blue
        topic_para = doc.add_paragraph()
        topic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        topic_run = topic_para.add_run(topic)
        topic_run.font.name = 'Arial'
        topic_run.font.size = Pt(18)
        topic_run.font.bold = True
        topic_run.font.color.rgb = RGBColor(48, 48, 255)
        
        # Spacing before logo
        for _ in range(8):
            doc.add_paragraph()
        
        # Add partner logo
        logo_path = PARTNER_LOGOS.get(partner_institute, PARTNER_LOGOS["Default"])
        
        if os.path.exists(logo_path):
            logo_para = doc.add_paragraph()
            logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            try:
                logo_para.add_run().add_picture(logo_path, width=Inches(5))
            except Exception as e:
                # If logo fails, add text placeholder
                error_run = logo_para.add_run(f"[{partner_institute} Logo]")
                error_run.font.size = Pt(12)
                error_run.font.italic = True
        else:
            # Logo file doesn't exist
            logo_para = doc.add_paragraph()
            logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            placeholder_run = logo_para.add_run(f"[{partner_institute} Logo - File not found]")
            placeholder_run.font.size = Pt(12)
            placeholder_run.font.italic = True
        
        # Page break after cover
        doc.add_page_break()
    
    def _apply_answer_formatting(self, paragraph, answer: str, important_words: List[str]):
        """Apply formatting with important words in blue and bold"""
        if not important_words:
            run = paragraph.add_run(answer)
            run.font.name = 'Calibri'
            run.font.size = Pt(18)
            return
        
        # Sort by length to avoid partial replacements
        sorted_words = sorted(important_words, key=len, reverse=True)
        remaining = answer
        
        for word in sorted_words:
            if not word or not isinstance(word, str):
                continue
            
            if word.lower() in remaining.lower():
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                match = pattern.search(remaining)
                
                if match:
                    # Add text before important word
                    before = remaining[:match.start()]
                    if before:
                        run = paragraph.add_run(before)
                        run.font.name = 'Calibri'
                        run.font.size = Pt(18)
                    
                    # Add important word (bold + blue)
                    important_run = paragraph.add_run(match.group())
                    important_run.font.name = 'Calibri'
                    important_run.font.size = Pt(18)
                    important_run.font.bold = True
                    important_run.font.color.rgb = RGBColor(48, 48, 255)  # #3030ff
                    
                    # Continue with rest
                    remaining = remaining[match.end():]
        
        # Add remaining text
        if remaining:
            run = paragraph.add_run(remaining)
            run.font.name = 'Calibri'
            run.font.size = Pt(18)
    
    def generate(self, qa_pairs: List[Dict], title: str, topic: str, partner_institute: str = "IIT Kanpur") -> bytes:
        """Generate Word document with proper formatting"""
        doc = Document()
        
        # Set document margins (1 inch = 914400 EMU)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Add cover page
        self._add_cover_page(doc, title, topic, partner_institute)
        
        # Detect important words
        important_words_map = self.detector.detect_batch(qa_pairs)
        
        # Add questions and answers
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
            
            # Question text
            q_para = doc.add_paragraph()
            q_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            q_run = q_para.add_run(question)
            q_run.font.name = 'Calibri'
            q_run.font.size = Pt(18)
            q_run.font.bold = True
            q_para.paragraph_format.line_spacing = 1.5
            
            # Type badge
            type_para = doc.add_paragraph()
            type_run = type_para.add_run(f"[{qa_type}]")
            type_run.font.name = 'Calibri'
            type_run.font.size = Pt(14)
            type_run.font.italic = True
            type_run.font.color.rgb = RGBColor(102, 102, 102)
            
            # Answer with important words
            a_para = doc.add_paragraph()
            a_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            a_para.paragraph_format.line_spacing = 1.5
            
            important_words = important_words_map.get(qa_id, [])
            self._apply_answer_formatting(a_para, answer, important_words)
            
            # Spacing between questions
            doc.add_paragraph()
        
        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
